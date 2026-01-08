// Idle detection for Cirkelline Local Agent
// Detects when the user is not actively using the computer

use std::sync::atomic::{AtomicU32, Ordering};
use std::time::{Duration, Instant};

/// Platform-independent idle detector
pub struct IdleDetector {
    last_activity: std::sync::RwLock<Instant>,
    idle_threshold: AtomicU32,
    poll_interval: Duration,
}

impl IdleDetector {
    pub fn new(idle_threshold_seconds: u32) -> Self {
        Self {
            last_activity: std::sync::RwLock::new(Instant::now()),
            idle_threshold: AtomicU32::new(idle_threshold_seconds),
            poll_interval: Duration::from_secs(5),
        }
    }

    /// Check if system is currently idle
    pub fn is_idle(&self) -> bool {
        let idle_seconds = self.get_idle_seconds();
        let threshold = self.idle_threshold.load(Ordering::Relaxed);
        idle_seconds >= threshold
    }

    /// Get current idle time in seconds
    pub fn get_idle_seconds(&self) -> u32 {
        // Try platform-specific idle detection first
        if let Some(idle) = get_platform_idle_time() {
            return idle;
        }

        // Fallback to heuristic-based detection
        self.get_heuristic_idle_seconds()
    }

    /// Heuristic-based idle detection using CPU usage
    fn get_heuristic_idle_seconds(&self) -> u32 {
        let last = self.last_activity.read().unwrap();
        last.elapsed().as_secs() as u32
    }

    /// Update last activity time (called on user input detection)
    pub fn record_activity(&self) {
        let mut last = self.last_activity.write().unwrap();
        *last = Instant::now();
    }

    /// Update idle threshold
    pub fn set_threshold(&self, seconds: u32) {
        self.idle_threshold.store(seconds, Ordering::Relaxed);
    }

    /// Get idle threshold
    pub fn get_threshold(&self) -> u32 {
        self.idle_threshold.load(Ordering::Relaxed)
    }
}

/// Get platform-specific idle time
#[cfg(target_os = "windows")]
fn get_platform_idle_time() -> Option<u32> {
    // Windows: Use GetLastInputInfo
    use winapi::um::winuser::{GetLastInputInfo, LASTINPUTINFO};
    use winapi::um::sysinfoapi::GetTickCount;

    let mut lii = LASTINPUTINFO {
        cbSize: std::mem::size_of::<LASTINPUTINFO>() as u32,
        dwTime: 0,
    };

    unsafe {
        if GetLastInputInfo(&mut lii) != 0 {
            let tick_count = GetTickCount();
            let idle_ms = tick_count.wrapping_sub(lii.dwTime);
            return Some((idle_ms / 1000) as u32);
        }
    }
    None
}

#[cfg(target_os = "macos")]
fn get_platform_idle_time() -> Option<u32> {
    // macOS: Use CGEventSourceSecondsSinceLastEventType
    use core_graphics::event_source::{CGEventSourceStateID, CGEventSourceRef};
    use core_graphics::event::CGEventType;

    unsafe {
        let source = CGEventSourceRef::new(CGEventSourceStateID::HIDSystemState);
        if let Some(source) = source {
            let seconds = source.seconds_since_last_event_type(CGEventType::Null);
            return Some(seconds as u32);
        }
    }
    None
}

#[cfg(target_os = "linux")]
fn get_platform_idle_time() -> Option<u32> {
    // Linux: Try XScreenSaver extension first, then /proc/stat
    if let Some(idle) = get_x11_idle_time() {
        return Some(idle);
    }

    // Fallback: Check /proc/stat for CPU idle
    get_proc_idle_estimate()
}

#[cfg(target_os = "linux")]
fn get_x11_idle_time() -> Option<u32> {
    // Try to get idle time from X11 screensaver extension
    // This requires libxss-dev to be installed

    // For now, return None to use heuristic
    // In production, use x11rb or xscreensaver-rs crate
    None
}

