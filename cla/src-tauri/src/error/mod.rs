// Error handling module for Cirkelline Local Agent
// Provides comprehensive error types and fallback mechanisms

use serde::{Deserialize, Serialize};
use std::fmt;

/// Main error type for CLA
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ClaError {
    // Storage errors
    Storage(StorageError),

    // Network errors
    Network(NetworkError),

    // Inference errors
    Inference(InferenceError),

    // Security errors
    Security(SecurityError),

    // Resource errors
    Resource(ResourceError),

    // Sync errors
    Sync(SyncError),

    // Configuration errors
    Config(ConfigError),

    // General errors
    Internal(String),
    NotImplemented(String),
    Cancelled,
}

impl fmt::Display for ClaError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Storage(e) => write!(f, "Storage error: {}", e),
            Self::Network(e) => write!(f, "Network error: {}", e),
            Self::Inference(e) => write!(f, "Inference error: {}", e),
            Self::Security(e) => write!(f, "Security error: {}", e),
            Self::Resource(e) => write!(f, "Resource error: {}", e),
            Self::Sync(e) => write!(f, "Sync error: {}", e),
            Self::Config(e) => write!(f, "Config error: {}", e),
            Self::Internal(msg) => write!(f, "Internal error: {}", msg),
            Self::NotImplemented(feature) => write!(f, "Not implemented: {}", feature),
            Self::Cancelled => write!(f, "Operation cancelled"),
        }
    }
}

impl std::error::Error for ClaError {}

// ============ Storage Errors ============

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum StorageError {
    NotFound { key: String },
    WriteError { message: String },
    ReadError { message: String },
    CorruptedData { message: String },
    QuotaExceeded { used_mb: u64, limit_mb: u64 },
    DatabaseError { message: String },
}

impl fmt::Display for StorageError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NotFound { key } => write!(f, "Not found: {}", key),
            Self::WriteError { message } => write!(f, "Write failed: {}", message),
            Self::ReadError { message } => write!(f, "Read failed: {}", message),
            Self::CorruptedData { message } => write!(f, "Corrupted data: {}", message),
            Self::QuotaExceeded { used_mb, limit_mb } => {
                write!(f, "Storage quota exceeded: {}MB / {}MB", used_mb, limit_mb)
            }
            Self::DatabaseError { message } => write!(f, "Database error: {}", message),
        }
    }
}

// ============ Network Errors ============

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum NetworkError {
    ConnectionFailed { url: String, reason: String },
    Timeout { url: String, timeout_ms: u64 },
    Offline,
    InvalidResponse { status: u16, body: String },
    TlsError { message: String },
    DnsError { host: String },
}

impl fmt::Display for NetworkError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ConnectionFailed { url, reason } => {
                write!(f, "Connection to {} failed: {}", url, reason)
            }
            Self::Timeout { url, timeout_ms } => {
                write!(f, "Request to {} timed out after {}ms", url, timeout_ms)
            }
            Self::Offline => write!(f, "No network connection"),
            Self::InvalidResponse { status, body } => {
                write!(f, "Invalid response ({}): {}", status, body)
            }
            Self::TlsError { message } => write!(f, "TLS error: {}", message),
            Self::DnsError { host } => write!(f, "DNS lookup failed for {}", host),
        }
    }
}

// ============ Inference Errors ============

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum InferenceError {
    ModelNotLoaded { model_id: String },
    ModelNotFound { model_id: String },
    InferenceFailed { model_id: String, reason: String },
    InvalidInput { reason: String },
    OutOfMemory { required_mb: u64, available_mb: u64 },
    UnsupportedFormat { format: String },
    DownloadFailed { model_id: String, reason: String },
}

impl fmt::Display for InferenceError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ModelNotLoaded { model_id } => write!(f, "Model not loaded: {}", model_id),
            Self::ModelNotFound { model_id } => write!(f, "Model not found: {}", model_id),
            Self::InferenceFailed { model_id, reason } => {
                write!(f, "Inference with {} failed: {}", model_id, reason)
            }
            Self::InvalidInput { reason } => write!(f, "Invalid input: {}", reason),
            Self::OutOfMemory { required_mb, available_mb } => {
                write!(
                    f,
                    "Out of memory: need {}MB, have {}MB",
                    required_mb, available_mb
                )
            }
            Self::UnsupportedFormat { format } => write!(f, "Unsupported format: {}", format),
            Self::DownloadFailed { model_id, reason } => {
                write!(f, "Failed to download {}: {}", model_id, reason)
            }
        }
    }
}

