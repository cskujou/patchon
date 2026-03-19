# patchon

[![CI](https://github.com/cskujou/patchon/actions/workflows/ci.yml/badge.svg)](https://github.com/cskujou/patchon/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/patchon)](https://pypi.org/project/patchon/)
[![Python](https://img.shields.io/pypi/pyversions/patchon)](https://pypi.org/project/patchon/)

`patchon` (pronounced `patch-on`) runs your Python code with temporary source patches applied before execution, then restores the original files afterward.

[中文文档](README_zh.md)

## What It Does

Use `patchon` when you want to temporarily change installed Python package code without manually editing `site-packages` and then cleaning up later.

Typical use cases:

- Debug a library by adding prints or logging
- Try a local hotfix before an upstream release lands
- Inject instrumentation for profiling or tracing
- Reproduce and test a package-level workaround safely

## Install

Choose one of these user-facing install flows:

```bash
pip install patchon
```

Or install it as a tool with `uv`:

```bash
uv tool install patchon
```

After that, `patchon` is available on your shell just like `python`.

## Quick Start

### 1. Create a config

`patchon` looks upward from the current directory for:

1. `pyproject.toml` with a `[tool.patchon]` section
2. `patchon.yaml`

Recommended `pyproject.toml` example:

```toml
[tool.patchon]
verbose = true
strict = true

[[tool.patchon.patches]]
package = "requests"
expected_version = "2.31.0"
patch_root = "./patches/requests"
```

You can also start from [`examples/patchon.yaml.example`](examples/patchon.yaml.example).

### 2. Create your patch files

Mirror the package's Python file layout under `patch_root`.

Example:

```text
your-project/
├── pyproject.toml
└── patches/
    └── requests/
        └── sessions.py
```

If `patch_root = "./patches/requests"`, then `patchon` will map:

`patches/requests/sessions.py` -> `requests/sessions.py`

`patch_root` is resolved relative to the config file, not the current shell directory.

### 3. Run your code with `patchon`

```bash
patchon myscript.py
```

Instead of:

```bash
python myscript.py
```

You can also use it with modules and `-c` commands:

```bash
patchon -m http.server 8000
patchon -c "import requests; print(requests.__version__)"
patchon server.py --port 8000 --debug
```

## A Typical Workflow

1. Find the package file you want to patch.
2. Copy that `.py` file into your local patch directory.
3. Edit the local copy.
4. Run your command with `patchon`.
5. Let `patchon` restore the original files when the run finishes.

Example:

```bash
python -c "import requests; print(requests.__file__)"
mkdir -p patches/requests
cp /path/to/site-packages/requests/sessions.py patches/requests/
patchon --dry-run myscript.py
patchon myscript.py
```

## CLI Basics

Useful built-in commands:

```bash
patchon --help
patchon --version
patchon --check
patchon --print-config
patchon --dry-run myscript.py
patchon --cleanup-status
patchon --cleanup
```

`patchon` parses its own flags first, then forwards the remaining arguments to Python.

## Safety Behavior

`patchon` is designed for temporary, reversible source patching:

- Only patches `.py` files
- Backs up files before modification
- Restores files on normal exit
- Can check package versions with `expected_version`
- Warns when your patch tree looks suspicious
- Tries to prevent concurrent patch sessions from colliding

## Troubleshooting

### No configuration found

Create `pyproject.toml` with `[tool.patchon]` or create `patchon.yaml`.

### Version mismatch

Your installed package version does not match `expected_version`. Update the patch or remove the version pin if that check is not needed.

### Files not restored

If the process was killed hard, run:

```bash
patchon --cleanup
```

If needed, reinstall the affected package:

```bash
pip install --force-reinstall package_name
```

## More Docs

- [中文文档](README_zh.md)
- [Installation](docs/docs/getting-started/installation.md)
- [Configuration](docs/docs/getting-started/configuration.md)
- [Advanced Guide](docs/docs/user-guide/advanced.md)

## Development

If you want to hack on `patchon` itself, the deeper build and contributor docs live under `docs/` and `.github/`.

## License

MIT License. See [LICENSE](LICENSE).
