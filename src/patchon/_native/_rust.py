"""Rust extension wrapper.

This module wraps the Rust extension and provides:
1. Python-friendly interface
2. Type hints
3. Error conversion
"""

# mypy: ignore-errors
# This module imports from the compiled Rust extension which mypy cannot analyze

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from patchon._native._rust_ext import (
        PatchSessionRust as PatchSession,
    )
    from patchon._native._rust_ext import (
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
else:
    # Import from Rust module (runtime)
    from patchon._native._rust_ext import (  # type: ignore[import-not-found]
        PatchSessionRust as PatchSession,
    )
    from patchon._native._rust_ext import (
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
