// Health monitoring for CLA
// Tracks system health and component status

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Overall health status
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct HealthStatus {
    /// Overall health state
    pub state: HealthState,
    /// Component-level health
    pub components: HashMap<String, ComponentHealth>,
    /// Error count since start
    pub error_count: u64,
    /// Last error message
    pub last_error: Option<String>,
    /// Last health check time
    pub last_check: DateTime<Utc>,
    /// Uptime in seconds
    pub uptime_seconds: u64,
}

impl Default for HealthStatus {
    fn default() -> Self {
        Self {
            state: HealthState::Healthy,
            components: default_components(),
            error_count: 0,
            last_error: None,
            last_check: Utc::now(),
            uptime_seconds: 0,
        }
    }
}

impl HealthStatus {
    /// Update overall state based on component health
    pub fn update_state(&mut self) {
        let unhealthy_count = self.components.values()
            .filter(|c| c.state == HealthState::Unhealthy)
            .count();

        let degraded_count = self.components.values()
            .filter(|c| c.state == HealthState::Degraded)
            .count();

        self.state = if unhealthy_count > 0 {
            HealthState::Unhealthy
        } else if degraded_count > 0 {
            HealthState::Degraded
        } else {
            HealthState::Healthy
        };

        self.last_check = Utc::now();
    }

    /// Set component health
    pub fn set_component_health(&mut self, name: &str, health: ComponentHealth) {
        self.components.insert(name.to_string(), health);
        self.update_state();
    }

    /// Get component health
    pub fn get_component(&self, name: &str) -> Option<&ComponentHealth> {
        self.components.get(name)
    }

    /// Check if system is healthy enough to run tasks
    pub fn can_run_tasks(&self) -> bool {
        matches!(self.state, HealthState::Healthy | HealthState::Degraded)
    }
}

/// Health state enum
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum HealthState {
    Healthy,
    Degraded,
    Unhealthy,
}

/// Individual component health
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ComponentHealth {
    pub state: HealthState,
    pub message: Option<String>,
    pub last_check: DateTime<Utc>,
    pub consecutive_failures: u32,
}

impl Default for ComponentHealth {
    fn default() -> Self {
        Self {
            state: HealthState::Healthy,
            message: None,
            last_check: Utc::now(),
            consecutive_failures: 0,
        }
    }
}

impl ComponentHealth {
    pub fn healthy() -> Self {
        Self::default()
    }

    pub fn degraded(message: &str) -> Self {
        Self {
            state: HealthState::Degraded,
            message: Some(message.to_string()),
            last_check: Utc::now(),
            consecutive_failures: 0,
        }
    }

    pub fn unhealthy(message: &str, failures: u32) -> Self {
        Self {
            state: HealthState::Unhealthy,
            message: Some(message.to_string()),
            last_check: Utc::now(),
            consecutive_failures: failures,
        }
    }

    pub fn record_success(&mut self) {
        self.state = HealthState::Healthy;
        self.message = None;
        self.consecutive_failures = 0;
        self.last_check = Utc::now();
    }

    pub fn record_failure(&mut self, message: &str) {
        self.consecutive_failures += 1;
        self.message = Some(message.to_string());
        self.last_check = Utc::now();

        // After 3 consecutive failures, mark as unhealthy
        self.state = if self.consecutive_failures >= 3 {
            HealthState::Unhealthy
        } else {
            HealthState::Degraded
        };
    }
}

/// Create default component health map
fn default_components() -> HashMap<String, ComponentHealth> {
    let mut components = HashMap::new();

    components.insert("database".to_string(), ComponentHealth::healthy());
    components.insert("inference_engine".to_string(), ComponentHealth::healthy());
    components.insert("sync_service".to_string(), ComponentHealth::healthy());
    components.insert("resource_monitor".to_string(), ComponentHealth::healthy());

    components
}

/// Health check runner
pub struct HealthChecker {
    checks: Vec<Box<dyn HealthCheck + Send + Sync>>,
}

impl HealthChecker {
    pub fn new() -> Self {
        Self { checks: Vec::new() }
    }

    pub fn add_check<C: HealthCheck + Send + Sync + 'static>(&mut self, check: C) {
        self.checks.push(Box::new(check));
    }

    pub async fn run_all(&self, status: &mut HealthStatus) {
        for check in &self.checks {
            let result = check.check().await;
            status.set_component_health(check.name(), result);
        }
    }
}

impl Default for HealthChecker {
    fn default() -> Self {
        Self::new()
    }
}

