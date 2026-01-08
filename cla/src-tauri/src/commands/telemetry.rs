// Telemetry commands for Cirkelline Local Agent

use tauri::State;
use crate::AppState;
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

/// Telemetry consent status
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TelemetryConsent {
    pub enabled: bool,
    pub consented_at: Option<DateTime<Utc>>,
    pub version: String,
}

/// Telemetry stats summary
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TelemetryStats {
    pub session_id: String,
    pub app_starts: u64,
    pub inference_count: u64,
    pub sync_count: u64,
    pub error_count: u64,
    pub uptime_hours: f64,
    pub last_report: Option<DateTime<Utc>>,
}

/// Get telemetry consent status
#[tauri::command]
pub async fn get_telemetry_consent(
    state: State<'_, AppState>,
) -> Result<TelemetryConsent, String> {
    let settings = state.settings.read().await;

    Ok(TelemetryConsent {
        enabled: settings.telemetry_enabled,
        consented_at: settings.telemetry_consent_date,
        version: env!("CARGO_PKG_VERSION").to_string(),
    })
}

/// Set telemetry consent
#[tauri::command]
pub async fn set_telemetry_consent(
    state: State<'_, AppState>,
    enabled: bool,
) -> Result<TelemetryConsent, String> {
    let mut settings = state.settings.write().await;

    settings.telemetry_enabled = enabled;
    if enabled {
        settings.telemetry_consent_date = Some(Utc::now());
    }

    // Save settings
    // TODO: Persist to disk

    log::info!("Telemetry consent updated: {}", enabled);

    Ok(TelemetryConsent {
        enabled,
        consented_at: settings.telemetry_consent_date,
        version: env!("CARGO_PKG_VERSION").to_string(),
    })
}

/// Get telemetry statistics
#[tauri::command]
pub async fn get_telemetry_stats(
    state: State<'_, AppState>,
) -> Result<TelemetryStats, String> {
    let telemetry = state.telemetry_stats.read().await;

    Ok(TelemetryStats {
        session_id: telemetry.session_id.clone(),
        app_starts: telemetry.app_starts,
        inference_count: telemetry.inference_count,
        sync_count: telemetry.sync_count,
        error_count: telemetry.error_count,
        uptime_hours: telemetry.uptime_hours,
        last_report: telemetry.last_report,
    })
}

/// Force send telemetry report (if enabled)
#[tauri::command]
pub async fn send_telemetry_report(
    state: State<'_, AppState>,
) -> Result<bool, String> {
    let settings = state.settings.read().await;

    if !settings.telemetry_enabled {
        return Err("Telemetry is disabled".to_string());
    }

    let endpoint = settings.ckc_endpoint.clone()
        .unwrap_or_else(|| "https://ckc.cirkelline.com".to_string());

    drop(settings);

    let telemetry = state.telemetry_stats.read().await;

    // Build report
    let report = serde_json::json!({
        "session_id": telemetry.session_id,
        "version": env!("CARGO_PKG_VERSION"),
        "platform": std::env::consts::OS,
        "metrics": {
            "app_starts": telemetry.app_starts,
            "inference_count": telemetry.inference_count,
            "sync_count": telemetry.sync_count,
            "error_count": telemetry.error_count,
            "uptime_hours": telemetry.uptime_hours
        },
        "timestamp": Utc::now().to_rfc3339()
    });

    drop(telemetry);

    // Send report
    let client = reqwest::Client::new();
    let response = client
        .post(&format!("{}/api/cla/telemetry", endpoint))
        .json(&report)
        .timeout(std::time::Duration::from_secs(30))
        .send()
        .await
        .map_err(|e| format!("Failed to send telemetry: {}", e))?;

    if response.status().is_success() {
        let mut telemetry = state.telemetry_stats.write().await;
        telemetry.last_report = Some(Utc::now());

        log::info!("Telemetry report sent successfully");
        Ok(true)
    } else {
        Err(format!("Server returned status: {}", response.status()))
    }
}

/// Record an event locally
#[tauri::command]
pub async fn record_telemetry_event(
    state: State<'_, AppState>,
    event_type: String,
    _details: Option<serde_json::Value>,
) -> Result<(), String> {
    let mut telemetry = state.telemetry_stats.write().await;

    match event_type.as_str() {
        "app_start" => telemetry.app_starts += 1,
        "inference" => telemetry.inference_count += 1,
        "sync" => telemetry.sync_count += 1,
        "error" => telemetry.error_count += 1,
        _ => {}
    }

    Ok(())
}

/// Get privacy information
#[tauri::command]
pub fn get_privacy_info() -> String {
    r#"
CLA Telemetry - Fortrolighedsoplysninger

Når aktiveret, indsamler CLA anonyme brugsdata for at forbedre applikationen.

Hvad vi indsamler:
- Performance metrics (latens, succesrater)
- Fejltyper (ingen fejlmeddelelser eller stack traces)
- Feature-brugstællinger
- Ressourceforbrug mønstre

Hvad vi IKKE indsamler:
- Personlige oplysninger
- Filindhold eller stier
- Bruger-identifikatorer
- IP-adresser (anonymiseret på server)
- Samtaleindhold
- Hukommelsesindhold

Data er:
- Krypteret under transport (HTTPS)
- Aggregeret og anonymiseret
- Slettet efter 90 dage
- Aldrig solgt eller delt

Du kan deaktivere telemetri når som helst i Indstillinger.
"#.to_string()
}
