# Patchon

[![CI](https://github.com/cskujou/patchon/actions/workflows/ci.yml/badge.svg)](https://github.com/cskujou/patchon/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/patchon)](https://pypi.org/project/patchon/)
[![Python](https://img.shields.io/pypi/pyversions/patchon)](https://pypi.org/project/patchon/)

`patchon` (pronounced `patch-on`) runs your Python code with temporary source patches applied before execution, then restores the original files afterward.

## What It Does

Use `patchon` when you want to temporarily change installed Python package code without manually editing `site-packages` and then cleaning up later.

Typical use cases:

- Debug a library by adding prints or logging
- Try a local hotfix before an upstream release lands
- Inject instrumentation for profiling or tracing
- Reproduce and test a package-level workaround safely

## Install

```bash
pip install patchon
```

Or install it as a user-facing CLI tool with `uv`:

```bash
uv tool install patchon
```

## Quick Example

```bash
# Instead of: python myscript.py
patchon myscript.py
```

Patches defined in your configuration are applied before the command runs, then restored when the run finishes.

## Key Features

| Feature | Description |
|---------|-------------|
| 🚀 Rust-Accelerated | High-performance file operations via optional Rust extension |
| 🔒 Safe | Automatic backups, verification, and guaranteed restoration |
| 🔄 Recovery | `--cleanup` command recovers from SIGKILL or crashes |
| 🔐 Exclusive Locks | Prevents concurrent modification conflicts |
| 📝 Simple Config | `pyproject.toml` or `patchon.yaml` |
| 🧪 Dry Run | Preview changes without applying them |

## Next Steps

- [Installation Guide](getting-started/installation.md) - Detailed installation options
- [Quick Start](getting-started/quickstart.md) - Get up and running in 5 minutes
- [Configuration](getting-started/configuration.md) - Learn about configuration options

## License

MIT License - See [License](about/license.md) for details.