#[cfg(target_os = "linux")]
fn get_proc_idle_estimate() -> Option<u32> {
    // Read /proc/stat to estimate system idle state
    // This is a rough heuristic based on CPU usage

    use std::fs;
    use std::io::{BufRead, BufReader};

    let file = fs::File::open("/proc/stat").ok()?;
    let reader = BufReader::new(file);

    for line in reader.lines().flatten() {
        if line.starts_with("cpu ") {
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() >= 5 {
                let user: u64 = parts[1].parse().unwrap_or(0);
                let nice: u64 = parts[2].parse().unwrap_or(0);
                let system: u64 = parts[3].parse().unwrap_or(0);
                let idle: u64 = parts[4].parse().unwrap_or(0);

                let total = user + nice + system + idle;
                let idle_percent = if total > 0 {
                    (idle as f64 / total as f64) * 100.0
                } else {
                    0.0
                };

                // If CPU is >95% idle, estimate user is idle
                if idle_percent > 95.0 {
                    // We don't know actual idle time, return a reasonable estimate
                    return Some(60);
                }
            }
        }
    }
    None
}

#[cfg(not(any(target_os = "windows", target_os = "macos", target_os = "linux")))]
fn get_platform_idle_time() -> Option<u32> {
    // Unsupported platform
    None
}

/// Idle callback manager
pub struct IdleCallbackManager {
    detector: IdleDetector,
    callbacks: std::sync::RwLock<Vec<Box<dyn Fn(bool) + Send + Sync>>>,
    last_state: std::sync::atomic::AtomicBool,
}

impl IdleCallbackManager {
    pub fn new(idle_threshold_seconds: u32) -> Self {
        Self {
            detector: IdleDetector::new(idle_threshold_seconds),
            callbacks: std::sync::RwLock::new(Vec::new()),
            last_state: std::sync::atomic::AtomicBool::new(false),
        }
    }

    /// Register a callback for idle state changes
    pub fn on_idle_change(&self, callback: impl Fn(bool) + Send + Sync + 'static) {
        let mut callbacks = self.callbacks.write().unwrap();
        callbacks.push(Box::new(callback));
    }

    /// Poll idle state and fire callbacks on change
    pub fn poll(&self) {
        let is_idle = self.detector.is_idle();
        let was_idle = self.last_state.swap(is_idle, Ordering::Relaxed);

        if is_idle != was_idle {
            let callbacks = self.callbacks.read().unwrap();
            for callback in callbacks.iter() {
                callback(is_idle);
            }
        }
    }

    /// Get current idle state
    pub fn is_idle(&self) -> bool {
        self.detector.is_idle()
    }

    /// Get idle seconds
    pub fn get_idle_seconds(&self) -> u32 {
        self.detector.get_idle_seconds()
    }

    /// Update threshold
    pub fn set_threshold(&self, seconds: u32) {
        self.detector.set_threshold(seconds);
    }
}

/// Start idle monitoring loop
pub async fn start_idle_monitor(
    manager: std::sync::Arc<IdleCallbackManager>,
    poll_interval: Duration,
) {
    let mut interval = tokio::time::interval(poll_interval);

    loop {
        interval.tick().await;
        manager.poll();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_idle_detector_creation() {
        let detector = IdleDetector::new(120);
        assert_eq!(detector.get_threshold(), 120);
    }

    #[test]
    fn test_idle_detector_threshold_update() {
        let detector = IdleDetector::new(120);
        detector.set_threshold(60);
        assert_eq!(detector.get_threshold(), 60);
    }

    #[test]
    fn test_activity_recording() {
        let detector = IdleDetector::new(120);

        // Record activity
        detector.record_activity();

        // Should not be idle immediately after activity
        let idle_seconds = detector.get_heuristic_idle_seconds();
        assert!(idle_seconds < 5);
    }
}
