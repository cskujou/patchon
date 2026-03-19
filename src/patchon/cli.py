"""Command-line interface for patchon."""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from . import __version__
from .cleanup import cleanup_all, check_status, format_status
from .config import load_config
from .core import PatchSession
from .discover import discover_config

logger = logging.getLogger("patchon")


def setup_logging(verbose: bool, quiet: bool = False) -> None:
    """Configure logging level."""
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format="%(message)s",
        stream=sys.stderr,
    )


def parse_args(args: Sequence[str] | None = None) -> tuple[argparse.Namespace, list[str]]:
    """Parse command line arguments.

    Returns:
        Tuple of (patchon_args, python_args)
    """
    parser = argparse.ArgumentParser(
        prog="patchon",
        description="Run Python scripts with temporary source-file hot patches.",
        add_help=False,  # We'll handle help ourselves
    )

    # patchon-specific options
    parser.add_argument(
        "-h", "--help",
        action="store_true",
        help="Show this help message and exit"
    )
    parser.add_argument(
        "-V", "--version",
        action="store_true",
        help="Show version and exit"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check configuration without running"
    )
    parser.add_argument(
        "--print-config",
        action="store_true",
        help="Print configuration and exit"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be patched without applying"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Recover files left in patched state due to crash or SIGKILL"
    )
    parser.add_argument(
        "--cleanup-status",
        action="store_true",
        help="Show status of orphaned patches and cleanup needs"
    )
    parser.add_argument(
        "--cleanup-force",
        action="store_true",
        help="Force cleanup even if process may still be alive (use with caution)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress non-error output"
    )

    # Python-specific flags we need to recognize
    parser.add_argument(
        "-m",
        dest="module",
        help="Run library module as a script"
    )
    parser.add_argument(
        "-c",
        dest="command",
        help="Program passed in as string"
    )

    # Collect known args and remaining
    parsed, remaining = parser.parse_known_args(args)
    return parsed, remaining


def split_args(args: Sequence[str] | None) -> tuple[argparse.Namespace, list[str]]:
    """Split args into patchon args and python args.

    We need to handle: patchon [patchon-opts] [script-or-module] [script-args]

    Strategy:
    1. Parse known patchon options
    2. Everything after first python-specific arg (-m/-c) goes to python
    3. But still parse -m/-c values from the python_args for patchon's use
    """
    if args is None:
        args = sys.argv[1:]

    patchon_opts = []
    python_args = []

    # Known patchon-only flags (not -m/-c)
    patchon_flags = {"-h", "--help", "-V", "--version", "--check", "--print-config",
                     "--dry-run", "-v", "--verbose", "-q", "--quiet"}

    # Python flags that change execution mode
    mode_flags = {"-m", "-c"}

    i = 0
    found_python_mode = False
    while i < len(args):
        arg = args[i]

        if found_python_mode:
            # Everything after finding -m/-c (and its value) goes to python args
            python_args = args[i:]
            break

        if arg in patchon_flags:
            patchon_opts.append(arg)
            i += 1
        elif arg in mode_flags:
            # Found a mode flag (-m or -c)
            # The flag and its value ARE part of python args,
            # but we also want to capture it for patchon's use
            if i + 1 < len(args):
                python_args = args[i:]
                # Also add to patchon_opts so parse_args can set module/command
                patchon_opts.extend([arg, args[i + 1]])
                break
            else:
                # No value provided, add flag only
                python_args = args[i:]
                patchon_opts.append(arg)
                break
        elif arg.startswith("-"):
            # Unknown flag - check if it takes a value
            if i + 1 < len(args) and not args[i + 1].startswith("-"):
                patchon_opts.append(arg)
                i += 1
            else:
                # Unknown flag, treat as start of python args
                python_args = args[i:]
                break
        else:
            # First non-option arg and everything after goes to python
            python_args = args[i:]
            break

    parsed, _ = parse_args(patchon_opts)
    return parsed, python_args


def print_help() -> None:
    """Print help message."""
    help_text = f"""patchon {__version__}

Run Python scripts with temporary source-file hot patches.

Usage:
  patchon [patchon-options] script.py [script-args...]
  patchon [patchon-options] -m module [script-args...]
  patchon [patchon-options] -c "command"

Patchon Options:
  -h, --help           Show this help message and exit
  -V, --version        Show version and exit
  --check              Check configuration without running
  --print-config       Print configuration and exit
  --dry-run            Show what would be patched without applying
  --cleanup            Recover files left in patched state due to crash/SIGKILL
  --cleanup-status     Show status of orphaned patches
  --cleanup-force      Force cleanup even if process may still be alive
  -v, --verbose        Enable verbose output
  -q, --quiet          Suppress non-error output

Python Options (forwarded to Python interpreter):
  -m module         Run library module as a script
  -c command        Program passed in as string

Examples:
  patchon myscript.py
  patchon myscript.py --port 8000
  patchon -m http.server 8000
  patchon -c "print('hello')"
  patchon --check
  patchon --print-config
  patchon --cleanup-status
  patchon --cleanup

Configuration:
  Configuration is auto-discovered from current directory upward:
  1. pyproject.toml with [tool.patchon] section
  2. patchon.yaml file

See https://github.com/cskujou/patchon for more information.
"""
    print(help_text)


