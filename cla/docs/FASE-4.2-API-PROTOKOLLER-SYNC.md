# FASE 4.2: API'er, Protokoller og Synkronisering
## Cirkelline Local Agent (CLA) Implementation

**Version:** 1.0
**Dato:** 2025-12-08
**Status:** Specifikation Komplet

---

## 4.2.1: INTERNE API'ER FOR CLA-LOKAL RESSOURCEKOMMUNIKATION

### Tauri IPC Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CLA INTERNAL API ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    FRONTEND (WebView)                               │   │
│  │                                                                     │   │
│  │   TypeScript/React Application                                      │   │
│  │   └── @tauri-apps/api/invoke('command_name', { params })           │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                  │                                         │
│                          Tauri IPC Bridge                                  │
│                                  │                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    BACKEND (Rust Core)                              │   │
│  │                                                                     │   │
│  │   #[tauri::command] functions                                       │   │
│  │   ├── Resource Monitor Commands                                     │   │
│  │   ├── Model Inference Commands                                      │   │
│  │   ├── File System Commands                                          │   │
│  │   ├── Database Commands                                             │   │
│  │   └── Network Commands                                              │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Resource Monitor API

```rust
// src-tauri/src/commands/resource_monitor.rs

use serde::{Deserialize, Serialize};
use sysinfo::{System, SystemExt, ProcessorExt, DiskExt, ComponentExt};
use tauri::command;

#[derive(Serialize)]
pub struct SystemMetrics {
    pub cpu_usage: f32,
    pub cpu_count: usize,
    pub memory_used_mb: u64,
    pub memory_total_mb: u64,
    pub memory_usage_percent: f32,
    pub gpu_available: bool,
    pub gpu_usage: Option<f32>,
    pub gpu_memory_used_mb: Option<u64>,
    pub gpu_memory_total_mb: Option<u64>,
    pub battery_level: Option<f32>,
    pub is_charging: bool,
    pub temperature_cpu: Option<f32>,
    pub disk_available_mb: u64,
    pub network_connected: bool,
}

#[derive(Serialize)]
pub struct ResourceLimits {
    pub cpu_max_percent: f32,
    pub memory_max_percent: f32,
    pub gpu_max_percent: f32,
    pub battery_min_percent: f32,
    pub temperature_max_celsius: f32,
}

#[derive(Serialize)]
pub struct CanExecuteResult {
    pub can_execute: bool,
    pub reason: Option<String>,
    pub estimated_wait_seconds: Option<u32>,
}

/// Get current system metrics
#[command]
pub async fn get_system_metrics() -> Result<SystemMetrics, String> {
    let mut sys = System::new_all();
    sys.refresh_all();

    let cpu_usage = sys.global_processor_info().cpu_usage();
    let memory_used = sys.used_memory() / 1024 / 1024;
    let memory_total = sys.total_memory() / 1024 / 1024;
    let memory_percent = (memory_used as f32 / memory_total as f32) * 100.0;

    // GPU detection (platform-specific)
    let (gpu_available, gpu_usage, gpu_mem_used, gpu_mem_total) = detect_gpu_metrics();

    // Battery (platform-specific)
    let (battery_level, is_charging) = get_battery_status();

    // Temperature
    let temperature = sys.components()
        .iter()
        .find(|c| c.label().contains("CPU") || c.label().contains("Core"))
        .map(|c| c.temperature());

    // Disk
    let disk_available = sys.disks()
        .first()
        .map(|d| d.available_space() / 1024 / 1024)
        .unwrap_or(0);

    Ok(SystemMetrics {
        cpu_usage,
        cpu_count: sys.processors().len(),
        memory_used_mb: memory_used,
        memory_total_mb: memory_total,
        memory_usage_percent: memory_percent,
        gpu_available,
        gpu_usage,
        gpu_memory_used_mb: gpu_mem_used,
        gpu_memory_total_mb: gpu_mem_total,
        battery_level,
        is_charging,
        temperature_cpu: temperature,
        disk_available_mb: disk_available,
        network_connected: check_network_connectivity(),
    })
}

/// Check if task can be executed with current resources
#[command]
pub async fn can_execute_task(
    task_type: String,
    estimated_cpu: f32,
    estimated_memory_mb: u64,
    requires_gpu: bool,
) -> Result<CanExecuteResult, String> {
    let metrics = get_system_metrics().await?;
    let limits = get_resource_limits().await?;

    // Check CPU
    if metrics.cpu_usage + estimated_cpu > limits.cpu_max_percent {
        return Ok(CanExecuteResult {
            can_execute: false,
            reason: Some(format!(
                "CPU usage too high: {:.1}% + {:.1}% > {:.1}%",
                metrics.cpu_usage, estimated_cpu, limits.cpu_max_percent
            )),
            estimated_wait_seconds: Some(30),
        });
    }

    // Check Memory
    let estimated_memory_percent = (estimated_memory_mb as f32 / metrics.memory_total_mb as f32) * 100.0;
    if metrics.memory_usage_percent + estimated_memory_percent > limits.memory_max_percent {
        return Ok(CanExecuteResult {
            can_execute: false,
            reason: Some("Insufficient memory available".to_string()),
            estimated_wait_seconds: Some(60),
        });
    }

    // Check GPU if required
    if requires_gpu && !metrics.gpu_available {
        return Ok(CanExecuteResult {
            can_execute: false,
            reason: Some("GPU required but not available".to_string()),
            estimated_wait_seconds: None,
        });
    }

    // Check Battery
    if let Some(battery) = metrics.battery_level {
        if battery < limits.battery_min_percent && !metrics.is_charging {
            return Ok(CanExecuteResult {
                can_execute: false,
                reason: Some(format!("Battery too low: {:.0}%", battery)),
                estimated_wait_seconds: None,
            });
        }
    }

    // Check Temperature
    if let Some(temp) = metrics.temperature_cpu {
        if temp > limits.temperature_max_celsius {
            return Ok(CanExecuteResult {
                can_execute: false,
                reason: Some(format!("CPU temperature too high: {:.1}°C", temp)),
                estimated_wait_seconds: Some(120),
            });
        }
    }

    Ok(CanExecuteResult {
        can_execute: true,
        reason: None,
        estimated_wait_seconds: None,
    })
}

/// Get user idle time in seconds
#[command]
pub fn get_idle_time_seconds() -> u64 {
    #[cfg(target_os = "windows")]
    {
        use windows::Win32::UI::Input::KeyboardAndMouse::{GetLastInputInfo, LASTINPUTINFO};
        unsafe {
            let mut lii = LASTINPUTINFO {
                cbSize: std::mem::size_of::<LASTINPUTINFO>() as u32,
                dwTime: 0,
            };
            if GetLastInputInfo(&mut lii).as_bool() {
                let tick_count = windows::Win32::System::SystemInformation::GetTickCount();
                return ((tick_count - lii.dwTime) / 1000) as u64;
            }
        }
        0
    }

    #[cfg(target_os = "macos")]
    {
        use core_graphics::event_source::{
            CGEventSourceGetSecondsSinceLastEventType,
            CGEventSourceStateID,
            CGEventType,
        };
        unsafe {
            CGEventSourceGetSecondsSinceLastEventType(
                CGEventSourceStateID::HIDSystemState,
                CGEventType::MouseMoved,
            ) as u64
        }
    }

    #[cfg(target_os = "linux")]
    {
        // X11 XScreenSaver extension
        0 // TODO: Implement X11 idle detection
    }
}

/// Get current resource limits (from user settings)
#[command]
pub async fn get_resource_limits() -> Result<ResourceLimits, String> {
    // Load from settings file or use defaults
    Ok(ResourceLimits {
        cpu_max_percent: 30.0,
        memory_max_percent: 20.0,
        gpu_max_percent: 40.0,
        battery_min_percent: 20.0,
        temperature_max_celsius: 75.0,
    })
}

/// Set resource limits
#[command]
pub async fn set_resource_limits(limits: ResourceLimits) -> Result<(), String> {
    // Save to settings file
    // Validate limits are reasonable
    if limits.cpu_max_percent > 80.0 || limits.cpu_max_percent < 5.0 {
        return Err("CPU limit must be between 5% and 80%".to_string());
    }
    // ... more validation
    Ok(())
}
```

