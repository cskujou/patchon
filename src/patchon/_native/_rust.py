"""Rust extension wrapper.

This module wraps the Rust extension and provides:
1. Python-friendly interface
2. Type hints
3. Error conversion
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from patchon_rust import (
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

# Import from Rust module
from patchon_rust import (
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

__all__ = [
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
