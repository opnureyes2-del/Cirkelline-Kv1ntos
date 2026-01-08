// Voice Controller - Main orchestrator for voice interaction
// Coordinates speech recognition, synthesis, and command execution

use std::sync::Arc;
use tokio::sync::{broadcast, RwLock};

use crate::accessibility::{
    AccessibilityConfig, AccessibilityEvent, VoiceState,
    SpeechSynthesizer, HotwordDetector,
    command_parser::{CommandParser, VoiceCommand},
};

/// Main voice controller that orchestrates all voice interaction
pub struct VoiceController {
    config: Arc<RwLock<AccessibilityConfig>>,
    state: Arc<RwLock<VoiceState>>,
    synthesizer: Arc<RwLock<SpeechSynthesizer>>,
    hotword_detector: Arc<RwLock<HotwordDetector>>,
    command_parser: Arc<CommandParser>,
    event_tx: broadcast::Sender<AccessibilityEvent>,
    last_response: Arc<RwLock<String>>,
}

impl VoiceController {
    /// Create new voice controller with configuration
    pub fn new(config: AccessibilityConfig) -> Self {
        let synthesizer = SpeechSynthesizer::new(&config.language, config.speech_rate);
        let hotword_detector = HotwordDetector::new(&config.hotword);
        let command_parser = CommandParser::new(&config.language);
        let (event_tx, _) = broadcast::channel(100);

        Self {
            config: Arc::new(RwLock::new(config)),
            state: Arc::new(RwLock::new(VoiceState::Idle)),
            synthesizer: Arc::new(RwLock::new(synthesizer)),
            hotword_detector: Arc::new(RwLock::new(hotword_detector)),
            command_parser: Arc::new(command_parser),
            event_tx,
            last_response: Arc::new(RwLock::new(String::new())),
        }
    }

    /// Initialize voice controller (load models, check dependencies)
    pub async fn initialize(&self) -> Result<(), String> {
        log::info!("Initializing voice controller...");

        // Initialize synthesizer
        {
            let synthesizer = self.synthesizer.read().await;
            synthesizer.initialize().await?;
        }

        // Initialize hotword detector
        {
            let detector = self.hotword_detector.read().await;
            detector.initialize().await?;
        }

        self.emit_event(AccessibilityEvent::Initialized).await;
        log::info!("Voice controller initialized");
        Ok(())
    }

    /// Start voice control (begins listening for hotword)
    pub async fn start(&mut self) -> Result<(), String> {
        let config = self.config.read().await;

        if !config.voice_enabled {
            return Err("Voice control is disabled".to_string());
        }

        // Initialize if not already done
        self.initialize().await?;

        // Start hotword detection if continuous listening is enabled
        if config.continuous_listening {
            let detector = self.hotword_detector.read().await;
            detector.start().await?;
        }

        self.set_state(VoiceState::Idle).await;
        self.emit_event(AccessibilityEvent::Started).await;

        // Play startup sound
        if config.sound_feedback {
            let synth = self.synthesizer.read().await;
            let _ = synth.play_sound("listening").await;
        }

        // Start the main voice loop
        let config_clone = self.config.clone();
        let state_clone = self.state.clone();
        let detector_clone = self.hotword_detector.clone();
        let event_tx_clone = self.event_tx.clone();

        tokio::spawn(async move {
            loop {
                let config = config_clone.read().await;
                if !config.voice_enabled {
                    break;
                }

                if config.continuous_listening {
                    // Check for hotword
                    let detector = detector_clone.read().await;
                    if detector.detected().await {
                        // Hotword detected - transition to listening state
                        let mut state = state_clone.write().await;
                        *state = VoiceState::Listening;
                        let _ = event_tx_clone.send(AccessibilityEvent::HotwordDetected);
                    }
                }

                drop(config);
                tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
            }
        });

        log::info!("Voice control started");
        Ok(())
    }

