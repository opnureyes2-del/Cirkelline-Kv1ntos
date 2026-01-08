// CKC Sync - Synchronization with Cirkelline Knowledge Center

use super::{SyncStatus, ResearchFinding};
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use tokio::sync::RwLock;
use std::collections::VecDeque;

/// Sync configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncConfig {
    pub ckc_url: String,
    pub api_key: Option<String>,
    pub sync_interval_seconds: u64,
    pub batch_size: usize,
    pub retry_attempts: u32,
    pub offline_queue_max: usize,
}

impl Default for SyncConfig {
    fn default() -> Self {
        Self {
            ckc_url: "http://localhost:7779".to_string(),
            api_key: None,
            sync_interval_seconds: 60,
            batch_size: 10,
            retry_attempts: 3,
            offline_queue_max: 1000,
        }
    }
}

/// Sync item for offline queue
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncItem {
    pub id: String,
    pub item_type: SyncItemType,
    pub data: serde_json::Value,
    pub created_at: DateTime<Utc>,
    pub retry_count: u32,
}

/// Types of items to sync
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum SyncItemType {
    Finding,
    Decision,
    Telemetry,
    AgentLearning,
}

/// CKC Synchronization Manager
pub struct CkcSync {
    config: RwLock<SyncConfig>,
    status: RwLock<SyncStatus>,
    offline_queue: RwLock<VecDeque<SyncItem>>,
    last_sync: RwLock<Option<DateTime<Utc>>>,
}

impl CkcSync {
    pub fn new() -> Self {
        Self {
            config: RwLock::new(SyncConfig::default()),
            status: RwLock::new(SyncStatus::Disconnected),
            offline_queue: RwLock::new(VecDeque::new()),
            last_sync: RwLock::new(None),
        }
    }

    /// Get current sync status
    pub async fn get_status(&self) -> SyncStatus {
        self.status.read().await.clone()
    }

    /// Update sync configuration
    pub async fn update_config(&self, config: SyncConfig) {
        let mut cfg = self.config.write().await;
        *cfg = config;
    }

    /// Attempt to connect to CKC
    pub async fn connect(&self) -> Result<(), SyncError> {
        log::info!("Attempting to connect to CKC...");

        let config = self.config.read().await;
        let url = format!("{}/health", config.ckc_url);
        drop(config);

        // Update status to syncing while we try
        {
            let mut status = self.status.write().await;
            *status = SyncStatus::Syncing;
        }

        // Try to connect (using reqwest in real implementation)
        // For now, simulate connection
        let connected = self.try_connect(&url).await;

        let mut status = self.status.write().await;
        if connected {
            *status = SyncStatus::Connected;
            log::info!("Connected to CKC successfully");
            Ok(())
        } else {
            *status = SyncStatus::Disconnected;
            log::warn!("Failed to connect to CKC");
            Err(SyncError::ConnectionFailed)
        }
    }

    /// Try to establish connection to CKC health endpoint
    async fn try_connect(&self, url: &str) -> bool {
        use std::time::Duration;

        let client = match reqwest::Client::builder()
            .timeout(Duration::from_secs(5))
            .build()
        {
            Ok(c) => c,
            Err(e) => {
                log::debug!("Failed to create HTTP client: {}", e);
                return false;
            }
        };

        match client.get(url).send().await {
            Ok(response) => {
                let success = response.status().is_success();
                if success {
                    log::info!("CKC health check passed: {}", url);
                } else {
                    log::warn!("CKC returned non-success status: {}", response.status());
                }
                success
            }
            Err(e) => {
                log::debug!("CKC connection failed: {}", e);
                false
            }
        }
    }

    /// Sync now - push all pending items to CKC
    pub async fn sync_now(&self) -> Result<SyncResult, SyncError> {
        log::info!("Starting sync...");

        let status = self.status.read().await.clone();
        if status == SyncStatus::Disconnected {
            // Try to connect first
            drop(status);
            self.connect().await?;
        }

        // Process offline queue
        let items_synced = self.process_offline_queue().await?;

        // Update last sync time
        {
            let mut last = self.last_sync.write().await;
            *last = Some(Utc::now());
        }

        Ok(SyncResult {
            items_synced,
            items_failed: 0,
            sync_time: Utc::now(),
        })
    }

    /// Process the offline queue
    async fn process_offline_queue(&self) -> Result<usize, SyncError> {
        let config = self.config.read().await;
        let batch_size = config.batch_size;
        drop(config);

        let mut queue = self.offline_queue.write().await;
        let mut synced = 0;

        // Process up to batch_size items
        for _ in 0..batch_size {
            if let Some(item) = queue.pop_front() {
                // In real implementation, would POST to CKC
                log::debug!("Syncing item: {} ({:?})", item.id, item.item_type);
                synced += 1;
            } else {
                break;
            }
        }

        Ok(synced)
    }

    /// Queue an item for sync (used when offline)
    pub async fn queue_for_sync(&self, item_type: SyncItemType, data: serde_json::Value) {
        let item = SyncItem {
            id: uuid::Uuid::new_v4().to_string(),
            item_type,
            data,
            created_at: Utc::now(),
            retry_count: 0,
        };

        let config = self.config.read().await;
        let max_queue = config.offline_queue_max;
        drop(config);

        let mut queue = self.offline_queue.write().await;

        // Maintain max queue size
        if queue.len() >= max_queue {
            queue.pop_front();
        }

        queue.push_back(item);
        log::debug!("Item queued for sync. Queue size: {}", queue.len());
    }

    /// Queue a finding for sync
    pub async fn queue_finding(&self, finding: &ResearchFinding) {
        let data = serde_json::to_value(finding).unwrap_or_default();
        self.queue_for_sync(SyncItemType::Finding, data).await;
    }

    /// Get offline queue size
    pub async fn get_queue_size(&self) -> usize {
        self.offline_queue.read().await.len()
    }

    /// Get last sync time
    pub async fn get_last_sync(&self) -> Option<DateTime<Utc>> {
        *self.last_sync.read().await
    }

    /// Get sync statistics
    pub async fn get_stats(&self) -> SyncStats {
        SyncStats {
            status: self.get_status().await,
            queue_size: self.get_queue_size().await,
            last_sync: self.get_last_sync().await,
        }
    }
}

impl Default for CkcSync {
    fn default() -> Self {
        Self::new()
    }
}

/// Sync errors
#[derive(Debug, thiserror::Error)]
pub enum SyncError {
    #[error("Connection failed")]
    ConnectionFailed,

    #[error("Authentication failed")]
    AuthFailed,

    #[error("Network error: {0}")]
    NetworkError(String),

    #[error("Server error: {0}")]
    ServerError(String),

    #[error("Serialization error: {0}")]
    SerializationError(String),
}

/// Sync result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncResult {
    pub items_synced: usize,
    pub items_failed: usize,
    pub sync_time: DateTime<Utc>,
}

/// Sync statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncStats {
    pub status: SyncStatus,
    pub queue_size: usize,
    pub last_sync: Option<DateTime<Utc>>,
}
