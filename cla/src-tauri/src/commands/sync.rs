// Sync commands for Cirkelline Local Agent

use tauri::State;
use crate::AppState;
use crate::models::{SyncStatus, SyncConflict, ConflictResolution, SyncResult};
use chrono::Utc;
use uuid::Uuid;

/// Get current sync status
#[tauri::command]
pub async fn get_sync_status(state: State<'_, AppState>) -> Result<SyncStatus, String> {
    let status = state.sync_status.read().await;
    Ok(status.clone())
}

/// Trigger immediate sync
#[tauri::command]
pub async fn sync_now(state: State<'_, AppState>) -> Result<SyncResult, String> {
    let settings = state.settings.read().await;

    // Check if offline mode
    if settings.offline_mode {
        return Ok(SyncResult::Failed {
            error: "Offline-tilstand er aktiveret".to_string(),
        });
    }

    // Update status to syncing
    {
        let mut status = state.sync_status.write().await;
        status.is_syncing = true;
    }

    // Perform sync (placeholder for actual implementation)
    let endpoint = settings.ckc_endpoint.as_deref()
        .unwrap_or("https://ckc.cirkelline.com");
    let result = perform_sync(endpoint, settings.api_key.as_deref()).await;

    // Update status
    {
        let mut status = state.sync_status.write().await;
        status.is_syncing = false;
        status.last_sync = Some(Utc::now());
        status.last_sync_result = Some(result.clone());
    }

    Ok(result)
}

/// Get pending changes not yet synced
#[tauri::command]
pub async fn get_pending_changes(
    state: State<'_, AppState>,
) -> Result<PendingChanges, String> {
    let status = state.sync_status.read().await;

    Ok(PendingChanges {
        uploads: status.pending_uploads,
        downloads: status.pending_downloads,
        conflicts: status.conflicts.len() as u32,
    })
}

/// Resolve a sync conflict
#[tauri::command]
pub async fn resolve_conflict(
    state: State<'_, AppState>,
    conflict_id: Uuid,
    resolution: ConflictResolution,
) -> Result<(), String> {
    let mut status = state.sync_status.write().await;

    // Find and remove the conflict
    let conflict_idx = status
        .conflicts
        .iter()
        .position(|c| c.id == conflict_id)
        .ok_or("Konflikt ikke fundet")?;

    let conflict = status.conflicts.remove(conflict_idx);

    // Apply resolution (placeholder)
    apply_conflict_resolution(&conflict, &resolution).await?;

    log::info!(
        "Resolved conflict {} with {:?}",
        conflict_id,
        resolution
    );

    Ok(())
}

/// Perform the actual sync operation
async fn perform_sync(endpoint: &str, api_key: Option<&str>) -> SyncResult {
    // Check connectivity
    let client = reqwest::Client::new();
    let health_url = format!("{}/health", endpoint);

    match client.get(&health_url).send().await {
        Ok(response) if response.status().is_success() => {
            // Connection OK, proceed with sync

            // 1. Upload local changes
            // TODO: Implement actual upload logic

            // 2. Download remote changes
            // TODO: Implement actual download logic

            // 3. Handle conflicts
            // TODO: Implement conflict detection

            SyncResult::Success
        }
        Ok(response) => SyncResult::Failed {
            error: format!("Server svarede med status: {}", response.status()),
        },
        Err(e) => SyncResult::Failed {
            error: format!("Kunne ikke forbinde til server: {}", e),
        },
    }
}

/// Apply a conflict resolution
async fn apply_conflict_resolution(
    conflict: &SyncConflict,
    resolution: &ConflictResolution,
) -> Result<(), String> {
    match resolution {
        ConflictResolution::KeepLocal => {
            // Mark local version as authoritative, queue for upload
            log::info!("Keeping local version for {:?}", conflict.data_type);
        }
        ConflictResolution::KeepRemote => {
            // Download and overwrite local version
            log::info!("Keeping remote version for {:?}", conflict.data_type);
        }
        ConflictResolution::Merge => {
            // Attempt automatic merge
            log::info!("Merging versions for {:?}", conflict.data_type);
        }
        ConflictResolution::Manual => {
            // User will handle manually
            log::info!("Manual resolution requested for {:?}", conflict.data_type);
        }
    }
    Ok(())
}

#[derive(serde::Serialize, serde::Deserialize)]
pub struct PendingChanges {
    pub uploads: u32,
    pub downloads: u32,
    pub conflicts: u32,
}
