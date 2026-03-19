"""Tests for core patching logic."""

import tempfile
from pathlib import Path
import shutil
import sys

from patchon.core import PatchSession
from patchon.models import Config, PatchConfig
from patchon._native import cleanup_stale_locks
import tempfile as _tf


# Clean up stale locks before each test module
def setup_module(module):
    """Clean up any stale locks before running tests."""
    lock_dir = Path(_tf.gettempdir()) / "patchon_locks"
    if lock_dir.exists():
        cleanup_stale_locks(str(lock_dir))


def test_find_package_path_stdlib():
    """Test finding a stdlib package path."""
    config = Config(patches=[])
    session = PatchSession(config)

    # Should find http package
    path = session._find_package_path("http")
    assert path is not None


def test_find_package_path_nonexistent():
    """Test finding non-existent package returns None."""
    config = Config(patches=[])
    session = PatchSession(config)

    path = session._find_package_path("definitely_not_installed_package_xyz")
    assert path is None


def test_check_version_existing_package():
    """Test version check for installed packages."""
    config = Config(patches=[])
    session = PatchSession(config)

    # yaml should be available via pyyaml
    ok = session._check_version("pyyaml", "6.0.1") if session._check_version("yaml", "") else True
    # Just test the method doesn't crash


def test_session_apply_and_restore(tmp_path: Path):
    """Test applying and restoring patches."""
    # Create a mock package structure
    pkg_dir = tmp_path / "mock_pkg"
    pkg_dir.mkdir()
    init_file = pkg_dir / "__init__.py"
    init_file.write_text("ORIGINAL = True\n")

    # Create patch root with modified file
    # patch_root should point to the directory containing the package folder
    patches_dir = tmp_path / "patches"
    patch_dir = patches_dir / "mock_pkg"
    patch_dir.mkdir(parents=True)
    patch_file = patch_dir / "__init__.py"
    patch_file.write_text("ORIGINAL = False\nPATCHED = True\n")

    # Create config - patch_root points to patches/, not patches/mock_pkg/
    # The relative path from patch_root to the .py file should match
    # the relative path from package root to the target file
    patch_config = PatchConfig(
        package="mock_pkg",
        patch_root=patch_dir,  # Point to the package directory
    )
    config = Config(patches=[patch_config])

    session = PatchSession(config)

    # Monkey-patch to return our test directory
    original_find = session._find_package_path
    session._find_package_path = lambda name: pkg_dir

    try:
        # Apply patches
        assert session.apply_all() is True

        # Check file was patched
        content = init_file.read_text()
        assert "PATCHED = True" in content

        # Restore
        session.restore()

        # Check file was restored
        content = init_file.read_text()
        assert content == "ORIGINAL = True\n"
    finally:
        session._find_package_path = original_find
        # Ensure lock is released to prevent interference with other tests
        if session._env_lock:
            session._env_lock.release()


def test_dry_run(tmp_path: Path, caplog):
    """Test dry-run mode doesn't modify files."""
    import logging

    pkg_dir = tmp_path / "mock_pkg"
    pkg_dir.mkdir()
    init_file = pkg_dir / "__init__.py"
    init_file.write_text("ORIGINAL = True\n")

    patch_dir = tmp_path / "patches" / "mock_pkg"
    patch_dir.mkdir(parents=True)
    patch_file = patch_dir / "__init__.py"
    patch_file.write_text("PATCHED = True\n")

    patch_config = PatchConfig(
        package="mock_pkg",
        patch_root=patch_dir,  # Point directly to package dir
    )
    config = Config(patches=[patch_config])

    session = PatchSession(config, dry_run=True)
    session._find_package_path = lambda name: pkg_dir

    try:
        assert session.apply_all() is True

        # File should be unchanged
        content = init_file.read_text()
        assert content == "ORIGINAL = True\n"
    finally:
        # Clean up and release lock even in dry-run mode
        session.restore()
        if session._env_lock:
            session._env_lock.release()


def test_new_file_warning(tmp_path: Path, caplog):
    """Test warning when most patches are new files."""
    import logging

    pkg_dir = tmp_path / "mock_pkg"
    pkg_dir.mkdir()
    # Only one existing file
    (pkg_dir / "__init__.py").write_text("")

    patch_dir = tmp_path / "patches" / "mock_pkg"
    patch_dir.mkdir(parents=True)
    # Create 3 new files (more than 50% if original had 1 file)
    (patch_dir / "__init__.py").write_text("")
    (patch_dir / "new_file1.py").write_text("")
    (patch_dir / "new_file2.py").write_text("")

    patch_config = PatchConfig(package="mock_pkg", patch_root=patch_dir)
    config = Config(patches=[patch_config])

    session = PatchSession(config)
    session._find_package_path = lambda name: pkg_dir

    # Should complete but with warning
    import logging
    try:
        with caplog.at_level(logging.WARNING, logger="patchon"):
            assert session.apply_all() is True
            # Warning about too many new files
            assert "50%" in caplog.text or "new files" in caplog.text
    finally:
        # Clean up resources and release lock
        session.restore()
        if session._env_lock:
            session._env_lock.release()
