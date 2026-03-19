# Core API

The `patchon.core` module contains the main `PatchSession` class that manages patching operations.

## PatchSession

### Constructor

```python
session = PatchSession(config, dry_run=False)
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `config` | `Config` | Configuration object with patch definitions |
| `dry_run` | `bool` | If `True`, don't actually modify files |

### Methods

#### apply_all()

Apply all configured patches.

```python
success = session.apply_all()
```

**Returns**: `bool` - `True` if all patches applied successfully

This method:
1. Acquires environment lock to prevent concurrent patching
2. Applies patches for each configured package
3. Creates backups of original files
4. Saves state for crash recovery

#### restore()

Restore all patched files from backups.

```python
session.restore()
```

This method is automatically called via `atexit` handler. It:
1. Restores each file from its backup
2. Removes backup files
3. Removes state file
4. Releases environment lock

#### check()

Check configuration without applying patches.

```python
ok = session.check()
```

**Returns**: `bool` - `True` if all checks pass

Validates:
- All packages can be found
- Versions match (if specified)
- Patch roots exist
- Patch files are valid

### Usage Example

```python
from patchon.core import PatchSession
from patchon.config import load_config
from patchon.discover import discover_config

# Discover and load configuration
config_path, source_type = discover_config()
config = load_config(config_path, source_type)

# Create session
session = PatchSession(config, dry_run=False)

# Apply patches
if session.apply_all():
    print("Patches applied successfully")
    try:
        # Run your code here
        pass
    finally:
        # Always restore
        session.restore()
else:
    print("Failed to apply patches")
```

## Error Handling

The `PatchSession` handles various error conditions:

| Error | Response |
|-------|----------|
| Environment lock conflict | Logs error, returns `False` |
| Version mismatch | Logs error, returns `False` (or warning if not strict) |
| Missing package | Logs error, returns `False` |
| Backup failure | Logs error, skips that file |
| Patch failure | Restores from backup, logs error |

## Internal Methods

These methods are used internally but may be useful for advanced use cases:

### _find_package_path()

```python
path = session._find_package_path("requests")
```

Finds the filesystem path of an installed package.

### _check_version()

```python
ok = session._check_version("requests", "2.28.0")
```

Checks if installed package version matches expected version.

### _create_backup()

```python
backup_path = session._create_backup(Path("/path/to/file.py"))
```

Creates a backup of an original file.

## Context Manager Pattern

While `PatchSession` doesn't implement `__enter__` and `__exit__` directly, you can use it with `contextlib`:

```python
from contextlib import contextmanager

@contextmanager
def patched_session(config):
    session = PatchSession(config)
    if not session.apply_all():
        raise RuntimeError("Failed to apply patches")
    try:
        yield session
    finally:
        session.restore()

# Usage
with patched_session(config):
    # Run code with patches applied
    import requests
    # ...
# Patches automatically restored
```
