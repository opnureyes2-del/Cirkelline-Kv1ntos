// Commander Unit Module - FASE 6
// Autonomous research and decision-making system

pub mod unit;
pub mod decision_engine;
pub mod task_scheduler;
pub mod sync;

pub use unit::CommanderUnit;
pub use decision_engine::{DecisionEngine, Decision, Action, Signal};
pub use task_scheduler::{TaskScheduler, ResearchTask, TaskPriority};
pub use sync::CkcSync;

use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

/// Commander Unit Status
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommanderStatus {
    pub is_running: bool,
    pub uptime_seconds: u64,
    pub tasks_completed: u64,
    pub tasks_pending: u64,
    pub last_decision_at: Option<DateTime<Utc>>,
    pub sync_status: SyncStatus,
    pub autonomy_level: AutonomyLevel,
}

impl Default for CommanderStatus {
    fn default() -> Self {
        Self {
            is_running: false,
            uptime_seconds: 0,
            tasks_completed: 0,
            tasks_pending: 0,
            last_decision_at: None,
            sync_status: SyncStatus::Disconnected,
            autonomy_level: AutonomyLevel::Supervised,
        }
    }
}

/// Sync status with CKC backend
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum SyncStatus {
    Connected,
    Syncing,
    Disconnected,
    Error(String),
}

/// Autonomy level for Commander decisions
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum AutonomyLevel {
    /// All decisions require user approval
    Supervised,
    /// Low-risk decisions are automatic, high-risk require approval
    Assisted,
    /// Most decisions automatic, only critical require approval
    Autonomous,
    /// Full autonomy (24h+ operation)
    FullAutonomy,
}

/// Research finding from Commander
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResearchFinding {
    pub id: String,
    pub source: ResearchSource,
    pub title: String,
    pub summary: String,
    pub relevance_score: f32,
    pub discovered_at: DateTime<Utc>,
    pub tags: Vec<String>,
    pub url: Option<String>,
    pub metadata: serde_json::Value,
}

/// Research source type
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ResearchSource {
    GitHub,
    ArXiv,
    Twitter,
    Farcaster,
    LensProtocol,
    CustomFeed(String),
}

/// Commander configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommanderConfig {
    pub enabled: bool,
    pub autonomy_level: AutonomyLevel,
    pub scan_interval_minutes: u32,
    pub max_concurrent_tasks: u32,
    pub relevance_threshold: f32,
    pub sources: Vec<ResearchSource>,
    pub alert_on_critical: bool,
    pub sync_to_cosmic_library: bool,
    pub offline_mode_enabled: bool,
}

impl Default for CommanderConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            autonomy_level: AutonomyLevel::Supervised,
            scan_interval_minutes: 30,
            max_concurrent_tasks: 5,
            relevance_threshold: 0.6,
            sources: vec![ResearchSource::GitHub, ResearchSource::ArXiv],
            alert_on_critical: true,
            sync_to_cosmic_library: true,
            offline_mode_enabled: true,
        }
    }
}