    /// Stop voice control
    pub async fn stop(&mut self) -> Result<(), String> {
        // Stop hotword detection
        {
            let detector = self.hotword_detector.read().await;
            detector.stop().await?;
        }

        // Stop any ongoing speech
        {
            let synth = self.synthesizer.read().await;
            synth.stop().await?;
        }

        self.set_state(VoiceState::Idle).await;
        self.emit_event(AccessibilityEvent::Stopped).await;

        log::info!("Voice control stopped");
        Ok(())
    }

    /// Listen for a single command (manual trigger)
    pub async fn listen_now(&self) -> Result<String, String> {
        self.set_state(VoiceState::Listening).await;
        self.emit_event(AccessibilityEvent::ListeningStarted).await;

        let config = self.config.read().await;
        if config.sound_feedback {
            let synth = self.synthesizer.read().await;
            let _ = synth.play_sound("listening").await;
        }
        drop(config);

        // Record audio and transcribe
        let transcription = self.transcribe_audio().await?;

        self.set_state(VoiceState::Processing).await;
        self.emit_event(AccessibilityEvent::Processing {
            text: transcription.clone()
        }).await;

        // Parse command
        let command = self.command_parser.parse(&transcription).await;

        // Execute command and get response
        let response = self.execute_command(command).await?;

        // Speak response if auto-speak is enabled
        let config = self.config.read().await;
        if config.auto_speak_responses {
            drop(config);
            self.speak(&response).await?;
        }

        self.set_state(VoiceState::Idle).await;
        self.emit_event(AccessibilityEvent::CommandProcessed {
            input: transcription.clone(),
            response: response.clone(),
        }).await;

        Ok(transcription)
    }

    /// Speak text aloud
    pub async fn speak(&self, text: &str) -> Result<(), String> {
        self.set_state(VoiceState::Speaking).await;
        self.emit_event(AccessibilityEvent::SpeakingStarted {
            text: text.to_string(),
        }).await;

        // Store for repeat
        {
            let mut last = self.last_response.write().await;
            *last = text.to_string();
        }

        let synth = self.synthesizer.read().await;
        synth.speak(text).await?;

        self.set_state(VoiceState::Idle).await;
        self.emit_event(AccessibilityEvent::SpeakingFinished).await;

        Ok(())
    }

    /// Get current voice state
    pub async fn get_state(&self) -> VoiceState {
        self.state.read().await.clone()
    }

    /// Subscribe to accessibility events
    pub fn subscribe(&self) -> broadcast::Receiver<AccessibilityEvent> {
        self.event_tx.subscribe()
    }

    /// Update configuration
    pub async fn update_config(&self, config: AccessibilityConfig) {
        // Update synthesizer settings
        {
            let mut synth = self.synthesizer.write().await;
            synth.set_rate(config.speech_rate);
        }

        // Update hotword
        {
            let mut detector = self.hotword_detector.write().await;
            detector.set_hotword(&config.hotword);
        }

        // Store new config
        {
            let mut cfg = self.config.write().await;
            *cfg = config;
        }

        log::info!("Voice controller config updated");
    }

    // Internal: Record audio and transcribe
    async fn transcribe_audio(&self) -> Result<String, String> {
        use std::process::Command;

        // Record audio (3 seconds)
        let temp_path = format!("/tmp/voice_input_{}.wav", uuid::Uuid::new_v4());

        let record_result = Command::new("arecord")
            .args([
                "-f", "S16_LE",
                "-r", "16000",
                "-c", "1",
                "-d", "3",  // 3 seconds
                "-q",       // Quiet mode
                &temp_path,
            ])
            .output()
            .map_err(|e| format!("Failed to record audio: {}", e))?;

        if !record_result.status.success() {
            return Err("Audio recording failed".to_string());
        }

        // Clean up temp file (transcription would use Whisper in production)
        let _ = std::fs::remove_file(&temp_path);
        
        // Placeholder - in production, use Whisper model for transcription
        Err("Speech recognition requires Whisper model. Install with: download-models command.".to_string())
    }

