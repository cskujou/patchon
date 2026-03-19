"""Cleanup utilities for recovering from interrupted patching sessions.

This module handles cleanup of files that weren't restored due to SIGKILL,
power failure, or other unclean shutdowns.
"""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from ._native import is_process_alive

logger = logging.getLogger("patchon")

STATE_FILE_NAME = ".patchon_state.json"
STATE_FILE_VERSION = 1


class PatchState:
    """Tracks the state of an active patching session."""

    def __init__(
        self,
        pid: int,
        env_id: str,
        backups: dict[str, str],
        patched_files: list[str],
        config_path: str,
        timestamp: str | None = None,
    ):
        """Initialize patch state.

        Args:
            pid: Process ID that created the state
            env_id: Environment identifier
            backups: Mapping of original_path -> backup_path
            patched_files: List of patched file paths
            config_path: Path to configuration file
            timestamp: Optional timestamp string
        """
        self.pid = pid
        self.env_id = env_id
        self.backups = backups  # original_path -> backup_path
        self.patched_files = patched_files
        self.config_path = config_path
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self) -> dict[str, object]:
        """Convert state to dictionary."""
        return {
            "version": STATE_FILE_VERSION,
            "pid": self.pid,
            "env_id": self.env_id,
            "backups": self.backups,
            "patched_files": self.patched_files,
            "config_path": self.config_path,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> PatchState:
        """Create PatchState from dictionary."""
        from typing import cast

        return cls(
            pid=cast(int, data["pid"]),
            env_id=cast(str, data["env_id"]),
            backups=cast(dict[str, str], data.get("backups", {})),
            patched_files=cast(list[str], data.get("patched_files", [])),
            config_path=cast(str, data.get("config_path", "")),
            timestamp=cast(str | None, data.get("timestamp")),
        )


class StateManager:
    """Manages persistence of patching state."""

    def __init__(self, state_dir: Path | None = None):
        """Initialize state manager.

        Args:
            state_dir: Directory for storing state files (default: tempdir/patchon_state)
        """
        self.state_dir = state_dir or Path(tempfile.gettempdir()) / "patchon_state"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _get_state_file(self, env_id: str) -> Path:
        """Get state file path for given environment."""
        safe_id = hashlib.sha256(env_id.encode()).hexdigest()[:16]
        return self.state_dir / f"{safe_id}.json"

    def save_state(self, state: PatchState) -> None:
        """Save patching state to disk."""
        state_file = self._get_state_file(state.env_id)
        with state_file.open("w") as f:
            json.dump(state.to_dict(), f, indent=2)
        logger.debug(f"Saved state to {state_file}")

    def load_state(self, env_id: str) -> PatchState | None:
        """Load patching state from disk."""
        state_file = self._get_state_file(env_id)
        if not state_file.exists():
            return None
        try:
            with state_file.open() as f:
                data = json.load(f)
            return PatchState.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load state from {state_file}: {e}")
            return None

    def remove_state(self, env_id: str) -> None:
        """Remove state file for given environment."""
        state_file = self._get_state_file(env_id)
        if state_file.exists():
            state_file.unlink()
            logger.debug(f"Removed state file {state_file}")

    def list_all_states(self) -> list[tuple[str, PatchState]]:
        """List all saved states with their environment IDs."""
        states = []
        for state_file in self.state_dir.glob("*.json"):
            try:
                with state_file.open() as f:
                    data = json.load(f)
                state = PatchState.from_dict(data)
                # Extract env_id from filename
                env_hash = state_file.stem
                states.append((env_hash, state))
            except Exception as e:
                logger.warning(f"Failed to load state file {state_file}: {e}")
        return states


def generate_env_id(patched_packages: list[str]) -> str:
    """Generate unique environment ID from patched packages."""
    # Sort to ensure consistent ID
    packages_str = ",".join(sorted(patched_packages))
    return hashlib.sha256(packages_str.encode()).hexdigest()[:16]


def find_orphaned_backups(
    state_manager: StateManager,
    max_age_hours: int = 24,
) -> list[tuple[Path, Path, PatchState]]:
    """Find backup files from processes that no longer exist.

    Returns list of (original_path, backup_path, state) tuples.
    """
    orphaned = []
    cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

    for _env_id, state in state_manager.list_all_states():
        # Check if process is still alive
        if is_process_alive(state.pid):
            logger.debug(f"Process {state.pid} is still alive, skipping")
            continue

        # Check timestamp for old entries
        try:
            state_time = datetime.fromisoformat(state.timestamp)
            if state_time < cutoff_time:
                logger.warning(f"Found old orphaned state from {state.timestamp}")
        except (ValueError, TypeError):
            pass

        for original, backup in state.backups.items():
            original_path = Path(original)
            backup_path = Path(backup)
            if backup_path.exists():
                orphaned.append((original_path, backup_path, state))

    return orphaned


def restore_from_backup(original: Path, backup: Path) -> bool:
    """Restore original file from backup.

    Returns True if successful.
    """
    try:
        if not backup.exists():
            logger.error(f"Backup file missing: {backup}")
            return False

        # Ensure parent directory exists
        original.parent.mkdir(parents=True, exist_ok=True)

        # Copy backup to original
        shutil.copy2(backup, original)
        logger.info(f"Restored: {original}")

        # Clean up backup
        backup.unlink()
        logger.debug(f"Removed backup: {backup}")

        return True
    except Exception as e:
        logger.error(f"Failed to restore {original} from {backup}: {e}")
        return False


def cleanup_all(
    dry_run: bool = False,
    max_age_hours: int = 24,
    force: bool = False,
) -> tuple[int, int]:
    """Clean up all orphaned patches.

    Args:
        dry_run: If True, only show what would be done
        max_age_hours: Only consider backups older than this
        force: Restore even if process might be alive (use with caution)

    Returns:
        Tuple of (restored_count, failed_count)
    """
    state_manager = StateManager()

    orphaned: list[tuple[Path, Path, PatchState]]
    if force:
        # In force mode, don't filter by process alive check
        orphaned = []
        for _env_id, state in state_manager.list_all_states():
            for original_str, backup_str in state.backups.items():
                original_path = Path(original_str)
                backup_path = Path(backup_str)
                if backup_path.exists():
                    orphaned.append((original_path, backup_path, state))
    else:
        orphaned = find_orphaned_backups(state_manager, max_age_hours)

    if not orphaned:
        logger.info("No orphaned backups found")
        return (0, 0)

    restored = 0
    failed = 0

    # Group by state file for cleanup
    processed_states: set[str] = set()

    for original, backup, state in orphaned:
        if dry_run:
            logger.info(f"[DRY-RUN] Would restore: {original} <- {backup}")
            continue

        if restore_from_backup(original, backup):
            restored += 1
            processed_states.add(state.env_id)
        else:
            failed += 1

    # Clean up state files for fully processed entries
    for env_id in processed_states:
        state_manager.remove_state(env_id)

    # Clean up any leftover state files that no longer have valid backups
    _clean_stale_states(state_manager)

    return (restored, failed)


def _clean_stale_states(state_manager: StateManager) -> None:
    """Remove state files that have no remaining backups."""
    for env_id, state in state_manager.list_all_states():
        has_valid_backup = False
        for backup in state.backups.values():
            if Path(backup).exists():
                has_valid_backup = True
                break

        if not has_valid_backup:
            state_manager.remove_state(env_id)
            logger.debug(f"Cleaned up stale state for {env_id}")


def check_status() -> dict[str, object]:
    """Check current cleanup status and return diagnostic info."""
    state_manager = StateManager()
    states = state_manager.list_all_states()

    active_processes = 0
    orphaned_processes = 0
    total_backups = 0
    orphaned_backups = 0

    for _env_id, state in states:
        is_alive = is_process_alive(state.pid)
        if is_alive:
            active_processes += 1
        else:
            orphaned_processes += 1

        for backup in state.backups.values():
            total_backups += 1
            if Path(backup).exists() and not is_alive:
                orphaned_backups += 1

    return {
        "active_sessions": active_processes,
        "orphaned_sessions": orphaned_processes,
        "total_backups_tracked": total_backups,
        "orphaned_backups": orphaned_backups,
        "cleanup_needed": orphaned_backups > 0,
    }


def format_status(status: dict[str, object]) -> str:
    """Format status dict into human-readable string."""
    lines = [
        "Patchon Cleanup Status:",
        f"  Active patching sessions: {status['active_sessions']}",
        f"  Orphaned sessions: {status['orphaned_sessions']}",
        f"  Total backups tracked: {status['total_backups_tracked']}",
        f"  Orphaned backups: {status['orphaned_backups']}",
    ]

    if status["cleanup_needed"]:
        lines.append("\n  ⚠️  Cleanup is needed - run 'patchon --cleanup'")
    else:
        lines.append("\n  ✓  No cleanup needed")

    return "\n".join(lines)
