//! patchon-rust: High-performance core for Python hot patching
//!
//! This module provides optimized operations for:
//! - Fast file scanning and copying
//! - Atomic file operations with backups
//! - Parallel processing of batch operations
//! - File locking for concurrent safety

use pyo3::prelude::*;
use rayon::prelude::*;
use std::collections::HashMap;
use std::fs;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

/// Batch file copy with parallel processing
///
/// Operations are processed in parallel using Rayon for maximum performance
#[pyfunction]
fn batch_copy_files(operations: Vec<(String, String)>) -> PyResult<Vec<Option<String>>> {
    let results: Vec<Option<String>> = operations
        .par_iter()
        .map(|(src, dst)| match fast_file_copy_internal(src, dst) {
            Ok(_) => None,
            Err(e) => Some(e.to_string()),
        })
        .collect();

    Ok(results)
}

/// Internal fast file copy implementation
fn fast_file_copy_internal(src: &str, dst: &str) -> Result<(), Box<dyn std::error::Error>> {
    let src_path = Path::new(src);
    let dst_path = Path::new(dst);

    // Ensure parent directory exists
    if let Some(parent) = dst_path.parent() {
        fs::create_dir_all(parent)?;
    }

    // Use 256KB buffer for better throughput with larger files
    const BUFFER_SIZE: usize = 256 * 1024;

    let mut src_file = fs::File::open(src_path)?;
    let mut dst_file = fs::File::create(dst_path)?;

    let mut buffer = vec![0u8; BUFFER_SIZE];

    loop {
        match src_file.read(&mut buffer) {
            Ok(0) => break,
            Ok(n) => {
                dst_file.write_all(&buffer[..n])?;
            }
            Err(e) => return Err(Box::new(e)),
        }
    }

    // Copy metadata
    let metadata = fs::metadata(src_path)?;
    let permissions = metadata.permissions();
    fs::set_permissions(dst_path, permissions)?;

    Ok(())
}

/// Python-exposed fast file copy
#[pyfunction]
fn fast_file_copy(src: &str, dst: &str) -> PyResult<()> {
    fast_file_copy_internal(src, dst).map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))
}

/// Scan Python files in directory with optimized parallel walker
#[pyfunction(signature = (dir, recursive=None))]
fn scan_python_files(dir: &str, recursive: Option<bool>) -> PyResult<Vec<String>> {
    let recursive = recursive.unwrap_or(true);
    let path = PathBuf::from(dir);

    let mut walker = WalkDir::new(path);
    if !recursive {
        walker = walker.max_depth(1);
    }

    let files: Vec<String> = walker
        .into_iter()
        .filter_entry(|e: &walkdir::DirEntry| {
            // Skip hidden directories
            !e.file_name()
                .to_str()
                .map(|s: &str| s.starts_with('.'))
                .unwrap_or(false)
        })
        .filter_map(|entry: Result<walkdir::DirEntry, walkdir::Error>| match entry {
            Ok(e) => {
                if e.file_type().is_file() {
                    let path = e.path();
                    if path.extension().map_or(false, |ext| ext == "py") {
                        return Some(path.to_string_lossy().to_string());
                    }
                }
                None
            }
            Err(_) => None,
        })
        .collect();

    Ok(files)
}

/// Calculate file hash for change detection (xxhash-inspired fast hash)
#[pyfunction]
fn calculate_file_hash(path: &str) -> PyResult<u64> {
    use std::collections::hash_map::DefaultHasher;
    use std::hash::{Hash, Hasher};

    let content =
        fs::read(path).map_err(|e| pyo3::exceptions::PyIOError::new_err(format!("Failed to read file: {}", e)))?;

    let mut hasher = DefaultHasher::new();
    content.hash(&mut hasher);
    Ok(hasher.finish())
}

