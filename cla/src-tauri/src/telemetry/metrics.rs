// Metrics collection for CLA
// Collects and aggregates performance metrics

use chrono::{DateTime, Duration, Utc};
use serde::{Deserialize, Serialize};
use std::collections::VecDeque;
use std::sync::Arc;
use tokio::sync::RwLock;

/// Performance metrics collector
pub struct MetricsCollector {
    /// Inference latency samples (ms)
    inference_latencies: Arc<RwLock<VecDeque<LatencySample>>>,
    /// Sync latency samples (ms)
    sync_latencies: Arc<RwLock<VecDeque<LatencySample>>>,
    /// Resource usage samples
    resource_samples: Arc<RwLock<VecDeque<ResourceSample>>>,
    /// Error counts by type
    error_counts: Arc<RwLock<std::collections::HashMap<String, u64>>>,
    /// Maximum samples to keep
    max_samples: usize,
}

impl MetricsCollector {
    pub fn new(max_samples: usize) -> Self {
        Self {
            inference_latencies: Arc::new(RwLock::new(VecDeque::with_capacity(max_samples))),
            sync_latencies: Arc::new(RwLock::new(VecDeque::with_capacity(max_samples))),
            resource_samples: Arc::new(RwLock::new(VecDeque::with_capacity(max_samples))),
            error_counts: Arc::new(RwLock::new(std::collections::HashMap::new())),
            max_samples,
        }
    }

    /// Record inference latency
    pub async fn record_inference_latency(&self, model_id: &str, latency_ms: u64) {
        let mut latencies = self.inference_latencies.write().await;

        if latencies.len() >= self.max_samples {
            latencies.pop_front();
        }

        latencies.push_back(LatencySample {
            label: model_id.to_string(),
            latency_ms,
            timestamp: Utc::now(),
        });
    }

    /// Record sync latency
    pub async fn record_sync_latency(&self, direction: &str, latency_ms: u64) {
        let mut latencies = self.sync_latencies.write().await;

        if latencies.len() >= self.max_samples {
            latencies.pop_front();
        }

        latencies.push_back(LatencySample {
            label: direction.to_string(),
            latency_ms,
            timestamp: Utc::now(),
        });
    }

    /// Record resource usage
    pub async fn record_resource_usage(&self, cpu: f32, ram: f32, gpu: Option<f32>, idle: bool) {
        let mut samples = self.resource_samples.write().await;

        if samples.len() >= self.max_samples {
            samples.pop_front();
        }

        samples.push_back(ResourceSample {
            cpu_percent: cpu,
            ram_percent: ram,
            gpu_percent: gpu,
            is_idle: idle,
            timestamp: Utc::now(),
        });
    }

    /// Record error
    pub async fn record_error(&self, error_type: &str) {
        let mut counts = self.error_counts.write().await;
        *counts.entry(error_type.to_string()).or_insert(0) += 1;
    }

    /// Get inference latency statistics
    pub async fn get_inference_stats(&self) -> LatencyStats {
        let latencies = self.inference_latencies.read().await;
        calculate_latency_stats(&latencies)
    }

    /// Get sync latency statistics
    pub async fn get_sync_stats(&self) -> LatencyStats {
        let latencies = self.sync_latencies.read().await;
        calculate_latency_stats(&latencies)
    }

    /// Get resource usage statistics
    pub async fn get_resource_stats(&self) -> ResourceStats {
        let samples = self.resource_samples.read().await;
        calculate_resource_stats(&samples)
    }

    /// Get error statistics
    pub async fn get_error_stats(&self) -> std::collections::HashMap<String, u64> {
        self.error_counts.read().await.clone()
    }

    /// Get summary metrics for reporting
    pub async fn get_summary(&self) -> MetricsSummary {
        MetricsSummary {
            inference: self.get_inference_stats().await,
            sync: self.get_sync_stats().await,
            resources: self.get_resource_stats().await,
            errors: self.get_error_stats().await,
            timestamp: Utc::now(),
        }
    }

    /// Clear all metrics (useful after successful report)
    pub async fn clear(&self) {
        self.inference_latencies.write().await.clear();
        self.sync_latencies.write().await.clear();
        self.resource_samples.write().await.clear();
        self.error_counts.write().await.clear();
    }
}

impl Default for MetricsCollector {
    fn default() -> Self {
        Self::new(1000)
    }
}

/// Latency sample
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LatencySample {
    pub label: String,
    pub latency_ms: u64,
    pub timestamp: DateTime<Utc>,
}

/// Resource usage sample
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ResourceSample {
    pub cpu_percent: f32,
    pub ram_percent: f32,
    pub gpu_percent: Option<f32>,
    pub is_idle: bool,
    pub timestamp: DateTime<Utc>,
}

/// Latency statistics
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct LatencyStats {
    pub count: u64,
    pub min_ms: u64,
    pub max_ms: u64,
    pub avg_ms: f64,
    pub p50_ms: u64,
    pub p95_ms: u64,
    pub p99_ms: u64,
}

/// Resource usage statistics
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct ResourceStats {
    pub sample_count: u64,
    pub avg_cpu_percent: f32,
    pub avg_ram_percent: f32,
    pub avg_gpu_percent: Option<f32>,
    pub max_cpu_percent: f32,
    pub max_ram_percent: f32,
    pub idle_percentage: f32,
}

