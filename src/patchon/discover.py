"""Configuration discovery logic."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("patchon")

CONFIG_FILENAMES = ["pyproject.toml", "patchon.yaml", "patchon.yml"]


def discover_config(start_dir: Path | None = None) -> tuple[Path, str] | None:
    """Discover configuration file by walking up from start_dir.

    Priority:
    1. Find the nearest pyproject.toml with [tool.patchon] section
    2. Or find the nearest patchon.yaml/patchon.yml

    Returns:
        Tuple of (config_path, source_type) where source_type is "pyproject" or "yaml"
        None if no config found
    """
    if start_dir is None:
        start_dir = Path.cwd()

    current = start_dir.resolve()

    # First pass: find pyproject.toml with [tool.patchon]
    pyproject_path = _find_nearest_pyproject(current)
    if pyproject_path and _has_patchon_section(pyproject_path):
        logger.debug(f"Found pyproject.toml with [tool.patchon]: {pyproject_path}")
        return (pyproject_path, "pyproject")

    # Second pass: find patchon.yaml
    yaml_path = _find_nearest_yaml(current)
    if yaml_path:
        logger.debug(f"Found patchon.yaml: {yaml_path}")
        return (yaml_path, "yaml")

    # No config found
    return None


def _find_nearest_pyproject(start_dir: Path) -> Path | None:
    """Find the nearest pyproject.toml by walking up."""
    current = start_dir
    while True:
        pyproject = current / "pyproject.toml"
        if pyproject.exists():
            return pyproject

        parent = current.parent
        if parent == current:  # Reached root
            break
        current = parent
    return None


def _find_nearest_yaml(start_dir: Path) -> Path | None:
    """Find the nearest patchon.yaml by walking up."""
    current = start_dir
    while True:
        for name in ["patchon.yaml", "patchon.yml"]:
            yaml_file = current / name
            if yaml_file.exists():
                return yaml_file

        parent = current.parent
        if parent == current:  # Reached root
            break
        current = parent
    return None


def _has_patchon_section(pyproject_path: Path) -> bool:
    """Check if pyproject.toml contains [tool.patchon] section."""
    try:
        import tomllib

        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)

        return "tool" in data and "patchon" in data["tool"]
    except Exception:
        return False
