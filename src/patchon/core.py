"""Core patching logic: apply, backup, and restore patches."""

from __future__ import annotations

import atexit
import importlib.metadata
import importlib.util
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from ._native import (
    batch_restore,
    fast_file_copy,
)
from .cleanup import PatchState, StateManager, generate_env_id
from .lock import EnvironmentLock

if TYPE_CHECKING:
    from .models import Config, PatchConfig

logger = logging.getLogger("patchon")


class PatchSession:
    """Manages a patching session with automatic restoration."""

    def __init__(self, config: Config, dry_run: bool = False):
        """Initialize patch session.

        Args:
            config: Patch configuration
            dry_run: If True, don't actually apply patches
        """
        self.config = config
        self.dry_run = dry_run
        self.backups: dict[Path, Path] = {}  # original -> backup
        self.patched_files: set[Path] = set()
        self._restored = False
        self._state_manager: StateManager | None = None
        self._env_lock: EnvironmentLock | None = None
        self._state: PatchState | None = None

        # Register cleanup at exit
        atexit.register(self.restore)

    def apply_all(self) -> bool:
        """Apply all patches from configuration.

        Returns:
            True if all patches applied successfully
        """
        # Acquire environment lock to prevent concurrent patching
        self._env_lock = EnvironmentLock(timeout=60.0)

        # Generate environment ID from packages being patched
        packages = [p.package for p in self.config.patches]
        env_id = generate_env_id(packages)

        if not self._env_lock.acquire(env_id):
            logger.error(
                "Failed to acquire environment lock. Another patchon process may be "
                "currently patching the same packages. Wait for it to complete or "
                "run 'patchon --cleanup' if the previous process was terminated."
            )
            return False

        logger.debug(f"Acquired environment lock for: {env_id}")

        # Initialize state manager for crash recovery
        self._state_manager = StateManager()

        success = True
        for patch_config in self.config.patches:
            if not self._apply_patch(patch_config):
                if self.config.strict:
                    logger.error(f"Failed to apply patch for {patch_config.package}")
                    return False
                logger.warning(f"Failed to apply patch for {patch_config.package}, continuing")
                success = False

        # Save initial state for potential cleanup
        self._save_state(env_id)

        return success

    def _save_state(self, env_id: str) -> None:
        """Save current patching state for crash recovery."""
        if self._state_manager is None or self.dry_run:
            return

        config_path_str = str(self.config.config_path) if self.config.config_path else ""

        # Convert Path objects to strings for serialization
        backups = {str(k): str(v) for k, v in self.backups.items()}
        patched = [str(p) for p in self.patched_files]

        self._state = PatchState(
            pid=os.getpid(),
            env_id=env_id,
            backups=backups,
            patched_files=patched,
            config_path=config_path_str,
        )

        self._state_manager.save_state(self._state)
        logger.debug(f"Saved patch state for PID {os.getpid()}")

    def _apply_patch(self, patch_config: PatchConfig) -> bool:
        """Apply a single patch configuration."""
        logger.info(f"Applying patch for package: {patch_config.package}")

        # Find package location
        package_path = self._find_package_path(patch_config.package)
        if not package_path:
            logger.error(f"Cannot find package: {patch_config.package}")
            return False

        logger.debug(f"Package location: {package_path}")

        # Check version if specified
        if patch_config.expected_version and not self._check_version(
            patch_config.package, patch_config.expected_version
        ):
            return False

        # Validate patch root exists
        if not patch_config.patch_root.exists():
            logger.error(f"Patch root does not exist: {patch_config.patch_root}")
            return False

        # Collect patch files
        patch_files = list(patch_config.patch_root.rglob("*.py"))
        if not patch_files:
            logger.warning(f"No .py files found in patch root: {patch_config.patch_root}")
            return True  # Not an error, just nothing to patch

        logger.info(f"Found {len(patch_files)} patch files")

        # Check for too many new files (possible user error)
        new_files = 0
        for patch_file in patch_files:
            rel_path = patch_file.relative_to(patch_config.patch_root)
            target_file = package_path / rel_path
            if not target_file.exists():
                new_files += 1

        if patch_files and new_files > len(patch_files) * 0.5:
            logger.warning(
                f"More than 50% of patch files ({new_files}/{len(patch_files)}) "
                f"are new files not in the original package. "
                f"Is your patch_root configured correctly?"
            )

        # Apply patches
        for patch_file in patch_files:
            rel_path = patch_file.relative_to(patch_config.patch_root)
            target_file = package_path / rel_path

            if not self._apply_single_file(patch_file, target_file, patch_config.package):
                return False

        return True

    def _apply_single_file(self, patch_file: Path, target_file: Path, _package_name: str) -> bool:
        """Apply a single file patch."""
        # Check for duplicate patch
        if target_file in self.patched_files:
            logger.error(f"Attempting to patch the same file twice: {target_file}")
            return False

        if self.dry_run:
            logger.info(f"[DRY-RUN] Would patch: {target_file} <- {patch_file}")
            self.patched_files.add(target_file)
            return True

        # If target doesn't exist, it's a new file - just copy
        if not target_file.exists():
            logger.info(f"Creating new file: {target_file}")
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(patch_file, target_file)
            self.patched_files.add(target_file)
            # No backup needed for new files
            return True

        # Backup original file
        backup = self._create_backup(target_file)
        if backup is None:
            return False

        # Copy patch file
        try:
            shutil.copy2(patch_file, target_file)
            self.patched_files.add(target_file)
            logger.debug(f"Patched: {target_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply patch to {target_file}: {e}")
            # Try to restore from backup immediately
            self._restore_single(target_file, backup)
            return False

    def _create_backup(self, original: Path) -> Path | None:
        """Create a backup of the original file."""
        try:
            backup = Path(tempfile.mktemp(suffix=f".{original.name}.backup"))
            # Use fast copy (Rust-accelerated if available)
            fast_file_copy(str(original), str(backup))
            self.backups[original] = backup
            # Update state after each backup
            if self._state and self._state_manager:
                self._state.backups[str(original)] = str(backup)
                self._state_manager.save_state(self._state)
            logger.debug(f"Created backup: {backup}")
            return backup
        except Exception as e:
            logger.error(f"Failed to create backup for {original}: {e}")
            return None

    def restore(self) -> None:
        """Restore all patched files from backups."""
        if self._restored:
            return

        self._restored = True

        if self.dry_run:
            logger.info("[DRY-RUN] Would restore patched files")
            return

        logger.info("Restoring original files...")

        # Use batch restore for better performance with Rust backend
        if len(self.backups) > 1:
            pairs = [(str(b), str(o)) for o, b in self.backups.items()]
            errors = batch_restore(pairs)
            for (_backup, _original), err in zip(pairs, errors, strict=False):
                if err:
                    logger.warning(f"Batch restore warning: {err}")
        else:
            for original, backup in self.backups.items():
                self._restore_single(original, backup)

        self.backups.clear()
        self.patched_files.clear()

        # Clean up state file
        if self._state_manager and self._state:
            self._state_manager.remove_state(self._state.env_id)

        # Release environment lock
        if self._env_lock:
            self._env_lock.release()

    def _restore_single(self, original: Path, backup: Path) -> None:
        """Restore a single file from backup."""
        try:
            if backup.exists():
                fast_file_copy(str(backup), str(original))
                backup.unlink()
                logger.debug(f"Restored: {original}")
        except Exception as e:
            logger.error(f"Failed to restore {original}: {e}")

    def _find_package_path(self, package_name: str) -> Path | None:
        """Find the filesystem path of an installed package."""
        try:
            spec = importlib.util.find_spec(package_name)
            if spec is None:
                return None

            if spec.origin is None:
                # Could be a namespace package
                if spec.submodule_search_locations:
                    return Path(spec.submodule_search_locations[0])
                return None

            origin = Path(spec.origin)
            if origin.name == "__init__.py":
                # Package directory
                return origin.parent
            # Single-file module
            return origin
        except Exception as e:
            logger.debug(f"Error finding package {package_name}: {e}")
            return None

    def _check_version(self, package_name: str, expected_version: str) -> bool:
        """Check if installed package version matches expected."""
        try:
            installed_version = importlib.metadata.version(package_name)
            if installed_version != expected_version:
                logger.error(
                    f"Version mismatch for {package_name}: expected {expected_version}, found {installed_version}"
                )
                return False
            logger.debug(f"Version check passed: {package_name} == {expected_version}")
            return True
        except importlib.metadata.PackageNotFoundError:
            logger.error(f"Cannot check version: {package_name} not found")
            return False
        except Exception as e:
            logger.error(f"Version check failed for {package_name}: {e}")
            return False

    def check(self) -> bool:
        """Check configuration without applying patches.

        Returns:
            True if all checks pass
        """
        logger.info("Checking configuration...")
        all_ok = True

        for patch_config in self.config.patches:
            logger.info(f"Checking patch for: {patch_config.package}")

            # Check package exists
            package_path = self._find_package_path(patch_config.package)
            if not package_path:
                logger.error(f"  X Package not found: {patch_config.package}")
                all_ok = False
                continue
            logger.info(f"  V Package found at: {package_path}")

            # Check version
            if patch_config.expected_version:
                if self._check_version(patch_config.package, patch_config.expected_version):
                    logger.info(f"  V Version matches: {patch_config.expected_version}")
                else:
                    all_ok = False
            else:
                logger.info("  - No version check configured")

            # Check patch root exists
            if not patch_config.patch_root.exists():
                logger.error(f"  X Patch root not found: {patch_config.patch_root}")
                all_ok = False
                continue
            logger.info(f"  V Patch root found: {patch_config.patch_root}")

            # Check patch files
            patch_files = list(patch_config.patch_root.rglob("*.py"))
            logger.info(f"  - Found {len(patch_files)} patch files")

            # Map each patch file to target
            missing_targets = 0
            for patch_file in patch_files:
                rel_path = patch_file.relative_to(patch_config.patch_root)
                target_file = package_path / rel_path
                if target_file.exists():
                    logger.debug(f"    - {rel_path} -> {target_file}")
                else:
                    logger.debug(f"    - {rel_path} -> NEW FILE at {target_file}")
                    missing_targets += 1

            if patch_files and missing_targets > len(patch_files) * 0.5:
                logger.warning(f"  ! More than 50% of patches are new files ({missing_targets}/{len(patch_files)})")

        return all_ok
