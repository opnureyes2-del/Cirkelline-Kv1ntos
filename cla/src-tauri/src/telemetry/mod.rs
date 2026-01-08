// Telemetry module for CLA
// Privacy-respecting usage analytics and health monitoring

pub mod metrics;
pub mod health;
pub mod reporter;

pub use metrics::*;
pub use health::*;
pub use reporter::*;

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::RwLock;

/// Telemetry configuration
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TelemetryConfig {
    /// Whether telemetry is enabled
    pub enabled: bool,
    /// Endpoint for sending telemetry data
    pub endpoint: Option<String>,
    /// How often to send reports (in seconds)
    pub report_interval_seconds: u64,
    /// Whether to include detailed metrics
    pub detailed_metrics: bool,
    /// Maximum events to buffer before sending
    pub max_buffer_size: usize,
}

impl Default for TelemetryConfig {
    fn default() -> Self {
        Self {
            enabled: false, // Opt-in by default (privacy first)
            endpoint: None,
            report_interval_seconds: 3600, // 1 hour
            detailed_metrics: false,
            max_buffer_size: 1000,
        }
    }
}

/// Telemetry event types
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum TelemetryEvent {
    /// App lifecycle events
    AppStarted {
        version: String,
        platform: String,
        timestamp: DateTime<Utc>,
    },
    AppStopped {
        uptime_seconds: u64,
        timestamp: DateTime<Utc>,
    },

    /// Inference events (anonymized)
    InferenceCompleted {
        model_id: String,
        task_type: String,
        duration_ms: u64,
        success: bool,
        timestamp: DateTime<Utc>,
    },

    /// Sync events
    SyncCompleted {
        direction: String, // "upload" | "download" | "both"
        items_count: u32,
        bytes_transferred: u64,
        duration_ms: u64,
        success: bool,
        timestamp: DateTime<Utc>,
    },

    /// Resource usage (aggregated, no personal data)
    ResourceSnapshot {
        avg_cpu_percent: f32,
        avg_ram_percent: f32,
        avg_gpu_percent: Option<f32>,
        idle_hours: f32,
        timestamp: DateTime<Utc>,
    },

    /// Error events (anonymized)
    Error {
        error_type: String,
        error_code: Option<String>,
        recoverable: bool,
        timestamp: DateTime<Utc>,
    },

    /// Feature usage (anonymous counts)
    FeatureUsed {
        feature: String,
        count: u32,
        timestamp: DateTime<Utc>,
    },
}

/// Main telemetry service
pub struct TelemetryService {
    config: Arc<RwLock<TelemetryConfig>>,
    events: Arc<RwLock<Vec<TelemetryEvent>>>,
    metrics: Arc<RwLock<AggregatedMetrics>>,
    health: Arc<RwLock<HealthStatus>>,
    session_id: String,
}

impl TelemetryService {
    pub fn new(config: TelemetryConfig) -> Self {
        Self {
            config: Arc::new(RwLock::new(config)),
            events: Arc::new(RwLock::new(Vec::new())),
            metrics: Arc::new(RwLock::new(AggregatedMetrics::default())),
            health: Arc::new(RwLock::new(HealthStatus::default())),
            session_id: generate_session_id(),
        }
    }

    /// Record a telemetry event
    pub async fn record(&self, event: TelemetryEvent) {
        let config = self.config.read().await;
        if !config.enabled {
            return;
        }

        let mut events = self.events.write().await;

        // Buffer management
        if events.len() >= config.max_buffer_size {
            events.remove(0);
        }

        events.push(event);
    }

    /// Record app start
    pub async fn record_app_start(&self, version: &str) {
        self.record(TelemetryEvent::AppStarted {
            version: version.to_string(),
            platform: std::env::consts::OS.to_string(),
            timestamp: Utc::now(),
        })
        .await;
    }

    /// Record inference completion
    pub async fn record_inference(
        &self,
        model_id: &str,
        task_type: &str,
        duration_ms: u64,
        success: bool,
    ) {
        self.record(TelemetryEvent::InferenceCompleted {
            model_id: model_id.to_string(),
            task_type: task_type.to_string(),
            duration_ms,
            success,
            timestamp: Utc::now(),
        })
        .await;

        // Update aggregated metrics
        let mut metrics = self.metrics.write().await;
        metrics.total_inferences += 1;
        if success {
            metrics.successful_inferences += 1;
        }
        metrics.total_inference_time_ms += duration_ms;
    }

    /// Record sync completion
    pub async fn record_sync(
        &self,
        direction: &str,
        items: u32,
        bytes: u64,
        duration_ms: u64,
        success: bool,
    ) {
        self.record(TelemetryEvent::SyncCompleted {
            direction: direction.to_string(),
            items_count: items,
            bytes_transferred: bytes,
            duration_ms,
            success,
            timestamp: Utc::now(),
        })
        .await;

        // Update aggregated metrics
        let mut metrics = self.metrics.write().await;
        metrics.total_syncs += 1;
        if success {
            metrics.successful_syncs += 1;
        }
        metrics.total_bytes_transferred += bytes;
    }

