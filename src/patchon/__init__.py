"""Patchon: Run Python scripts with temporary source-file hot patches."""

__version__ = "0.1.0"

# Native backend info
from ._native import NATIVE_BACKEND

# Utilities
from .cleanup import check_status, cleanup_all

# Core components
from .core import PatchSession
from .lock import EnvironmentLock

__all__ = [
    "NATIVE_BACKEND",
    "EnvironmentLock",
    "PatchSession",
    "__version__",
    "check_status",
    "cleanup_all",
]
