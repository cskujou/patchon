# Patchon

[![CI](https://github.com/cskujou/patchon/actions/workflows/ci.yml/badge.svg)](https://github.com/cskujou/patchon/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/patchon)](https://pypi.org/project/patchon/)
[![Python](https://img.shields.io/pypi/pyversions/patchon)](https://pypi.org/project/patchon/)

**Run Python scripts with temporary source-file hot patches applied before execution and restored afterward.**

## What is Patchon?

`patchon` provides a seamless way to apply temporary patches to Python libraries while running scripts. It automatically:

- ✅ Applies patches from your `.py` patch files before running
- ✅ Runs your script normally with patched libraries
- ✅ Automatically restores original files when done
- ✅ Prevents concurrent patching conflicts (process-safe)
- ✅ Recover from crashes with `--cleanup` command

## Quick Example

```bash
# Instead of: python myscript.py
patchon myscript.py
```

That's it! Patches defined in your configuration are automatically applied, your script runs, and files are restored.

## Use Cases

- **Debugging**: Add logging or print statements to library internals
- **Hotfixes**: Apply temporary fixes before official patches are released
- **Testing**: Inject mocks or instrumentation without modifying the library permanently
- **Profiling**: Add performance probes temporarily

## Key Features

| Feature | Description |
|---------|-------------|
| 🚀 Rust-Accelerated | High-performance file operations via optional Rust extension |
| 🔒 Safe | Automatic backups, verification, and guaranteed restoration |
| 🔄 Recovery | `--cleanup` command recovers from SIGKILL or crashes |
| 🔐 Exclusive Locks | Prevents concurrent modification conflicts |
| 📝 Simple Config | pyproject.toml or YAML-based configuration |
| 🧪 Dry Run | Preview changes without applying them |

## Installation

```bash
pip install patchon
```

For development with Rust acceleration:

```bash
pip install patchon[rust]
```

## Next Steps

- [Installation Guide](getting-started/installation.md) - Detailed installation options
- [Quick Start](getting-started/quickstart.md) - Get up and running in 5 minutes
- [Configuration](getting-started/configuration.md) - Learn about configuration options

## License

MIT License - See [License](about/license.md) for details.