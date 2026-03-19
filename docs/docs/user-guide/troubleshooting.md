# Troubleshooting

## Common Issues

### "No configuration found"

**Cause**: `patchon` couldn't find a configuration file.

**Solution**:

1. Ensure you're in the project directory or a subdirectory
2. Check that `pyproject.toml` or `patchon.yaml` exists
3. Verify the config file has the `[tool.patchon]` section

```bash
# Check current directory
pwd
ls -la pyproject.toml patchon.yaml 2>/dev/null || echo "No config found"
```

Example minimal `pyproject.toml`:

```toml
[tool.patchon]
patches = []
```

### "Version mismatch"

**Cause**: The installed package version doesn't match `expected_version`.

**Solutions**:

1. Update your patch files for the new version
2. Remove `expected_version` from config (not recommended for production)
3. Pin the package version in your requirements

```bash
# Check installed version
python -c "import requests; print(requests.__version__)"
```

### "Failed to acquire environment lock"

**Cause**: Another `patchon` process is currently patching the same packages.

**Solutions**:

1. Wait for the other process to complete
2. Check for stuck processes:

```bash
ps aux | grep patchon
```

3. If the process is dead but lock remains, run:

```bash
patchon --cleanup --cleanup-force
```

### "More than 50% of patches are new files"

**Cause**: Most patch files don't have corresponding target files.

**Common causes**:
- Wrong `patch_root` directory structure
- Package structure mismatch
- Patching the wrong package version

**Solutions**:

1. Verify patch structure:

```bash
# See what patchon sees
patchon --check --verbose
```

2. Compare directory structures:

```bash
tree patches/requests  # Your patches
python -c "import requests; print(requests.__file__)"  # Target location
```

### Files Not Restored (After SIGKILL)

**Cause**: Process was killed with `kill -9`.

**Solution**:

1. Check status:

```bash
patchon --cleanup-status
```

2. Restore files:

```bash
patchon --cleanup
```

3. If that doesn't work, reinstall the affected packages:

```bash
pip install --force-reinstall requests
```

## Installation Issues

### Rust Extension Build Fails

**Cause**: Rust toolchain not installed or incompatible.

**Solutions**:

1. Install Rust:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

2. Install without Rust (pure Python):

```bash
pip install patchon  # No [rust] extra
```

3. For development, use the maturin develop:

```bash
pip install maturin
maturin develop --release
```

### Permission Errors

**Cause**: Insufficient permissions to modify package files.

**Solutions**:

1. Don't patch system packages - use virtual environments
2. Check file permissions:

```bash
# Check permissions
python -c "import requests; import os; print(os.stat(requests.__file__))"
```

3. Use user installation:

```bash
pip install --user package-to-patch
```

## Debug Mode

Enable verbose debugging:

```bash
patchon -v --dry-run script.py
```

This shows:
- All files being processed
- Package locations
- Lock acquisition
- Backup locations

## Getting Help

If you encounter an issue not covered here:

1. Run with `-v` and capture the output
2. Check existing [issues](https://github.com/cskujou/patchon/issues)
3. Create a new issue with:
   - `patchon --version` output
   - `patchon --print-config` output
   - Full error message
   - Steps to reproduce