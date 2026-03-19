"""File locking utilities for preventing concurrent patch operations."""
from __future__ import annotations

import atexit
import logging
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from ._native import (
    acquire_file_lock,
    cleanup_stale_locks,
    is_process_alive,
    release_file_lock,
)

if TYPE_CHECKING:
    from typing import Optional

logger = logging.getLogger("patchon")


class EnvironmentLock:
    """Manages filesystem locking for concurrent patch operations.
    
    Uses file-based locking with automatic stale lock cleanup.
    """
    
    def __init__(self, timeout: float = 60.0, lock_dir: Optional[str] = None):
        self.timeout = timeout
        self.lock_dir = Path(lock_dir) if lock_dir else Path(tempfile.gettempdir()) / "patchon_locks"
        self._lock_fd: Optional[int] = None
        self._lock_file: Optional[Path] = None
    
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
            
            self._lock_fd = acquire_file_lock(
                str(self._lock_file),
                timeout_secs=int(self.timeout)
            )
            
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
                    try:
                        self._lock_file.unlink()
                    except OSError:
                        pass
                
                logger.debug("Released environment lock")
            except Exception as e:
                logger.debug(f"Error releasing lock: {e}")
