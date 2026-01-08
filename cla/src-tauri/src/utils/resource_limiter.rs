// Resource limiter for Cirkelline Local Agent
// Ensures CLA never exceeds configured resource limits

use std::sync::atomic::{AtomicBool, AtomicU32, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::RwLock;

/// Resource limiter configuration
#[derive(Clone)]
pub struct ResourceLimits {
    pub max_cpu_percent: u8,
    pub max_ram_percent: u8,
    pub max_gpu_percent: u8,
    pub max_disk_mb: u32,
    pub idle_only: bool,
    pub idle_threshold_seconds: u32,
    pub run_on_battery: bool,
    pub min_battery_percent: u8,
}

impl Default for ResourceLimits {
    fn default() -> Self {
        Self {
            max_cpu_percent: 30,
            max_ram_percent: 20,
            max_gpu_percent: 30,
            max_disk_mb: 2000,
            idle_only: true,
            idle_threshold_seconds: 120,
            run_on_battery: false,
            min_battery_percent: 20,
        }
    }
}

/// Resource limiter state
pub struct ResourceLimiter {
    limits: Arc<RwLock<ResourceLimits>>,
    paused: AtomicBool,
    current_cpu: AtomicU32,
    current_ram: AtomicU32,
    active_tasks: AtomicU32,
    last_check: RwLock<Instant>,
}

impl ResourceLimiter {
    pub fn new(limits: ResourceLimits) -> Self {
        Self {
            limits: Arc::new(RwLock::new(limits)),
            paused: AtomicBool::new(false),
            current_cpu: AtomicU32::new(0),
            current_ram: AtomicU32::new(0),
            active_tasks: AtomicU32::new(0),
            last_check: RwLock::new(Instant::now()),
        }
    }

    /// Check if a task can be executed given current resource usage
    pub async fn can_execute(
        &self,
        required_cpu: u8,
        required_ram_mb: u64,
        requires_gpu: bool,
        system_metrics: &SystemMetrics,
    ) -> ExecutionPermission {
        // Check if paused
        if self.paused.load(Ordering::Relaxed) {
            return ExecutionPermission::Denied {
                reason: "CLA er sat på pause".to_string(),
                wait_seconds: None,
            };
        }

        let limits = self.limits.read().await;

        // Check idle requirement
        if limits.idle_only && !system_metrics.is_idle {
            let wait = limits.idle_threshold_seconds.saturating_sub(system_metrics.idle_seconds);
            return ExecutionPermission::Denied {
                reason: format!(
                    "Venter på idle-tilstand ({}/{}s)",
                    system_metrics.idle_seconds, limits.idle_threshold_seconds
                ),
                wait_seconds: Some(wait),
            };
        }

        // Check battery
        if system_metrics.on_battery {
            if !limits.run_on_battery {
                return ExecutionPermission::Denied {
                    reason: "Kører ikke på batteri".to_string(),
                    wait_seconds: None,
                };
            }
            if let Some(battery) = system_metrics.battery_percent {
                if battery < limits.min_battery_percent {
                    return ExecutionPermission::Denied {
                        reason: format!(
                            "Batteri for lavt ({}%, minimum {}%)",
                            battery, limits.min_battery_percent
                        ),
                        wait_seconds: None,
                    };
                }
            }
        }

        // Check CPU headroom
        let current_cpu = system_metrics.cpu_usage_percent;
        let projected_cpu = current_cpu + required_cpu as f32;
        if projected_cpu > limits.max_cpu_percent as f32 {
            return ExecutionPermission::Denied {
                reason: format!(
                    "CPU-grænse overskredet ({:.0}% + {}% > {}%)",
                    current_cpu, required_cpu, limits.max_cpu_percent
                ),
                wait_seconds: Some(30),
            };
        }

        // Check RAM headroom
        let current_ram_percent = system_metrics.ram_usage_percent;
        if current_ram_percent > limits.max_ram_percent as f32 {
            return ExecutionPermission::Denied {
                reason: format!(
                    "RAM-grænse overskredet ({:.0}% > {}%)",
                    current_ram_percent, limits.max_ram_percent
                ),
                wait_seconds: Some(60),
            };
        }

        // Check GPU requirement
        if requires_gpu {
            if !system_metrics.gpu_available {
                return ExecutionPermission::Denied {
                    reason: "GPU ikke tilgængelig".to_string(),
                    wait_seconds: None,
                };
            }
            if let Some(gpu_usage) = system_metrics.gpu_usage_percent {
                if gpu_usage > limits.max_gpu_percent as f32 {
                    return ExecutionPermission::Denied {
                        reason: format!(
                            "GPU-grænse overskredet ({:.0}% > {}%)",
                            gpu_usage, limits.max_gpu_percent
                        ),
                        wait_seconds: Some(30),
                    };
                }
            }
        }

        ExecutionPermission::Granted {
            max_duration: Duration::from_secs(300), // 5 min max per task
        }
    }

    /// Update limits
    pub async fn update_limits(&self, new_limits: ResourceLimits) {
        let mut limits = self.limits.write().await;
        *limits = new_limits;
    }

    /// Pause/resume execution
    pub fn set_paused(&self, paused: bool) {
        self.paused.store(paused, Ordering::Relaxed);
    }

    pub fn is_paused(&self) -> bool {
        self.paused.load(Ordering::Relaxed)
    }

    /// Track active tasks
    pub fn task_started(&self) {
        self.active_tasks.fetch_add(1, Ordering::Relaxed);
    }

    pub fn task_completed(&self) {
        self.active_tasks.fetch_sub(1, Ordering::Relaxed);
    }

    pub fn active_task_count(&self) -> u32 {
        self.active_tasks.load(Ordering::Relaxed)
    }
}

/// Result of permission check
pub enum ExecutionPermission {
    Granted {
        max_duration: Duration,
    },
    Denied {
        reason: String,
        wait_seconds: Option<u32>,
    },
}

/// System metrics snapshot
pub struct SystemMetrics {
    pub cpu_usage_percent: f32,
    pub ram_usage_percent: f32,
    pub gpu_available: bool,
    pub gpu_usage_percent: Option<f32>,
    pub on_battery: bool,
    pub battery_percent: Option<u8>,
    pub idle_seconds: u32,
    pub is_idle: bool,
}

/// Task priority levels
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum TaskPriority {
    Low = 1,
    Normal = 5,
    High = 8,
    Critical = 10,
}

/// Resource-aware task executor
pub struct TaskExecutor {
    limiter: Arc<ResourceLimiter>,
    queue: tokio::sync::mpsc::Sender<QueuedTask>,
}

pub struct QueuedTask {
    pub id: String,
    pub priority: TaskPriority,
    pub cpu_estimate: u8,
    pub ram_estimate_mb: u64,
    pub requires_gpu: bool,
    pub callback: Box<dyn FnOnce() -> Result<(), String> + Send>,
}

impl TaskExecutor {
    pub fn new(limiter: Arc<ResourceLimiter>) -> Self {
        let (tx, mut rx) = tokio::sync::mpsc::channel::<QueuedTask>(100);

        // Spawn task processor
        let limiter_clone = limiter.clone();
        tokio::spawn(async move {
            while let Some(task) = rx.recv().await {
                // Wait until we can execute
                loop {
                    let metrics = get_current_metrics().await;
                    match limiter_clone
                        .can_execute(task.cpu_estimate, task.ram_estimate_mb, task.requires_gpu, &metrics)
                        .await
                    {
                        ExecutionPermission::Granted { .. } => break,
                        ExecutionPermission::Denied { wait_seconds, .. } => {
                            let wait = wait_seconds.unwrap_or(30);
                            tokio::time::sleep(Duration::from_secs(wait as u64)).await;
                        }
                    }
                }

                // Execute task
                limiter_clone.task_started();
                let result = (task.callback)();
                limiter_clone.task_completed();

                if let Err(e) = result {
                    log::error!("Task {} failed: {}", task.id, e);
                }
            }
        });

        Self { limiter, queue: tx }
    }

    pub async fn submit(&self, task: QueuedTask) -> Result<(), String> {
        self.queue
            .send(task)
            .await
            .map_err(|e| format!("Failed to queue task: {}", e))
    }
}

/// Get current system metrics (placeholder)
async fn get_current_metrics() -> SystemMetrics {
    // In production, this would use sysinfo crate
    SystemMetrics {
        cpu_usage_percent: 10.0,
        ram_usage_percent: 30.0,
        gpu_available: false,
        gpu_usage_percent: None,
        on_battery: false,
        battery_percent: None,
        idle_seconds: 150,
        is_idle: true,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_resource_limiter_default() {
        let limiter = ResourceLimiter::new(ResourceLimits::default());

        let metrics = SystemMetrics {
            cpu_usage_percent: 10.0,
            ram_usage_percent: 15.0,
            gpu_available: false,
            gpu_usage_percent: None,
            on_battery: false,
            battery_percent: None,
            idle_seconds: 150,
            is_idle: true,
        };

        let result = limiter.can_execute(10, 100, false, &metrics).await;
        assert!(matches!(result, ExecutionPermission::Granted { .. }));
    }

    #[tokio::test]
    async fn test_resource_limiter_paused() {
        let limiter = ResourceLimiter::new(ResourceLimits::default());
        limiter.set_paused(true);

        let metrics = SystemMetrics {
            cpu_usage_percent: 10.0,
            ram_usage_percent: 15.0,
            gpu_available: false,
            gpu_usage_percent: None,
            on_battery: false,
            battery_percent: None,
            idle_seconds: 150,
            is_idle: true,
        };

        let result = limiter.can_execute(10, 100, false, &metrics).await;
        assert!(matches!(result, ExecutionPermission::Denied { .. }));
    }

    #[tokio::test]
    async fn test_resource_limiter_cpu_exceeded() {
        let limiter = ResourceLimiter::new(ResourceLimits::default());

        let metrics = SystemMetrics {
            cpu_usage_percent: 25.0, // Already at 25%
            ram_usage_percent: 15.0,
            gpu_available: false,
            gpu_usage_percent: None,
            on_battery: false,
            battery_percent: None,
            idle_seconds: 150,
            is_idle: true,
        };

        // Request 10% more CPU, which would exceed 30% limit
        let result = limiter.can_execute(10, 100, false, &metrics).await;
        assert!(matches!(result, ExecutionPermission::Denied { .. }));
    }
}
