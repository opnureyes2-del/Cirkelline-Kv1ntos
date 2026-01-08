// Data models for Cirkelline Local Agent

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;

/// User settings for CLA
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Settings {
    // Resource limits
    pub max_cpu_percent: u8,
    pub max_ram_percent: u8,
    pub max_gpu_percent: u8,
    pub max_disk_mb: u32,

    // Behavior
    pub idle_only: bool,
    pub idle_threshold_seconds: u32,
    pub paused: bool,
    pub auto_start: bool,
    pub run_on_battery: bool,
    pub min_battery_percent: u8,

    // Sync settings
    pub sync_interval_minutes: u32,
    pub sync_on_startup: bool,
    pub offline_mode: bool,

    // Model settings
    pub enable_transcription: bool,
    pub enable_ocr: bool,
    pub enable_embeddings: bool,
    pub download_tier2_models: bool,
    pub download_tier3_models: bool,

    // Connection
    pub ckc_endpoint: Option<String>,
    pub api_key: Option<String>,

    // Telemetry
    pub telemetry_enabled: bool,
    pub telemetry_consent_date: Option<DateTime<Utc>>,
}

impl Default for Settings {
    fn default() -> Self {
        Self {
            // Conservative defaults
            max_cpu_percent: 30,
            max_ram_percent: 20,
            max_gpu_percent: 30,
            max_disk_mb: 2000, // 2GB

            idle_only: true,
            idle_threshold_seconds: 120, // 2 minutes
            paused: false,
            auto_start: false,
            run_on_battery: false,
            min_battery_percent: 20,

            sync_interval_minutes: 15,
            sync_on_startup: true,
            offline_mode: false,

            enable_transcription: true,
            enable_ocr: true,
            enable_embeddings: true,
            download_tier2_models: false,
            download_tier3_models: false,

            ckc_endpoint: Some("https://ckc.cirkelline.com".to_string()),
            api_key: None,

            telemetry_enabled: false, // Opt-in by default
            telemetry_consent_date: None,
        }
    }
}

/// Current sync status
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct SyncStatus {
    pub is_syncing: bool,
    pub last_sync: Option<DateTime<Utc>>,
    pub last_sync_result: Option<SyncResult>,
    pub pending_uploads: u32,
    pub pending_downloads: u32,
    pub conflicts: Vec<SyncConflict>,
    pub bytes_uploaded: u64,
    pub bytes_downloaded: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SyncResult {
    Success,
    PartialSuccess { errors: Vec<String> },
    Failed { error: String },
}

/// A sync conflict that needs resolution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncConflict {
    pub id: Uuid,
    pub data_type: DataType,
    pub local_version: DateTime<Utc>,
    pub remote_version: DateTime<Utc>,
    pub description: String,
    pub resolution_options: Vec<ConflictResolution>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ConflictResolution {
    KeepLocal,
    KeepRemote,
    Merge,
    Manual,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DataType {
    Memory,
    Session,
    Setting,
    Knowledge,
}

/// System metrics snapshot
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemMetrics {
    // CPU
    pub cpu_usage_percent: f32,
    pub cpu_count: u32,

    // Memory
    pub ram_used_mb: u64,
    pub ram_total_mb: u64,
    pub ram_usage_percent: f32,

    // GPU (optional)
    pub gpu_available: bool,
    pub gpu_usage_percent: Option<f32>,
    pub gpu_memory_used_mb: Option<u64>,
    pub gpu_memory_total_mb: Option<u64>,

    // Disk
    pub disk_used_mb: u64,
    pub disk_available_mb: u64,

    // Power
    pub on_battery: bool,
    pub battery_percent: Option<u8>,

    // Idle
    pub idle_seconds: u32,
    pub is_idle: bool,

    // Timestamp
    pub timestamp: DateTime<Utc>,
}

/// Result of checking if task can execute
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CanExecuteResult {
    pub can_execute: bool,
    pub reason: Option<String>,
    pub estimated_wait_seconds: Option<u32>,
}

/// Local memory entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LocalMemory {
    pub id: Uuid,
    pub content: String,
    pub memory_type: String,
    pub topics: Vec<String>,
    pub embedding_local: Option<Vec<f32>>,  // 384-dim MiniLM
    pub importance: f32,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub synced_at: Option<DateTime<Utc>>,
    pub cloud_id: Option<String>,
    pub pending_sync: bool,
}

/// Local session data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LocalSession {
    pub id: Uuid,
    pub session_type: String,
    pub context: serde_json::Value,
    pub messages: Vec<LocalMessage>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub synced_at: Option<DateTime<Utc>>,
    pub cloud_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LocalMessage {
    pub role: String,
    pub content: String,
    pub timestamp: DateTime<Utc>,
}

/// Preloaded knowledge chunk
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LocalKnowledgeChunk {
    pub id: Uuid,
    pub source_id: String,
    pub content: String,
    pub embedding_local: Vec<f32>,
    pub metadata: serde_json::Value,
    pub priority: u8,
    pub expires_at: Option<DateTime<Utc>>,
}

/// Pending task in queue
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PendingTask {
    pub id: Uuid,
    pub task_type: TaskType,
    pub priority: u8,
    pub payload: serde_json::Value,
    pub created_at: DateTime<Utc>,
    pub retry_count: u8,
    pub max_retries: u8,
    pub status: TaskStatus,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TaskType {
    GenerateEmbedding,
    TranscribeAudio,
    ExtractText,
    SyncMemory,
    PreloadKnowledge,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TaskStatus {
    Queued,
    Running,
    Completed,
    Failed { error: String },
    Cancelled,
}

/// AI model information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelInfo {
    pub id: String,
    pub name: String,
    pub size_mb: u64,
    pub tier: u8,
    pub capabilities: Vec<String>,
    pub downloaded: bool,
    pub download_progress: Option<f32>,
    pub version: String,
}

/// Embedding result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EmbeddingResult {
    pub embedding: Vec<f32>,
    pub model_used: String,
    pub processing_time_ms: u64,
}

/// Transcription result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TranscriptionResult {
    pub text: String,
    pub language: Option<String>,
    pub confidence: f32,
    pub segments: Vec<TranscriptionSegment>,
    pub processing_time_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TranscriptionSegment {
    pub start_ms: u64,
    pub end_ms: u64,
    pub text: String,
    pub confidence: f32,
}

/// OCR/Text extraction result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TextExtractionResult {
    pub text: String,
    pub confidence: f32,
    pub regions: Vec<TextRegion>,
    pub processing_time_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TextRegion {
    pub text: String,
    pub bbox: BoundingBox,
    pub confidence: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BoundingBox {
    pub x: f32,
    pub y: f32,
    pub width: f32,
    pub height: f32,
}

/// Connection status
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConnectionStatus {
    pub connected: bool,
    pub endpoint: String,
    pub latency_ms: Option<u32>,
    pub last_check: DateTime<Utc>,
    pub error: Option<String>,
}

/// Telemetry statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TelemetryStats {
    pub session_id: String,
    pub app_starts: u64,
    pub inference_count: u64,
    pub sync_count: u64,
    pub error_count: u64,
    pub uptime_hours: f64,
    pub last_report: Option<DateTime<Utc>>,
}

impl Default for TelemetryStats {
    fn default() -> Self {
        Self {
            session_id: uuid::Uuid::new_v4().to_string(),
            app_starts: 0,
            inference_count: 0,
            sync_count: 0,
            error_count: 0,
            uptime_hours: 0.0,
            last_report: None,
        }
    }
}
