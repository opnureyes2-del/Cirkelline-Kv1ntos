// Accessibility Tauri Commands - Voice control interface for handicapped users
// Enables complete hands-free operation

use tauri::{State, Emitter};
use std::sync::Arc;
use tokio::sync::RwLock;

use crate::accessibility::{
    AccessibilityConfig, AccessibilityEvent, VoiceState,
    VoiceController, VoiceCommand,
};

/// Accessibility state (managed by Tauri)
pub struct AccessibilityState {
    pub controller: Arc<RwLock<VoiceController>>,
    pub config: Arc<RwLock<AccessibilityConfig>>,
}

impl AccessibilityState {
    pub fn new(config: AccessibilityConfig) -> Self {
        Self {
            controller: Arc::new(RwLock::new(VoiceController::new(config.clone()))),
            config: Arc::new(RwLock::new(config)),
        }
    }
}

impl Default for AccessibilityState {
    fn default() -> Self {
        Self::new(AccessibilityConfig::default())
    }
}

/// Get accessibility configuration
#[tauri::command]
pub async fn get_accessibility_config(
    state: State<'_, AccessibilityState>,
) -> Result<AccessibilityConfig, String> {
    let config = state.config.read().await;
    Ok(config.clone())
}

/// Update accessibility configuration
#[tauri::command]
pub async fn update_accessibility_config(
    state: State<'_, AccessibilityState>,
    new_config: AccessibilityConfig,
) -> Result<(), String> {
    // Update stored config
    {
        let mut config = state.config.write().await;
        *config = new_config.clone();
    }

    // Update controller
    let controller = state.controller.read().await;
    controller.update_config(new_config).await;

    log::info!("Accessibility config updated");
    Ok(())
}

/// Get current voice state
#[tauri::command]
pub async fn get_voice_state(
    state: State<'_, AccessibilityState>,
) -> Result<VoiceState, String> {
    let controller = state.controller.read().await;
    Ok(controller.get_state().await)
}

/// Start voice control
#[tauri::command]
pub async fn start_voice_control(
    state: State<'_, AccessibilityState>,
    window: tauri::Window,
) -> Result<(), String> {
    let mut controller = state.controller.write().await;

    // Subscribe to events and forward to frontend
    let mut event_rx = controller.subscribe();
    let window_clone = window.clone();

    tokio::spawn(async move {
        while let Ok(event) = event_rx.recv().await {
            let _ = window_clone.emit("accessibility-event", &event);
        }
    });

    // Start the voice controller
    controller.start().await?;

    log::info!("Voice control started");
    Ok(())
}

/// Stop voice control
#[tauri::command]
pub async fn stop_voice_control(
    state: State<'_, AccessibilityState>,
) -> Result<(), String> {
    let mut controller = state.controller.write().await;
    controller.stop().await?;

    log::info!("Voice control stopped");
    Ok(())
}

/// Speak text aloud (text-to-speech)
#[tauri::command]
pub async fn speak_text(
    state: State<'_, AccessibilityState>,
    text: String,
) -> Result<(), String> {
    let controller = state.controller.read().await;
    controller.speak(&text).await
}

/// Listen for voice command (manual trigger)
#[tauri::command]
pub async fn listen_for_command(
    state: State<'_, AccessibilityState>,
) -> Result<String, String> {
    let controller = state.controller.read().await;
    controller.listen_now().await
}

/// Execute a voice command programmatically
#[tauri::command]
pub async fn execute_voice_command(
    command: String,
) -> Result<String, String> {
    // Parse command string into VoiceCommand
    use crate::accessibility::CommandParser;

    let parser = CommandParser::new("da-DK");
    let voice_command = parser.parse(&command).await;

    // Return description of what would be done
    match voice_command {
        VoiceCommand::StartCommander => Ok("Commander Unit startes".to_string()),
        VoiceCommand::StopCommander => Ok("Commander Unit stoppes".to_string()),
        VoiceCommand::GetStatus => Ok("Henter status...".to_string()),
        VoiceCommand::Search { query } => Ok(format!("Søger efter: {}", query)),
        VoiceCommand::CreateTask { description, priority } => {
            Ok(format!("Opretter opgave: {} (prioritet: {})", description, priority))
        }
        VoiceCommand::ReadNotifications => Ok("Læser notifikationer...".to_string()),
        VoiceCommand::Help => Ok("Viser hjælp...".to_string()),
        VoiceCommand::Cancel => Ok("Handling annulleret".to_string()),
        VoiceCommand::Repeat => Ok("Gentager sidste besked...".to_string()),
        VoiceCommand::Unknown(text) => Ok(format!("Ukendt kommando: {}", text)),
    }
}

