# Quick Start

Get up and running with `patchon` in 5 minutes.

## Quick Start with uvx

The fastest way to try `patchon` without installing:

```bash
# Run patchon directly without installation
uvx patchon --version

# Patch and run your script
uvx patchon your_script.py

# Run with arguments
uvx patchon your_script.py --port 8080
```

For development within this project, use `uv run` instead:

```bash
uv run patchon --help
uv run patchon test_script.py
```

## 1. Create a Patch

Let's patch the `requests` library to add some debug logging.

First, find where requests is installed:

```bash
python -c "import requests; print(requests.__file__)"
# Output: /path/to/site-packages/requests/__init__.py
```

## 2. Set Up Your Project

Create a project directory:

```bash
mkdir myproject
cd myproject
```

Create `pyproject.toml`:

```toml
[tool.patchon]
verbose = true

[[tool.patchon.patches]]
package = "requests"
patch_root = "./patches/requests"
```

## 3. Create the Patch Structure

```bash
mkdir -p patches/requests
```

Copy and modify the file you want to patch:

```bash
cp /path/to/site-packages/requests/sessions.py patches/requests/
```

Edit `patches/requests/sessions.py` to add logging:

```python
# At the top of the file, add after imports:
import logging
logger = logging.getLogger("requests.patched")

# In the Session.request method, add at the beginning:
def request(self, method, url, **kwargs):
    logger.info(f"Making {method} request to {url}")
    # ... rest of the method
```

## 4. Test Your Patch

Check that patchon can find and apply your patch:

```bash
patchon --check
```

You should see output like:

```
Checking patch for: requests
  ✓ Package found at: /path/to/site-packages/requests
  - No version check configured
  ✓ Patch root found: /path/to/myproject/patches/requests
  - Found 1 patch files
```

## 5. Run Your Script

Create a test script `test_script.py`:

```python
import requests

response = requests.get("https://httpbin.org/get")
print(f"Status: {response.status_code}")
```

Run with patchon:

```bash
patchon test_script.py
```

You should see your debug logging:

```
Applying patch for package: requests
... request logging output ...
Status: 200
```

After your script finishes, the original files are automatically restored.

## 6. Dry Run (Optional)

Before running, see what would be patched:

```bash
patchon --dry-run test_script.py
```

## Next Steps

- [Configuration Guide](configuration.md) - Learn about all configuration options
- [Advanced Features](../user-guide/advanced.md) - Rust acceleration, recovery, and more