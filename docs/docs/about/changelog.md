# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial release of patchon
- Core patching functionality with `PatchSession`
- Configuration via `pyproject.toml` and YAML
- Automatic backup and restoration
- Environment locking for process safety
- Crash recovery with `--cleanup` command
- Rust-accelerated file operations (optional)
- Dry-run mode for testing configurations
- Version checking for patched packages
- Support for running scripts, modules, and commands

## [0.1.0] - 2024-01-15

### Added

- `PatchSession` class for managing patch lifecycle
- Configuration discovery from current directory upward
- Support for multiple patches in single session
- Backup creation before patching
- Automatic restoration via `atexit` handler
- `StateManager` for crash recovery
- `EnvironmentLock` for preventing concurrent patching
- CLI with multiple execution modes:
  - Script mode: `patchon script.py`
  - Module mode: `patchon -m module`
  - Command mode: `patchon -c "command"`
- Verbose and quiet output modes
- Configuration validation with `--check`
- Configuration display with `--print-config`
- Cleanup commands:
  - `--cleanup-status` to check for orphaned patches
  - `--cleanup` to restore orphaned files
  - `--cleanup-force` to force cleanup
- Support for new file creation via patches
- Warning for patches with mostly new files
- Comprehensive test suite
- Documentation with MkDocs

### Security

- Process-safe environment locking prevents concurrent modification
- State persistence for recovery from SIGKILL
- Backup verification before patch application

[Unreleased]: https://github.com/cskujou/patchon/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/cskujou/patchon/releases/tag/v0.1.0
