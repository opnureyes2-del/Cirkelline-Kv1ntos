// Commander Tauri Commands - Expose Commander Unit to frontend
// Connected to real CommanderUnit implementation

use crate::commander::{
    CommanderConfig, CommanderStatus, CommanderUnit, ResearchFinding, TaskPriority,
    task_scheduler::QueueStatus,
    sync::SyncStats,
};
use tauri::State;
use std::sync::Arc;
use tokio::sync::{RwLock, mpsc};

/// Commander state (managed by Tauri)
/// Holds the actual CommanderUnit instance
pub struct CommanderState {
    /// The actual Commander Unit
    pub unit: Arc<RwLock<CommanderUnit>>,
    /// Receiver for findings (for future event streaming)
    pub findings_rx: Arc<RwLock<mpsc::Receiver<ResearchFinding>>>,
}

impl CommanderState {
    /// Create a new CommanderState with a configured CommanderUnit
    pub fn new(config: CommanderConfig) -> Self {
        let (findings_tx, findings_rx) = mpsc::channel::<ResearchFinding>(100);
        let unit = CommanderUnit::new(config, findings_tx);

        Self {
            unit: Arc::new(RwLock::new(unit)),
            findings_rx: Arc::new(RwLock::new(findings_rx)),
        }
    }
}

impl Default for CommanderState {
    fn default() -> Self {
        Self::new(CommanderConfig::default())
    }
}

/// Get Commander status
#[tauri::command]
pub async fn get_commander_status(
    state: State<'_, CommanderState>,
) -> Result<CommanderStatus, String> {
    let unit = state.unit.read().await;
    Ok(unit.get_status().await)
}

/// Get Commander configuration
#[tauri::command]
pub async fn get_commander_config(
    state: State<'_, CommanderState>,
) -> Result<CommanderConfig, String> {
    let unit = state.unit.read().await;
    Ok(unit.get_config().await)
}

/// Update Commander configuration
#[tauri::command]
pub async fn update_commander_config(
    state: State<'_, CommanderState>,
    new_config: CommanderConfig,
) -> Result<(), String> {
    let unit = state.unit.read().await;
    unit.update_config(new_config).await;
    log::info!("Commander config updated via API");
    Ok(())
}

/// Start Commander Unit
#[tauri::command]
pub async fn start_commander(
    state: State<'_, CommanderState>,
) -> Result<(), String> {
    let mut unit = state.unit.write().await;

    // Check if already running
    let status = unit.get_status().await;
    if status.is_running {
        return Err("Commander is already running".to_string());
    }

    unit.start().await
        .map_err(|e| format!("Failed to start Commander: {}", e))?;

    log::info!("Commander Unit started via API");
    Ok(())
}

/// Stop Commander Unit
#[tauri::command]
pub async fn stop_commander(
    state: State<'_, CommanderState>,
) -> Result<(), String> {
    let mut unit = state.unit.write().await;

    // Check if already stopped
    let status = unit.get_status().await;
    if !status.is_running {
        return Err("Commander is not running".to_string());
    }

    unit.stop().await
        .map_err(|e| format!("Failed to stop Commander: {}", e))?;

    log::info!("Commander Unit stopped via API");
    Ok(())
}

/// Add a research task
#[tauri::command]
pub async fn add_research_task(
    state: State<'_, CommanderState>,
    topic: String,
    priority: String,
) -> Result<String, String> {
    let priority = match priority.to_lowercase().as_str() {
        "critical" => TaskPriority::Critical,
        "high" => TaskPriority::High,
        "normal" => TaskPriority::Normal,
        "low" => TaskPriority::Low,
        "background" => TaskPriority::Background,
        _ => TaskPriority::Normal,
    };

    let unit = state.unit.read().await;
    unit.add_research_task(topic.clone(), priority).await;

    // Generate task ID for tracking (the actual task has its own internal ID)
    let task_id = uuid::Uuid::new_v4().to_string();
    log::info!("Research task added via API: {} with priority {:?}", topic, priority);

    Ok(task_id)
}

/// Get research task queue status
#[tauri::command]
pub async fn get_task_queue_status(
    state: State<'_, CommanderState>,
) -> Result<QueueStatus, String> {
    let unit = state.unit.read().await;
    Ok(unit.get_queue_status().await)
}

/// Get recent findings
#[tauri::command]
pub async fn get_recent_findings(
    state: State<'_, CommanderState>,
    limit: Option<usize>,
) -> Result<Vec<ResearchFinding>, String> {
    let limit = limit.unwrap_or(10);
    let unit = state.unit.read().await;
    let findings = unit.get_recent_findings(limit).await;
    log::debug!("Retrieved {} recent findings via API", findings.len());
    Ok(findings)
}

/// Force sync with CKC
#[tauri::command]
pub async fn force_commander_sync(
    state: State<'_, CommanderState>,
) -> Result<(), String> {
    let unit = state.unit.read().await;
    unit.force_sync().await
        .map_err(|e| format!("Sync failed: {}", e))?;

    log::info!("Commander sync forced via API");
    Ok(())
}

/// Get sync statistics
#[tauri::command]
pub async fn get_sync_stats(
    state: State<'_, CommanderState>,
) -> Result<SyncStats, String> {
    let unit = state.unit.read().await;
    Ok(unit.get_sync_stats().await)
}

/// Set Commander autonomy level
#[tauri::command]
pub async fn set_autonomy_level(
    state: State<'_, CommanderState>,
    level: String,
) -> Result<(), String> {
    use crate::commander::AutonomyLevel;

    let autonomy_level = match level.to_lowercase().as_str() {
        "supervised" => AutonomyLevel::Supervised,
        "assisted" => AutonomyLevel::Assisted,
        "autonomous" => AutonomyLevel::Autonomous,
        "full_autonomy" | "fullautonomy" => AutonomyLevel::FullAutonomy,
        _ => return Err(format!("Invalid autonomy level: {}", level)),
    };

    // Get current config, update autonomy level, and save
    let unit = state.unit.read().await;
    let mut config = unit.get_config().await;
    config.autonomy_level = autonomy_level.clone();
    unit.update_config(config).await;

    log::info!("Autonomy level set to: {:?} via API", autonomy_level);
    Ok(())
}