/// Atomic file write with automatic backup creation
///
/// Returns the backup path if a backup was created, None if target didn't exist
#[pyfunction(signature = (target, content, backup_dir=None))]
fn atomic_write_with_backup(target: &str, content: &str, backup_dir: Option<&str>) -> PyResult<Option<String>> {
    let target_path = Path::new(target);

    // Create backup if file exists
    let backup_path: Option<PathBuf> = if target_path.exists() {
        let backup_path = if let Some(dir) = backup_dir {
            PathBuf::from(dir).join(format!(
                "{}.{}.backup",
                target_path.file_name().unwrap_or_default().to_string_lossy(),
                std::process::id()
            ))
        } else {
            std::env::temp_dir().join(format!(
                "patchon_backup_{}_{}",
                target_path.file_name().unwrap_or_default().to_string_lossy(),
                std::process::id()
            ))
        };

        fast_file_copy_internal(target, backup_path.to_str().unwrap())
            .map_err(|e| pyo3::exceptions::PyIOError::new_err(format!("Failed to create backup: {}", e)))?;

        Some(backup_path)
    } else {
        None
    };

    // Atomic write using temp file + rename
    let temp_path = target_path.with_extension("tmp");
    fs::write(&temp_path, content)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(format!("Failed to write temp file: {}", e)))?;

    fs::rename(&temp_path, target_path)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(format!("Failed to rename: {}", e)))?;

    Ok(backup_path.map(|p| p.to_string_lossy().to_string()))
}

/// Restore file from backup
#[pyfunction]
fn restore_from_backup(backup_path: &str, target: &str) -> PyResult<()> {
    fast_file_copy_internal(backup_path, target)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(format!("Failed to restore backup: {}", e)))
}

/// Batch restore operations in parallel
#[pyfunction]
fn batch_restore(backups: Vec<(String, String)>) -> PyResult<Vec<Option<String>>> {
    let results: Vec<Option<String>> = backups
        .par_iter()
        .map(|(backup, target)| match restore_from_backup_internal(backup, target) {
            Ok(_) => None,
            Err(e) => Some(format!("Failed to restore {}: {}", target, e)),
        })
        .collect();

    Ok(results)
}

fn restore_from_backup_internal(backup: &str, target: &str) -> Result<(), Box<dyn std::error::Error>> {
    fast_file_copy_internal(backup, target)
}

/// File lock for preventing concurrent patch operations
#[cfg(unix)]
#[pyfunction(signature = (lock_path, timeout_secs=None))]
fn acquire_file_lock(lock_path: &str, timeout_secs: Option<u64>) -> PyResult<i32> {
    use nix::fcntl::{flock, open, FlockArg};
    use nix::sys::stat::Mode;
    use nix::unistd::close;
    use std::time::{Duration, Instant};

    let timeout = Duration::from_secs(timeout_secs.unwrap_or(30));
    let start = Instant::now();

    let fd = loop {
        match open(
            Path::new(lock_path),
            nix::fcntl::OFlag::O_RDWR | nix::fcntl::OFlag::O_CREAT,
            Mode::from_bits_truncate(0o644),
        ) {
            Ok(fd) => break fd,
            Err(_e) => {
                if start.elapsed() > timeout {
                    return Err(pyo3::exceptions::PyTimeoutError::new_err(format!(
                        "Failed to open lock file: {}",
                        _e
                    )));
                }
                std::thread::sleep(Duration::from_millis(10));
            }
        }
    };

    loop {
        match flock(fd, FlockArg::LockExclusiveNonblock) {
            Ok(_) => return Ok(fd),
            Err(_) => {
                if start.elapsed() > timeout {
                    let _ = close(fd);
                    return Err(pyo3::exceptions::PyTimeoutError::new_err(
                        "Failed to acquire lock within timeout",
                    ));
                }
                std::thread::sleep(Duration::from_millis(10));
            }
        }
    }
}

#[cfg(unix)]
#[pyfunction]
fn release_file_lock(fd: i32) -> PyResult<()> {
    use nix::fcntl::{flock, FlockArg};
    use nix::unistd::close;

    flock(fd, FlockArg::UnlockNonblock)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(format!("Failed to unlock: {}", e)))?;

    close(fd).map_err(|e| pyo3::exceptions::PyIOError::new_err(format!("Failed to close: {}", e)))?;

    Ok(())
}

