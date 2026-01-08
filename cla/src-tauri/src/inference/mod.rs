// AI Inference Engine for Cirkelline Local Agent
// Uses ONNX Runtime for cross-platform inference

mod embedding;
mod whisper;
mod ocr;

pub use embedding::EmbeddingModel;
pub use whisper::{WhisperModel, TranscriptionResult as TranscriptionOutput, TranscriptionSegment};
pub use ocr::{OcrEngine, OcrResult as OcrOutput, TextRegion as OcrRegion};

use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::Mutex;

/// Main inference engine managing all AI models
pub struct InferenceEngine {
    models_dir: PathBuf,
    embedding_model: Option<Arc<Mutex<EmbeddingModel>>>,
    whisper_model: Option<Arc<Mutex<WhisperModel>>>,
    ocr_engine: Option<Arc<Mutex<OcrEngine>>>,
}

impl InferenceEngine {
    /// Create a new inference engine
    pub async fn new(models_dir: PathBuf) -> Result<Self, String> {
        std::fs::create_dir_all(&models_dir)
            .map_err(|e| format!("Failed to create models directory: {}", e))?;

        let mut engine = Self {
            models_dir,
            embedding_model: None,
            whisper_model: None,
            ocr_engine: None,
        };

        // Try to load available models
        engine.load_available_models().await?;

        Ok(engine)
    }

    /// Load all available models from disk
    async fn load_available_models(&mut self) -> Result<(), String> {
        // Load embedding model if available
        let embedding_model_path = self.models_dir.join("all-minilm-l6-v2.onnx");

        if embedding_model_path.exists() {
            match EmbeddingModel::load(&embedding_model_path) {
                Ok(model) => {
                    log::info!("Loaded embedding model from {:?}", embedding_model_path);
                    self.embedding_model = Some(Arc::new(Mutex::new(model)));
                }
                Err(e) => {
                    log::warn!("Failed to load embedding model: {}", e);
                }
            }
        } else {
            log::info!("Embedding model not found at {:?}", embedding_model_path);
        }

        // Load Whisper model if available
        let whisper_dir = self.models_dir.join("whisper-tiny-en");

        if whisper_dir.exists() {
            match WhisperModel::load(&whisper_dir, "tiny-en") {
                Ok(model) => {
                    log::info!("Loaded Whisper model from {:?}", whisper_dir);
                    self.whisper_model = Some(Arc::new(Mutex::new(model)));
                }
                Err(e) => {
                    log::warn!("Failed to load Whisper model: {}", e);
                }
            }
        } else {
            log::info!("Whisper model not found at {:?}", whisper_dir);
        }

        // Initialize OCR engine
        match OcrEngine::new("eng") {
            Ok(engine) => {
                log::info!("Initialized OCR engine");
                self.ocr_engine = Some(Arc::new(Mutex::new(engine)));
            }
            Err(e) => {
                log::warn!("Failed to initialize OCR: {}", e);
            }
        }

        Ok(())
    }

    /// Check if embedding model is available
    pub fn has_embedding_model(&self) -> bool {
        self.embedding_model.is_some()
    }

    /// Check if whisper model is available
    pub fn has_whisper_model(&self) -> bool {
        self.whisper_model.is_some()
    }

    /// Generate embedding for text
    pub async fn generate_embedding(&self, text: &str) -> Result<Vec<f32>, String> {
        let model = self.embedding_model
            .as_ref()
            .ok_or("Embedding model not loaded. Download the model first.")?;

        let mut model = model.lock().await;
        // encode() is synchronous, no await needed
        model.encode(text)
    }

    /// Transcribe audio file
    pub async fn transcribe(
        &self,
        audio_path: &str,
        language: Option<&str>,
    ) -> Result<TranscriptionOutput, String> {
        let model = self.whisper_model
            .as_ref()
            .ok_or("Whisper model not loaded. Download the model first.")?;

        let mut model = model.lock().await;
        // transcribe() is synchronous, no await needed
        model.transcribe(audio_path, language)
    }

    /// Extract text from image
    pub async fn extract_text(&self, image_path: &str) -> Result<OcrOutput, String> {
        let engine = self.ocr_engine
            .as_ref()
            .ok_or("OCR engine not initialized")?;

        let engine = engine.lock().await;
        // extract() is synchronous, no await needed
        engine.extract(image_path)
    }

    /// Get models directory path
    pub fn models_dir(&self) -> &PathBuf {
        &self.models_dir
    }
}