### Model Inference API

```rust
// src-tauri/src/commands/inference.rs

use ort::{Environment, Session, SessionBuilder, Value};
use std::sync::Arc;
use tokio::sync::Mutex;

/// Lazy-loaded ONNX sessions
struct ModelManager {
    embedding_session: Option<Arc<Session>>,
    whisper_encoder: Option<Arc<Session>>,
    whisper_decoder: Option<Arc<Session>>,
    ocr_session: Option<Arc<Session>>,
    llm_session: Option<Arc<Session>>,
}

lazy_static::lazy_static! {
    static ref MODEL_MANAGER: Mutex<ModelManager> = Mutex::new(ModelManager {
        embedding_session: None,
        whisper_encoder: None,
        whisper_decoder: None,
        ocr_session: None,
        llm_session: None,
    });

    static ref ONNX_ENV: Arc<Environment> = Arc::new(
        Environment::builder()
            .with_name("CLA")
            .with_execution_providers([
                #[cfg(feature = "cuda")]
                ort::ExecutionProvider::CUDA(Default::default()),
                #[cfg(target_os = "macos")]
                ort::ExecutionProvider::CoreML(Default::default()),
                ort::ExecutionProvider::CPU(Default::default()),
            ])
            .build()
            .expect("Failed to create ONNX environment")
    );
}

#[derive(Serialize)]
pub struct EmbeddingResult {
    pub embedding: Vec<f32>,
    pub dimensions: usize,
    pub processing_time_ms: u64,
}

#[derive(Serialize)]
pub struct TranscriptionResult {
    pub text: String,
    pub segments: Vec<TranscriptSegment>,
    pub language: String,
    pub processing_time_ms: u64,
}

#[derive(Serialize)]
pub struct TranscriptSegment {
    pub start_time: f32,
    pub end_time: f32,
    pub text: String,
    pub confidence: f32,
}

#[derive(Serialize)]
pub struct OCRResult {
    pub text: String,
    pub boxes: Vec<TextBox>,
    pub confidence: f32,
    pub processing_time_ms: u64,
}

#[derive(Serialize)]
pub struct TextBox {
    pub x: i32,
    pub y: i32,
    pub width: i32,
    pub height: i32,
    pub text: String,
    pub confidence: f32,
}

/// Load model into memory
#[command]
pub async fn load_model(model_type: String) -> Result<(), String> {
    let mut manager = MODEL_MANAGER.lock().await;
    let models_dir = get_models_directory();

    match model_type.as_str() {
        "embedding" => {
            if manager.embedding_session.is_none() {
                let model_path = models_dir.join("embedding/all-MiniLM-L6-v2.onnx");
                let session = SessionBuilder::new(&ONNX_ENV)
                    .map_err(|e| e.to_string())?
                    .with_model_from_file(&model_path)
                    .map_err(|e| e.to_string())?;
                manager.embedding_session = Some(Arc::new(session));
            }
        }
        "whisper_tiny" => {
            if manager.whisper_encoder.is_none() {
                let encoder_path = models_dir.join("whisper/encoder.onnx");
                let decoder_path = models_dir.join("whisper/decoder.onnx");
                // Load encoder and decoder
            }
        }
        "ocr" => {
            // Tesseract WASM is handled differently in frontend
        }
        "llm" => {
            if manager.llm_session.is_none() {
                let model_path = models_dir.join("llm/phi-3-mini-4k.onnx");
                if model_path.exists() {
                    let session = SessionBuilder::new(&ONNX_ENV)
                        .map_err(|e| e.to_string())?
                        .with_model_from_file(&model_path)
                        .map_err(|e| e.to_string())?;
                    manager.llm_session = Some(Arc::new(session));
                } else {
                    return Err("LLM model not installed".to_string());
                }
            }
        }
        _ => return Err(format!("Unknown model type: {}", model_type)),
    }

    Ok(())
}

/// Generate embedding for text
#[command]
pub async fn generate_embedding(text: String) -> Result<EmbeddingResult, String> {
    let start = std::time::Instant::now();

    let manager = MODEL_MANAGER.lock().await;
    let session = manager.embedding_session
        .as_ref()
        .ok_or("Embedding model not loaded")?;

    // Tokenize
    let tokenized = tokenize_for_embedding(&text)?;

    // Run inference
    let outputs = session.run(vec![
        Value::from_array(tokenized.input_ids.view())?,
        Value::from_array(tokenized.attention_mask.view())?,
    ]).map_err(|e| e.to_string())?;

    // Extract embedding (mean pooling)
    let embedding = mean_pooling(&outputs[0], &tokenized.attention_mask)?;

    Ok(EmbeddingResult {
        embedding: embedding.clone(),
        dimensions: embedding.len(),
        processing_time_ms: start.elapsed().as_millis() as u64,
    })
}

/// Transcribe audio file
#[command]
pub async fn transcribe_audio(
    audio_path: String,
    language: Option<String>,
) -> Result<TranscriptionResult, String> {
    let start = std::time::Instant::now();

    // Read and preprocess audio
    let audio_data = load_and_preprocess_audio(&audio_path)?;

    let manager = MODEL_MANAGER.lock().await;
    let encoder = manager.whisper_encoder
        .as_ref()
        .ok_or("Whisper model not loaded")?;
    let decoder = manager.whisper_decoder
        .as_ref()
        .ok_or("Whisper model not loaded")?;

    // Run inference
    let (text, segments, detected_language) = whisper_inference(
        encoder, decoder, &audio_data, language
    )?;

    Ok(TranscriptionResult {
        text,
        segments,
        language: detected_language,
        processing_time_ms: start.elapsed().as_millis() as u64,
    })
}

/// Check if model is loaded
#[command]
pub async fn is_model_loaded(model_type: String) -> bool {
    let manager = MODEL_MANAGER.lock().await;
    match model_type.as_str() {
        "embedding" => manager.embedding_session.is_some(),
        "whisper" => manager.whisper_encoder.is_some(),
        "llm" => manager.llm_session.is_some(),
        _ => false,
    }
}

/// Unload model to free memory
#[command]
pub async fn unload_model(model_type: String) -> Result<(), String> {
    let mut manager = MODEL_MANAGER.lock().await;
    match model_type.as_str() {
        "embedding" => manager.embedding_session = None,
        "whisper" => {
            manager.whisper_encoder = None;
            manager.whisper_decoder = None;
        }
        "llm" => manager.llm_session = None,
        _ => return Err(format!("Unknown model type: {}", model_type)),
    }
    Ok(())
}
```

