# Basic Usage

## Running Scripts

### Standard Script Execution

```bash
patchon script.py
```

With arguments:

```bash
patchon script.py --arg1 value1 --arg2
```

### Running Modules

```bash
patchon -m module.name
patchon -m http.server 8000
patchon -m pytest -v tests/
```

### Running Code Directly

```bash
patchon -c "import requests; print(requests.__version__)"
```

## CLI Options

| Option | Description |
|--------|-------------|
| `--help` | Show help message |
| `--version` | Show version |
| `--check` | Verify configuration without running |
| `--print-config` | Display parsed configuration |
| `--dry-run` | Show what would be patched |
| `-v, --verbose` | Enable verbose output |
| `-q, --quiet` | Suppress non-error output |

## Verification Commands

### Check Configuration

Verify everything is set up correctly:

```bash
patchon --check
```

Output:
```
Checking configuration...
Checking patch for: requests
  ✓ Package found at: /path/to/site-packages/requests
  ✓ Version matches: 2.31.0
  ✓ Patch root found: ./patches/requests
  - Found 3 patch files
```

### Print Configuration

See the parsed configuration:

```bash
patchon --print-config
```

Output:
```json
{
  "config_source": "pyproject.toml",
  "config_path": "/home/user/project/pyproject.toml",
  "verbose": true,
  "strict": true,
  "patches": [
    {
      "package": "requests",
      "expected_version": "2.31.0",
      "patch_root": "/home/user/project/patches/requests"
    }
  ]
}
```

### Dry Run

Preview what would happen:

```bash
patchon --dry-run script.py
```

Output:
```
[DRY-RUN] Would patch: /path/to/site-packages/requests/sessions.py <- ./patches/requests/sessions.py
[DRY-RUN] Would patch: /path/to/site-packages/requests/adapters.py <- ./patches/requests/adapters.py
Dry run complete. No changes made.
```

## Logging Levels

Control verbosity with `-v` and `-q`:

```bash
# Default: info level
patchon script.py

# Verbose: debug level (shows internal operations)
patchon -v script.py

# Quiet: warning level (only errors)
patchon -q script.py
```

## Safety Features

### Automatic Backups

Before applying any patch, the original file is backed up to a temporary location.

### Guaranteed Restoration

Files are restored via:
1. Normal exit
2. `atexit` handlers
3. `finally` blocks
4. Signal handlers (SIGINT, SIGTERM)

!!! note "SIGKILL Limitation"
    If the process receives `SIGKILL` (kill -9), files may not be restored.
    Use `patchon --cleanup` to recover.