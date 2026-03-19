"""Data models for patchon configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PatchConfig:
    """Configuration for a single patch target."""

    package: str
    patch_root: Path
    expected_version: str | None = None

    def __post_init__(self) -> None:
        """Ensure patch_root is a Path object."""
        if isinstance(self.patch_root, str):
            self.patch_root = Path(self.patch_root)


@dataclass
class Config:
    """Main configuration for patchon."""

    patches: list[PatchConfig] = field(default_factory=list)
    verbose: bool = False
    strict: bool = True
    config_path: Path | None = None
    config_source: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary for display."""
        return {
            "config_source": self.config_source,
            "config_path": str(self.config_path) if self.config_path else None,
            "verbose": self.verbose,
            "strict": self.strict,
            "patches": [
                {
                    "package": p.package,
                    "expected_version": p.expected_version,
                    "patch_root": str(p.patch_root),
                }
                for p in self.patches
            ],
        }