    // Internal: Execute a voice command
    async fn execute_command(&self, command: VoiceCommand) -> Result<String, String> {
        let config = self.config.read().await;
        let is_danish = config.language.starts_with("da");
        drop(config);

        match command {
            VoiceCommand::StartCommander => {
                Ok(if is_danish {
                    "Commander Unit starter. Du kan nu oprette opgaver med din stemme.".to_string()
                } else {
                    "Commander Unit starting. You can now create tasks with your voice.".to_string()
                })
            }
            VoiceCommand::StopCommander => {
                Ok(if is_danish {
                    "Commander Unit stoppes. Alle igangværende opgaver sættes på pause.".to_string()
                } else {
                    "Commander Unit stopping. All ongoing tasks are being paused.".to_string()
                })
            }
            VoiceCommand::GetStatus => {
                Ok(if is_danish {
                    "Systemet kører normalt. Ingen aktive opgaver i øjeblikket.".to_string()
                } else {
                    "System running normally. No active tasks at the moment.".to_string()
                })
            }
            VoiceCommand::Search { query } => {
                Ok(if is_danish {
                    format!("Søger efter: {}. Vent venligst.", query)
                } else {
                    format!("Searching for: {}. Please wait.", query)
                })
            }
            VoiceCommand::CreateTask { description, priority } => {
                Ok(if is_danish {
                    format!("Opretter opgave: {} med {} prioritet.", description,
                        match priority.as_str() {
                            "critical" => "kritisk",
                            "high" => "høj",
                            _ => "normal"
                        })
                } else {
                    format!("Creating task: {} with {} priority.", description, priority)
                })
            }
            VoiceCommand::ReadNotifications => {
                Ok(if is_danish {
                    "Du har ingen ulæste notifikationer.".to_string()
                } else {
                    "You have no unread notifications.".to_string()
                })
            }
            VoiceCommand::Help => {
                Ok(if is_danish {
                    "Du kan sige: start, stop, status, søg efter noget, opret opgave, notifikationer, hjælp, annuller, eller gentag.".to_string()
                } else {
                    "You can say: start, stop, status, search for something, create task, notifications, help, cancel, or repeat.".to_string()
                })
            }
            VoiceCommand::Cancel => {
                Ok(if is_danish {
                    "Handling annulleret.".to_string()
                } else {
                    "Action cancelled.".to_string()
                })
            }
            VoiceCommand::Repeat => {
                let last = self.last_response.read().await;
                if last.is_empty() {
                    Ok(if is_danish {
                        "Der er intet at gentage.".to_string()
                    } else {
                        "There is nothing to repeat.".to_string()
                    })
                } else {
                    Ok(last.clone())
                }
            }
            VoiceCommand::Unknown(text) => {
                Ok(if is_danish {
                    format!("Jeg forstod ikke kommandoen: {}. Sig hjælp for at se muligheder.", text)
                } else {
                    format!("I didn't understand the command: {}. Say help to see options.", text)
                })
            }
        }
    }

    // Internal: Set state and emit event
    async fn set_state(&self, state: VoiceState) {
        let mut current = self.state.write().await;
        *current = state.clone();
        let _ = self.event_tx.send(AccessibilityEvent::StateChanged { state });
    }

    // Internal: Emit event
    async fn emit_event(&self, event: AccessibilityEvent) {
        let _ = self.event_tx.send(event);
    }
}

impl Default for VoiceController {
    fn default() -> Self {
        Self::new(AccessibilityConfig::default())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_voice_controller_creation() {
        let config = AccessibilityConfig::default();
        let controller = VoiceController::new(config);
        let state = controller.get_state().await;
        assert!(matches!(state, VoiceState::Idle));
    }

    #[tokio::test]
    async fn test_execute_help_command() {
        let controller = VoiceController::new(AccessibilityConfig::default());
        let response = controller.execute_command(VoiceCommand::Help).await.unwrap();
        assert!(response.contains("hjælp") || response.contains("help"));
    }
}
