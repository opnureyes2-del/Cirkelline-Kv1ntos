// Telemetry reporter for CLA
// Sends anonymized telemetry to CKC (when enabled)

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::RwLock;
use tokio::time::{interval, Duration};

use super::{TelemetryConfig, TelemetryEvent, TelemetryService, MetricsSummary};
use crate::error::{ClaError, ClaResult};

/// Telemetry report structure
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TelemetryReport {
    /// Anonymous session ID
    pub session_id: String,
    /// CLA version
    pub version: String,
    /// Platform (os)
    pub platform: String,
    /// Report timestamp
    pub timestamp: DateTime<Utc>,
    /// Metrics summary
    pub metrics: MetricsSummary,
    /// Events since last report
    pub events: Vec<TelemetryEvent>,
    /// Report sequence number
    pub sequence: u64,
}

/// Telemetry reporter service
pub struct TelemetryReporter {
    config: Arc<RwLock<TelemetryConfig>>,
    telemetry_service: Arc<TelemetryService>,
    sequence: Arc<RwLock<u64>>,
    version: String,
    http_client: reqwest::Client,
}

impl TelemetryReporter {
    pub fn new(
        config: TelemetryConfig,
        telemetry_service: Arc<TelemetryService>,
        version: &str,
    ) -> Self {
        Self {
            config: Arc::new(RwLock::new(config)),
            telemetry_service,
            sequence: Arc::new(RwLock::new(0)),
            version: version.to_string(),
            http_client: reqwest::Client::builder()
                .timeout(Duration::from_secs(30))
                .build()
                .expect("Failed to create HTTP client"),
        }
    }

    /// Start the background reporting task
    pub fn start(self: Arc<Self>) {
        tokio::spawn(async move {
            self.run_reporter_loop().await;
        });
    }

    /// Main reporter loop
    async fn run_reporter_loop(&self) {
        let mut report_interval = interval(Duration::from_secs(3600)); // Default 1 hour

        loop {
            report_interval.tick().await;

            // Check if telemetry is enabled
            let config = self.config.read().await;
            if !config.enabled {
                continue;
            }

            let interval_secs = config.report_interval_seconds;
            drop(config);

            // Update interval if changed
            report_interval = interval(Duration::from_secs(interval_secs));

            // Try to send report
            if let Err(e) = self.send_report().await {
                log::warn!("Failed to send telemetry report: {}", e);
            }
        }
    }

    /// Send a telemetry report
    pub async fn send_report(&self) -> ClaResult<()> {
        let config = self.config.read().await;

        if !config.enabled {
            return Ok(());
        }

        let endpoint = config.endpoint.clone().ok_or_else(|| {
            ClaError::Config(crate::error::ConfigError::MissingRequired { key: "telemetry_endpoint".to_string() })
        })?;

        drop(config);

        // Build report
        let report = self.build_report().await?;

        // Send report
        let response = self
            .http_client
            .post(&format!("{}/api/cla/telemetry", endpoint))
            .json(&report)
            .send()
            .await
            .map_err(|e| ClaError::Network(crate::error::NetworkError::ConnectionFailed {
                url: endpoint.clone(),
                reason: e.to_string(),
            }))?;

        if response.status().is_success() {
            // Clear buffer on successful send
            self.telemetry_service.clear_buffer().await;

            // Increment sequence
            let mut seq = self.sequence.write().await;
            *seq += 1;

            log::info!("Telemetry report sent successfully");
            Ok(())
        } else {
            Err(ClaError::Network(crate::error::NetworkError::InvalidResponse {
                status: response.status().as_u16(),
                body: format!("Server returned {}", response.status()),
            }))
        }
    }

