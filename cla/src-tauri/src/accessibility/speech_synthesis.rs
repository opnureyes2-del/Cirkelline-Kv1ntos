// Speech Synthesis - Text-to-Speech for accessibility
// Uses espeak-ng on Linux, native APIs on other platforms

use std::process::Command;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

/// Speech Synthesizer for text-to-speech output
pub struct SpeechSynthesizer {
    language: String,
    rate: f32,
    volume: f32,
    is_speaking: Arc<AtomicBool>,
    last_text: Arc<tokio::sync::RwLock<String>>,
}

impl SpeechSynthesizer {
    /// Create new speech synthesizer
    pub fn new(language: &str, rate: f32) -> Self {
        Self {
            language: language.to_string(),
            rate,
            volume: 1.0,
            is_speaking: Arc::new(AtomicBool::new(false)),
            last_text: Arc::new(tokio::sync::RwLock::new(String::new())),
        }
    }

    /// Initialize the synthesizer
    pub async fn initialize(&self) -> Result<(), String> {
        // Check if espeak-ng is available
        let result = Command::new("espeak-ng")
            .arg("--version")
            .output();

        match result {
            Ok(output) if output.status.success() => {
                log::info!("Speech synthesis available via espeak-ng");
                Ok(())
            }
            _ => {
                // Try piper as alternative
                let piper = Command::new("piper")
                    .arg("--version")
                    .output();

                match piper {
                    Ok(output) if output.status.success() => {
                        log::info!("Speech synthesis available via piper");
                        Ok(())
                    }
                    _ => {
                        log::warn!("No TTS engine found. Install espeak-ng: sudo apt install espeak-ng");
                        Err("No TTS engine available".to_string())
                    }
                }
            }
        }
    }

    /// Speak text aloud
    pub async fn speak(&self, text: &str) -> Result<(), String> {
        if self.is_speaking.load(Ordering::SeqCst) {
            // Wait for current speech to finish
            while self.is_speaking.load(Ordering::SeqCst) {
                tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
            }
        }

        self.is_speaking.store(true, Ordering::SeqCst);

        // Store for repeat command
        {
            let mut last = self.last_text.write().await;
            *last = text.to_string();
        }

        // Map language code to espeak voice
        let voice = match self.language.as_str() {
            "da-DK" | "da" => "da",
            "en-US" | "en" => "en-us",
            "en-GB" => "en-gb",
            "de-DE" | "de" => "de",
            "sv-SE" | "sv" => "sv",
            "no-NO" | "no" => "no",
            _ => "en-us",
        };

        // Calculate words per minute (default 175, adjust by rate)
        let wpm = (175.0 * self.rate) as u32;

        // Build command
        let result = Command::new("espeak-ng")
            .args([
                "-v", voice,
                "-s", &wpm.to_string(),
                "-a", &((self.volume * 100.0) as u32).to_string(),
                text,
            ])
            .output();

        self.is_speaking.store(false, Ordering::SeqCst);

        match result {
            Ok(output) if output.status.success() => {
                log::debug!("Spoke: {}", text);
                Ok(())
            }
            Ok(output) => {
                Err(format!("TTS failed: {}", String::from_utf8_lossy(&output.stderr)))
            }
            Err(e) => {
                // Fallback: Try piper
                self.speak_with_piper(text).await
                    .map_err(|_| format!("TTS failed: {}", e))
            }
        }
    }

    /// Speak with piper TTS (higher quality but requires model)
    async fn speak_with_piper(&self, text: &str) -> Result<(), String> {
        // Piper requires piping text to stdin
        use std::io::Write;
        use std::process::Stdio;

        let model_path = dirs::data_dir()
            .ok_or("No data dir")?
            .join("cirkelline-cla")
            .join("models")
            .join("piper-da.onnx");

        if !model_path.exists() {
            return Err("Piper model not found".to_string());
        }

        let mut child = Command::new("piper")
            .args([
                "--model", model_path.to_str().unwrap(),
                "--output-raw",
            ])
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to start piper: {}", e))?;

        if let Some(mut stdin) = child.stdin.take() {
            stdin.write_all(text.as_bytes())
                .map_err(|e| format!("Failed to write to piper: {}", e))?;
        }

        let output = child.wait_with_output()
            .map_err(|e| format!("Piper failed: {}", e))?;

        if output.status.success() {
            // Play raw audio with aplay
            let mut play = Command::new("aplay")
                .args(["-r", "22050", "-f", "S16_LE", "-c", "1"])
                .stdin(Stdio::piped())
                .spawn()
                .map_err(|e| format!("Failed to play audio: {}", e))?;

            if let Some(mut stdin) = play.stdin.take() {
                stdin.write_all(&output.stdout)
                    .map_err(|e| format!("Failed to write audio: {}", e))?;
            }

            play.wait().map_err(|e| format!("Playback failed: {}", e))?;
            Ok(())
        } else {
            Err("Piper synthesis failed".to_string())
        }
    }

    /// Play a notification sound
    pub async fn play_sound(&self, sound_type: &str) -> Result<(), String> {
        let sound_file = match sound_type {
            "listening" => "/usr/share/sounds/freedesktop/stereo/dialog-information.oga",
            "success" => "/usr/share/sounds/freedesktop/stereo/complete.oga",
            "error" => "/usr/share/sounds/freedesktop/stereo/dialog-error.oga",
            "notification" => "/usr/share/sounds/freedesktop/stereo/message.oga",
            _ => return Ok(()), // No sound for unknown types
        };

        if std::path::Path::new(sound_file).exists() {
            let _ = Command::new("paplay")
                .arg(sound_file)
                .output();
        }

        Ok(())
    }

    /// Repeat last spoken text
    pub async fn repeat(&self) -> Result<(), String> {
        let text = self.last_text.read().await.clone();
        if text.is_empty() {
            self.speak("Der er intet at gentage.").await
        } else {
            self.speak(&text).await
        }
    }

    /// Stop current speech
    pub async fn stop(&self) -> Result<(), String> {
        // Kill any running espeak processes
        let _ = Command::new("pkill")
            .args(["-9", "espeak-ng"])
            .output();

        self.is_speaking.store(false, Ordering::SeqCst);
        Ok(())
    }

    /// Check if currently speaking
    pub fn is_speaking(&self) -> bool {
        self.is_speaking.load(Ordering::SeqCst)
    }

    /// Set speech rate
    pub fn set_rate(&mut self, rate: f32) {
        self.rate = rate.clamp(0.25, 3.0);
    }

    /// Set volume
    pub fn set_volume(&mut self, volume: f32) {
        self.volume = volume.clamp(0.0, 1.0);
    }
}