### TypeScript API Client

```typescript
// src/lib/cla-api.ts

import { invoke } from '@tauri-apps/api/tauri';

// Types
export interface SystemMetrics {
  cpu_usage: number;
  cpu_count: number;
  memory_used_mb: number;
  memory_total_mb: number;
  memory_usage_percent: number;
  gpu_available: boolean;
  gpu_usage?: number;
  gpu_memory_used_mb?: number;
  gpu_memory_total_mb?: number;
  battery_level?: number;
  is_charging: boolean;
  temperature_cpu?: number;
  disk_available_mb: number;
  network_connected: boolean;
}

export interface ResourceLimits {
  cpu_max_percent: number;
  memory_max_percent: number;
  gpu_max_percent: number;
  battery_min_percent: number;
  temperature_max_celsius: number;
}

export interface CanExecuteResult {
  can_execute: boolean;
  reason?: string;
  estimated_wait_seconds?: number;
}

export interface EmbeddingResult {
  embedding: number[];
  dimensions: number;
  processing_time_ms: number;
}

export interface TranscriptionResult {
  text: string;
  segments: TranscriptSegment[];
  language: string;
  processing_time_ms: number;
}

export interface TranscriptSegment {
  start_time: number;
  end_time: number;
  text: string;
  confidence: number;
}

// Resource Monitor API
export const ResourceMonitor = {
  async getMetrics(): Promise<SystemMetrics> {
    return invoke('get_system_metrics');
  },

  async canExecuteTask(
    taskType: string,
    estimatedCpu: number,
    estimatedMemoryMb: number,
    requiresGpu: boolean
  ): Promise<CanExecuteResult> {
    return invoke('can_execute_task', {
      task_type: taskType,
      estimated_cpu: estimatedCpu,
      estimated_memory_mb: estimatedMemoryMb,
      requires_gpu: requiresGpu,
    });
  },

  async getIdleTime(): Promise<number> {
    return invoke('get_idle_time_seconds');
  },

  async getLimits(): Promise<ResourceLimits> {
    return invoke('get_resource_limits');
  },

  async setLimits(limits: ResourceLimits): Promise<void> {
    return invoke('set_resource_limits', { limits });
  },
};

// Model Inference API
export const ModelInference = {
  async loadModel(modelType: string): Promise<void> {
    return invoke('load_model', { model_type: modelType });
  },

  async isModelLoaded(modelType: string): Promise<boolean> {
    return invoke('is_model_loaded', { model_type: modelType });
  },

  async unloadModel(modelType: string): Promise<void> {
    return invoke('unload_model', { model_type: modelType });
  },

  async generateEmbedding(text: string): Promise<EmbeddingResult> {
    return invoke('generate_embedding', { text });
  },

  async transcribeAudio(
    audioPath: string,
    language?: string
  ): Promise<TranscriptionResult> {
    return invoke('transcribe_audio', { audio_path: audioPath, language });
  },
};

// Database API
export const LocalDatabase = {
  async query<T>(storeName: string, index?: string, range?: IDBKeyRange): Promise<T[]> {
    return invoke('db_query', { store_name: storeName, index, range });
  },

  async put<T>(storeName: string, data: T): Promise<void> {
    return invoke('db_put', { store_name: storeName, data });
  },

  async delete(storeName: string, key: string): Promise<void> {
    return invoke('db_delete', { store_name: storeName, key });
  },

  async count(storeName: string): Promise<number> {
    return invoke('db_count', { store_name: storeName });
  },
};

// File System API
export const FileSystem = {
  async readFile(path: string): Promise<Uint8Array> {
    return invoke('read_file_for_processing', { path });
  },

  async writeFile(filename: string, data: Uint8Array): Promise<string> {
    return invoke('store_processed_result', { filename, data: Array.from(data) });
  },

  async getCacheDir(): Promise<string> {
    return invoke('get_cache_directory');
  },

  async getModelsDir(): Promise<string> {
    return invoke('get_models_directory');
  },
};
```