/// Get available voice commands
#[tauri::command]
pub async fn get_available_commands() -> Result<Vec<CommandInfo>, String> {
    let commands = vec![
        CommandInfo {
            danish: vec![
                "start".to_string(),
                "start arbejde".to_string(),
                "begynd".to_string(),
            ],
            english: vec![
                "start".to_string(),
                "start working".to_string(),
                "begin".to_string(),
            ],
            description: "Start Commander Unit".to_string(),
            category: "Control".to_string(),
        },
        CommandInfo {
            danish: vec![
                "stop".to_string(),
                "stop arbejde".to_string(),
                "stands".to_string(),
            ],
            english: vec![
                "stop".to_string(),
                "stop working".to_string(),
                "halt".to_string(),
            ],
            description: "Stop Commander Unit".to_string(),
            category: "Control".to_string(),
        },
        CommandInfo {
            danish: vec![
                "status".to_string(),
                "hvad er status".to_string(),
                "hvordan går det".to_string(),
            ],
            english: vec![
                "status".to_string(),
                "what's the status".to_string(),
                "how's it going".to_string(),
            ],
            description: "Get system status".to_string(),
            category: "Information".to_string(),
        },
        CommandInfo {
            danish: vec![
                "søg efter [emne]".to_string(),
                "find [emne]".to_string(),
            ],
            english: vec![
                "search for [topic]".to_string(),
                "find [topic]".to_string(),
            ],
            description: "Search for something".to_string(),
            category: "Tasks".to_string(),
        },
        CommandInfo {
            danish: vec![
                "opret opgave [beskrivelse]".to_string(),
                "ny opgave [beskrivelse]".to_string(),
            ],
            english: vec![
                "create task [description]".to_string(),
                "new task [description]".to_string(),
            ],
            description: "Create a new task".to_string(),
            category: "Tasks".to_string(),
        },
        CommandInfo {
            danish: vec![
                "notifikationer".to_string(),
                "læs beskeder".to_string(),
            ],
            english: vec![
                "notifications".to_string(),
                "read messages".to_string(),
            ],
            description: "Read notifications".to_string(),
            category: "Information".to_string(),
        },
        CommandInfo {
            danish: vec![
                "hjælp".to_string(),
                "hvad kan du".to_string(),
            ],
            english: vec![
                "help".to_string(),
                "what can you do".to_string(),
            ],
            description: "Get help".to_string(),
            category: "Help".to_string(),
        },
        CommandInfo {
            danish: vec![
                "annuller".to_string(),
                "afbryd".to_string(),
            ],
            english: vec![
                "cancel".to_string(),
                "abort".to_string(),
            ],
            description: "Cancel current operation".to_string(),
            category: "Control".to_string(),
        },
        CommandInfo {
            danish: vec![
                "gentag".to_string(),
                "sig det igen".to_string(),
            ],
            english: vec![
                "repeat".to_string(),
                "say that again".to_string(),
            ],
            description: "Repeat last response".to_string(),
            category: "Help".to_string(),
        },
    ];

    Ok(commands)
}

/// Enable/disable accessibility mode quickly
#[tauri::command]
pub async fn toggle_accessibility_mode(
    state: State<'_, AccessibilityState>,
    enabled: bool,
) -> Result<AccessibilityConfig, String> {
    let mut config = state.config.write().await;

    config.voice_enabled = enabled;
    config.auto_speak_responses = enabled;
    config.continuous_listening = enabled;
    config.sound_feedback = enabled;

    // If enabling, also enable helpful UI features
    if enabled {
        config.high_contrast = true;
        config.large_text = true;
    }

    // Update controller
    let controller = state.controller.read().await;
    controller.update_config(config.clone()).await;

    log::info!("Accessibility mode: {}", if enabled { "enabled" } else { "disabled" });
    Ok(config.clone())
}

/// Command information for help display
#[derive(serde::Serialize, Clone)]
pub struct CommandInfo {
    pub danish: Vec<String>,
    pub english: Vec<String>,
    pub description: String,
    pub category: String,
}