/// Health check trait
#[async_trait::async_trait]
pub trait HealthCheck {
    fn name(&self) -> &str;
    async fn check(&self) -> ComponentHealth;
}

/// Database health check
pub struct DatabaseHealthCheck;

#[async_trait::async_trait]
impl HealthCheck for DatabaseHealthCheck {
    fn name(&self) -> &str {
        "database"
    }

    async fn check(&self) -> ComponentHealth {
        // In real implementation, would check IndexedDB status
        ComponentHealth::healthy()
    }
}

/// Inference engine health check
pub struct InferenceHealthCheck;

#[async_trait::async_trait]
impl HealthCheck for InferenceHealthCheck {
    fn name(&self) -> &str {
        "inference_engine"
    }

    async fn check(&self) -> ComponentHealth {
        // In real implementation, would check ONNX runtime status
        ComponentHealth::healthy()
    }
}

/// Sync service health check
pub struct SyncHealthCheck {
    pub endpoint: String,
}

#[async_trait::async_trait]
impl HealthCheck for SyncHealthCheck {
    fn name(&self) -> &str {
        "sync_service"
    }

    async fn check(&self) -> ComponentHealth {
        // In real implementation, would ping CKC endpoint
        match reqwest::Client::new()
            .get(&format!("{}/health", self.endpoint))
            .timeout(std::time::Duration::from_secs(5))
            .send()
            .await
        {
            Ok(resp) if resp.status().is_success() => ComponentHealth::healthy(),
            Ok(_) => ComponentHealth::degraded("CKC returned non-200 status"),
            Err(e) => {
                if e.is_timeout() {
                    ComponentHealth::degraded("CKC connection timeout")
                } else {
                    ComponentHealth::unhealthy(&format!("CKC unreachable: {}", e), 1)
                }
            }
        }
    }
}

/// System resource health check
pub struct ResourceHealthCheck {
    pub max_cpu_percent: f32,
    pub max_ram_percent: f32,
}

#[async_trait::async_trait]
impl HealthCheck for ResourceHealthCheck {
    fn name(&self) -> &str {
        "resource_monitor"
    }

    async fn check(&self) -> ComponentHealth {
        // In real implementation, would check system resources
        let mut sys = sysinfo::System::new();
        sys.refresh_all();

        let cpu_usage = sys.global_cpu_info().cpu_usage();
        let ram_usage = (sys.used_memory() as f64 / sys.total_memory() as f64 * 100.0) as f32;

        if cpu_usage > 95.0 || ram_usage > 95.0 {
            ComponentHealth::unhealthy("System resources critically low", 1)
        } else if cpu_usage > self.max_cpu_percent * 2.0 || ram_usage > self.max_ram_percent * 2.0 {
            ComponentHealth::degraded("System resources constrained")
        } else {
            ComponentHealth::healthy()
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_health_status_default() {
        let status = HealthStatus::default();
        assert_eq!(status.state, HealthState::Healthy);
        assert_eq!(status.error_count, 0);
    }

    #[test]
    fn test_component_failure_tracking() {
        let mut component = ComponentHealth::healthy();

        component.record_failure("Error 1");
        assert_eq!(component.state, HealthState::Degraded);
        assert_eq!(component.consecutive_failures, 1);

        component.record_failure("Error 2");
        component.record_failure("Error 3");
        assert_eq!(component.state, HealthState::Unhealthy);
        assert_eq!(component.consecutive_failures, 3);
    }

    #[test]
    fn test_component_recovery() {
        let mut component = ComponentHealth::unhealthy("Failed", 3);

        component.record_success();
        assert_eq!(component.state, HealthState::Healthy);
        assert_eq!(component.consecutive_failures, 0);
    }

    #[test]
    fn test_overall_state_calculation() {
        let mut status = HealthStatus::default();

        // All healthy
        status.update_state();
        assert_eq!(status.state, HealthState::Healthy);

        // One degraded
        status.set_component_health("database", ComponentHealth::degraded("Slow"));
        assert_eq!(status.state, HealthState::Degraded);

        // One unhealthy
        status.set_component_health("sync_service", ComponentHealth::unhealthy("Failed", 3));
        assert_eq!(status.state, HealthState::Unhealthy);
    }

    #[test]
    fn test_can_run_tasks() {
        let mut status = HealthStatus::default();
        assert!(status.can_run_tasks());

        status.state = HealthState::Degraded;
        assert!(status.can_run_tasks());

        status.state = HealthState::Unhealthy;
        assert!(!status.can_run_tasks());
    }
}