/// Complete metrics summary
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct MetricsSummary {
    pub inference: LatencyStats,
    pub sync: LatencyStats,
    pub resources: ResourceStats,
    pub errors: std::collections::HashMap<String, u64>,
    pub timestamp: DateTime<Utc>,
}

/// Calculate latency statistics from samples
fn calculate_latency_stats(samples: &VecDeque<LatencySample>) -> LatencyStats {
    if samples.is_empty() {
        return LatencyStats::default();
    }

    let mut latencies: Vec<u64> = samples.iter().map(|s| s.latency_ms).collect();
    latencies.sort_unstable();

    let count = latencies.len() as u64;
    let sum: u64 = latencies.iter().sum();

    LatencyStats {
        count,
        min_ms: *latencies.first().unwrap_or(&0),
        max_ms: *latencies.last().unwrap_or(&0),
        avg_ms: sum as f64 / count as f64,
        p50_ms: percentile(&latencies, 50),
        p95_ms: percentile(&latencies, 95),
        p99_ms: percentile(&latencies, 99),
    }
}

/// Calculate percentile from sorted values
fn percentile(sorted_values: &[u64], p: usize) -> u64 {
    if sorted_values.is_empty() {
        return 0;
    }

    let index = (p as f64 / 100.0 * (sorted_values.len() - 1) as f64).round() as usize;
    sorted_values[index.min(sorted_values.len() - 1)]
}

/// Calculate resource statistics from samples
fn calculate_resource_stats(samples: &VecDeque<ResourceSample>) -> ResourceStats {
    if samples.is_empty() {
        return ResourceStats::default();
    }

    let count = samples.len() as f32;
    let sum_cpu: f32 = samples.iter().map(|s| s.cpu_percent).sum();
    let sum_ram: f32 = samples.iter().map(|s| s.ram_percent).sum();
    let sum_gpu: Option<f32> = {
        let gpu_samples: Vec<f32> = samples.iter().filter_map(|s| s.gpu_percent).collect();
        if gpu_samples.is_empty() {
            None
        } else {
            Some(gpu_samples.iter().sum::<f32>() / gpu_samples.len() as f32)
        }
    };

    let max_cpu = samples.iter().map(|s| s.cpu_percent).fold(0.0f32, f32::max);
    let max_ram = samples.iter().map(|s| s.ram_percent).fold(0.0f32, f32::max);
    let idle_count = samples.iter().filter(|s| s.is_idle).count() as f32;

    ResourceStats {
        sample_count: samples.len() as u64,
        avg_cpu_percent: sum_cpu / count,
        avg_ram_percent: sum_ram / count,
        avg_gpu_percent: sum_gpu,
        max_cpu_percent: max_cpu,
        max_ram_percent: max_ram,
        idle_percentage: (idle_count / count) * 100.0,
    }
}

/// Rate limiter for metrics collection
pub struct MetricsRateLimiter {
    last_collection: Arc<RwLock<DateTime<Utc>>>,
    min_interval: Duration,
}

impl MetricsRateLimiter {
    pub fn new(min_interval_seconds: i64) -> Self {
        Self {
            last_collection: Arc::new(RwLock::new(Utc::now() - Duration::seconds(min_interval_seconds))),
            min_interval: Duration::seconds(min_interval_seconds),
        }
    }

    pub async fn should_collect(&self) -> bool {
        let last = *self.last_collection.read().await;
        Utc::now() - last >= self.min_interval
    }

    pub async fn mark_collected(&self) {
        *self.last_collection.write().await = Utc::now();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_inference_latency_recording() {
        let collector = MetricsCollector::new(100);

        collector.record_inference_latency("model1", 100).await;
        collector.record_inference_latency("model1", 150).await;
        collector.record_inference_latency("model1", 200).await;

        let stats = collector.get_inference_stats().await;
        assert_eq!(stats.count, 3);
        assert_eq!(stats.min_ms, 100);
        assert_eq!(stats.max_ms, 200);
        assert!((stats.avg_ms - 150.0).abs() < 0.01);
    }

    #[tokio::test]
    async fn test_resource_recording() {
        let collector = MetricsCollector::new(100);

        collector.record_resource_usage(20.0, 30.0, None, true).await;
        collector.record_resource_usage(40.0, 50.0, None, false).await;

        let stats = collector.get_resource_stats().await;
        assert_eq!(stats.sample_count, 2);
        assert!((stats.avg_cpu_percent - 30.0).abs() < 0.01);
        assert!((stats.idle_percentage - 50.0).abs() < 0.01);
    }

    #[tokio::test]
    async fn test_error_counting() {
        let collector = MetricsCollector::new(100);

        collector.record_error("network").await;
        collector.record_error("network").await;
        collector.record_error("disk").await;

        let errors = collector.get_error_stats().await;
        assert_eq!(errors.get("network"), Some(&2));
        assert_eq!(errors.get("disk"), Some(&1));
    }

    #[test]
    fn test_percentile_calculation() {
        let values: Vec<u64> = (1..=100).collect();
        assert_eq!(percentile(&values, 50), 50);
        assert_eq!(percentile(&values, 95), 95);
        assert_eq!(percentile(&values, 99), 99);
    }

    #[tokio::test]
    async fn test_max_samples_limit() {
        let collector = MetricsCollector::new(5);

        for i in 0..10 {
            collector.record_inference_latency("model", i * 10).await;
        }

        let stats = collector.get_inference_stats().await;
        assert_eq!(stats.count, 5);
        // Should keep the last 5 samples
        assert_eq!(stats.min_ms, 50);
    }
}
