# patchon

[![CI](https://github.com/cskujou/patchon/actions/workflows/ci.yml/badge.svg)](https://github.com/cskujou/patchon/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/patchon)](https://pypi.org/project/patchon/)
[![Python](https://img.shields.io/pypi/pyversions/patchon)](https://pypi.org/project/patchon/)

Run Python scripts with temporary source-file hot patches applied before execution and restored afterward.

[中文文档](README_zh.md)

## Why patchon?

When developing or debugging Python applications, you often need to temporarily modify library code:
- Add logging to understand internal behavior
- Patch a bug before the upstream fix is released
- Inject instrumentation for profiling
- Test changes without affecting the global environment

`patchon` provides a seamless experience: write your patches as regular `.py` files, and `patchon` will automatically apply them before running your script, then restore the original files when done.

## Installation

```bash
pip install patchon
```

Or using `uv`:

```bash
uv add --dev patchon
```

## Basic Usage

### Replace `python` with `patchon`

```bash
# Before
python myscript.py

# After - automatically applies patches before running
patchon myscript.py
```

### Pass arguments to your script

```bash
# Before
python server.py --port 8000 --debug

# After
patchon server.py --port 8000 --debug
```

### Run a module

```bash
# Before
python -m http.server 8000

# After
patchon -m http.server 8000
```

### Execute a command string

```bash
# Before
python -c "import requests; print(requests.__version__)"

# After
patchon -c "import requests; print(requests.__version__)"
```

## Configuration

`patchon` auto-discovers configuration by walking up from the current directory:

1. First, looks for `pyproject.toml` with `[tool.patchon]` section
2. Falls back to `patchon.yaml` if no `[tool.patchon]` found
3. Errors if neither is found

### pyproject.toml (Recommended)

```toml
[tool.patchon]
verbose = true
strict = true

[[tool.patchon.patches]]
package = "requests"
expected_version = "2.31.0"
patch_root = "./patches/requests"

[[tool.patchon.patches]]
package = "fastapi"
patch_root = "./patches/fastapi"
```

### patchon.yaml

```yaml
verbose: true
strict: true

patches:
  - package: requests
    expected_version: "2.31.0"
    patch_root: "./patches/requests"

  - package: fastapi
    patch_root: "./patches/fastapi"
```

### Configuration Fields

| Field | Type | Description |
|-------|------|-------------|
| `verbose` | boolean | Enable detailed logging |
| `strict` | boolean | Fail on any patch error if `true` |
| `package` | string | Package name to patch (required) |
| `expected_version` | string | Expected package version (optional) |
| `patch_root` | string | Directory containing patch files (relative to config) |

### Path Resolution

The `patch_root` path is resolved relative to the configuration file's directory, not the current working directory. This ensures consistent behavior regardless of where you run `patchon` from.

For example, with this structure:

```
project/
├── pyproject.toml
├── src/
│   └── main.py
└── patches/
    └── requests/
        └── sessions.py
```

If `pyproject.toml` contains `patch_root = "./patches/requests"`, it will resolve to `/path/to/project/patches/requests/` no matter where you run `patchon` from.

## CLI Options

`patchon` accepts its own options and forwards the rest to Python:

```bash
# Patchon options
patchon --help                    # Show help
patchon --version                 # Show version
patchon --check                   # Validate configuration
patchon --print-config            # Print resolved configuration
patchon --dry-run script.py       # Show what would be patched
patchon --verbose script.py       # Enable verbose output
patchon --quiet script.py         # Suppress non-error output

# Forwarded to Python
patchon -m module                 # Run module
patchon -c "command"              # Execute command string
patchon script.py args...         # Run script with arguments
```

## Safety Features

`patchon` includes several safety mechanisms:

- **Only `.py` files**: Will not touch binary extensions (`.so`, `.pyd`, etc.)
- **Version checking**: Optionally verify package version before patching
- **File existence**: Verifies target files exist before patching
- **Automatic backup**: Backs up all files before modification
- **Guaranteed restore**: Uses `atexit` and `finally` blocks to ensure restoration
- **Duplicate prevention**: Refuses to patch the same file twice in one session
- **New file warnings**: Warns if >50% of patches are new files (possible misconfiguration)

## Example Workflow

1. **Identify the file to patch**:
   ```bash
   patchon --check
   ```

2. **Locate the package**:
   ```python
   import requests
   print(requests.__file__)
   # /path/to/site-packages/requests/__init__.py
   ```

3. **Create the patch structure**:
   ```bash
   mkdir -p patches/requests
   ```

4. **Copy and modify the file**:
   ```bash
   cp /path/to/site-packages/requests/sessions.py patches/requests/
   # Edit patches/requests/sessions.py
   ```

5. **Test your patch**:
   ```bash
   patchon --dry-run myscript.py
   patchon myscript.py
   ```

## Known Limitations

- Cannot restore files if the process is killed with `SIGKILL` (`kill -9`)
- Only supports patching `.py` source files (no binary extensions)
- Windows file locking may prevent some edge cases from restoring correctly
- Running multiple `patchon` processes simultaneously on the same package is not recommended

## Development

### Setup

Using `uv` (recommended):

```bash
# Clone the repository
git clone https://github.com/cskujou/patchon.git
cd patchon

# Sync dependencies
uv sync

# Run tests
uv run pytest

# Run patchon locally
uv run patchon --help
```

### Build

```bash
uv build
```

This creates both wheel and sdist in `dist/`.

### Local Installation

```bash
uv run pip install dist/patchon-0.1.0-py3-none-any.whl
```

Or directly:

```bash
uv pip install -e .
```

### Publishing

#### Manual with `uv`

```bash
# Build and publish to PyPI
uv build
uv publish
```

You'll need to configure PyPI credentials first:

```bash
uv publish --token $PYPI_TOKEN
# or
uv publish --username $PYPI_USERNAME --password $PYPI_PASSWORD
```

#### Automated with GitHub Actions

See `.github/workflows/publish.yml` for automated publishing using Trusted Publishing.

## Troubleshooting

### "No configuration found"

`patchon` requires a configuration file. Create a `pyproject.toml` or `patchon.yaml` in your project root.

### "Version mismatch"

The package version doesn't match `expected_version`. Either update your patches or remove the version constraint.

### "More than 50% of patches are new files"

This warning indicates most of your patches would create new files rather than modify existing ones. Double-check your `patch_root` configuration and directory structure.

### Files not restoring

If restoration fails (e.g., process killed), you may need to manually reinstall the affected package:

```bash
pip install --force-reinstall package_name
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run tests (`uv run pytest`)
5. Commit your changes (`git commit -am 'Add feature'`)
6. Push to the branch (`git push origin feature/my-feature`)
7. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.