// ============ Security Errors ============

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SecurityError {
    Unauthorized,
    TokenExpired,
    InvalidToken,
    PermissionDenied { action: String },
    EncryptionFailed { reason: String },
    DecryptionFailed { reason: String },
    ValidationFailed { field: String, reason: String },
}

impl fmt::Display for SecurityError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Unauthorized => write!(f, "Authentication required"),
            Self::TokenExpired => write!(f, "Session expired, please log in again"),
            Self::InvalidToken => write!(f, "Invalid authentication token"),
            Self::PermissionDenied { action } => write!(f, "Permission denied: {}", action),
            Self::EncryptionFailed { reason } => write!(f, "Encryption failed: {}", reason),
            Self::DecryptionFailed { reason } => write!(f, "Decryption failed: {}", reason),
            Self::ValidationFailed { field, reason } => {
                write!(f, "Validation failed for {}: {}", field, reason)
            }
        }
    }
}

// ============ Resource Errors ============

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ResourceError {
    CpuLimitExceeded { current: f32, limit: f32 },
    RamLimitExceeded { current: f32, limit: f32 },
    GpuNotAvailable,
    GpuLimitExceeded { current: f32, limit: f32 },
    DiskSpaceLow { available_mb: u64, required_mb: u64 },
    BatteryTooLow { current: u8, minimum: u8 },
    NotIdle { idle_seconds: u32, required_seconds: u32 },
}

impl fmt::Display for ResourceError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::CpuLimitExceeded { current, limit } => {
                write!(f, "CPU limit exceeded: {:.0}% / {:.0}%", current, limit)
            }
            Self::RamLimitExceeded { current, limit } => {
                write!(f, "RAM limit exceeded: {:.0}% / {:.0}%", current, limit)
            }
            Self::GpuNotAvailable => write!(f, "GPU not available"),
            Self::GpuLimitExceeded { current, limit } => {
                write!(f, "GPU limit exceeded: {:.0}% / {:.0}%", current, limit)
            }
            Self::DiskSpaceLow { available_mb, required_mb } => {
                write!(
                    f,
                    "Not enough disk space: {}MB available, {}MB required",
                    available_mb, required_mb
                )
            }
            Self::BatteryTooLow { current, minimum } => {
                write!(f, "Battery too low: {}% / min {}%", current, minimum)
            }
            Self::NotIdle { idle_seconds, required_seconds } => {
                write!(
                    f,
                    "System not idle: {}s / {}s required",
                    idle_seconds, required_seconds
                )
            }
        }
    }
}

// ============ Sync Errors ============

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SyncError {
    ConflictDetected { entity_id: String, entity_type: String },
    ServerUnreachable { endpoint: String },
    VersionMismatch { local: u64, remote: u64 },
    MergeConflict { message: String },
    QuotaExceeded { message: String },
}

impl fmt::Display for SyncError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ConflictDetected { entity_id, entity_type } => {
                write!(f, "Sync conflict: {} {}", entity_type, entity_id)
            }
            Self::ServerUnreachable { endpoint } => {
                write!(f, "Server unreachable: {}", endpoint)
            }
            Self::VersionMismatch { local, remote } => {
                write!(f, "Version mismatch: local={}, remote={}", local, remote)
            }
            Self::MergeConflict { message } => write!(f, "Merge conflict: {}", message),
            Self::QuotaExceeded { message } => write!(f, "Cloud quota exceeded: {}", message),
        }
    }
}

// ============ Config Errors ============

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ConfigError {
    InvalidValue { key: String, value: String, reason: String },
    MissingRequired { key: String },
    ParseError { message: String },
    FileError { path: String, reason: String },
}

impl fmt::Display for ConfigError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidValue { key, value, reason } => {
                write!(f, "Invalid config {}: '{}' - {}", key, value, reason)
            }
            Self::MissingRequired { key } => write!(f, "Missing required config: {}", key),
            Self::ParseError { message } => write!(f, "Config parse error: {}", message),
            Self::FileError { path, reason } => {
                write!(f, "Config file error at {}: {}", path, reason)
            }
        }
    }
}

// ============ Error Recovery ============

/// Recovery action for errors
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RecoveryAction {
    /// Retry the operation
    Retry { delay_ms: u64, max_attempts: u32 },
    /// Use cached/fallback data
    UseFallback { fallback_type: String },
    /// Skip this operation
    Skip,
    /// Require user intervention
    RequireUserAction { message: String },
    /// No recovery possible
    Fatal,
}

