// Cirkelline Local Agent - Main Entry Point
// Prevents additional console window on Windows in release
// Voice-first accessibility for hands-free operation
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod models;
mod utils;
mod inference;
mod security;
mod error;
mod telemetry;
mod commander;
mod research;
mod accessibility;

use commands::{resource, sync, inference as inference_cmd, settings, telemetry as telemetry_cmd, commander as commander_cmd, accessibility as accessibility_cmd};
use tauri::Manager;
use std::sync::Arc;
use tokio::sync::RwLock;

/// Application state shared across all commands
pub struct AppState {
    pub settings: Arc<RwLock<models::Settings>>,
    pub sync_status: Arc<RwLock<models::SyncStatus>>,
    pub resource_monitor: Arc<RwLock<utils::ResourceMonitor>>,
    pub inference_engine: Arc<RwLock<Option<inference::InferenceEngine>>>,
    pub telemetry_stats: Arc<RwLock<models::TelemetryStats>>,
}

impl Default for AppState {
    fn default() -> Self {
        Self {
            settings: Arc::new(RwLock::new(models::Settings::default())),
            sync_status: Arc::new(RwLock::new(models::SyncStatus::default())),
            resource_monitor: Arc::new(RwLock::new(utils::ResourceMonitor::new())),
            inference_engine: Arc::new(RwLock::new(None)),
            telemetry_stats: Arc::new(RwLock::new(models::TelemetryStats::default())),
        }
    }
}

#[tokio::main]
async fn main() {
    // Initialize logging
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info"))
        .init();

    log::info!("Starting Cirkelline Local Agent v{}", env!("CARGO_PKG_VERSION"));

    // Create application state
    let app_state = AppState::default();

    tauri::Builder::default()
        // Plugins
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_store::Builder::default().build())

        // State management
        .manage(app_state)
        .manage(commander_cmd::CommanderState::default())
        .manage(accessibility_cmd::AccessibilityState::default())

        // Commands
        .invoke_handler(tauri::generate_handler![
            // Resource monitoring
            resource::get_system_metrics,
            resource::can_execute_task,
            resource::get_resource_limits,
            resource::set_resource_limits,

            // Sync operations
            sync::get_sync_status,
            sync::sync_now,
            sync::get_pending_changes,
            sync::resolve_conflict,

            // AI inference
            inference_cmd::generate_embedding,
            inference_cmd::transcribe_audio,
            inference_cmd::extract_text,
            inference_cmd::get_model_status,
            inference_cmd::download_model,

            // Settings
            settings::get_settings,
            settings::update_settings,
            settings::reset_settings,
            settings::get_connection_status,
            settings::test_connection,

            // Telemetry
            telemetry_cmd::get_telemetry_consent,
            telemetry_cmd::set_telemetry_consent,
            telemetry_cmd::get_telemetry_stats,
            telemetry_cmd::send_telemetry_report,
            telemetry_cmd::record_telemetry_event,
            telemetry_cmd::get_privacy_info,

            // Commander Unit (FASE 6)
            commander_cmd::get_commander_status,
            commander_cmd::get_commander_config,
            commander_cmd::update_commander_config,
            commander_cmd::start_commander,
            commander_cmd::stop_commander,
            commander_cmd::add_research_task,
            commander_cmd::get_task_queue_status,
            commander_cmd::get_recent_findings,
            commander_cmd::force_commander_sync,
            commander_cmd::get_sync_stats,
            commander_cmd::set_autonomy_level,

            // Accessibility / Voice Control (Hands-free for handicapped users)
            accessibility_cmd::get_accessibility_config,
            accessibility_cmd::update_accessibility_config,
            accessibility_cmd::get_voice_state,
            accessibility_cmd::start_voice_control,
            accessibility_cmd::stop_voice_control,
            accessibility_cmd::speak_text,
            accessibility_cmd::listen_for_command,
            accessibility_cmd::execute_voice_command,
            accessibility_cmd::get_available_commands,
            accessibility_cmd::toggle_accessibility_mode,
        ])

        // Window events - Tauri v2 API
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                // Hide instead of close
                let _ = window.hide();
                api.prevent_close();
            }
        })

        // Setup
        .setup(|app| {
            log::info!("Application setup started");

            // Get main window - Tauri v2 uses get_webview_window
            if let Some(window) = app.get_webview_window("main") {
                // Don't hide on startup for now - user needs to see the app
                let _ = window.show();
            }

            // Start background tasks
            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                // Start resource monitoring loop
                utils::start_resource_monitor(app_handle.clone()).await;
            });

            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                // Start sync loop
                utils::start_sync_loop(app_handle).await;
            });

            Ok(())
        })

        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