    /// Build a telemetry report
    async fn build_report(&self) -> ClaResult<TelemetryReport> {
        let metrics = self.telemetry_service.get_metrics().await;
        let events = self.telemetry_service.get_buffered_events().await;
        let sequence = *self.sequence.read().await;

        // Build metrics summary from collected data
        let summary = MetricsSummary {
            inference: crate::telemetry::metrics::LatencyStats {
                count: metrics.total_inferences,
                min_ms: 0,
                max_ms: 0,
                avg_ms: metrics.avg_inference_time_ms(),
                p50_ms: 0,
                p95_ms: 0,
                p99_ms: 0,
            },
            sync: crate::telemetry::metrics::LatencyStats::default(),
            resources: crate::telemetry::metrics::ResourceStats {
                sample_count: 0,
                avg_cpu_percent: 0.0,
                avg_ram_percent: 0.0,
                avg_gpu_percent: None,
                max_cpu_percent: 0.0,
                max_ram_percent: 0.0,
                idle_percentage: metrics.idle_percentage() as f32,
            },
            errors: std::collections::HashMap::new(),
            timestamp: Utc::now(),
        };

        Ok(TelemetryReport {
            session_id: self.telemetry_service.session_id().to_string(),
            version: self.version.clone(),
            platform: std::env::consts::OS.to_string(),
            timestamp: Utc::now(),
            metrics: summary,
            events,
            sequence,
        })
    }

    /// Update configuration
    pub async fn update_config(&self, config: TelemetryConfig) {
        let mut current = self.config.write().await;
        *current = config.clone();

        // Also update service config
        self.telemetry_service.update_config(config).await;
    }

    /// Force send a report now
    pub async fn force_report(&self) -> ClaResult<()> {
        self.send_report().await
    }
}

/// Telemetry consent manager
pub struct ConsentManager {
    consent_given: Arc<RwLock<bool>>,
    consent_timestamp: Arc<RwLock<Option<DateTime<Utc>>>>,
}

impl ConsentManager {
    pub fn new() -> Self {
        Self {
            consent_given: Arc::new(RwLock::new(false)),
            consent_timestamp: Arc::new(RwLock::new(None)),
        }
    }

    /// Check if consent has been given
    pub async fn has_consent(&self) -> bool {
        *self.consent_given.read().await
    }

    /// Give consent
    pub async fn give_consent(&self) {
        *self.consent_given.write().await = true;
        *self.consent_timestamp.write().await = Some(Utc::now());
    }

    /// Revoke consent
    pub async fn revoke_consent(&self) {
        *self.consent_given.write().await = false;
    }

    /// Get consent timestamp
    pub async fn consent_timestamp(&self) -> Option<DateTime<Utc>> {
        *self.consent_timestamp.read().await
    }

    /// Get consent status for UI
    pub async fn get_status(&self) -> ConsentStatus {
        ConsentStatus {
            consented: self.has_consent().await,
            timestamp: self.consent_timestamp().await,
        }
    }
}

impl Default for ConsentManager {
    fn default() -> Self {
        Self::new()
    }
}

/// Consent status for UI
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ConsentStatus {
    pub consented: bool,
    pub timestamp: Option<DateTime<Utc>>,
}

/// Privacy information to display to users
pub const PRIVACY_INFO: &str = r#"
CLA Telemetry - Privacy Information

When enabled, CLA collects anonymous usage data to help improve the application.

What we collect:
- Performance metrics (latency, success rates)
- Error types (no error messages or stack traces)
- Feature usage counts
- Resource utilization patterns

What we DON'T collect:
- Personal information
- File contents or paths
- User identifiers
- IP addresses (anonymized on server)
- Conversation content
- Memory contents

Data is:
- Encrypted in transit (HTTPS)
- Aggregated and anonymized
- Deleted after 90 days
- Never sold or shared

You can disable telemetry at any time in Settings.
"#;

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_consent_manager() {
        let manager = ConsentManager::new();

        assert!(!manager.has_consent().await);

        manager.give_consent().await;
        assert!(manager.has_consent().await);
        assert!(manager.consent_timestamp().await.is_some());

        manager.revoke_consent().await;
        assert!(!manager.has_consent().await);
    }

    #[test]
    fn test_privacy_info_not_empty() {
        assert!(!PRIVACY_INFO.is_empty());
        assert!(PRIVACY_INFO.contains("NOT collect"));
    }
}