---

## 4.2.2: DATAUDVEKSLINGSPROTOKOLLER MED CKC

### Protocol Buffer Definitions (gRPC)

```protobuf
// proto/cla_sync.proto

syntax = "proto3";

package cirkelline.cla;

option java_package = "com.cirkelline.cla";
option go_package = "cirkelline/cla";

// ═══════════════════════════════════════════════════════════════════════════
// AUTHENTICATION SERVICE
// ═══════════════════════════════════════════════════════════════════════════

service AuthService {
  // Authenticate CLA with CKC
  rpc Authenticate(AuthRequest) returns (AuthResponse);
  // Refresh authentication token
  rpc RefreshToken(RefreshRequest) returns (AuthResponse);
  // Revoke CLA access
  rpc RevokeAccess(RevokeRequest) returns (RevokeResponse);
}

message AuthRequest {
  string user_token = 1;        // User's JWT from web login
  string device_id = 2;         // Unique device identifier
  DeviceInfo device_info = 3;   // Device metadata
}

message DeviceInfo {
  string os = 1;                // "windows", "macos", "linux"
  string os_version = 2;        // "10", "14.0", "22.04"
  string cla_version = 3;       // "1.0.0"
  bool has_gpu = 4;
  string gpu_model = 5;
  uint64 memory_mb = 6;
  uint64 storage_mb = 7;
}

message AuthResponse {
  string cla_token = 1;         // Token for CLA-CKC communication
  int64 expires_at = 2;         // Unix timestamp
  repeated string permissions = 3; // Granted permissions
  SyncConfig sync_config = 4;   // Initial sync configuration
}

message RefreshRequest {
  string cla_token = 1;
}

message RevokeRequest {
  string cla_token = 1;
  string device_id = 2;
  string reason = 3;
}

message RevokeResponse {
  bool success = 1;
}

// ═══════════════════════════════════════════════════════════════════════════
// SYNC SERVICE
// ═══════════════════════════════════════════════════════════════════════════

service SyncService {
  // Get current sync status
  rpc GetSyncStatus(SyncStatusRequest) returns (SyncStatusResponse);

  // Pull changes from cloud
  rpc PullChanges(PullRequest) returns (stream PullResponse);

  // Push local changes to cloud
  rpc PushChanges(stream PushRequest) returns (PushResponse);

  // Bidirectional real-time sync
  rpc RealtimeSync(stream SyncMessage) returns (stream SyncMessage);
}

message SyncStatusRequest {
  string cla_token = 1;
}

message SyncStatusResponse {
  int64 last_sync_timestamp = 1;
  uint32 pending_upload_count = 2;
  uint32 pending_download_count = 3;
  repeated string conflict_ids = 4;
  SyncHealth health = 5;
}

enum SyncHealth {
  HEALTHY = 0;
  DEGRADED = 1;
  OFFLINE = 2;
  ERROR = 3;
}

message PullRequest {
  string cla_token = 1;
  DataType data_type = 2;
  int64 since_timestamp = 3;    // Pull changes since this time
  uint32 limit = 4;             // Max items per batch
  string cursor = 5;            // Pagination cursor
}

enum DataType {
  MEMORIES = 0;
  SESSIONS = 1;
  KNOWLEDGE_CHUNKS = 2;
  SETTINGS = 3;
  ALL = 4;
}

message PullResponse {
  repeated SyncItem items = 1;
  string next_cursor = 2;
  bool has_more = 3;
  int64 server_timestamp = 4;
}

message SyncItem {
  string id = 1;
  DataType data_type = 2;
  SyncOperation operation = 3;
  bytes data = 4;               // JSON-encoded item data
  int64 timestamp = 5;
  string checksum = 6;          // For integrity verification
}

enum SyncOperation {
  CREATE = 0;
  UPDATE = 1;
  DELETE = 2;
}

message PushRequest {
  string cla_token = 1;
  repeated SyncItem items = 2;
}

message PushResponse {
  bool success = 1;
  repeated SyncResult results = 2;
  repeated ConflictInfo conflicts = 3;
}

message SyncResult {
  string id = 1;
  bool success = 2;
  string error = 3;
  string server_id = 4;         // Server-assigned ID if different
}

message ConflictInfo {
  string id = 1;
  SyncItem local_version = 2;
  SyncItem server_version = 3;
  ConflictResolution suggested_resolution = 4;
}

enum ConflictResolution {
  USE_LOCAL = 0;
  USE_SERVER = 1;
  MERGE = 2;
  MANUAL = 3;
}

message SyncMessage {
  oneof payload {
    SyncItem item = 1;
    SyncAck ack = 2;
    SyncHeartbeat heartbeat = 3;
    SyncError error = 4;
  }
}

message SyncAck {
  string item_id = 1;
  bool success = 2;
}

message SyncHeartbeat {
  int64 timestamp = 1;
  SyncHealth health = 2;
}

message SyncError {
  string code = 1;
  string message = 2;
  bool recoverable = 3;
}

// ═══════════════════════════════════════════════════════════════════════════
// MODEL SERVICE
// ═══════════════════════════════════════════════════════════════════════════

service ModelService {
  // List available models
  rpc ListModels(ListModelsRequest) returns (ListModelsResponse);

  // Download model
  rpc DownloadModel(DownloadRequest) returns (stream DownloadChunk);

  // Check for model updates
  rpc CheckModelUpdates(ModelUpdateRequest) returns (ModelUpdateResponse);
}

message ListModelsRequest {
  string cla_token = 1;
  ModelTier tier = 2;           // Filter by tier
}

enum ModelTier {
  ALL_TIERS = 0;
  TIER_1 = 1;                   // Core models
  TIER_2 = 2;                   // Optional models
  TIER_3 = 3;                   // Power user models
}

message ListModelsResponse {
  repeated ModelInfo models = 1;
}

message ModelInfo {
  string model_id = 1;
  string name = 2;
  string description = 3;
  ModelTier tier = 4;
  uint64 size_bytes = 5;
  string version = 6;
  string checksum = 7;
  bool requires_gpu = 8;
  uint64 min_memory_mb = 9;
  repeated string supported_tasks = 10;
}

message DownloadRequest {
  string cla_token = 1;
  string model_id = 2;
}

message DownloadChunk {
  bytes data = 1;
  uint64 offset = 2;
  uint64 total_size = 3;
  bool is_last = 4;
}

message ModelUpdateRequest {
  string cla_token = 1;
  repeated InstalledModel installed = 2;
}

message InstalledModel {
  string model_id = 1;
  string version = 2;
  string checksum = 3;
}

message ModelUpdateResponse {
  repeated ModelUpdate updates = 1;
}

message ModelUpdate {
  string model_id = 1;
  string current_version = 2;
  string new_version = 3;
  uint64 update_size_bytes = 4;
  string changelog = 5;
  bool required = 6;
}

// ═══════════════════════════════════════════════════════════════════════════
// TELEMETRY SERVICE
// ═══════════════════════════════════════════════════════════════════════════

service TelemetryService {
  // Send anonymous telemetry
  rpc SendTelemetry(TelemetryBatch) returns (TelemetryResponse);
}

message TelemetryBatch {
  string cla_token = 1;
  string device_id = 2;         // Hashed device ID
  repeated TelemetryEvent events = 3;
}

message TelemetryEvent {
  string event_type = 1;
  int64 timestamp = 2;
  map<string, string> properties = 3;
  map<string, double> metrics = 4;
}

message TelemetryResponse {
  bool accepted = 1;
}

// ═══════════════════════════════════════════════════════════════════════════
// SYNC CONFIG
// ═══════════════════════════════════════════════════════════════════════════

message SyncConfig {
  uint32 sync_interval_seconds = 1;      // How often to sync (default: 60)
  uint32 batch_size = 2;                 // Items per batch (default: 50)
  bool realtime_enabled = 3;             // Use WebSocket for realtime
  repeated DataType priority_types = 4;  // Sync these first
  uint64 max_cache_size_mb = 5;          // Local cache limit
  uint32 retention_days = 6;             // How long to keep local data
}
```

