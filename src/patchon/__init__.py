"""Patchon: Run Python scripts with temporary source-file hot patches."""

__version__ = "0.1.0"

# Native backend info
from ._native import NATIVE_BACKEND

# Core components
from .core import PatchSession
from .lock import EnvironmentLock

# Utilities
from .cleanup import cleanup_all, check_status

__all__ = [
    "__version__",
    "NATIVE_BACKEND",
    "PatchSession",
    "EnvironmentLock",
    "cleanup_all",
    "check_status",
]