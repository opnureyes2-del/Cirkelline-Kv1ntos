// AI inference commands for Cirkelline Local Agent

use tauri::{State, Emitter};
use crate::AppState;
use crate::models::{
    EmbeddingResult, TranscriptionResult, TextExtractionResult, ModelInfo,
};
use std::time::Instant;

/// Generate embeddings for text using local model
#[tauri::command]
pub async fn generate_embedding(
    state: State<'_, AppState>,
    text: String,
) -> Result<EmbeddingResult, String> {
    let start = Instant::now();

    // Check if inference engine is available
    let engine_guard = state.inference_engine.read().await;
    let engine = engine_guard
        .as_ref()
        .ok_or("Inference-motor ikke initialiseret")?;

    // Generate embedding
    let embedding = engine.generate_embedding(&text).await?;

    Ok(EmbeddingResult {
        embedding,
        model_used: "all-MiniLM-L6-v2".to_string(),
        processing_time_ms: start.elapsed().as_millis() as u64,
    })
}

/// Transcribe audio file using local Whisper model
#[tauri::command]
pub async fn transcribe_audio(
    state: State<'_, AppState>,
    audio_path: String,
    language: Option<String>,
) -> Result<TranscriptionResult, String> {
    let start = Instant::now();

    // Validate file exists
    if !std::path::Path::new(&audio_path).exists() {
        return Err(format!("Lydfil ikke fundet: {}", audio_path));
    }

    // Check settings
    let settings = state.settings.read().await;
    if !settings.enable_transcription {
        return Err("Transskription er deaktiveret i indstillinger".to_string());
    }

    // Check inference engine
    let engine_guard = state.inference_engine.read().await;
    let engine = engine_guard
        .as_ref()
        .ok_or("Inference-motor ikke initialiseret")?;

    // Perform transcription
    let result = engine.transcribe(&audio_path, language.as_deref()).await?;

    Ok(TranscriptionResult {
        text: result.text,
        language: result.detected_language,
        confidence: result.confidence,
        segments: result
            .segments
            .into_iter()
            .map(|s| crate::models::TranscriptionSegment {
                start_ms: s.start_ms,
                end_ms: s.end_ms,
                text: s.text,
                confidence: s.confidence,
            })
            .collect(),
        processing_time_ms: start.elapsed().as_millis() as u64,
    })
}

/// Extract text from image using OCR
#[tauri::command]
pub async fn extract_text(
    state: State<'_, AppState>,
    image_path: String,
) -> Result<TextExtractionResult, String> {
    let start = Instant::now();

    // Validate file exists
    if !std::path::Path::new(&image_path).exists() {
        return Err(format!("Billedfil ikke fundet: {}", image_path));
    }

    // Check settings
    let settings = state.settings.read().await;
    if !settings.enable_ocr {
        return Err("OCR er deaktiveret i indstillinger".to_string());
    }

    // Check inference engine
    let engine_guard = state.inference_engine.read().await;
    let engine = engine_guard
        .as_ref()
        .ok_or("Inference-motor ikke initialiseret")?;

    // Perform OCR
    let result = engine.extract_text(&image_path).await?;

    Ok(TextExtractionResult {
        text: result.text,
        confidence: result.confidence,
        regions: result
            .regions
            .into_iter()
            .map(|r| crate::models::TextRegion {
                text: r.text,
                bbox: crate::models::BoundingBox {
                    x: r.x,
                    y: r.y,
                    width: r.width,
                    height: r.height,
                },
                confidence: r.confidence,
            })
            .collect(),
        processing_time_ms: start.elapsed().as_millis() as u64,
    })
}