### REST API Fallback

For situations where gRPC is not available (corporate firewalls, etc.):

```yaml
# openapi/cla-api.yaml
openapi: 3.0.0
info:
  title: CLA REST API
  version: 1.0.0
  description: REST fallback for CLA-CKC communication

servers:
  - url: https://api.cirkelline.com/cla/v1
    description: Production
  - url: http://localhost:7777/cla/v1
    description: Local development

paths:
  /auth/authenticate:
    post:
      summary: Authenticate CLA
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                user_token:
                  type: string
                device_id:
                  type: string
                device_info:
                  $ref: '#/components/schemas/DeviceInfo'
      responses:
        '200':
          description: Authentication successful
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AuthResponse'

  /sync/status:
    get:
      summary: Get sync status
      security:
        - BearerAuth: []
      responses:
        '200':
          description: Sync status
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SyncStatus'

  /sync/pull:
    get:
      summary: Pull changes from cloud
      security:
        - BearerAuth: []
      parameters:
        - name: data_type
          in: query
          schema:
            type: string
            enum: [memories, sessions, knowledge_chunks, settings, all]
        - name: since
          in: query
          schema:
            type: integer
            format: int64
        - name: limit
          in: query
          schema:
            type: integer
            default: 50
        - name: cursor
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Changes to pull
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PullResponse'

  /sync/push:
    post:
      summary: Push local changes to cloud
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                items:
                  type: array
                  items:
                    $ref: '#/components/schemas/SyncItem'
      responses:
        '200':
          description: Push result
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PushResponse'

  /models:
    get:
      summary: List available models
      security:
        - BearerAuth: []
      parameters:
        - name: tier
          in: query
          schema:
            type: integer
            enum: [1, 2, 3]
      responses:
        '200':
          description: Model list
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/ModelInfo'

  /models/{model_id}/download:
    get:
      summary: Download model file
      security:
        - BearerAuth: []
      parameters:
        - name: model_id
          in: path
          required: true
          schema:
            type: string
        - name: range
          in: header
          schema:
            type: string
            description: HTTP Range header for resumable downloads
      responses:
        '200':
          description: Model file
          content:
            application/octet-stream:
              schema:
                type: string
                format: binary
        '206':
          description: Partial content (range request)

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    DeviceInfo:
      type: object
      properties:
        os:
          type: string
        os_version:
          type: string
        cla_version:
          type: string
        has_gpu:
          type: boolean
        gpu_model:
          type: string
        memory_mb:
          type: integer
        storage_mb:
          type: integer

    AuthResponse:
      type: object
      properties:
        cla_token:
          type: string
        expires_at:
          type: integer
          format: int64
        permissions:
          type: array
          items:
            type: string
        sync_config:
          $ref: '#/components/schemas/SyncConfig'

    SyncStatus:
      type: object
      properties:
        last_sync_timestamp:
          type: integer
          format: int64
        pending_upload_count:
          type: integer
        pending_download_count:
          type: integer
        conflict_ids:
          type: array
          items:
            type: string
        health:
          type: string
          enum: [healthy, degraded, offline, error]

    SyncItem:
      type: object
      properties:
        id:
          type: string
        data_type:
          type: string
        operation:
          type: string
          enum: [create, update, delete]
        data:
          type: object
        timestamp:
          type: integer
          format: int64
        checksum:
          type: string

    PullResponse:
      type: object
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/SyncItem'
        next_cursor:
          type: string
        has_more:
          type: boolean
        server_timestamp:
          type: integer
          format: int64

    PushResponse:
      type: object
      properties:
        success:
          type: boolean
        results:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
              success:
                type: boolean
              error:
                type: string
        conflicts:
          type: array
          items:
            $ref: '#/components/schemas/ConflictInfo'

    ConflictInfo:
      type: object
      properties:
        id:
          type: string
        local_version:
          $ref: '#/components/schemas/SyncItem'
        server_version:
          $ref: '#/components/schemas/SyncItem'
        suggested_resolution:
          type: string
          enum: [use_local, use_server, merge, manual]

    ModelInfo:
      type: object
      properties:
        model_id:
          type: string
        name:
          type: string
        description:
          type: string
        tier:
          type: integer
        size_bytes:
          type: integer
          format: int64
        version:
          type: string
        checksum:
          type: string
        requires_gpu:
          type: boolean
        min_memory_mb:
          type: integer
        supported_tasks:
          type: array
          items:
            type: string

    SyncConfig:
      type: object
      properties:
        sync_interval_seconds:
          type: integer
        batch_size:
          type: integer
        realtime_enabled:
          type: boolean
        priority_types:
          type: array
          items:
            type: string
        max_cache_size_mb:
          type: integer
        retention_days:
          type: integer
```

