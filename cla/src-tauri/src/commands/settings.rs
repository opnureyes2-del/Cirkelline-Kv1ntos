// Settings commands for Cirkelline Local Agent

use tauri::State;
use crate::AppState;
use crate::models::{Settings, ConnectionStatus};
use chrono::Utc;

/// Get all settings
#[tauri::command]
pub async fn get_settings(state: State<'_, AppState>) -> Result<Settings, String> {
    let settings = state.settings.read().await;
    Ok(settings.clone())
}

/// Update settings
#[tauri::command]
pub async fn update_settings(
    state: State<'_, AppState>,
    new_settings: SettingsUpdate,
) -> Result<Settings, String> {
    let mut settings = state.settings.write().await;

    // Apply updates with validation
    if let Some(cpu) = new_settings.max_cpu_percent {
        if cpu > 80 {
            return Err("CPU-grænse kan ikke overstige 80%".to_string());
        }
        settings.max_cpu_percent = cpu;
    }

    if let Some(ram) = new_settings.max_ram_percent {
        if ram > 50 {
            return Err("RAM-grænse kan ikke overstige 50%".to_string());
        }
        settings.max_ram_percent = ram;
    }

    if let Some(gpu) = new_settings.max_gpu_percent {
        if gpu > 80 {
            return Err("GPU-grænse kan ikke overstige 80%".to_string());
        }
        settings.max_gpu_percent = gpu;
    }

    if let Some(disk) = new_settings.max_disk_mb {
        settings.max_disk_mb = disk;
    }

    if let Some(idle_only) = new_settings.idle_only {
        settings.idle_only = idle_only;
    }

    if let Some(threshold) = new_settings.idle_threshold_seconds {
        if threshold < 30 {
            return Err("Idle-tærskel skal være mindst 30 sekunder".to_string());
        }
        settings.idle_threshold_seconds = threshold;
    }

    if let Some(auto_start) = new_settings.auto_start {
        settings.auto_start = auto_start;
        // TODO: Actually enable/disable auto-start in OS
    }

    if let Some(run_on_battery) = new_settings.run_on_battery {
        settings.run_on_battery = run_on_battery;
    }

    if let Some(min_battery) = new_settings.min_battery_percent {
        settings.min_battery_percent = min_battery;
    }

    if let Some(interval) = new_settings.sync_interval_minutes {
        if interval < 5 {
            return Err("Synkroniseringsinterval skal være mindst 5 minutter".to_string());
        }
        settings.sync_interval_minutes = interval;
    }

    if let Some(sync_on_startup) = new_settings.sync_on_startup {
        settings.sync_on_startup = sync_on_startup;
    }

    if let Some(offline) = new_settings.offline_mode {
        settings.offline_mode = offline;
    }

    if let Some(transcription) = new_settings.enable_transcription {
        settings.enable_transcription = transcription;
    }

    if let Some(ocr) = new_settings.enable_ocr {
        settings.enable_ocr = ocr;
    }

    if let Some(embeddings) = new_settings.enable_embeddings {
        settings.enable_embeddings = embeddings;
    }

    if let Some(tier2) = new_settings.download_tier2_models {
        settings.download_tier2_models = tier2;
    }

    if let Some(tier3) = new_settings.download_tier3_models {
        settings.download_tier3_models = tier3;
    }

    if let Some(endpoint) = new_settings.ckc_endpoint {
        // Validate URL
        if !endpoint.starts_with("http://") && !endpoint.starts_with("https://") {
            return Err("Ugyldig endpoint URL".to_string());
        }
        settings.ckc_endpoint = Some(endpoint);
    }

    if let Some(api_key) = new_settings.api_key {
        settings.api_key = if api_key.is_empty() { None } else { Some(api_key) };
    }

    // Persist settings
    persist_settings(&settings).await?;

    Ok(settings.clone())
}

/// Reset settings to defaults
#[tauri::command]
pub async fn reset_settings(state: State<'_, AppState>) -> Result<Settings, String> {
    let mut settings = state.settings.write().await;
    *settings = Settings::default();

    persist_settings(&settings).await?;

    Ok(settings.clone())
}

