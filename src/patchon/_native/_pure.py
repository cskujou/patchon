"""Pure Python fallback implementation.

Provides same interface as Rust extension but with pure Python implementation
for maximum compatibility.
"""

from __future__ import annotations

import fcntl as _fcntl
import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

FCNTL: Any = _fcntl

if TYPE_CHECKING:
    pass


def fast_file_copy(src: str, dst: str) -> None:
    """Copy file with metadata preservation."""
    dst_path = Path(dst)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def batch_copy_files(operations: list[tuple[str, str]]) -> list[str | None]:
    """Execute multiple copy operations."""
    results: list[str | None] = []
    for src, dst in operations:
        try:
            fast_file_copy(src, dst)
            results.append(None)
        except Exception as e:
            results.append(str(e))
    return results


def scan_python_files(dir: str, recursive: bool = True) -> list[str]:
    """Scan directory for Python files."""
    result = []
    path = Path(dir)

    if recursive:
        for py_file in path.rglob("*.py"):
            result.append(str(py_file))
    else:
        for py_file in path.glob("*.py"):
            result.append(str(py_file))

    return result


def calculate_file_hash(path: str) -> int:
    """Calculate file hash for change detection."""
    hasher = hashlib.blake2b(digest_size=8)
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return int.from_bytes(hasher.digest(), "big")


def atomic_write_with_backup(target: str, content: str, backup_dir: str | None = None) -> str | None:
    """Atomically write file with backup creation."""
    target_path = Path(target)
    backup_path = None

    if target_path.exists():
        if backup_dir:
            backup_path = Path(backup_dir) / f"{target_path.name}.{os.getpid()}.backup"
        else:
            backup_path = Path(tempfile.gettempdir()) / f"patchon_backup_{target_path.name}_{os.getpid()}"
        shutil.copy2(target, backup_path)

    # Atomic write
    temp_path = target_path.with_suffix(".tmp")
    temp_path.write_text(content)
    temp_path.rename(target_path)

    return str(backup_path) if backup_path else None


def restore_from_backup(backup_path: str, target: str) -> None:
    """Restore file from backup."""
    shutil.copy2(backup_path, target)


def batch_restore(backups: list[tuple[str, str]]) -> list[str | None]:
    """Execute multiple restore operations."""
    results: list[str | None] = []
    for backup, target in backups:
        try:
            restore_from_backup(backup, target)
            results.append(None)
        except Exception as e:
            results.append(f"Failed to restore {target}: {e}")
    return results


def acquire_file_lock(lock_path: str, timeout_secs: int = 30) -> int:
    """Acquire exclusive file lock."""
    import time

    start = time.time()
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT)

    while time.time() - start < timeout_secs:
        try:
            FCNTL.flock(fd, FCNTL.LOCK_EX | FCNTL.LOCK_NB)
            return fd
        except OSError:
            time.sleep(0.01)

    os.close(fd)
    raise TimeoutError(f"Failed to acquire lock within {timeout_secs}s")


def release_file_lock(fd: int) -> None:
    """Release file lock."""
    FCNTL.flock(fd, FCNTL.LOCK_UN)
    os.close(fd)


def is_process_alive(pid: int) -> bool:
    """Check if process is still running."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def cleanup_stale_locks(lock_dir: str) -> int:
    """Remove stale lock files."""
    cleaned = 0
    lock_path = Path(lock_dir)

    if not lock_path.exists():
        return 0

    for lock_file in lock_path.glob("*.lock"):
        try:
            fd = os.open(lock_file, os.O_RDWR)
            try:
                FCNTL.flock(fd, FCNTL.LOCK_EX | FCNTL.LOCK_NB)
                # If we can acquire the lock, it's stale
                FCNTL.flock(fd, FCNTL.LOCK_UN)
                Path(lock_file).unlink()
                cleaned += 1
            except Exception:
                pass
            finally:
                os.close(fd)
        except Exception:
            pass

    return cleaned


class PatchSession:
    """Pure Python implementation of patch session."""

    def __init__(self) -> None:
        self._applied: dict[str, str] = {}
        self._lock_fd: int | None = None

    def apply_patches(self, patches: list[tuple[str, str]]) -> list[tuple[str, str | None]]:
        """Apply patches and store backups."""
        results = []
        for source, target in patches:
            content = Path(source).read_text()
            backup = atomic_write_with_backup(target, content)
            if backup:
                self._applied[target] = backup
            results.append((target, backup))
        return results

    def restore_all(self) -> list[tuple[str, bool]]:
        """Restore all applied patches."""
        results = []
        for target, backup in self._applied.items():
            try:
                restore_from_backup(backup, target)
                results.append((target, True))
            except Exception:
                results.append((target, False))
        return results

    def patch_count(self) -> int:
        """Get number of applied patches."""
        return len(self._applied)

    def acquire_lock(self, lock_path: str) -> None:
        """Acquire session lock."""
        self._lock_fd = acquire_file_lock(lock_path)

    def release_lock(self) -> None:
        """Release session lock."""
        if self._lock_fd is not None:
            release_file_lock(self._lock_fd)
            self._lock_fd = None


__all__ = [
    "PatchSession",
    "acquire_file_lock",
    "atomic_write_with_backup",
    "batch_copy_files",
    "batch_restore",
    "calculate_file_hash",
    "cleanup_stale_locks",
    "fast_file_copy",
    "is_process_alive",
    "release_file_lock",
    "restore_from_backup",
    "scan_python_files",
]
