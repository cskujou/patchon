"""File locking utilities for preventing concurrent patch operations."""

from __future__ import annotations

import atexit
import contextlib
import logging
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from ._native import (
    acquire_file_lock,
    cleanup_stale_locks,
    release_file_lock,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger("patchon")


class EnvironmentLock:
    """Manages filesystem locking for concurrent patch operations.

    Uses file-based locking with automatic stale lock cleanup.
    """

    def __init__(self, timeout: float = 60.0, lock_dir: str | None = None):
        """Initialize environment lock.

        Args:
            timeout: Lock acquisition timeout in seconds
            lock_dir: Directory for lock files (None for default temp dir)
        """
        self.timeout = timeout
        self.lock_dir = Path(lock_dir) if lock_dir else Path(tempfile.gettempdir()) / "patchon_locks"
        self._lock_fd: int | None = None
        self._lock_file: Path | None = None

    def acquire(self, env_id: str) -> bool:
        """Acquire lock for environment.

        Args:
            env_id: Environment identifier (typically package names hash)

        Returns:
            True if lock acquired
        """
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self._lock_file = self.lock_dir / f"{env_id}.lock"

        try:
            # Clean up stale locks first
            cleanup_stale_locks(str(self.lock_dir))

            self._lock_fd = acquire_file_lock(str(self._lock_file), timeout_secs=int(self.timeout))

            # Register cleanup on exit
            atexit.register(self.release)
            return True

        except TimeoutError:
            logger.error(f"Failed to acquire lock within {self.timeout}s")
            return False
        except Exception as e:
            logger.error(f"Failed to acquire lock: {e}")
            return False

    def release(self) -> None:
        """Release the lock."""
        if self._lock_fd is not None:
            try:
                release_file_lock(self._lock_fd)
                self._lock_fd = None

                # Remove lock file
                if self._lock_file and self._lock_file.exists():
                    with contextlib.suppress(OSError):
                        self._lock_file.unlink()

                logger.debug("Released environment lock")
            except Exception as e:
                logger.debug(f"Error releasing lock: {e}")