/// Windows implementation of file locking
#[cfg(windows)]
#[pyfunction(signature = (lock_path, timeout_secs=None))]
fn acquire_file_lock(lock_path: &str, timeout_secs: Option<u64>) -> PyResult<isize> {
    use std::os::windows::ffi::OsStrExt;
    use std::time::{Duration, Instant};
    use windows_sys::Win32::Foundation::{CloseHandle, GetLastError, ERROR_LOCK_VIOLATION};
    use windows_sys::Win32::Storage::FileSystem::{
        CreateFileW, LockFile, FILE_GENERIC_READ, FILE_GENERIC_WRITE, OPEN_ALWAYS,
    };

    let timeout = Duration::from_secs(timeout_secs.unwrap_or(30));
    let start = Instant::now();

    // Convert path to wide string
    let wide_path: Vec<u16> = std::ffi::OsStr::new(lock_path).encode_wide().chain(Some(0)).collect();

    loop {
        unsafe {
            let handle = CreateFileW(
                wide_path.as_ptr(),
                FILE_GENERIC_READ | FILE_GENERIC_WRITE,
                0, // No sharing - exclusive access
                std::ptr::null_mut(),
                OPEN_ALWAYS,
                0,
                std::ptr::null_mut(),
            );

            if handle == -1isize as usize {
                if start.elapsed() > timeout {
                    let err = GetLastError();
                    return Err(pyo3::exceptions::PyTimeoutError::new_err(format!(
                        "Failed to open lock file: error {}",
                        err
                    )));
                }
                std::thread::sleep(Duration::from_millis(10));
                continue;
            }

            // Try to lock file
            let lock_result = LockFile(handle, 0, 0, u32::MAX, u32::MAX);

            if lock_result == 0 {
                let err = GetLastError();
                CloseHandle(handle);

                if err == ERROR_LOCK_VIOLATION && start.elapsed() <= timeout {
                    std::thread::sleep(Duration::from_millis(10));
                    continue;
                }

                return Err(pyo3::exceptions::PyTimeoutError::new_err(format!(
                    "Failed to acquire lock: error {}",
                    err
                )));
            }

            return Ok(handle as isize);
        }
    }
}

#[cfg(windows)]
#[pyfunction]
fn release_file_lock(handle: isize) -> PyResult<()> {
    use windows_sys::Win32::Foundation::CloseHandle;
    use windows_sys::Win32::Storage::FileSystem::UnlockFile;

    unsafe {
        let unlock_result = UnlockFile(handle as usize, 0, 0, u32::MAX, u32::MAX);
        if unlock_result == 0 {
            return Err(pyo3::exceptions::PyIOError::new_err(
                "Failed to unlock file".to_string(),
            ));
        }

        let close_result = CloseHandle(handle as usize);
        if close_result == 0 {
            return Err(pyo3::exceptions::PyIOError::new_err(
                "Failed to close file handle".to_string(),
            ));
        }
    }

    Ok(())
}

/// Check if a process is still alive
#[cfg(unix)]
#[pyfunction]
fn is_process_alive(pid: i32) -> bool {
    use nix::sys::signal::kill;

    kill(nix::unistd::Pid::from_raw(pid), None).is_ok()
}

#[cfg(windows)]
#[pyfunction]
fn is_process_alive(pid: i32) -> bool {
    use windows_sys::Win32::Foundation::{CloseHandle, GetLastError};
    use windows_sys::Win32::System::Threading::OpenProcess;
    use windows_sys::Win32::System::Threading::PROCESS_QUERY_INFORMATION;

    unsafe {
        let handle = OpenProcess(PROCESS_QUERY_INFORMATION, 0, pid as u32);
        if handle == 0 {
            return false;
        }
        CloseHandle(handle);
        true
    }
}

/// Cleanup stale lock files
#[pyfunction]
fn cleanup_stale_locks(lock_dir: &str) -> PyResult<usize> {
    let mut cleaned = 0;
    let dir = Path::new(lock_dir);

    if !dir.exists() {
        return Ok(0);
    }

    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        let path = entry.path();

        if path.extension().map_or(false, |ext| ext == "lock") {
            // Try to acquire lock - if succeeds, it's stale
            if let Ok(fd) = try_acquire_lock(&path) {
                release_file_lock(fd)?;
                fs::remove_file(&path)?;
                cleaned += 1;
            }
        }
    }

    Ok(cleaned)
}

