"""Tests for patchon models."""

from pathlib import Path

from patchon.models import Config, PatchConfig


def test_patch_config():
    """Test PatchConfig creation."""
    pc = PatchConfig(
        package="mypackage",
        patch_root=Path("/tmp/patches"),
        expected_version="1.0.0",
    )
    assert pc.package == "mypackage"
    assert pc.patch_root == Path("/tmp/patches")
    assert pc.expected_version == "1.0.0"


def test_patch_config_post_init():
    """Test PatchConfig string to Path conversion."""
    pc = PatchConfig(
        package="mypackage",
        patch_root="/tmp/patches",  # string
    )
    assert isinstance(pc.patch_root, Path)
    assert pc.patch_root == Path("/tmp/patches")


def test_config():
    """Test Config creation."""
    pc = PatchConfig(package="mypackage", patch_root=Path("/tmp/patches"))
    config = Config(
        patches=[pc],
        verbose=True,
        strict=False,
    )
    assert len(config.patches) == 1
    assert config.verbose is True
    assert config.strict is False


def test_config_to_dict():
    """Test Config to_dict method."""
    pc = PatchConfig(
        package="mypackage",
        patch_root=Path("/tmp/patches"),
        expected_version="1.0.0",
    )
    config = Config(
        patches=[pc],
        verbose=True,
        strict=True,
        config_path=Path("/project/pyproject.toml"),
        config_source="pyproject.toml",
    )

    d = config.to_dict()
    assert d["verbose"] is True
    assert d["strict"] is True
    assert d["config_source"] == "pyproject.toml"
    assert d["config_path"] == "/project/pyproject.toml"
    assert len(d["patches"]) == 1
    assert d["patches"][0]["package"] == "mypackage"
