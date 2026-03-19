"""Tests for config discovery."""

import os
import tempfile
from pathlib import Path

from patchon.discover import discover_config, _find_nearest_pyproject, _find_nearest_yaml
from patchon.discover import _has_patchon_section


def test_find_nearest_pyproject(tmp_path: Path):
    """Test finding pyproject.toml walking up directories."""
    # Create nested structure
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)

    # No pyproject.toml
    result = _find_nearest_pyproject(nested)
    assert result is None

    # Create at root
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("")

    result = _find_nearest_pyproject(nested)
    assert result == pyproject


def test_find_nearest_yaml(tmp_path: Path):
    """Test finding patchon.yaml walking up directories."""
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)

    # Create patchon.yaml at a level up
    yaml_file = tmp_path / "a" / "patchon.yaml"
    yaml_file.write_text("patches: []")

    result = _find_nearest_yaml(nested)
    assert result == yaml_file


def test_find_nearest_yml_also_works(tmp_path: Path):
    """Test that patchon.yml also works."""
    yml_file = tmp_path / "patchon.yml"
    yml_file.write_text("patches: []")

    result = _find_nearest_yaml(tmp_path)
    assert result == yml_file


def test_has_patchon_section(tmp_path: Path):
    """Test detecting [tool.patchon] in pyproject.toml."""
    # Without tool.patchon
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "test"\n')
    assert _has_patchon_section(pyproject) is False

    # With tool.patchon
    pyproject.write_text(
        '[project]\nname = "test"\n\n[tool.patchon]\nverbose = true\n'
    )
    assert _has_patchon_section(pyproject) is True


def test_discover_config_pyproject_priority(tmp_path: Path):
    """Test that pyproject.toml with [tool.patchon] takes priority."""
    # Create both pyproject.toml and patchon.yaml
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "test"\n\n[tool.patchon]\nverbose = true\n'
    )
    yaml_file = tmp_path / "patchon.yaml"
    yaml_file.write_text("verbose: false\n")

    result = discover_config(tmp_path)
    assert result is not None
    assert result[0] == pyproject
    assert result[1] == "pyproject"


def test_discover_config_fallback_to_yaml(tmp_path: Path):
    """Test falling back to patchon.yaml when pyproject has no [tool.patchon]."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "test"\n')
    yaml_file = tmp_path / "patchon.yaml"
    yaml_file.write_text("verbose: false\n")

    result = discover_config(tmp_path)
    assert result is not None
    assert result[0] == yaml_file
    assert result[1] == "yaml"


def test_discover_config_no_config(tmp_path: Path):
    """Test returning None when no config found."""
    nested = tmp_path / "subdir"
    nested.mkdir()

    result = discover_config(nested)
    assert result is None
