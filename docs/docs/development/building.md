# Building from Source

This guide explains how to build `patchon` from source using **uv** as the primary development tool, with optional Rust extensions for improved performance.

> **Note**: This project uses [uv](https://docs.astral.sh/uv/) as the main development and build tool, which provides a modern Python workflow with fast dependency management and building capabilities.

## Prerequisites

### Required

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python development tool)

### Optional (for Rust extension)

- Rust toolchain (latest stable)
- cargo (comes with Rust)
- On Windows: GNU toolchain support via `rustup-gnu` and `mingw-winlibs-llvm-ucrt`

## Setup

### 1. Install uv

If you haven't installed uv yet:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone the Repository

```bash
git clone https://github.com/cskujou/patchon.git
cd patchon
```

### 3. Sync Dependencies

```bash
# Sync project dependencies (creates virtual environment automatically)
uv sync

# For development with all dev dependencies
uv sync --group dev
```

## Installation Options

### Pure Python (Default)

The simplest approach without Rust extensions:

```bash
# Install in editable mode
uv pip install -e .

# Or install from PyPI
uv add patchon
```

### With Rust Extension (Recommended for Performance)

For optimal performance, build with the Rust extension:

```bash
# Windows (recommended)
scoop install rustup-gnu mingw-winlibs-llvm-ucrt

# macOS/Linux
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Build and install with Rust extension using maturin
uv run maturin develop --release
```

On Windows, `patchon` targets `x86_64-pc-windows-gnu` for local development. This avoids requiring MSVC Build Tools or the Windows SDK.

## uv Workflow Commands

uv provides a streamlined workflow for Python projects. Here are the common commands:

### Development Commands

```bash
# Run Python commands within the project environment
uv run python --version

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=patchon --cov-report=html

# Run linter
uv run ruff check src/patchon tests

# Run formatter
uv run ruff format src/patchon tests

# Type checking
uv run mypy src/patchon

# Run the CLI
uv run patchon --help
```

### Building

```bash
# Build wheel and sdist (default)
uv build

# Build only wheel
uv build --wheel

# Build only sdist
uv build --sdist

# Build with Rust extension (requires maturin)
uv run maturin build --release
```

The build artifacts are placed in `dist/`.

### Installing Locally

```bash
# Install from local build
uv pip install dist/patchon-0.1.0-py3-none-any.whl

# Or install in editable mode for development
uv pip install -e .
```

### Publishing

```bash
# Build and publish to PyPI
uv publish

# Or publish to Test PyPI first
uv publish --index testpypi
```

## Project Structure

```
patchon/
├── pyproject.toml              # Project configuration (PEP 621)
├── README.md                   # English documentation
├── README_zh.md               # Chinese documentation
├── LICENSE                     # MIT License
├── patchon.yaml.example        # Example configuration
├── src/
│   ├── patchon/               # Main Python package
│   │   ├── __init__.py
│   │   ├── __main__.py        # python -m patchon entry
│   │   ├── cli.py             # CLI implementation
│   │   ├── core.py            # PatchSession core logic
│   │   ├── models.py          # Data models
│   │   ├── config.py          # Configuration parsing
│   │   ├── discover.py        # Config auto-discovery
│   │   ├── cleanup.py         # Crash recovery
│   └── patchon/
│       ├── _native/           # Python/native abstraction layer
│       └── ...
├── rust/                      # Rust extension crate
│   ├── Cargo.toml             # Rust package manifest
│   └── src/
│       └── lib.rs             # Rust source code
├── tests/                      # Test suite
│   ├── test_cli.py
│   ├── test_core.py
│   ├── test_config.py
│   ├── test_discover.py
│   └── test_models.py
└── docs/                       # Documentation (MkDocs)
    ├── mkdocs.yml
    └── docs/
```

## Troubleshooting

### Rust Extension Build Fails

**Error**: `cargo not found`

```bash
# Windows
scoop install rustup-gnu mingw-winlibs-llvm-ucrt

# macOS/Linux
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

**Error**: `linker 'cc' not found` (Linux)

```bash
# Install build essentials
sudo apt-get install build-essential  # Debian/Ubuntu
sudo yum groupinstall "Development Tools"  # RHEL/CentOS
```

### Python Module Not Found

```bash
# Ensure dependencies are synced
uv sync

# Check Python path
uv run python -c "import patchon; print(patchon.__file__)"
```

### uv Permission Issues

uv handles permissions automatically by using virtual environments. If you see permission errors:

```bash
# uv creates .venv automatically - use it
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\activate  # Windows

# Then run with uv
uv run patchon --help
```

## Development Workflow

### Day-to-Day Development

```bash
# 1. Make changes to source files
# 2. Run tests
uv run pytest

# 3. Run linting
uv run ruff check src tests

# 4. Fix any issues
uv run ruff check --fix src tests

# 5. Run the tool
uv run patchon --help

# 6. Test with a script
uv run patchon demo.py
```

### Working with Rust Code

```bash
# After modifying Rust source
uv run maturin develop

# For optimized build
uv run maturin develop --release

# Test the changes
uv run patchon --version
```

On Windows, make sure the active Rust toolchain is GNU:

```bash
rustup show
```

You should see `x86_64-pc-windows-gnu` as the active default toolchain.

### Release Process

1. Update version in `src/patchon/__init__.py`
2. Update `CHANGELOG.md`
3. Create git tag:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
4. Build and publish:
   ```bash
   uv build
   uv publish
   ```

## Key Differences: uv vs pip/poetry

| Task | Traditional (pip) | Modern (uv) |
|------|-------------------|-------------|
| Install tool | `pip install patchon` | `uv add patchon` |
| Install editable | `pip install -e .` | `uv pip install -e .` |
| Run command | `python xx.py` | `uv run python xx.py` |
| Run tests | `pytest` | `uv run pytest` |
| Build | `python -m build` | `uv build` |
| Publish | `twine upload dist/*` | `uv publish` |

## Additional Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [maturin Documentation](https://www.maturin.rs/)
- [PEP 621 – Storing project metadata in pyproject.toml](https://peps.python.org/pep-0621/)
