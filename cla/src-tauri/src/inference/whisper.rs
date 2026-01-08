// Whisper model implementation using ONNX Runtime v2
// Model: whisper-tiny.en (39MB) or whisper-small (466MB)

use std::path::Path;
use ort::session::{Session, builder::GraphOptimizationLevel};
use ort::value::Tensor;

/// Audio transcription using Whisper
pub struct WhisperModel {
    encoder: Session,
    decoder: Session,
    model_id: String,
    sample_rate: u32,
}

/// Transcription result
pub struct TranscriptionResult {
    pub text: String,
    pub detected_language: Option<String>,
    pub confidence: f32,
    pub segments: Vec<TranscriptionSegment>,
}

pub struct TranscriptionSegment {
    pub start_ms: u64,
    pub end_ms: u64,
    pub text: String,
    pub confidence: f32,
}

impl WhisperModel {
    /// Load Whisper model from disk
    pub fn load(model_dir: &Path, model_variant: &str) -> Result<Self, String> {
        let encoder_path = model_dir.join("encoder.onnx");
        let decoder_path = model_dir.join("decoder.onnx");

        // Check files exist
        if !encoder_path.exists() {
            return Err(format!("Encoder not found: {:?}", encoder_path));
        }
        if !decoder_path.exists() {
            return Err(format!("Decoder not found: {:?}", decoder_path));
        }

        // Load encoder using ort v2 API
        let encoder = Session::builder()
            .map_err(|e| format!("Failed to create encoder builder: {}", e))?
            .with_optimization_level(GraphOptimizationLevel::Level3)
            .map_err(|e| format!("Failed to set optimization: {}", e))?
            .commit_from_file(&encoder_path)
            .map_err(|e| format!("Failed to load encoder: {}", e))?;

        // Load decoder using ort v2 API
        let decoder = Session::builder()
            .map_err(|e| format!("Failed to create decoder builder: {}", e))?
            .with_optimization_level(GraphOptimizationLevel::Level3)
            .map_err(|e| format!("Failed to set optimization: {}", e))?
            .commit_from_file(&decoder_path)
            .map_err(|e| format!("Failed to load decoder: {}", e))?;

        Ok(Self {
            encoder,
            decoder,
            model_id: format!("whisper-{}", model_variant),
            sample_rate: 16000,
        })
    }

    /// Transcribe audio file (synchronous)
    pub fn transcribe(
        &mut self,
        audio_path: &str,
        language: Option<&str>,
    ) -> Result<TranscriptionResult, String> {
        // Load and preprocess audio
        let audio_data = load_audio(audio_path, self.sample_rate)?;

        // Extract mel spectrogram features
        let mel_features = compute_mel_spectrogram(&audio_data, self.sample_rate)?;

        // Run encoder
        let encoder_output = self.run_encoder(&mel_features)?;

        // Run decoder with greedy search
        let (tokens, confidence) = self.run_decoder(&encoder_output, language)?;

        // Decode tokens to text
        let text = decode_tokens(&tokens);

        Ok(TranscriptionResult {
            text: text.clone(),
            detected_language: language.map(|s| s.to_string()),
            confidence,
            segments: vec![TranscriptionSegment {
                start_ms: 0,
                end_ms: (audio_data.len() as f64 / self.sample_rate as f64 * 1000.0) as u64,
                text,
                confidence,
            }],
        })
    }

    fn run_encoder(&mut self, mel_features: &[f32]) -> Result<Vec<f32>, String> {
        // Create mel tensor (1, 80, 3000)
        let mel_tensor = Tensor::from_array(([1usize, 80, 3000], mel_features.to_vec()))
            .map_err(|e| format!("Failed to create mel tensor: {}", e))?;

        // Build inputs vec - ort v2 inputs! returns Vec directly
        let inputs = ort::inputs![
            "mel" => mel_tensor
        ];

        let outputs = self.encoder.run(inputs)
            .map_err(|e| format!("Encoder inference failed: {}", e))?;

        let output = outputs.get("encoder_output")
            .or_else(|| outputs.get("last_hidden_state"))
            .ok_or("Missing encoder output")?;

        // ort v2: try_extract_tensor returns (&Shape, &[T]) tuple
        let (_shape, data) = output.try_extract_tensor::<f32>()
            .map_err(|e| format!("Failed to extract encoder output: {}", e))?;

        Ok(data.to_vec())
    }

