# Installation

## Requirements

- Python 3.11 or higher
- For Rust extension: Rust toolchain (optional but recommended)

## Quick Try (No Installation)

The fastest way to try `patchon` without installing is using `uvx`:

```bash
# Run patchon directly from PyPI
uvx patchon --version

# Patch and run a script
uvx patchon your_script.py

# Or with a module
uvx patchon -m http.server 8000
```

`uvx` downloads and runs the tool in a temporary environment, no permanent installation required.

## Standard Installation

Install from PyPI as a project dependency:

```bash
# Using uv (recommended)
uv add --dev patchon

# Or using pip
pip install patchon
```

## Install as a Tool

Install `patchon` globally using uv's tool system:

```bash
# Install to uv's tool directory
uv tool install patchon

# Now you can run patchon from anywhere
patchon --help
patchon your_script.py

# Update to latest version
uv tool upgrade patchon

# Uninstall when done
uv tool uninstall patchon
```

## Installation with Rust Extensions

For maximum performance, install with the Rust-accelerated extensions:

```bash
pip install "patchon[rust]"
```

This enables:

- Faster file copy operations (using optimized buffers)
- Faster directory scanning
- More efficient file locking

!!! note "Rust Toolchain Required"
    Installing with Rust extensions requires a working Rust toolchain.
    On Windows, prefer the GNU toolchain (`x86_64-pc-windows-gnu`) so no separate Windows SDK or MSVC installation is needed.

## Development Installation

Clone the repository and install in development mode:

```bash
git clone https://github.com/cskujou/patchon.git
cd patchon

# With uv (recommended)
uv sync
uv run maturin develop --release

# Or with pip
pip install -e ".[dev]"
maturin develop --release
```

On Windows, install the GNU Rust toolchain and linker first:

```bash
scoop install rustup-gnu mingw-winlibs-llvm-ucrt
```

## Verify Installation

Check that patchon is installed correctly:

```bash
patchon --version
```

You should see something like:

```
patchon 0.1.0
```

To check if Rust extensions are available:

```bash
python -c "from patchon._rust_ext import _RUST_AVAILABLE; print(f'Rust available: {_RUST_AVAILABLE}')"
```

## Next Steps

- [Quick Start Guide](quickstart.md) - Get up and running
- [Configuration](configuration.md) - Configure your patches
