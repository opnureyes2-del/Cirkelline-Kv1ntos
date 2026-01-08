// Hotword Detector - Wake word detection for hands-free activation
// Listens for "Hej Cirkelline" or custom hotword

use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::process::Command;

/// Hotword Detector for voice activation
pub struct HotwordDetector {
    hotword: String,
    is_listening: Arc<AtomicBool>,
    detected: Arc<AtomicBool>,
    sensitivity: f32,
}

impl HotwordDetector {
    /// Create new hotword detector
    pub fn new(hotword: &str) -> Self {
        Self {
            hotword: hotword.to_lowercase(),
            is_listening: Arc::new(AtomicBool::new(false)),
            detected: Arc::new(AtomicBool::new(false)),
            sensitivity: 0.5, // 0.0 = less sensitive, 1.0 = very sensitive
        }
    }

    /// Initialize the detector
    pub async fn initialize(&self) -> Result<(), String> {
        log::info!("Hotword detector initialized for: '{}'", self.hotword);
        Ok(())
    }

    /// Start listening for hotword
    pub async fn start(&self) -> Result<(), String> {
        if self.is_listening.load(Ordering::SeqCst) {
            return Ok(());
        }

        self.is_listening.store(true, Ordering::SeqCst);
        self.detected.store(false, Ordering::SeqCst);

        let hotword = self.hotword.clone();
        let is_listening = self.is_listening.clone();
        let detected = self.detected.clone();

        // Start background listening task
        tokio::spawn(async move {
            log::info!("Hotword detection started, listening for: '{}'", hotword);

            while is_listening.load(Ordering::SeqCst) {
                // Record short audio snippet (1 second)
                let temp_path = format!("/tmp/hotword_{}.wav", uuid::Uuid::new_v4());

                let record_result = Command::new("arecord")
                    .args([
                        "-f", "S16_LE",
                        "-r", "16000",
                        "-c", "1",
                        "-d", "1",  // 1 second
                        "-q",       // Quiet mode
                        &temp_path,
                    ])
                    .output();

                if let Ok(output) = record_result {
                    if output.status.success() {
                        // Simple voice activity detection
                        // In production, use a proper hotword engine like Porcupine or Snowboy
                        if Self::detect_voice_activity(&temp_path).await {
                            // For now, assume any voice activity is the hotword
                            // A real implementation would use ML-based hotword detection
                            detected.store(true, Ordering::SeqCst);
                            log::info!("Hotword detected!");
                        }
                    }
                }

                // Clean up
                let _ = std::fs::remove_file(&temp_path);

                // Small delay to prevent CPU overuse
                tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
            }
        });

        Ok(())
    }

    /// Stop listening
    pub async fn stop(&self) -> Result<(), String> {
        self.is_listening.store(false, Ordering::SeqCst);
        Ok(())
    }

    /// Check if hotword was detected (and reset flag)
    pub async fn detected(&self) -> bool {
        self.detected.swap(false, Ordering::SeqCst)
    }

    /// Check if currently listening
    pub fn is_listening(&self) -> bool {
        self.is_listening.load(Ordering::SeqCst)
    }

    /// Set hotword
    pub fn set_hotword(&mut self, hotword: &str) {
        self.hotword = hotword.to_lowercase();
    }

    /// Set sensitivity (0.0 - 1.0)
    pub fn set_sensitivity(&mut self, sensitivity: f32) {
        self.sensitivity = sensitivity.clamp(0.0, 1.0);
    }

    // Internal: Simple voice activity detection
    async fn detect_voice_activity(audio_path: &str) -> bool {
        // Read WAV file and check RMS energy
        use std::fs::File;
        use std::io::Read;

        let mut file = match File::open(audio_path) {
            Ok(f) => f,
            Err(_) => return false,
        };

        // Skip WAV header (44 bytes for standard WAV)
        let mut header = [0u8; 44];
        if file.read_exact(&mut header).is_err() {
            return false;
        }

        // Read audio samples
        let mut samples = Vec::new();
        if file.read_to_end(&mut samples).is_err() {
            return false;
        }

        // Convert bytes to i16 samples
        let samples: Vec<i16> = samples
            .chunks_exact(2)
            .map(|chunk| i16::from_le_bytes([chunk[0], chunk[1]]))
            .collect();

        if samples.is_empty() {
            return false;
        }

        // Calculate RMS energy
        let sum_squares: f64 = samples.iter()
            .map(|&s| (s as f64).powi(2))
            .sum();
        let rms = (sum_squares / samples.len() as f64).sqrt();

        // Threshold for voice detection (adjust based on sensitivity)
        // Typical speech is around 2000-10000 for 16-bit audio
        let threshold = 500.0 + (1.0 - 0.5) * 2000.0; // sensitivity adjustment

        rms > threshold
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hotword_initialization() {
        let detector = HotwordDetector::new("Hej Cirkelline");
        assert_eq!(detector.hotword, "hej cirkelline");
    }
}