    fn run_decoder(
        &mut self,
        encoder_output: &[f32],
        _language: Option<&str>,
    ) -> Result<(Vec<u32>, f32), String> {
        // Simplified greedy decoding
        let mut tokens = vec![50258u32]; // <|startoftranscript|>
        let max_length = 448;
        let mut total_log_prob = 0.0f32;
        let mut num_tokens = 0;

        // Add language token if specified
        tokens.push(50259); // <|en|> for English

        // Add task token
        tokens.push(50359); // <|transcribe|>

        // Estimate encoder output dimensions (assume 1, seq_len, hidden_dim)
        // For whisper-tiny: hidden_dim=384, for small: hidden_dim=768
        let encoder_hidden_dim = 384;
        let encoder_seq_len = encoder_output.len() / encoder_hidden_dim;

        for _ in 0..max_length {
            let input_ids: Vec<i64> = tokens.iter().map(|&x| x as i64).collect();
            let seq_len = input_ids.len();

            let input_tensor = Tensor::from_array(([1usize, seq_len], input_ids))
                .map_err(|e| format!("Failed to create decoder input: {}", e))?;

            let encoder_tensor = Tensor::from_array(([1usize, encoder_seq_len, encoder_hidden_dim], encoder_output.to_vec()))
                .map_err(|e| format!("Failed to create encoder hidden states tensor: {}", e))?;

            // Build inputs vec - ort v2 inputs! returns Vec directly
            let inputs = ort::inputs![
                "input_ids" => input_tensor,
                "encoder_hidden_states" => encoder_tensor
            ];

            let outputs = self.decoder.run(inputs)
                .map_err(|e| format!("Decoder inference failed: {}", e))?;

            let logits = outputs.get("logits")
                .ok_or("Missing logits output")?;

            // ort v2: try_extract_tensor returns (&Shape, &[T]) tuple
            let (_shape, logits_slice) = logits.try_extract_tensor::<f32>()
                .map_err(|e| format!("Failed to extract logits: {}", e))?;

            // Get last token logits
            // Logits shape: (1, seq_len, vocab_size) = 51865 for whisper
            let vocab_size = 51865;
            let last_idx = tokens.len() - 1;
            let start_offset = last_idx * vocab_size;

            let mut max_prob = f32::NEG_INFINITY;
            let mut max_token = 0u32;

            for i in 0..vocab_size {
                if let Some(&prob) = logits_slice.get(start_offset + i) {
                    if prob > max_prob {
                        max_prob = prob;
                        max_token = i as u32;
                    }
                }
            }

            // Check for end token
            if max_token == 50257 { // <|endoftext|>
                break;
            }

            tokens.push(max_token);
            total_log_prob += max_prob;
            num_tokens += 1;
        }

        let confidence = if num_tokens > 0 {
            (total_log_prob / num_tokens as f32).exp().min(1.0)
        } else {
            0.0
        };

        Ok((tokens, confidence))
    }

    pub fn model_id(&self) -> &str {
        &self.model_id
    }
}

/// Load audio file and convert to 16kHz mono f32
fn load_audio(path: &str, target_sample_rate: u32) -> Result<Vec<f32>, String> {
    let path = Path::new(path);
    let extension = path.extension()
        .and_then(|e| e.to_str())
        .unwrap_or("");

    match extension.to_lowercase().as_str() {
        "wav" => load_wav(path, target_sample_rate),
        "mp3" | "ogg" | "flac" => {
            Err("Audio format requires ffmpeg conversion. Use WAV format.".to_string())
        }
        _ => Err(format!("Unsupported audio format: {}", extension)),
    }
}