#[cfg(unix)]
fn try_acquire_lock(path: &Path) -> Result<i32, Box<dyn std::error::Error>> {
    use nix::fcntl::{flock, FlockArg};
    use nix::sys::stat::Mode;
    use nix::unistd::close;

    let fd = nix::fcntl::open(
        path,
        nix::fcntl::OFlag::O_RDWR | nix::fcntl::OFlag::O_CREAT,
        Mode::from_bits_truncate(0o644),
    )?;

    match flock(fd, FlockArg::LockExclusiveNonblock) {
        Ok(_) => Ok(fd),
        Err(e) => {
            let _ = close(fd);
            Err(Box::new(e))
        }
    }
}

#[cfg(windows)]
fn try_acquire_lock(path: &Path) -> Result<isize, Box<dyn std::error::Error>> {
    use std::os::windows::ffi::OsStrExt;
    use windows_sys::Win32::Foundation::CloseHandle;
    use windows_sys::Win32::Storage::FileSystem::{
        CreateFileW, LockFile, FILE_GENERIC_READ, FILE_GENERIC_WRITE, OPEN_ALWAYS,
    };

    let wide_path: Vec<u16> = path.as_os_str().encode_wide().chain(Some(0)).collect();

    unsafe {
        let handle = CreateFileW(
            wide_path.as_ptr(),
            FILE_GENERIC_READ | FILE_GENERIC_WRITE,
            0,
            std::ptr::null_mut(),
            OPEN_ALWAYS,
            0,
            std::ptr::null_mut(),
        );

        if handle == -1isize as usize {
            return Err(Box::new(std::io::Error::last_os_error()));
        }

        let lock_result = LockFile(handle, 0, 0, u32::MAX, u32::MAX);
        if lock_result == 0 {
            CloseHandle(handle);
            return Err(Box::new(std::io::Error::last_os_error()));
        }

        Ok(handle as isize)
    }
}

/// High-level patch session management
///
/// This struct manages the entire lifecycle of a patching session
#[cfg(unix)]
#[pyclass]
struct PatchSessionRust {
    applied_patches: HashMap<String, String>, // target -> backup_path
    lock_fd: Option<i32>,
}

#[cfg(windows)]
#[pyclass]
struct PatchSessionRust {
    applied_patches: HashMap<String, String>, // target -> backup_path
    lock_handle: Option<isize>,
}

#[cfg(unix)]
#[pymethods]
impl PatchSessionRust {
    #[new]
    fn new() -> Self {
        PatchSessionRust {
            applied_patches: HashMap::new(),
            lock_fd: None,
        }
    }

    /// Apply a batch of patches atomically
    ///
    /// Returns list of (target, backup_path) tuples for successful patches
    fn apply_patches(&mut self, patches: Vec<(String, String)>) -> PyResult<Vec<(String, Option<String>)>> {
        let mut results = Vec::new();

        for (source, target) in patches {
            // Calculate hash before patch
            let _before_hash = calculate_file_hash(&target).ok();

            // Read source content
            let content = match fs::read_to_string(&source) {
                Ok(c) => c,
                Err(_e) => {
                    results.push((target.clone(), None));
                    continue;
                }
            };

            // Apply atomic write with backup
            match atomic_write_with_backup_internal(&target, &content) {
                Ok(backup) => {
                    if let Some(ref b) = backup {
                        self.applied_patches.insert(target.clone(), b.clone());
                    }
                    results.push((target, backup));
                }
                Err(_) => {
                    results.push((target, None));
                }
            }
        }

        Ok(results)
    }

    /// Restore all applied patches
    fn restore_all(&self) -> PyResult<Vec<(String, bool)>> {
        let results: Vec<(String, bool)> = self
            .applied_patches
            .par_iter()
            .map(|(target, backup)| {
                let success = restore_from_backup_internal(backup, target).is_ok();
                (target.clone(), success)
            })
            .collect();

        Ok(results)
    }

    /// Get count of applied patches
    fn patch_count(&self) -> usize {
        self.applied_patches.len()
    }

    /// Acquire session lock
    fn acquire_lock(&mut self, lock_path: &str) -> PyResult<()> {
        let fd = acquire_file_lock(lock_path, Some(30))?;
        self.lock_fd = Some(fd);
        Ok(())
    }

    /// Release session lock
    fn release_lock(&mut self) -> PyResult<()> {
        if let Some(fd) = self.lock_fd {
            release_file_lock(fd)?;
            self.lock_fd = None;
        }
        Ok(())
    }
}

