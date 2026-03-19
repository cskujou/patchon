//! patchon-rust: High-performance core for Python hot patching
//!
//! This module provides optimized operations for:
//! - Fast file scanning and copying
//! - Atomic file operations with backups
//! - Parallel processing of batch operations
//! - File locking for concurrent safety

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use rayon::prelude::*;
use std::collections::HashMap;
use std::fs;
use std::io::{Read, Write};
use std::os::unix::fs::PermissionsExt;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

/// File operation result for batch processing
#[derive(Debug)]
struct FileOpResult {
    source: String,
    target: String,
    success: bool,
    error: Option<String>,
}

/// Batch file copy with parallel processing
/// 
/// Operations are processed in parallel using Rayon for maximum performance
#[pyfunction]
fn batch_copy_files(operations: Vec<(String, String)>) -> PyResult<Vec<Option<String>>> {
    let results: Vec<Option<String>> = operations
        .par_iter()
        .map(|(src, dst)| {
            match fast_file_copy_internal(src, dst) {
                Ok(_) => None,
                Err(e) => Some(e.to_string()),
            }
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
    fast_file_copy_internal(src, dst)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))
}

/// Scan Python files in directory with optimized parallel walker
#[pyfunction]
fn scan_python_files(dir: &str, recursive: Option<bool>) -> PyResult<Vec<String>> {
    let recursive = recursive.unwrap_or(true);
    let path = PathBuf::from(dir);
    
    let mut walker = WalkDir::new(&path);
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
        .filter_map(|entry: Result<walkdir::DirEntry, walkdir::Error>| {
            match entry {
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
            }
        })
        .collect();
    
    Ok(files)
}

/// Calculate file hash for change detection (xxhash-inspired fast hash)
#[pyfunction]
fn calculate_file_hash(path: &str) -> PyResult<u64> {
    use std::collections::hash_map::DefaultHasher;
    use std::hash::{Hash, Hasher};
    
    let content = fs::read(path)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(format!("Failed to read file: {}", e)))?;
    
    let mut hasher = DefaultHasher::new();
    content.hash(&mut hasher);
    Ok(hasher.finish())
}

/// Atomic file write with automatic backup creation
/// 
/// Returns the backup path if a backup was created, None if target didn't exist
#[pyfunction]
fn atomic_write_with_backup(
    target: &str, 
    content: &str, 
    backup_dir: Option<&str>
) -> PyResult<Option<String>> {
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
            .map_err(|e| pyo3::exceptions::PyIOError::new_err(
                format!("Failed to create backup: {}", e)
            ))?;
        
        Some(backup_path)
    } else {
        None
    };
    
    // Atomic write using temp file + rename
    let temp_path = target_path.with_extension("tmp");
    fs::write(&temp_path, content)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(
            format!("Failed to write temp file: {}", e)
        ))?;
    
    fs::rename(&temp_path, target_path)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(
            format!("Failed to rename: {}", e)
        ))?;
    
    Ok(backup_path.map(|p| p.to_string_lossy().to_string()))
}

/// Restore file from backup
#[pyfunction]
fn restore_from_backup(backup_path: &str, target: &str) -> PyResult<()> {
    fast_file_copy_internal(backup_path, target)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(
            format!("Failed to restore backup: {}", e)
        ))
}

/// Batch restore operations in parallel
#[pyfunction]
fn batch_restore(backups: Vec<(String, String)>) -> PyResult<Vec<Option<String>>> {
    let results: Vec<Option<String>> = backups
        .par_iter()
        .map(|(backup, target)| {
            match restore_from_backup_internal(backup, target) {
                Ok(_) => None,
                Err(e) => Some(format!("Failed to restore {}: {}", target, e)),
            }
        })
        .collect();
    
    Ok(results)
}

fn restore_from_backup_internal(backup: &str, target: &str) -> Result<(), Box<dyn std::error::Error>> {
    fast_file_copy_internal(backup, target)
}

/// File lock for preventing concurrent patch operations
#[pyfunction]
fn acquire_file_lock(lock_path: &str, timeout_secs: Option<u64>) -> PyResult<i32> {
    use nix::fcntl::{flock, FlockArg, open};
    use nix::unistd::close;
    use nix::sys::stat::Mode;
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
            Err(e) => {
                if start.elapsed() > timeout {
                    return Err(pyo3::exceptions::PyTimeoutError::new_err(
                        format!("Failed to open lock file: {}", e)
                    ));
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
                        "Failed to acquire lock within timeout"
                    ));
                }
                std::thread::sleep(Duration::from_millis(10));
            }
        }
    }
}

#[pyfunction]
fn release_file_lock(fd: i32) -> PyResult<()> {
    use nix::fcntl::{flock, FlockArg};
    use nix::unistd::close;
    
    flock(fd, FlockArg::UnlockNonblock)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(format!("Failed to unlock: {}", e)))?;
    
    close(fd)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(format!("Failed to close: {}", e)))?;
    
    Ok(())
}

/// Check if a process is still alive
#[pyfunction]
fn is_process_alive(pid: i32) -> bool {
    use nix::sys::signal::kill;
    
    match kill(nix::unistd::Pid::from_raw(pid), None) {
        Ok(_) => true,
        Err(_) => false,
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

fn try_acquire_lock(path: &Path) -> Result<i32, Box<dyn std::error::Error>> {
    use nix::fcntl::{flock, FlockArg};
    use nix::unistd::close;
    use nix::sys::stat::Mode;
    
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

/// High-level patch session management
/// 
/// This struct manages the entire lifecycle of a patching session
#[pyclass]
struct PatchSessionRust {
    applied_patches: HashMap<String, String>, // target -> backup_path
    lock_fd: Option<i32>,
}

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
                Err(e) => {
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
        let results: Vec<(String, bool)> = self.applied_patches
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

/// Internal atomic write without Python overhead
fn atomic_write_with_backup_internal(
    target: &str,
    content: &str
) -> Result<Option<String>, Box<dyn std::error::Error>> {
    use std::io::Write;
    
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
fn patchon_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
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
