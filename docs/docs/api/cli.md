# CLI API

The `patchon.cli` module provides the command-line interface. You can also use its functions programmatically.

## Command-Line Usage

```bash
patchon [patchon-options] script.py [script-args...]
patchon [patchon-options] -m module [script-args...]
patchon [patchon-options] -c "command"
```

## Options

### Information Options

| Option | Description |
|--------|-------------|
| `-h, --help` | Show help message and exit |
| `-V, --version` | Show version and exit |
| `--print-config` | Print configuration and exit |

### Execution Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Show what would be patched without applying |
| `--check` | Check configuration without running |

### Cleanup Options

| Option | Description |
|--------|-------------|
| `--cleanup` | Recover files from crashed patching sessions |
| `--cleanup-status` | Show cleanup status |
| `--cleanup-force` | Force cleanup even if process may be alive |

### Output Options

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Enable verbose output |
| `-q, --quiet` | Suppress non-error output |

### Python Options (Forwarded)

| Option | Description |
|--------|-------------|
| `-m module` | Run library module as script |
| `-c command` | Program passed in as string |

## Examples

### Basic Usage

```bash
# Run a script with patches
patchon myscript.py

# Run with verbose output
patchon -v myscript.py

# Dry run to preview changes
patchon --dry-run myscript.py
```

### Running Modules

```bash
# Run a module
patchon -m http.server 8000

# Run a package module
patchon -m pytest
```

### Running Commands

```bash
# Execute a command string
patchon -c "import requests; print(requests.get('https://api.example.com'))"
```

### Checking Configuration

```bash
# Check configuration
patchon --check

# Print configuration
patchon --print-config
```

### Cleanup

```bash
# Check cleanup status
patchon --cleanup-status

# Perform cleanup
patchon --cleanup

# Force cleanup
patchon --cleanup --cleanup-force
```

## Programmatic Usage

You can use CLI functions in your own code:

### main()

```python
from patchon.cli import main

# Run patchon programmatically
exit_code = main(["--check"])
print(f"Exit code: {exit_code}")

# Run with a script
exit_code = main(["-v", "myscript.py", "--arg1", "--arg2"])
```

### parse_args()

```python
from patchon.cli import parse_args

# Parse arguments
parsed, remaining = parse_args(["-v", "--check"])
print(parsed.verbose)  # True
print(parsed.check)    # True
```

### split_args()

```python
from patchon.cli import split_args

# Split patchon args from python args
patchon_args, python_args = split_args(
    ["-v", "myscript.py", "--port", "8000"]
)
# patchon_args: [-v]
# python_args: [myscript.py, --port, 8000]
```

### setup_logging()

```python
from patchon.cli import setup_logging

# Configure logging
setup_logging(verbose=True, quiet=False)
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (patching failed, cleanup failed, etc.) |
| 130 | Interrupted by user (Ctrl+C) |

## Configuration Discovery

The CLI automatically discovers configuration by walking up the directory tree from the current working directory:

1. Looks for `pyproject.toml` with `[tool.patchon]` section
2. Looks for `patchon.yaml` file
3. Stops at first match

If no configuration is found, an error is displayed with example configurations.

## Argument Parsing

The CLI uses a two-pass argument parsing strategy:

1. **First pass**: Identify `patchon`-specific options
2. **Second pass**: Everything else goes to Python interpreter

This allows seamless passing of arguments to your Python scripts:

```bash
patchon -v myscript.py --port 8000 --debug
# -v goes to patchon
# --port 8000 --debug goes to myscript.py
```