---

## 4.2.3: SYNKRONISERINGSMEKANISMER

### Sync Manager Implementation

```typescript
// src/lib/sync/sync-manager.ts

import { SyncItem, SyncStatus, ConflictInfo, ConflictResolution } from './types';
import { LocalDatabase } from '../cla-api';
import { grpcClient, restClient } from './clients';

export class SyncManager {
  private syncInterval: NodeJS.Timer | null = null;
  private isOnline: boolean = true;
  private pendingQueue: SyncItem[] = [];
  private conflictResolver: ConflictResolver;
  private eventEmitter: EventEmitter;

  constructor(private config: SyncConfig) {
    this.conflictResolver = new ConflictResolver();
    this.eventEmitter = new EventEmitter();

    // Monitor network status
    window.addEventListener('online', () => this.handleOnline());
    window.addEventListener('offline', () => this.handleOffline());
  }

  async initialize(): Promise<void> {
    // Load pending items from local storage
    this.pendingQueue = await this.loadPendingQueue();

    // Start periodic sync
    if (this.config.sync_interval_seconds > 0) {
      this.startPeriodicSync();
    }

    // Connect real-time sync if enabled
    if (this.config.realtime_enabled) {
      await this.connectRealtime();
    }

    // Process any pending items
    if (this.isOnline && this.pendingQueue.length > 0) {
      await this.processPendingQueue();
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // PUBLIC API
  // ═══════════════════════════════════════════════════════════════════════

  async sync(dataTypes: DataType[] = ['all']): Promise<SyncResult> {
    if (!this.isOnline) {
      return { success: false, error: 'Offline' };
    }

    try {
      // 1. Push local changes
      const pushResult = await this.pushChanges();

      // 2. Pull remote changes
      const pullResult = await this.pullChanges(dataTypes);

      // 3. Handle conflicts
      if (pushResult.conflicts.length > 0) {
        await this.handleConflicts(pushResult.conflicts);
      }

      // 4. Update last sync timestamp
      await this.updateLastSync();

      return {
        success: true,
        pushed: pushResult.results.filter(r => r.success).length,
        pulled: pullResult.items.length,
        conflicts: pushResult.conflicts.length,
      };
    } catch (error) {
      console.error('Sync failed:', error);
      return { success: false, error: error.message };
    }
  }

  async markDirty(item: SyncItem): Promise<void> {
    // Add to pending queue
    const existingIndex = this.pendingQueue.findIndex(
      i => i.id === item.id && i.data_type === item.data_type
    );

    if (existingIndex >= 0) {
      this.pendingQueue[existingIndex] = item;
    } else {
      this.pendingQueue.push(item);
    }

    // Persist queue
    await this.savePendingQueue();

    // Trigger immediate sync if realtime
    if (this.config.realtime_enabled && this.isOnline) {
      await this.pushItem(item);
    }
  }

  async resolveConflict(
    conflictId: string,
    resolution: ConflictResolution
  ): Promise<void> {
    const conflict = await this.getConflict(conflictId);
    if (!conflict) {
      throw new Error(`Conflict ${conflictId} not found`);
    }

    const resolvedItem = await this.conflictResolver.resolve(conflict, resolution);
    await this.applyResolution(conflict, resolvedItem);
  }

  // ═══════════════════════════════════════════════════════════════════════
  // SYNC OPERATIONS
  // ═══════════════════════════════════════════════════════════════════════

  private async pushChanges(): Promise<PushResponse> {
    if (this.pendingQueue.length === 0) {
      return { success: true, results: [], conflicts: [] };
    }

    // Batch items
    const batches = this.batchItems(this.pendingQueue, this.config.batch_size);
    const allResults: SyncResult[] = [];
    const allConflicts: ConflictInfo[] = [];

    for (const batch of batches) {
      try {
        const response = await grpcClient.pushChanges(batch);

        allResults.push(...response.results);
        allConflicts.push(...response.conflicts);

        // Remove successful items from queue
        const successfulIds = response.results
          .filter(r => r.success)
          .map(r => r.id);

        this.pendingQueue = this.pendingQueue.filter(
          item => !successfulIds.includes(item.id)
        );
      } catch (error) {
        console.error('Batch push failed:', error);
        // Continue with next batch
      }
    }

    await this.savePendingQueue();

    return {
      success: allConflicts.length === 0,
      results: allResults,
      conflicts: allConflicts,
    };
  }

  private async pullChanges(dataTypes: DataType[]): Promise<PullResponse> {
    const lastSync = await this.getLastSyncTimestamp();
    const allItems: SyncItem[] = [];

    for (const dataType of dataTypes) {
      let cursor: string | undefined;
      let hasMore = true;

      while (hasMore) {
        const response = await grpcClient.pullChanges({
          data_type: dataType,
          since_timestamp: lastSync,
          limit: this.config.batch_size,
          cursor,
        });

        // Apply changes locally
        for (const item of response.items) {
          await this.applyRemoteChange(item);
        }

        allItems.push(...response.items);
        cursor = response.next_cursor;
        hasMore = response.has_more;
      }
    }

    return { items: allItems };
  }

  private async applyRemoteChange(item: SyncItem): Promise<void> {
    const localItem = await LocalDatabase.get(item.data_type, item.id);

    if (!localItem) {
      // No local version - apply directly
      if (item.operation !== 'delete') {
        await LocalDatabase.put(item.data_type, item.data);
      }
      return;
    }

    // Check for conflict
    if (localItem.is_dirty && item.timestamp > localItem.updated_at) {
      // Conflict! Local changes AND newer server version
      await this.createConflict(item, localItem);
      return;
    }

    // Apply remote change
    switch (item.operation) {
      case 'create':
      case 'update':
        await LocalDatabase.put(item.data_type, {
          ...item.data,
          is_dirty: false,
          synced_at: Date.now(),
        });
        break;
      case 'delete':
        await LocalDatabase.delete(item.data_type, item.id);
        break;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // CONFLICT RESOLUTION
  // ═══════════════════════════════════════════════════════════════════════

  private async handleConflicts(conflicts: ConflictInfo[]): Promise<void> {
    for (const conflict of conflicts) {
      const autoResolution = this.conflictResolver.suggestResolution(conflict);

      if (autoResolution !== ConflictResolution.MANUAL) {
        // Auto-resolve
        await this.resolveConflict(conflict.id, autoResolution);
      } else {
        // Store for manual resolution
        await this.storeConflict(conflict);
        this.eventEmitter.emit('conflict', conflict);
      }
    }
  }
}

export class ConflictResolver {
  suggestResolution(conflict: ConflictInfo): ConflictResolution {
    const { local_version, server_version } = conflict;

    // Memories: Always merge (both versions are valuable)
    if (local_version.data_type === 'memories') {
      return ConflictResolution.MERGE;
    }

    // Sessions: Server wins (authoritative)
    if (local_version.data_type === 'sessions') {
      return ConflictResolution.USE_SERVER;
    }

    // Settings: Local wins (user's device-specific preferences)
    if (local_version.data_type === 'settings') {
      return ConflictResolution.USE_LOCAL;
    }

    // Knowledge: Server wins (source of truth)
    if (local_version.data_type === 'knowledge_chunks') {
      return ConflictResolution.USE_SERVER;
    }

    // Default: Most recent wins
    if (local_version.timestamp > server_version.timestamp) {
      return ConflictResolution.USE_LOCAL;
    } else {
      return ConflictResolution.USE_SERVER;
    }
  }

  async resolve(
    conflict: ConflictInfo,
    resolution: ConflictResolution
  ): Promise<SyncItem> {
    switch (resolution) {
      case ConflictResolution.USE_LOCAL:
        return conflict.local_version;

      case ConflictResolution.USE_SERVER:
        return conflict.server_version;

      case ConflictResolution.MERGE:
        return this.mergeItems(conflict.local_version, conflict.server_version);

      case ConflictResolution.MANUAL:
        throw new Error('Manual resolution required');
    }
  }

  private mergeItems(local: SyncItem, server: SyncItem): SyncItem {
    // Type-specific merge logic
    if (local.data_type === 'memories') {
      return this.mergeMemories(local, server);
    }

    // Default: Deep merge with server taking precedence for conflicts
    return {
      ...local,
      data: this.deepMerge(local.data, server.data),
      timestamp: Math.max(local.timestamp, server.timestamp),
    };
  }

  private mergeMemories(local: SyncItem, server: SyncItem): SyncItem {
    // For memories, combine topics and use longest content
    const localData = local.data;
    const serverData = server.data;

    return {
      ...server,
      data: {
        ...serverData,
        topics: [...new Set([...localData.topics, ...serverData.topics])],
        memory: localData.memory.length > serverData.memory.length
          ? localData.memory
          : serverData.memory,
        updated_at: Math.max(localData.updated_at, serverData.updated_at),
      },
    };
  }

  private deepMerge(obj1: any, obj2: any): any {
    const result = { ...obj1 };

    for (const key in obj2) {
      if (obj2.hasOwnProperty(key)) {
        if (typeof obj2[key] === 'object' && !Array.isArray(obj2[key])) {
          result[key] = this.deepMerge(result[key] || {}, obj2[key]);
        } else {
          result[key] = obj2[key];
        }
      }
    }

    return result;
  }
}
```

