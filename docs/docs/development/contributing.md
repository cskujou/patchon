# Contributing

Thank you for your interest in contributing to `patchon`! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a new branch for your feature or fix
4. Make your changes
5. Submit a pull request

## Development Setup

This project uses [uv](https://docs.astral.sh/uv/) as its primary development tool.

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/patchon.git
cd patchon

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies (uv creates .venv automatically)
uv sync --group dev

# Verify installation
uv run patchon --version
```

## uv Workflow

uv provides a modern Python workflow with fast dependency resolution and execution.

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_core.py

# Run with coverage
uv run pytest --cov=patchon --cov-report=html

# Run with verbose output
uv run pytest -v
```

### Code Quality

This project uses ruff for linting and formatting, and mypy for type checking:

```bash
# Check code style
uv run ruff check src/patchon tests

# Auto-fix issues
uv run ruff check --fix src/patchon tests

# Format code
uv run ruff format src/patchon tests

# Type checking
uv run mypy src/patchon
```

### Running the Tool

```bash
# Run patchon CLI
uv run patchon --help

# Run with a test script
uv run patchon demo.py

# Run tests in dry-run mode
uv run patchon --dry-run demo.py
```

## Code Style

### Python

- **Python Version**: 3.11+ with modern type hints (`list`, `dict`, `|` instead of `Union`)
- **Type Hints**: All functions should have complete type annotations
- **Docstrings**: Use Google style docstrings
- **Line Length**: 120 characters (enforced by ruff)

Example:

```python
def find_package_path(package_name: str) -> Path | None:
    """Find the filesystem path of an installed package.

    Args:
        package_name: Name of the package to find.

    Returns:
        Path to the package directory, or None if not found.
    """
    spec = importlib.util.find_spec(package_name)
    if spec is None or spec.origin is None:
        return None
    return Path(spec.origin).parent
```

### Rust (for extensions)

```bash
# Format Rust code
uv run cargo fmt

# Run Rust linter
uv run cargo clippy
```

## Testing

All new features should include tests. Tests are located in the `tests/` directory:

```python
# tests/test_core.py
import pytest
from patchon.core import PatchSession
from patchon.models import Config, PatchConfig

def test_patch_session_apply(tmp_path):
    """Test that PatchSession applies patches correctly."""
    config = Config(
        patches=[
            PatchConfig(
                package="test_pkg",
                patch_root=tmp_path / "patches"
            )
        ]
    )
    session = PatchSession(config, dry_run=True)
    assert session.apply_all() is True
```

Run tests before committing:

```bash
uv run pytest
```

## Pull Request Process

1. **Before submitting**:
   - Run `uv run pytest` to ensure all tests pass
   - Run `uv run ruff check src tests` to ensure no linting errors
   - Run `uv run mypy src/patchon` to ensure type correctness
   - Update documentation if needed
   - Add changelog entry to `docs/docs/about/changelog.md`

2. **PR description should include**:
   - Description of changes
   - Motivation for the changes
   - Any breaking changes
   - Related issue numbers

3. **Review process**:
   - Maintainers will review your PR
   - Address any requested changes
   - Once approved, a maintainer will merge

## Reporting Issues

### Bug Reports

Please include:

- `uv run patchon --version` output
- Python version (`uv run python --version`)
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages (full traceback if available)

### Feature Requests

Please include:

- Use case description
- Proposed API or behavior
- Any alternatives considered

## Commit Messages

Use conventional commit format:

```
feat: add support for Python 3.14
fix: handle edge case in version parsing
docs: update installation instructions
test: add tests for cleanup functionality
refactor: simplify PatchSession state management
perf: optimize file copy operations
chore: update dependencies
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

## Areas for Contribution

### Good First Issues

- Documentation improvements
- Error message improvements
- Additional test coverage
- Example configurations

### Feature Ideas

- Additional configuration formats
- Improved error reporting
- IDE integration
- Plugin system

### Performance

- Optimize file operations in Rust
- Improve memory usage
- Reduce startup time

## Code of Conduct

This project adheres to a code of conduct:

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Respect different viewpoints

## Development Commands Reference

| Task | Command |
|------|---------|
| Install dependencies | `uv sync --group dev` |
| Run tests | `uv run pytest` |
| Run with coverage | `uv run pytest --cov` |
| Lint code | `uv run ruff check src tests` |
| Fix linting | `uv run ruff check --fix src tests` |
| Format code | `uv run ruff format src tests` |
| Type check | `uv run mypy src/patchon` |
| Run CLI | `uv run patchon --help` |
| Build | `uv build` |
| Build with Rust | `uv run maturin develop --release` |

## Questions?

- Open an [issue](https://github.com/cskujou/patchon/issues) for questions
- Check existing [documentation](https://github.com/cskujou/patchon/tree/main/docs)
- Review closed issues for similar questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
