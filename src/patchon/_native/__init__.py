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
        batch_copy_files,
        batch_restore,
        fast_file_copy,
        scan_python_files,
        calculate_file_hash,
        atomic_write_with_backup,
        restore_from_backup,
        acquire_file_lock,
        release_file_lock,
        is_process_alive,
        cleanup_stale_locks,
        PatchSessionRust as PatchSession,
    )
    NATIVE_BACKEND = "rust"
except ImportError:
    from ._pure import (
        batch_copy_files,
        batch_restore,
        fast_file_copy,
        scan_python_files,
        calculate_file_hash,
        atomic_write_with_backup,
        restore_from_backup,
        acquire_file_lock,
        release_file_lock,
        is_process_alive,
        cleanup_stale_locks,
        PatchSession,
    )
    NATIVE_BACKEND = "pure"

__all__ = [
    "NATIVE_BACKEND",
    "batch_copy_files",
    "batch_restore",
    "fast_file_copy",
    "scan_python_files",
    "calculate_file_hash",
    "atomic_write_with_backup",
    "restore_from_backup",
    "acquire_file_lock",
    "release_file_lock",
    "is_process_alive",
    "cleanup_stale_locks",
    "PatchSession",
]