def main(args: Sequence[str] | None = None) -> int:
    """Main entry point."""
    parsed, python_args = split_args(args)

    # Handle simple options first
    if parsed.help:
        print_help()
        return 0

    if parsed.version:
        print(f"patchon {__version__}")
        return 0

    setup_logging(parsed.verbose or False, parsed.quiet or False)

    # Handle cleanup commands (don't require config)
    if parsed.cleanup_status:
        status = check_status()
        print(format_status(status))
        return 0

    if parsed.cleanup:
        restored, failed = cleanup_all(
            dry_run=parsed.dry_run or False,
            force=parsed.cleanup_force or False,
        )
        if failed == 0:
            logger.info(f"Cleanup complete: {restored} file(s) restored")
            return 0
        else:
            logger.error(f"Cleanup completed with errors: {restored} restored, {failed} failed")
            return 1

    # Discover and load configuration
    discovered = discover_config()
    if discovered is None:
        logger.error("No configuration found.")
        logger.error("Looked for pyproject.toml with [tool.patchon] or patchon.yaml")
        logger.error("Starting from current directory: %s", Path.cwd())
        logger.error("")
        logger.error("Example pyproject.toml:")
        logger.error('  [tool.patchon]')
        logger.error('  verbose = true')
        logger.error('  [[tool.patchon.patches]]')
        logger.error('  package = "mypackage"')
        logger.error('  expected_version = "1.0.0"')
        logger.error('  patch_root = "./patches/mypackage"')
        logger.error("")
        logger.error("Example patchon.yaml:")
        logger.error("  verbose: true")
        logger.error("  patches:")
        logger.error('    - package: mypackage')
        logger.error('      expected_version: "1.0.0"')
        logger.error('      patch_root: "./patches/mypackage"')
        return 1

    config_path, source_type = discovered
    config = load_config(config_path, source_type)

    # Override verbose if specified on command line
    if parsed.verbose:
        config.verbose = True

    # Handle config-only commands
    if parsed.print_config:
        print(json.dumps(config.to_dict(), indent=2))
        return 0

    if parsed.check:
        session = PatchSession(config, dry_run=False)
        ok = session.check()
        return 0 if ok else 1

    # Determine execution mode
    if parsed.module:
        # Module mode: patchon -m module args...
        exec_mode = "module"
        exec_target = parsed.module
    elif parsed.command:
        # Command mode: patchon -c "command"
        exec_mode = "command"
        exec_target = parsed.command
    elif python_args:
        # Script mode: patchon script.py args...
        if python_args[0].endswith(".py") or Path(python_args[0]).exists():
            exec_mode = "script"
            exec_target = python_args[0]
        else:
            # Unknown, just pass through to python
            exec_mode = "passthrough"
            exec_target = None
    else:
        logger.error("No script, module, or command specified.")
        print_help()
        return 1

    # Create patch session
    session = PatchSession(config, dry_run=parsed.dry_run or False)

    # Apply patches
    if not session.apply_all():
        logger.error("Failed to apply patches")
        return 1

    if parsed.dry_run:
        logger.info("Dry run complete. No changes made.")
        return 0

    # Build python command line
    python_cmd = [sys.executable]

    if exec_mode == "module":
        python_cmd.extend(["-m", exec_target])
        python_cmd.extend(python_args[1:] if len(python_args) > 1 else [])
    elif exec_mode == "command":
        python_cmd.extend(["-c", exec_target])
    elif exec_mode == "script":
        python_cmd.extend(python_args)
    else:
        python_cmd.extend(python_args)

    # Run the actual python process
    logger.debug(f"Running: {' '.join(python_cmd)}")
    exit_code = 0
    try:
        result = subprocess.run(python_cmd)
        exit_code = result.returncode
    except KeyboardInterrupt:
        logger.debug("Interrupted by user")
        exit_code = 130
    except Exception as e:
        logger.error(f"Failed to execute: {e}")
        exit_code = 1
    finally:
        # Restore patches
        session.restore()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