/// Load WAV file using hound crate
fn load_wav(path: &Path, target_sample_rate: u32) -> Result<Vec<f32>, String> {
    let reader = hound::WavReader::open(path)
        .map_err(|e| format!("Failed to open WAV file: {}", e))?;

    let spec = reader.spec();
    let sample_rate = spec.sample_rate;
    let channels = spec.channels as usize;

    // Read samples and convert to f32
    let samples: Vec<f32> = match spec.sample_format {
        hound::SampleFormat::Int => {
            let max_val = (1 << (spec.bits_per_sample - 1)) as f32;
            reader.into_samples::<i32>()
                .filter_map(|s| s.ok())
                .map(|s| s as f32 / max_val)
                .collect()
        }
        hound::SampleFormat::Float => {
            reader.into_samples::<f32>()
                .filter_map(|s| s.ok())
                .collect()
        }
    };

    // Convert to mono by averaging channels
    let mono_samples: Vec<f32> = if channels > 1 {
        samples.chunks(channels)
            .map(|chunk| chunk.iter().sum::<f32>() / channels as f32)
            .collect()
    } else {
        samples
    };

    // Resample if needed
    if sample_rate != target_sample_rate {
        Ok(resample(&mono_samples, sample_rate, target_sample_rate))
    } else {
        Ok(mono_samples)
    }
}

/// Simple linear resampling
fn resample(samples: &[f32], from_rate: u32, to_rate: u32) -> Vec<f32> {
    let ratio = from_rate as f64 / to_rate as f64;
    let new_len = (samples.len() as f64 / ratio) as usize;

    (0..new_len)
        .map(|i| {
            let pos = i as f64 * ratio;
            let idx = pos as usize;
            let frac = pos - idx as f64;

            let s1 = samples.get(idx).copied().unwrap_or(0.0);
            let s2 = samples.get(idx + 1).copied().unwrap_or(s1);

            s1 * (1.0 - frac as f32) + s2 * frac as f32
        })
        .collect()
}

/// Compute mel spectrogram features for Whisper
fn compute_mel_spectrogram(audio: &[f32], _sample_rate: u32) -> Result<Vec<f32>, String> {
    // Whisper expects 30 seconds of audio (480000 samples at 16kHz)
    // Output: (1, 80, 3000) mel spectrogram

    const N_MELS: usize = 80;
    const N_FRAMES: usize = 3000;
    const HOP_LENGTH: usize = 160;
    const N_FFT: usize = 400;

    // Pad or truncate to 30 seconds
    let target_len = 30 * 16000;
    let mut padded = vec![0.0f32; target_len];
    let copy_len = audio.len().min(target_len);
    padded[..copy_len].copy_from_slice(&audio[..copy_len]);

    // Compute STFT magnitude (simplified - in production use rustfft)
    let mut mel_spec = vec![0.0f32; N_MELS * N_FRAMES];

    for frame in 0..N_FRAMES {
        let start = frame * HOP_LENGTH;
        if start + N_FFT > padded.len() {
            break;
        }

        // Apply Hanning window and compute power spectrum
        let mut power = vec![0.0f32; N_FFT / 2 + 1];
        for i in 0..N_FFT {
            let window = 0.5 * (1.0 - (2.0 * std::f32::consts::PI * i as f32 / (N_FFT - 1) as f32).cos());
            let sample = padded[start + i] * window;
            // Simplified power estimation (proper implementation needs FFT)
            power[i % (N_FFT / 2 + 1)] += sample * sample;
        }

        // Apply mel filterbank (simplified)
        for mel in 0..N_MELS {
            let mut sum = 0.0f32;
            let mel_start = mel * (N_FFT / 2) / N_MELS;
            let mel_end = (mel + 1) * (N_FFT / 2) / N_MELS;
            for i in mel_start..mel_end.min(power.len()) {
                sum += power[i];
            }
            mel_spec[mel * N_FRAMES + frame] = (sum + 1e-10).log10();
        }
    }

    Ok(mel_spec)
}

/// Decode token IDs to text
fn decode_tokens(tokens: &[u32]) -> String {
    // Simplified token decoding - in production load tokenizer
    // Whisper uses GPT-2 style byte-level BPE

    // Filter special tokens and decode
    let text_tokens: Vec<_> = tokens.iter()
        .filter(|&&t| t < 50257) // Skip special tokens
        .collect();

    // This is a placeholder - real implementation needs tokenizer vocab
    if text_tokens.is_empty() {
        return String::new();
    }

    // For now, return placeholder
    format!("[{} tokens decoded]", text_tokens.len())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_resample() {
        let samples: Vec<f32> = (0..100).map(|i| i as f32).collect();
        let resampled = resample(&samples, 100, 50);
        assert_eq!(resampled.len(), 50);
    }
}
