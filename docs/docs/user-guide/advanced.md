# Advanced Features

## Rust Acceleration

`patchon` includes an optional Rust extension for high-performance operations.

### What's Accelerated

| Operation | Python Fallback | Rust Accelerated |
|-----------|-----------------|------------------|
| File copy | `shutil.copy2` | Optimized 64KB buffered I/O |
| Directory scan | `os.walk` | Fast recursive walk |
| File locking | `fcntl.flock` | Native flock with timeout |
| File hashing | `hash()` | xxHash-based (fast) |

### Installing with Rust

```bash
pip install "patchon[rust]"
```

Or build from source:

```bash
uv run maturin develop --release
```

On Windows, use the GNU Rust toolchain (`x86_64-pc-windows-gnu`) together with `mingw-winlibs-llvm-ucrt` instead of MSVC/Windows SDK.

### Verify Rust Extension

```python
from patchon._rust_ext import _RUST_AVAILABLE
print(_RUST_AVAILABLE)  # True if loaded
```

## Environment Locking

`patchon` uses file locking to prevent concurrent patching of the same packages.

### How It Works

1. Before patching, a lock is acquired based on the packages being patched
2. If another patchon process has the lock, the command waits (up to 60s timeout)
3. The lock is released after restoration

### Lock Timeout

If the lock cannot be acquired:

```
Failed to acquire environment lock. Another patchon process may be
currently patching the same packages. Wait for it to complete or
run 'patchon --cleanup' if the previous process was terminated.
```

## Crash Recovery

If `patchon` is killed or crashes, patched files may not be restored.

### Check Status

See if recovery is needed:

```bash
patchon --cleanup-status
```

Output:
```
Patchon Cleanup Status:
  Active patching sessions: 1
  Orphaned sessions: 0
  Total backups tracked: 3
  Orphaned backups: 0

  ✓  No cleanup needed
```

### Perform Cleanup

Restore files from orphaned backups:

```bash
patchon --cleanup
```

Output:
```
Restored: /path/to/site-packages/requests/sessions.py
Removed backup: /tmp/.../sessions.py.backup
Cleanup complete: 1 file(s) restored
```

### Force Cleanup

If you know the original process is dead but the lock file still exists:

```bash
patchon --cleanup --cleanup-force
```

!!! warning
    Using `--cleanup-force` may interfere with an active patching session.
    Only use when you're certain no patchon process is running.

## Batch Operations

For complex patching scenarios, you can use the Python API directly:

```python
from patchon.core import PatchSession
from patchon.config import load_config
from pathlib import Path

# Load config
config = load_config(Path("pyproject.toml"), "pyproject")

# Create session with options
session = PatchSession(config, dry_run=False)

# Apply patches
if session.apply_all():
    # Run your code
    import subprocess
    result = subprocess.run(["python", "script.py"])
    
    # Always restore
    session.restore()
```

## Custom Backup Location

By default, backups go to temp directories. You can customize this:

```python
from patchon._rust_ext import EnvironmentLock, fast_file_copy

# Use custom lock directory
lock = EnvironmentLock(lock_dir=Path("./.patchon_locks"))
with lock:
    # Your patching code
    pass
```

## Performance Tips

1. **Enable Rust extensions** for large projects
2. **Use `--dry-run`** to verify before applying
3. **Minimize patch files** - fewer files = faster patching
4. **Use SSD storage** for temp directory (faster backups)
