"""Tests for config parsing."""

from pathlib import Path

import yaml

from patchon.config import load_config


def test_load_pyproject(tmp_path: Path):
    """Test loading config from pyproject.toml."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "test"

[tool.patchon]
verbose = true
strict = false

[[tool.patchon.patches]]
package = "mypackage"
expected_version = "1.0.0"
patch_root = "./patches/mypackage"

[[tool.patchon.patches]]
package = "otherpackage"
patch_root = "./patches/other"
"""
    )

    config = load_config(pyproject, "pyproject")

    assert config.verbose is True
    assert config.strict is False
    assert len(config.patches) == 2
    assert config.patches[0].package == "mypackage"
    assert config.patches[0].expected_version == "1.0.0"
    # patch_root should be resolved relative to config location
    assert "patches/mypackage" in str(config.patches[0].patch_root)


def test_load_yaml(tmp_path: Path):
    """Test loading config from patchon.yaml."""
    yaml_file = tmp_path / "patchon.yaml"
    config_data = {
        "verbose": False,
        "strict": True,
        "patches": [
            {
                "package": "testpkg",
                "expected_version": "2.0.0",
                "patch_root": "./mypatches",
            }
        ],
    }
    yaml_file.write_text(yaml.dump(config_data))

    config = load_config(yaml_file, "yaml")

    assert config.verbose is False
    assert config.strict is True
    assert len(config.patches) == 1
    assert config.patches[0].package == "testpkg"
    assert config.patches[0].expected_version == "2.0.0"


def test_empty_patches(tmp_path: Path):
    """Test loading config with no patches."""
    yaml_file = tmp_path / "patchon.yaml"
    yaml_file.write_text("verbose: true\n")

    config = load_config(yaml_file, "yaml")

    assert config.verbose is True
    assert len(config.patches) == 0


def test_defaults(tmp_path: Path):
    """Test default values."""
    yaml_file = tmp_path / "patchon.yaml"
    yaml_file.write_text("patches: []\n")

    config = load_config(yaml_file, "yaml")

    assert config.verbose is False  # default
    assert config.strict is True  # default