#[cfg(windows)]
#[pymethods]
impl PatchSessionRust {
    #[new]
    fn new() -> Self {
        PatchSessionRust {
            applied_patches: HashMap::new(),
            lock_handle: None,
        }
    }

    /// Apply a batch of patches atomically
    ///
    /// Returns list of (target, backup_path) tuples for successful patches
    fn apply_patches(&mut self, patches: Vec<(String, String)>) -> PyResult<Vec<(String, Option<String>)>> {
        let mut results = Vec::new();

        for (source, target) in patches {
            // Calculate hash before patch
            let _before_hash = calculate_file_hash(&target).ok();

            // Read source content
            let content = match fs::read_to_string(&source) {
                Ok(c) => c,
                Err(_e) => {
                    results.push((target.clone(), None));
                    continue;
                }
            };

            // Apply atomic write with backup
            match atomic_write_with_backup_internal(&target, &content) {
                Ok(backup) => {
                    if let Some(ref b) = backup {
                        self.applied_patches.insert(target.clone(), b.clone());
                    }
                    results.push((target, backup));
                }
                Err(_) => {
                    results.push((target, None));
                }
            }
        }

        Ok(results)
    }

    /// Restore all applied patches
    fn restore_all(&self) -> PyResult<Vec<(String, bool)>> {
        let results: Vec<(String, bool)> = self
            .applied_patches
            .par_iter()
            .map(|(target, backup)| {
                let success = restore_from_backup_internal(backup, target).is_ok();
                (target.clone(), success)
            })
            .collect();

        Ok(results)
    }

    /// Get count of applied patches
    fn patch_count(&self) -> usize {
        self.applied_patches.len()
    }

    /// Acquire session lock
    fn acquire_lock(&mut self, lock_path: &str) -> PyResult<()> {
        let handle = acquire_file_lock(lock_path, Some(30))?;
        self.lock_handle = Some(handle);
        Ok(())
    }

    /// Release session lock
    fn release_lock(&mut self) -> PyResult<()> {
        if let Some(handle) = self.lock_handle {
            release_file_lock(handle)?;
            self.lock_handle = None;
        }
        Ok(())
    }
}

/// Internal atomic write without Python overhead
fn atomic_write_with_backup_internal(
    target: &str,
    content: &str,
) -> Result<Option<String>, Box<dyn std::error::Error>> {
    let target_path = Path::new(target);

    // Create backup if file exists
    let backup_path: Option<PathBuf> = if target_path.exists() {
        let backup_path = std::env::temp_dir().join(format!(
            "patchon_backup_{}_{}",
            target_path.file_name().unwrap_or_default().to_string_lossy(),
            std::process::id()
        ));

        fast_file_copy_internal(target, backup_path.to_str().unwrap())?;
        Some(backup_path)
    } else {
        None
    };

    // Atomic write
    let temp_path = target_path.with_extension("tmp");
    let mut temp_file = fs::File::create(&temp_path)?;
    temp_file.write_all(content.as_bytes())?;
    drop(temp_file);

    fs::rename(&temp_path, target_path)?;

    Ok(backup_path.map(|p| p.to_string_lossy().to_string()))
}

/// Module initialization
#[pymodule]
fn _rust_ext(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fast_file_copy, m)?)?;
    m.add_function(wrap_pyfunction!(batch_copy_files, m)?)?;
    m.add_function(wrap_pyfunction!(scan_python_files, m)?)?;
    m.add_function(wrap_pyfunction!(calculate_file_hash, m)?)?;
    m.add_function(wrap_pyfunction!(atomic_write_with_backup, m)?)?;
    m.add_function(wrap_pyfunction!(restore_from_backup, m)?)?;
    m.add_function(wrap_pyfunction!(batch_restore, m)?)?;
    m.add_function(wrap_pyfunction!(acquire_file_lock, m)?)?;
    m.add_function(wrap_pyfunction!(release_file_lock, m)?)?;
    m.add_function(wrap_pyfunction!(is_process_alive, m)?)?;
    m.add_function(wrap_pyfunction!(cleanup_stale_locks, m)?)?;
    m.add_class::<PatchSessionRust>()?;

    Ok(())
}
