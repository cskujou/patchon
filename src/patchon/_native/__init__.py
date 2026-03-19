"""Native code abstraction layer.

This module provides a clean abstraction over native implementations:
- _rust: Rust extension (high performance)
- _pure: Pure Python fallback

Usage:
    from patchon._native import batch_copy_files, PatchSession
"""

from __future__ import annotations

# Try to import Rust extension first
# Fallback to pure Python if not available

try:
    from ._rust import (
        PatchSession,
        acquire_file_lock,
        atomic_write_with_backup,
        batch_copy_files,
        batch_restore,
        calculate_file_hash,
        cleanup_stale_locks,
        fast_file_copy,
        is_process_alive,
        release_file_lock,
        restore_from_backup,
        scan_python_files,
    )

    NATIVE_BACKEND = "rust"
except ImportError:
    from ._pure import (
        PatchSession,
        acquire_file_lock,
        atomic_write_with_backup,
        batch_copy_files,
        batch_restore,
        calculate_file_hash,
        cleanup_stale_locks,
        fast_file_copy,
        is_process_alive,
        release_file_lock,
        restore_from_backup,
        scan_python_files,
    )

    NATIVE_BACKEND = "pure"

__all__ = [
    "NATIVE_BACKEND",
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
