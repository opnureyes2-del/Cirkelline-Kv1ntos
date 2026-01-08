// Accessibility Module - Voice-first interface for handicapped users
// Enables complete hands-free operation through voice commands
//
// Features:
// - Hotword detection ("Hej Cirkelline")
// - Speech-to-text via Whisper
// - Text-to-speech via espeak-ng
// - Natural language command parsing (Danish/English)
// - Continuous listening mode
// - Sound feedback

pub mod voice_controller;
pub mod speech_synthesis;
pub mod hotword_detector;
pub mod command_parser;

pub use voice_controller::VoiceController;
pub use speech_synthesis::SpeechSynthesizer;
pub use hotword_detector::HotwordDetector;
pub use command_parser::{CommandParser, VoiceCommand};

use serde::{Deserialize, Serialize};

/// Configuration for accessibility features
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AccessibilityConfig {
    /// Enable voice control
    pub voice_enabled: bool,
    /// Hotword phrase to activate listening (default: "Hej Cirkelline")
    pub hotword: String,
    /// Language code (e.g., "da-DK", "en-US")
    pub language: String,
    /// Speech rate (0.5 = slow, 1.0 = normal, 2.0 = fast)
    pub speech_rate: f32,
    /// Automatically speak responses
    pub auto_speak_responses: bool,
    /// Continuously listen for hotword
    pub continuous_listening: bool,
    /// Screen reader friendly mode
    pub screen_reader_mode: bool,
    /// High contrast UI
    pub high_contrast: bool,
    /// Large text mode
    pub large_text: bool,
    /// Play sound feedback for actions
    pub sound_feedback: bool,
}

impl Default for AccessibilityConfig {
    fn default() -> Self {
        Self {
            voice_enabled: true,
            hotword: "Hej Cirkelline".to_string(),
            language: "da-DK".to_string(),
            speech_rate: 1.0,
            auto_speak_responses: true,
            continuous_listening: true,
            screen_reader_mode: false,
            high_contrast: false,
            large_text: false,
            sound_feedback: true,
        }
    }
}

/// Current state of the voice controller
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum VoiceState {
    /// Not actively listening
    Idle,
    /// Listening for voice input
    Listening,
    /// Processing voice command
    Processing,
    /// Speaking response
    Speaking,
    /// Error state
    Error(String),
}

/// Events emitted by the accessibility system
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum AccessibilityEvent {
    /// System initialized
    Initialized,
    /// Voice control started
    Started,
    /// Voice control stopped
    Stopped,
    /// Hotword detected
    HotwordDetected,
    /// Started listening for command
    ListeningStarted,
    /// Processing voice input
    Processing { text: String },
    /// Speaking started
    SpeakingStarted { text: String },
    /// Speaking finished
    SpeakingFinished,
    /// Command processed
    CommandProcessed { input: String, response: String },
    /// State changed
    StateChanged { state: VoiceState },
    /// Error occurred
    Error { message: String },
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = AccessibilityConfig::default();
        assert!(config.voice_enabled);
        assert_eq!(config.hotword, "Hej Cirkelline");
        assert_eq!(config.language, "da-DK");
        assert_eq!(config.speech_rate, 1.0);
    }

    #[test]
    fn test_voice_state_serialization() {
        let state = VoiceState::Listening;
        let json = serde_json::to_string(&state).unwrap();
        assert!(json.contains("Listening"));
    }
}
