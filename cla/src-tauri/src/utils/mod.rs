// Utility modules for Cirkelline Local Agent

use crate::models::SystemMetrics;
use chrono::Utc;
use sysinfo::{System, Disks};
use std::time::{Duration, Instant};
use tauri::{Manager, Emitter};

/// Resource monitor that tracks system metrics
pub struct ResourceMonitor {
    system: System,
    disks: Disks,
    last_update: Instant,
    cached_metrics: Option<SystemMetrics>,
    idle_start: Option<Instant>,
    last_cpu_usage: f32,
}

impl ResourceMonitor {
    pub fn new() -> Self {
        let mut system = System::new();
        system.refresh_all();

        let disks = Disks::new_with_refreshed_list();

        Self {
            system,
            disks,
            last_update: Instant::now(),
            cached_metrics: None,
            idle_start: Some(Instant::now()),
            last_cpu_usage: 0.0,
        }
    }

    /// Update system metrics (call periodically)
    pub fn refresh(&mut self) {
        self.system.refresh_all();
        self.disks.refresh();
        self.last_update = Instant::now();

        // Update CPU usage cache
        self.last_cpu_usage = self.system.global_cpu_info().cpu_usage();
    }

    /// Get current system metrics
    pub fn get_current_metrics(&self) -> SystemMetrics {
        let cpu_usage = self.last_cpu_usage;
        let total_memory = self.system.total_memory() / 1024 / 1024; // MB
        let used_memory = self.system.used_memory() / 1024 / 1024; // MB
        let ram_percent = if total_memory > 0 {
            (used_memory as f32 / total_memory as f32) * 100.0
        } else {
            0.0
        };

        // Get disk info for app data directory
        let (disk_used, disk_available) = self.get_disk_usage();

        // Estimate idle time (simplified - in production use platform APIs)
        let idle_seconds = self.estimate_idle_time();
        let is_idle = idle_seconds >= 120; // 2 minutes default threshold

        // Check power status
        let (on_battery, battery_percent) = self.get_power_status();

        SystemMetrics {
            cpu_usage_percent: cpu_usage,
            cpu_count: self.system.cpus().len() as u32,
            ram_used_mb: used_memory,
            ram_total_mb: total_memory,
            ram_usage_percent: ram_percent,
            gpu_available: self.check_gpu_available(),
            gpu_usage_percent: self.get_gpu_usage(),
            gpu_memory_used_mb: None, // TODO: Implement GPU memory tracking
            gpu_memory_total_mb: None,
            disk_used_mb: disk_used,
            disk_available_mb: disk_available,
            on_battery,
            battery_percent,
            idle_seconds,
            is_idle,
            timestamp: Utc::now(),
        }
    }

    fn get_disk_usage(&self) -> (u64, u64) {
        // Get the disk where app data is stored
        let data_dir = dirs::data_dir().unwrap_or_default();

        for disk in self.disks.list() {
            if data_dir.starts_with(disk.mount_point()) {
                let total = disk.total_space() / 1024 / 1024;
                let available = disk.available_space() / 1024 / 1024;
                return (total - available, available);
            }
        }

        (0, 0)
    }

    fn estimate_idle_time(&self) -> u32 {
        // Simple heuristic: low CPU = idle
        // In production, use platform-specific APIs:
        // - Windows: GetLastInputInfo
        // - macOS: CGEventSourceSecondsSinceLastEventType
        // - Linux: XScreenSaverQueryInfo or libinput
        let cpu_usage = self.last_cpu_usage;

        if cpu_usage < 5.0 {
            // Very low CPU, probably idle
            if let Some(start) = self.idle_start {
                return start.elapsed().as_secs() as u32;
            }
        }

        0
    }

    fn get_power_status(&self) -> (bool, Option<u8>) {
        // TODO: Use battery crate or platform-specific APIs
        // For now, assume plugged in
        (false, None)
    }

    fn check_gpu_available(&self) -> bool {
        // TODO: Check for CUDA/WebGPU availability
        // For now, assume not available
        false
    }

    fn get_gpu_usage(&self) -> Option<f32> {
        // TODO: Use nvml or similar for GPU monitoring
        None
    }
}

/// Start the resource monitoring loop
pub async fn start_resource_monitor(app_handle: tauri::AppHandle) {
    let mut interval = tokio::time::interval(Duration::from_secs(5));

    loop {
        interval.tick().await;

        if let Some(state) = app_handle.try_state::<crate::AppState>() {
            let mut monitor = state.resource_monitor.write().await;
            monitor.refresh();

            // Emit metrics to frontend
            let metrics = monitor.get_current_metrics();
            let _ = app_handle.emit("system-metrics", &metrics);
        }
    }
}

/// Start the sync loop
pub async fn start_sync_loop(app_handle: tauri::AppHandle) {
    // Wait for initial startup
    tokio::time::sleep(Duration::from_secs(10)).await;

    loop {
        // Get sync interval from settings
        let interval_minutes = if let Some(state) = app_handle.try_state::<crate::AppState>() {
            let settings = state.settings.read().await;

            // Skip if paused or offline
            if settings.paused || settings.offline_mode {
                tokio::time::sleep(Duration::from_secs(60)).await;
                continue;
            }

            settings.sync_interval_minutes
        } else {
            15 // Default 15 minutes
        };

        // Wait for interval
        tokio::time::sleep(Duration::from_secs(interval_minutes as u64 * 60)).await;

        // Check if we can sync (respecting resource limits)
        if let Some(state) = app_handle.try_state::<crate::AppState>() {
            let settings = state.settings.read().await;
            let monitor = state.resource_monitor.read().await;
            let metrics = monitor.get_current_metrics();

            // Only sync if idle (if idle_only is set)
            if settings.idle_only && !metrics.is_idle {
                log::debug!("Skipping sync: not idle");
                continue;
            }

            // Check battery
            if metrics.on_battery && !settings.run_on_battery {
                log::debug!("Skipping sync: on battery");
                continue;
            }

            // Perform sync
            drop(monitor);
            drop(settings);

            log::info!("Starting scheduled sync");

            let mut status = state.sync_status.write().await;
            status.is_syncing = true;
            drop(status);

            // Emit sync start event
            let _ = app_handle.emit("sync-started", ());

            // TODO: Actual sync implementation
            tokio::time::sleep(Duration::from_secs(2)).await; // Simulated sync

            let mut status = state.sync_status.write().await;
            status.is_syncing = false;
            status.last_sync = Some(Utc::now());
            status.last_sync_result = Some(crate::models::SyncResult::Success);

            // Emit sync complete event
            let _ = app_handle.emit("sync-completed", &*status);
        }
    }
}