    /// Record an error
    pub async fn record_error(&self, error_type: &str, error_code: Option<&str>, recoverable: bool) {
        self.record(TelemetryEvent::Error {
            error_type: error_type.to_string(),
            error_code: error_code.map(|s| s.to_string()),
            recoverable,
            timestamp: Utc::now(),
        })
        .await;

        // Update health status
        let mut health = self.health.write().await;
        health.error_count += 1;
        health.last_error = Some(error_type.to_string());
    }

    /// Get current health status
    pub async fn get_health(&self) -> HealthStatus {
        self.health.read().await.clone()
    }

    /// Get aggregated metrics
    pub async fn get_metrics(&self) -> AggregatedMetrics {
        self.metrics.read().await.clone()
    }

    /// Get buffered events (for reporting)
    pub async fn get_buffered_events(&self) -> Vec<TelemetryEvent> {
        self.events.read().await.clone()
    }

    /// Clear buffered events after successful report
    pub async fn clear_buffer(&self) {
        let mut events = self.events.write().await;
        events.clear();
    }

    /// Update configuration
    pub async fn update_config(&self, config: TelemetryConfig) {
        let mut current = self.config.write().await;
        *current = config;
    }

    /// Check if telemetry is enabled
    pub async fn is_enabled(&self) -> bool {
        self.config.read().await.enabled
    }

    /// Get session ID (anonymous)
    pub fn session_id(&self) -> &str {
        &self.session_id
    }
}

/// Generate anonymous session ID
fn generate_session_id() -> String {
    use rand::Rng;
    let mut rng = rand::thread_rng();
    let bytes: [u8; 16] = rng.gen();
    hex::encode(bytes)
}

/// Aggregated metrics (no personal data)
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct AggregatedMetrics {
    pub total_inferences: u64,
    pub successful_inferences: u64,
    pub total_inference_time_ms: u64,
    pub total_syncs: u64,
    pub successful_syncs: u64,
    pub total_bytes_transferred: u64,
    pub total_uptime_seconds: u64,
    pub total_idle_seconds: u64,
}

impl AggregatedMetrics {
    pub fn inference_success_rate(&self) -> f64 {
        if self.total_inferences == 0 {
            return 0.0;
        }
        self.successful_inferences as f64 / self.total_inferences as f64
    }

    pub fn sync_success_rate(&self) -> f64 {
        if self.total_syncs == 0 {
            return 0.0;
        }
        self.successful_syncs as f64 / self.total_syncs as f64
    }

    pub fn avg_inference_time_ms(&self) -> f64 {
        if self.total_inferences == 0 {
            return 0.0;
        }
        self.total_inference_time_ms as f64 / self.total_inferences as f64
    }

    pub fn idle_percentage(&self) -> f64 {
        if self.total_uptime_seconds == 0 {
            return 0.0;
        }
        self.total_idle_seconds as f64 / self.total_uptime_seconds as f64 * 100.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_telemetry_disabled_by_default() {
        let service = TelemetryService::new(TelemetryConfig::default());
        assert!(!service.is_enabled().await);
    }

    #[tokio::test]
    async fn test_record_when_disabled() {
        let service = TelemetryService::new(TelemetryConfig::default());
        service.record_app_start("1.0.0").await;

        let events = service.get_buffered_events().await;
        assert!(events.is_empty());
    }

    #[tokio::test]
    async fn test_record_when_enabled() {
        let config = TelemetryConfig {
            enabled: true,
            ..Default::default()
        };
        let service = TelemetryService::new(config);
        service.record_app_start("1.0.0").await;

        let events = service.get_buffered_events().await;
        assert_eq!(events.len(), 1);
    }

    #[tokio::test]
    async fn test_inference_metrics() {
        let config = TelemetryConfig {
            enabled: true,
            ..Default::default()
        };
        let service = TelemetryService::new(config);

        service.record_inference("model1", "embedding", 100, true).await;
        service.record_inference("model1", "embedding", 150, true).await;
        service.record_inference("model1", "embedding", 200, false).await;

        let metrics = service.get_metrics().await;
        assert_eq!(metrics.total_inferences, 3);
        assert_eq!(metrics.successful_inferences, 2);
        assert!((metrics.inference_success_rate() - 0.666).abs() < 0.01);
    }

    #[test]
    fn test_session_id_uniqueness() {
        let id1 = generate_session_id();
        let id2 = generate_session_id();
        assert_ne!(id1, id2);
        assert_eq!(id1.len(), 32);
    }
}
