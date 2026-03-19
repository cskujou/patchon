"""Configuration parsing for pyproject.toml and patchon.yaml."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from .models import Config, PatchConfig

logger = logging.getLogger("patchon")


def load_config(config_path: Path, source_type: str) -> Config:
    """Load configuration from file.

    Args:
        config_path: Path to configuration file
        source_type: "pyproject" or "yaml"

    Returns:
        Parsed Config object
    """
    if source_type == "pyproject":
        return _load_pyproject(config_path)
    elif source_type in ("yaml", "yml"):
        return _load_yaml(config_path)
    else:
        raise ValueError(f"Unknown config source type: {source_type}")


def _load_pyproject(config_path: Path) -> Config:
    """Load configuration from pyproject.toml."""
    import tomllib

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    patchon_data = data.get("tool", {}).get("patchon", {})

    return _parse_config_data(
        patchon_data, config_path, "pyproject.toml", config_path.parent
    )


def _load_yaml(config_path: Path) -> Config:
    """Load configuration from patchon.yaml."""
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return _parse_config_data(
        data, config_path, "patchon.yaml", config_path.parent
    )


def _parse_config_data(
    data: dict[str, Any],
    config_path: Path,
    source_name: str,
    base_dir: Path,
) -> Config:
    """Parse configuration data into Config object."""
    patches_data = data.get("patches", [])
    patches: list[PatchConfig] = []

    for patch_data in patches_data:
        patch_root = patch_data.get("patch_root", "")
        # patch_root is relative to config file location
        patch_root_path = base_dir / patch_root

        patches.append(
            PatchConfig(
                package=patch_data["package"],
                patch_root=patch_root_path.resolve(),
                expected_version=patch_data.get("expected_version"),
            )
        )

    config = Config(
        patches=patches,
        verbose=data.get("verbose", False),
        strict=data.get("strict", True),
        config_path=config_path.resolve(),
        config_source=source_name,
    )

    return config