impl ClaError {
    /// Get suggested recovery action
    pub fn recovery_action(&self) -> RecoveryAction {
        match self {
            // Network errors - retry with backoff
            Self::Network(NetworkError::ConnectionFailed { .. }) => RecoveryAction::Retry {
                delay_ms: 5000,
                max_attempts: 3,
            },
            Self::Network(NetworkError::Timeout { .. }) => RecoveryAction::Retry {
                delay_ms: 10000,
                max_attempts: 2,
            },
            Self::Network(NetworkError::Offline) => RecoveryAction::UseFallback {
                fallback_type: "offline_mode".to_string(),
            },

            // Storage errors
            Self::Storage(StorageError::QuotaExceeded { .. }) => RecoveryAction::RequireUserAction {
                message: "Ryd noget lokal data for at frigøre plads".to_string(),
            },
            Self::Storage(StorageError::CorruptedData { .. }) => RecoveryAction::UseFallback {
                fallback_type: "cloud_sync".to_string(),
            },

            // Resource errors - wait and retry
            Self::Resource(ResourceError::NotIdle { .. }) => RecoveryAction::Retry {
                delay_ms: 30000,
                max_attempts: 10,
            },
            Self::Resource(ResourceError::CpuLimitExceeded { .. }) => RecoveryAction::Retry {
                delay_ms: 10000,
                max_attempts: 5,
            },
            Self::Resource(ResourceError::BatteryTooLow { .. }) => RecoveryAction::Skip,

            // Security errors - require user action
            Self::Security(SecurityError::TokenExpired) => RecoveryAction::RequireUserAction {
                message: "Log venligst ind igen".to_string(),
            },
            Self::Security(SecurityError::Unauthorized) => RecoveryAction::RequireUserAction {
                message: "Autentificering påkrævet".to_string(),
            },

            // Inference errors
            Self::Inference(InferenceError::ModelNotLoaded { .. }) => RecoveryAction::UseFallback {
                fallback_type: "cloud_inference".to_string(),
            },
            Self::Inference(InferenceError::OutOfMemory { .. }) => RecoveryAction::Skip,

            // Sync conflicts - require user action
            Self::Sync(SyncError::ConflictDetected { .. }) => RecoveryAction::RequireUserAction {
                message: "Løs sync-konflikt manuelt".to_string(),
            },

            // Default
            Self::Cancelled => RecoveryAction::Skip,
            _ => RecoveryAction::Fatal,
        }
    }

    /// Check if error is recoverable
    pub fn is_recoverable(&self) -> bool {
        !matches!(self.recovery_action(), RecoveryAction::Fatal)
    }

    /// Check if error should be retried
    pub fn should_retry(&self) -> bool {
        matches!(self.recovery_action(), RecoveryAction::Retry { .. })
    }

    /// Get user-friendly message
    pub fn user_message(&self) -> String {
        match self {
            Self::Network(NetworkError::Offline) => {
                "Ingen internetforbindelse. CLA arbejder i offline-tilstand.".to_string()
            }
            Self::Network(NetworkError::Timeout { .. }) => {
                "Serveren svarer langsomt. Prøver igen...".to_string()
            }
            Self::Resource(ResourceError::NotIdle { .. }) => {
                "Venter på at computeren bliver inaktiv...".to_string()
            }
            Self::Resource(ResourceError::BatteryTooLow { current, minimum }) => {
                format!("Batteri for lavt ({}%). Kræver mindst {}%.", current, minimum)
            }
            Self::Security(SecurityError::TokenExpired) => {
                "Din session er udløbet. Log venligst ind igen.".to_string()
            }
            Self::Inference(InferenceError::ModelNotLoaded { model_id }) => {
                format!("Model '{}' ikke indlæst. Download den fra Modeller-siden.", model_id)
            }
            Self::Storage(StorageError::QuotaExceeded { used_mb, limit_mb }) => {
                format!(
                    "Lokal lagring fuld ({}MB / {}MB). Ryd data eller øg grænsen.",
                    used_mb, limit_mb
                )
            }
            _ => self.to_string(),
        }
    }
}

/// Result type alias
pub type ClaResult<T> = Result<T, ClaError>;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_display() {
        let error = ClaError::Network(NetworkError::Offline);
        assert!(error.to_string().contains("No network"));
    }

    #[test]
    fn test_recovery_action() {
        let error = ClaError::Network(NetworkError::Offline);
        assert!(matches!(
            error.recovery_action(),
            RecoveryAction::UseFallback { .. }
        ));
    }

    #[test]
    fn test_user_message() {
        let error = ClaError::Resource(ResourceError::BatteryTooLow {
            current: 10,
            minimum: 20,
        });
        let msg = error.user_message();
        assert!(msg.contains("10%"));
        assert!(msg.contains("20%"));
    }
}