/// Get status of installed models
#[tauri::command]
pub async fn get_model_status() -> Result<Vec<ModelInfo>, String> {
    // Return list of available models and their status
    let models = vec![
        ModelInfo {
            id: "all-minilm-l6-v2".to_string(),
            name: "MiniLM Embeddings".to_string(),
            size_mb: 23,
            tier: 1,
            capabilities: vec!["embeddings".to_string()],
            downloaded: check_model_exists("all-minilm-l6-v2"),
            download_progress: None,
            version: "1.0.0".to_string(),
        },
        ModelInfo {
            id: "whisper-tiny-en".to_string(),
            name: "Whisper Tiny (Engelsk)".to_string(),
            size_mb: 39,
            tier: 1,
            capabilities: vec!["transcription".to_string()],
            downloaded: check_model_exists("whisper-tiny-en"),
            download_progress: None,
            version: "1.0.0".to_string(),
        },
        ModelInfo {
            id: "tesseract-wasm".to_string(),
            name: "Tesseract OCR".to_string(),
            size_mb: 15,
            tier: 1,
            capabilities: vec!["ocr".to_string()],
            downloaded: check_model_exists("tesseract-wasm"),
            download_progress: None,
            version: "5.3.0".to_string(),
        },
        ModelInfo {
            id: "whisper-small".to_string(),
            name: "Whisper Small (Flersproget)".to_string(),
            size_mb: 466,
            tier: 2,
            capabilities: vec!["transcription".to_string(), "multilingual".to_string()],
            downloaded: check_model_exists("whisper-small"),
            download_progress: None,
            version: "1.0.0".to_string(),
        },
        ModelInfo {
            id: "bge-small-en".to_string(),
            name: "BGE Small Embeddings".to_string(),
            size_mb: 133,
            tier: 2,
            capabilities: vec!["embeddings".to_string(), "high-quality".to_string()],
            downloaded: check_model_exists("bge-small-en"),
            download_progress: None,
            version: "1.5.0".to_string(),
        },
        ModelInfo {
            id: "phi-3-mini-4k".to_string(),
            name: "Phi-3 Mini (LLM)".to_string(),
            size_mb: 2400,
            tier: 3,
            capabilities: vec!["llm".to_string(), "reasoning".to_string()],
            downloaded: check_model_exists("phi-3-mini-4k"),
            download_progress: None,
            version: "3.0.0".to_string(),
        },
    ];

    Ok(models)
}

/// Download a model
#[tauri::command]
pub async fn download_model(
    model_id: String,
    window: tauri::Window,
) -> Result<(), String> {
    log::info!("Starting download of model: {}", model_id);

    // Get model URL based on ID
    let model_url = get_model_download_url(&model_id)
        .ok_or(format!("Ukendt model: {}", model_id))?;

    // Create download directory
    let models_dir = get_models_directory()?;
    std::fs::create_dir_all(&models_dir)
        .map_err(|e| format!("Kunne ikke oprette model-mappe: {}", e))?;

    // Download with progress reporting
    let client = reqwest::Client::new();
    let response = client
        .get(&model_url)
        .send()
        .await
        .map_err(|e| format!("Download fejlede: {}", e))?;

    let total_size = response.content_length().unwrap_or(0);
    let mut downloaded = 0u64;

    let model_path = models_dir.join(format!("{}.onnx", model_id));
    let mut file = std::fs::File::create(&model_path)
        .map_err(|e| format!("Kunne ikke oprette fil: {}", e))?;

    let mut stream = response.bytes_stream();
    use futures_util::StreamExt;
    use std::io::Write;

    while let Some(chunk) = stream.next().await {
        let chunk = chunk.map_err(|e| format!("Download fejl: {}", e))?;
        file.write_all(&chunk)
            .map_err(|e| format!("Skrivefejl: {}", e))?;

        downloaded += chunk.len() as u64;

        // Report progress
        if total_size > 0 {
            let progress = (downloaded as f64 / total_size as f64) * 100.0;
            let _ = window.emit("model-download-progress", DownloadProgress {
                model_id: model_id.clone(),
                progress: progress as f32,
                downloaded_mb: (downloaded / 1024 / 1024) as u32,
                total_mb: (total_size / 1024 / 1024) as u32,
            });
        }
    }

    log::info!("Model {} downloaded successfully", model_id);
    Ok(())
}

fn check_model_exists(model_id: &str) -> bool {
    if let Ok(models_dir) = get_models_directory() {
        models_dir.join(format!("{}.onnx", model_id)).exists()
    } else {
        false
    }
}

fn get_models_directory() -> Result<std::path::PathBuf, String> {
    let data_dir = dirs::data_dir()
        .ok_or("Kunne ikke finde data-mappe")?;
    Ok(data_dir.join("cirkelline-cla").join("models"))
}

fn get_model_download_url(model_id: &str) -> Option<String> {
    // In production, these would be actual URLs to model files
    match model_id {
        "all-minilm-l6-v2" => Some(
            "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/onnx/model.onnx".to_string()
        ),
        "whisper-tiny-en" => Some(
            "https://huggingface.co/openai/whisper-tiny.en/resolve/main/onnx/encoder.onnx".to_string()
        ),
        // Add more model URLs as needed
        _ => None,
    }
}

#[derive(serde::Serialize, Clone)]
struct DownloadProgress {
    model_id: String,
    progress: f32,
    downloaded_mb: u32,
    total_mb: u32,
}