/// Get connection status to CKC
#[tauri::command]
pub async fn get_connection_status(
    state: State<'_, AppState>,
) -> Result<ConnectionStatus, String> {
    let settings = state.settings.read().await;

    // Quick health check
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build()
        .map_err(|e| e.to_string())?;

    let start = std::time::Instant::now();
    let endpoint_str = settings.ckc_endpoint.as_deref()
        .unwrap_or("https://ckc.cirkelline.com");
    let health_url = format!("{}/health", endpoint_str);

    match client.get(&health_url).send().await {
        Ok(response) if response.status().is_success() => {
            Ok(ConnectionStatus {
                connected: true,
                endpoint: endpoint_str.to_string(),
                latency_ms: Some(start.elapsed().as_millis() as u32),
                last_check: Utc::now(),
                error: None,
            })
        }
        Ok(response) => {
            Ok(ConnectionStatus {
                connected: false,
                endpoint: endpoint_str.to_string(),
                latency_ms: None,
                last_check: Utc::now(),
                error: Some(format!("Server svarede: {}", response.status())),
            })
        }
        Err(e) => {
            Ok(ConnectionStatus {
                connected: false,
                endpoint: endpoint_str.to_string(),
                latency_ms: None,
                last_check: Utc::now(),
                error: Some(e.to_string()),
            })
        }
    }
}

/// Test connection to a specific endpoint
#[tauri::command]
pub async fn test_connection(endpoint: String) -> Result<ConnectionStatus, String> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(10))
        .build()
        .map_err(|e| e.to_string())?;

    let start = std::time::Instant::now();
    let health_url = format!("{}/health", endpoint);

    match client.get(&health_url).send().await {
        Ok(response) if response.status().is_success() => {
            Ok(ConnectionStatus {
                connected: true,
                endpoint,
                latency_ms: Some(start.elapsed().as_millis() as u32),
                last_check: Utc::now(),
                error: None,
            })
        }
        Ok(response) => {
            Ok(ConnectionStatus {
                connected: false,
                endpoint,
                latency_ms: None,
                last_check: Utc::now(),
                error: Some(format!("Server svarede: {}", response.status())),
            })
        }
        Err(e) => {
            Ok(ConnectionStatus {
                connected: false,
                endpoint,
                latency_ms: None,
                last_check: Utc::now(),
                error: Some(e.to_string()),
            })
        }
    }
}

/// Persist settings to disk
async fn persist_settings(settings: &Settings) -> Result<(), String> {
    let config_dir = dirs::config_dir()
        .ok_or("Kunne ikke finde config-mappe")?
        .join("cirkelline-cla");

    std::fs::create_dir_all(&config_dir)
        .map_err(|e| format!("Kunne ikke oprette config-mappe: {}", e))?;

    let settings_path = config_dir.join("settings.json");
    let json = serde_json::to_string_pretty(settings)
        .map_err(|e| format!("Kunne ikke serialisere indstillinger: {}", e))?;

    std::fs::write(&settings_path, json)
        .map_err(|e| format!("Kunne ikke gemme indstillinger: {}", e))?;

    Ok(())
}

/// Load settings from disk
pub async fn load_settings() -> Settings {
    let config_path = dirs::config_dir()
        .map(|d| d.join("cirkelline-cla").join("settings.json"));

    if let Some(path) = config_path {
        if path.exists() {
            if let Ok(json) = std::fs::read_to_string(&path) {
                if let Ok(settings) = serde_json::from_str(&json) {
                    return settings;
                }
            }
        }
    }

    Settings::default()
}

#[derive(serde::Deserialize)]
pub struct SettingsUpdate {
    pub max_cpu_percent: Option<u8>,
    pub max_ram_percent: Option<u8>,
    pub max_gpu_percent: Option<u8>,
    pub max_disk_mb: Option<u32>,
    pub idle_only: Option<bool>,
    pub idle_threshold_seconds: Option<u32>,
    pub auto_start: Option<bool>,
    pub run_on_battery: Option<bool>,
    pub min_battery_percent: Option<u8>,
    pub sync_interval_minutes: Option<u32>,
    pub sync_on_startup: Option<bool>,
    pub offline_mode: Option<bool>,
    pub enable_transcription: Option<bool>,
    pub enable_ocr: Option<bool>,
    pub enable_embeddings: Option<bool>,
    pub download_tier2_models: Option<bool>,
    pub download_tier3_models: Option<bool>,
    pub ckc_endpoint: Option<String>,
    pub api_key: Option<String>,
}
