//! Cirkelline Native Extensions
//!
//! High-performance Rust implementations for performance-critical operations.
//!
//! Build: maturin develop --release
//! Install: pip install .

use moka::sync::Cache;
use parking_lot::RwLock;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};
use std::collections::HashMap;
use std::sync::Arc;
use std::time::Duration;
use xxhash_rust::xxh3::xxh3_64;

/// High-performance LRU cache with TTL support
#[pyclass]
pub struct NativeCache {
    cache: Cache<String, String>,
    stats: Arc<RwLock<CacheStats>>,
}

struct CacheStats {
    hits: u64,
    misses: u64,
    evictions: u64,
}

#[pymethods]
impl NativeCache {
    /// Create a new cache with specified capacity and TTL
    #[new]
    #[pyo3(signature = (max_size=10000, ttl_seconds=300))]
    fn new(max_size: u64, ttl_seconds: u64) -> Self {
        let cache = Cache::builder()
            .max_capacity(max_size)
            .time_to_live(Duration::from_secs(ttl_seconds))
            .build();

        NativeCache {
            cache,
            stats: Arc::new(RwLock::new(CacheStats {
                hits: 0,
                misses: 0,
                evictions: 0,
            })),
        }
    }

    /// Get a value from the cache
    fn get(&self, key: &str) -> Option<String> {
        let result = self.cache.get(key);
        let mut stats = self.stats.write();
        if result.is_some() {
            stats.hits += 1;
        } else {
            stats.misses += 1;
        }
        result
    }

    /// Set a value in the cache
    fn set(&self, key: &str, value: &str) {
        self.cache.insert(key.to_string(), value.to_string());
    }

    /// Delete a key from the cache
    fn delete(&self, key: &str) -> bool {
        self.cache.invalidate(key);
        true
    }

    /// Check if key exists
    fn exists(&self, key: &str) -> bool {
        self.cache.contains_key(key)
    }

    /// Clear all entries
    fn clear(&self) {
        self.cache.invalidate_all();
    }

    /// Get cache statistics
    fn get_stats(&self, py: Python<'_>) -> PyResult<PyObject> {
        let stats = self.stats.read();
        let dict = PyDict::new(py);
        dict.set_item("hits", stats.hits)?;
        dict.set_item("misses", stats.misses)?;
        dict.set_item("size", self.cache.entry_count())?;

        let total = stats.hits + stats.misses;
        let hit_rate = if total > 0 {
            stats.hits as f64 / total as f64
        } else {
            0.0
        };
        dict.set_item("hit_rate", hit_rate)?;

        Ok(dict.into())
    }

    /// Get current size
    fn size(&self) -> u64 {
        self.cache.entry_count()
    }
}

/// Fast string hashing using xxHash3
#[pyfunction]
fn fast_hash(data: &str) -> u64 {
    xxh3_64(data.as_bytes())
}

/// Fast cache key builder
#[pyfunction]
fn build_cache_key(parts: Vec<&str>) -> String {
    let combined = parts.join(":");
    if combined.len() > 200 {
        format!("hash:{:x}", xxh3_64(combined.as_bytes()))
    } else {
        combined
    }
}

/// Batch hash multiple strings
#[pyfunction]
fn batch_hash(items: Vec<&str>) -> Vec<u64> {
    items.iter().map(|s| xxh3_64(s.as_bytes())).collect()
}

/// Fast JSON key extraction (for cache key building)
#[pyfunction]
fn extract_json_keys(json_str: &str, keys: Vec<&str>) -> PyResult<HashMap<String, String>> {
    let value: serde_json::Value = serde_json::from_str(json_str)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;

    let mut result = HashMap::new();

    if let serde_json::Value::Object(map) = value {
        for key in keys {
            if let Some(val) = map.get(key) {
                let str_val = match val {
                    serde_json::Value::String(s) => s.clone(),
                    _ => val.to_string(),
                };
                result.insert(key.to_string(), str_val);
            }
        }
    }

    Ok(result)
}

/// Python module definition
#[pymodule]
fn cirkelline_native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<NativeCache>()?;
    m.add_function(wrap_pyfunction!(fast_hash, m)?)?;
    m.add_function(wrap_pyfunction!(build_cache_key, m)?)?;
    m.add_function(wrap_pyfunction!(batch_hash, m)?)?;
    m.add_function(wrap_pyfunction!(extract_json_keys, m)?)?;

    // Module metadata
    m.add("__version__", "0.1.0")?;
    m.add("__author__", "Cirkelline Team")?;

    Ok(())
}
