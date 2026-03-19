"""Tests for CLI."""

import pytest

from patchon.cli import split_args


def test_split_args_script_only():
    """Test parsing script and args."""
    parsed, python_args = split_args(["script.py", "--foo", "bar"])
    assert parsed.module is None
    assert parsed.command is None
    assert python_args == ["script.py", "--foo", "bar"]


def test_split_args_with_patchon_options():
    """Test parsing with patchon-specific options."""
    parsed, python_args = split_args(["--verbose", "script.py", "--foo", "bar"])
    assert parsed.verbose is True
    assert python_args == ["script.py", "--foo", "bar"]


def test_split_args_module_mode():
    """Test parsing with -m flag."""
    parsed, python_args = split_args(["-m", "http.server", "8000"])
    assert parsed.module == "http.server"
    # python_args should include -m for passing to python subprocess
    assert python_args == ["-m", "http.server", "8000"]


def test_split_args_command_mode():
    """Test parsing with -c flag."""
    parsed, python_args = split_args(["-c", "print('hello')"])
    assert parsed.command == "print('hello')"
    assert python_args == ["-c", "print('hello')"]


def test_split_args_check_flag():
    """Test parsing --check flag."""
    parsed, python_args = split_args(["--check"])
    assert parsed.check is True
    assert python_args == []


def test_split_args_dry_run():
    """Test parsing --dry-run flag."""
    parsed, python_args = split_args(["--dry-run", "script.py"])
    assert parsed.dry_run is True
    assert python_args == ["script.py"]


def test_split_args_complex():
    """Test complex command with mixed options."""
    args = ["--verbose", "--dry-run", "-m", "pytest", "-x", "-v"]
    parsed, python_args = split_args(args)
    assert parsed.verbose is True
    assert parsed.dry_run is True
    assert parsed.module == "pytest"
    # python_args should include -m for the subprocess
    assert python_args == ["-m", "pytest", "-x", "-v"]


def test_split_args_help_only():
    """Test parsing --help without script."""
    parsed, python_args = split_args(["--help"])
    assert parsed.help is True
    assert python_args == []