### Real-time Sync (WebSocket)

```typescript
// src/lib/sync/realtime-sync.ts

import { SyncMessage, SyncItem, SyncAck } from './types';

export class RealtimeSync {
  private ws: WebSocket | null = null;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 1000;
  private heartbeatInterval: NodeJS.Timer | null = null;
  private pendingAcks: Map<string, (success: boolean) => void> = new Map();

  constructor(
    private url: string,
    private token: string,
    private onMessage: (item: SyncItem) => Promise<void>
  ) {}

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(`${this.url}?token=${this.token}`);

      this.ws.onopen = () => {
        console.log('Realtime sync connected');
        this.reconnectAttempts = 0;
        this.startHeartbeat();
        resolve();
      };

      this.ws.onmessage = async (event) => {
        const message: SyncMessage = JSON.parse(event.data);
        await this.handleMessage(message);
      };

      this.ws.onclose = (event) => {
        console.log('Realtime sync disconnected:', event.code);
        this.stopHeartbeat();

        if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('Realtime sync error:', error);
        reject(error);
      };
    });
  }

  async send(item: SyncItem): Promise<boolean> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return false;
    }

    return new Promise((resolve) => {
      // Set up ack handler
      this.pendingAcks.set(item.id, resolve);

      // Send message
      const message: SyncMessage = { item };
      this.ws!.send(JSON.stringify(message));

      // Timeout after 10 seconds
      setTimeout(() => {
        if (this.pendingAcks.has(item.id)) {
          this.pendingAcks.delete(item.id);
          resolve(false);
        }
      }, 10000);
    });
  }

  private async handleMessage(message: SyncMessage): Promise<void> {
    if (message.item) {
      // Incoming sync item
      await this.onMessage(message.item);

      // Send ack
      const ack: SyncAck = { item_id: message.item.id, success: true };
      this.ws?.send(JSON.stringify({ ack }));
    }

    if (message.ack) {
      // Received ack for our sent item
      const handler = this.pendingAcks.get(message.ack.item_id);
      if (handler) {
        handler(message.ack.success);
        this.pendingAcks.delete(message.ack.item_id);
      }
    }

    if (message.heartbeat) {
      // Server heartbeat - connection is alive
      console.debug('Heartbeat received:', message.heartbeat.health);
    }

    if (message.error) {
      console.error('Sync error from server:', message.error);
      if (!message.error.recoverable) {
        this.disconnect();
      }
    }
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        const heartbeat: SyncMessage = {
          heartbeat: {
            timestamp: Date.now(),
            health: 'healthy',
          },
        };
        this.ws.send(JSON.stringify(heartbeat));
      }
    }, 30000); // Every 30 seconds
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private async reconnect(): Promise<void> {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    await new Promise(resolve => setTimeout(resolve, delay));

    try {
      await this.connect();
    } catch (error) {
      console.error('Reconnect failed:', error);
    }
  }

  disconnect(): void {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }
}
```

