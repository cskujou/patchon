# Configuration

`patchon` supports two configuration formats:

1. **pyproject.toml** (recommended)
2. **patchon.yaml**

Configuration is auto-discovered by walking up from the current directory.

## pyproject.toml (Recommended)

Add a `[tool.patchon]` section to your `pyproject.toml`:

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

## patchon.yaml

Or use a separate YAML file:

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

An example file is available at `examples/patchon.yaml.example`.

## Configuration Fields

### Global Options

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `verbose` | bool | false | Enable verbose logging output |
| `strict` | bool | true | If true, any patch error stops execution |

### Patch Configuration

| Field | Required | Description |
|-------|----------|-------------|
| `package` | ✓ | Python package name to patch |
| `expected_version` | | Expected version string for validation |
| `patch_root` | ✓ | Directory containing patch files |

## Path Resolution

`patch_root` paths are **relative to the config file location**, not the current working directory.

Example structure:

```
project/
├── pyproject.toml
├── src/
│   └── main.py
└── patches/
    └── requests/
        └── sessions.py
```

With `patch_root = "./patches/requests"` in `pyproject.toml`, patchon will resolve this to `/path/to/project/patches/requests/` regardless of where you run patchon from.

## Version Checking

Use `expected_version` to ensure patches are only applied to known versions:

```toml
[[tool.patchon.patches]]
package = "django"
expected_version = "4.2.0"
patch_root = "./patches/django-4.2"
```

If the installed version doesn't match, patchon will fail (or warn if `strict = false`).

## Multiple Patches

You can patch multiple packages:

```toml
[[tool.patchon.patches]]
package = "requests"
patch_root = "./patches/requests"

[[tool.patchon.patches]]
package = "urllib3"
patch_root = "./patches/urllib3"

[[tool.patchon.patches]]
package = "somepackage"
patch_root = "./patches/somepackage"
expected_version = "1.0.0"
```

## Environment-Specific Config

Use environment variables with tools like [direnv](https://direnv.net/):

```toml
[tool.patchon]
verbose = {env = "PATCHON_VERBOSE", default = false}
```

Or separate config files per environment:

```bash
# Development
patchon --config patchon.dev.yaml myscript.py

# Production
patchon --config patchon.prod.yaml myscript.py
```

## Next Steps

- [Advanced Features](../user-guide/advanced.md) - Rust acceleration, recovery, and more
- [Troubleshooting](../user-guide/troubleshooting.md) - Common issues and solutions
