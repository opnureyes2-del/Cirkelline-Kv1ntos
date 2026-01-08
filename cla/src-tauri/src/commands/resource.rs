// Resource monitoring commands for Cirkelline Local Agent

use tauri::State;
use crate::AppState;
use crate::models::{SystemMetrics, CanExecuteResult};
use sysinfo::System;

/// Get current system metrics
#[tauri::command]
pub async fn get_system_metrics(state: State<'_, AppState>) -> Result<SystemMetrics, String> {
    let monitor = state.resource_monitor.read().await;
    Ok(monitor.get_current_metrics())
}

/// Check if a task with given requirements can execute now
#[tauri::command]
pub async fn can_execute_task(
    state: State<'_, AppState>,
    estimated_cpu_percent: u8,
    estimated_ram_mb: u64,
    requires_gpu: bool,
) -> Result<CanExecuteResult, String> {
    let settings = state.settings.read().await;
    let monitor = state.resource_monitor.read().await;
    let metrics = monitor.get_current_metrics();

    // Check if paused
    if settings.paused {
        return Ok(CanExecuteResult {
            can_execute: false,
            reason: Some("CLA er sat på pause".to_string()),
            estimated_wait_seconds: None,
        });
    }

    // Check idle requirement
    if settings.idle_only && !metrics.is_idle {
        return Ok(CanExecuteResult {
            can_execute: false,
            reason: Some(format!(
                "Venter på idle-tilstand ({}s / {}s)",
                metrics.idle_seconds, settings.idle_threshold_seconds
            )),
            estimated_wait_seconds: Some(settings.idle_threshold_seconds - metrics.idle_seconds),
        });
    }

    // Check battery
    if metrics.on_battery {
        if !settings.run_on_battery {
            return Ok(CanExecuteResult {
                can_execute: false,
                reason: Some("Kører ikke på batteri".to_string()),
                estimated_wait_seconds: None,
            });
        }
        if let Some(battery) = metrics.battery_percent {
            if battery < settings.min_battery_percent {
                return Ok(CanExecuteResult {
                    can_execute: false,
                    reason: Some(format!(
                        "Batteri for lavt ({}% / min {}%)",
                        battery, settings.min_battery_percent
                    )),
                    estimated_wait_seconds: None,
                });
            }
        }
    }

    // Check CPU headroom
    let cpu_headroom = settings.max_cpu_percent as f32 - metrics.cpu_usage_percent;
    if estimated_cpu_percent as f32 > cpu_headroom {
        return Ok(CanExecuteResult {
            can_execute: false,
            reason: Some(format!(
                "CPU-grænse nået ({:.0}% brugt, maks {}%)",
                metrics.cpu_usage_percent, settings.max_cpu_percent
            )),
            estimated_wait_seconds: Some(30), // Estimate
        });
    }

    // Check RAM headroom
    let ram_usage_percent = metrics.ram_usage_percent;
    if ram_usage_percent > settings.max_ram_percent as f32 {
        return Ok(CanExecuteResult {
            can_execute: false,
            reason: Some(format!(
                "RAM-grænse nået ({:.0}% brugt, maks {}%)",
                ram_usage_percent, settings.max_ram_percent
            )),
            estimated_wait_seconds: Some(60),
        });
    }

    // Check GPU if required
    if requires_gpu && !metrics.gpu_available {
        return Ok(CanExecuteResult {
            can_execute: false,
            reason: Some("GPU ikke tilgængelig".to_string()),
            estimated_wait_seconds: None,
        });
    }

    Ok(CanExecuteResult {
        can_execute: true,
        reason: None,
        estimated_wait_seconds: None,
    })
}

/// Get current resource limits
#[tauri::command]
pub async fn get_resource_limits(
    state: State<'_, AppState>,
) -> Result<ResourceLimits, String> {
    let settings = state.settings.read().await;
    Ok(ResourceLimits {
        max_cpu_percent: settings.max_cpu_percent,
        max_ram_percent: settings.max_ram_percent,
        max_gpu_percent: settings.max_gpu_percent,
        max_disk_mb: settings.max_disk_mb,
        idle_only: settings.idle_only,
        idle_threshold_seconds: settings.idle_threshold_seconds,
    })
}

/// Update resource limits
#[tauri::command]
pub async fn set_resource_limits(
    state: State<'_, AppState>,
    limits: ResourceLimits,
) -> Result<(), String> {
    let mut settings = state.settings.write().await;

    // Validate limits
    if limits.max_cpu_percent > 80 {
        return Err("CPU-grænse kan ikke overstige 80%".to_string());
    }
    if limits.max_ram_percent > 50 {
        return Err("RAM-grænse kan ikke overstige 50%".to_string());
    }
    if limits.max_gpu_percent > 80 {
        return Err("GPU-grænse kan ikke overstige 80%".to_string());
    }

    settings.max_cpu_percent = limits.max_cpu_percent;
    settings.max_ram_percent = limits.max_ram_percent;
    settings.max_gpu_percent = limits.max_gpu_percent;
    settings.max_disk_mb = limits.max_disk_mb;
    settings.idle_only = limits.idle_only;
    settings.idle_threshold_seconds = limits.idle_threshold_seconds;

    Ok(())
}

#[derive(serde::Serialize, serde::Deserialize)]
pub struct ResourceLimits {
    pub max_cpu_percent: u8,
    pub max_ram_percent: u8,
    pub max_gpu_percent: u8,
    pub max_disk_mb: u32,
    pub idle_only: bool,
    pub idle_threshold_seconds: u32,
}