---

## SYNC FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CLA SYNC FLOW                                       │
└─────────────────────────────────────────────────────────────────────────────┘

User creates/modifies data locally
     │
     ▼
┌─────────────────────────────────────┐
│  1. MARK AS DIRTY                  │
│                                     │
│  • Update local IndexedDB           │
│  • Set is_dirty = true             │
│  • Add to pending queue            │
│  • Generate local embedding        │
└─────────────────────────────────────┘
     │
     ├─── Realtime enabled? ─────────────────────────────────────┐
     │           │                                                │
     │           YES                                              NO
     │           │                                                │
     ▼           ▼                                                ▼
┌─────────────────────────────────────┐    ┌──────────────────────────────────┐
│  2a. IMMEDIATE PUSH (WebSocket)    │    │  2b. QUEUE FOR BATCH SYNC        │
│                                     │    │                                  │
│  • Send via WebSocket               │    │  • Add to pending queue          │
│  • Wait for server ACK              │    │  • Wait for next sync interval   │
│  • On ACK: set is_dirty = false    │    │  • Or manual sync trigger        │
└─────────────────────────────────────┘    └──────────────────────────────────┘
     │                                                │
     └────────────────────────┬───────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. SERVER PROCESSING                                                       │
│                                                                             │
│  • Validate data                                                            │
│  • Check for conflicts with other devices                                   │
│  • Store in database                                                        │
│  • Generate cloud embedding (768-dim)                                       │
│  • Broadcast to other connected CLAs                                        │
└─────────────────────────────────────────────────────────────────────────────┘
     │
     ├─── Conflict detected? ────────────────────────────────────┐
     │           │                                                │
     │           YES                                              NO
     │           │                                                │
     ▼           ▼                                                ▼
┌─────────────────────────────────────┐    ┌──────────────────────────────────┐
│  4a. CONFLICT RESOLUTION           │    │  4b. SUCCESS                     │
│                                     │    │                                  │
│  • Get conflict type                │    │  • Set is_dirty = false          │
│  • Auto-resolve if possible         │    │  • Update synced_at              │
│  • Otherwise: prompt user           │    │  • Remove from pending queue     │
│  • Apply resolution                 │    │                                  │
└─────────────────────────────────────┘    └──────────────────────────────────┘
```

---

## NÆSTE SKRIDT

FASE 4.2 er nu komplet. Dokumentet definerer:

1. **Interne API'er** med Tauri commands og TypeScript bindings
2. **gRPC Protokol** for effektiv cloud-kommunikation
3. **REST API Fallback** for firewall-begrænsede miljøer
4. **Sync Manager** med konfliktløsning og real-time support

Klar til **FASE 4.3: Implementering af CLA Core med Tauri**.

---

*Dokument oprettet: 2025-12-08*
*Forfatter: Claude (Opus 4.5)*
*Status: KOMPLET*
