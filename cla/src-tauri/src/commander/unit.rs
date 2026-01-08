// Commander Unit - Core autonomous operation logic

use super::{
    CommanderConfig, CommanderStatus, ResearchFinding, SyncStatus,
    DecisionEngine, TaskScheduler, CkcSync, Signal, Action,
};
use std::sync::Arc;
use tokio::sync::{RwLock, mpsc};
use chrono::Utc;

/// The Commander Unit - autonomous research and decision-making
pub struct CommanderUnit {
    config: Arc<RwLock<CommanderConfig>>,
    status: Arc<RwLock<CommanderStatus>>,
    decision_engine: Arc<DecisionEngine>,
    task_scheduler: Arc<TaskScheduler>,
    ckc_sync: Arc<CkcSync>,
    findings_tx: mpsc::Sender<ResearchFinding>,
    shutdown_tx: Option<mpsc::Sender<()>>,
}

impl CommanderUnit {
    /// Create a new Commander Unit
    pub fn new(
        config: CommanderConfig,
        findings_tx: mpsc::Sender<ResearchFinding>,
    ) -> Self {
        Self {
            config: Arc::new(RwLock::new(config)),
            status: Arc::new(RwLock::new(CommanderStatus::default())),
            decision_engine: Arc::new(DecisionEngine::new()),
            task_scheduler: Arc::new(TaskScheduler::new()),
            ckc_sync: Arc::new(CkcSync::new()),
            findings_tx,
            shutdown_tx: None,
        }
    }

    /// Start the Commander Unit's autonomous operation
    pub async fn start(&mut self) -> Result<(), CommanderError> {
        log::info!("Starting Commander Unit...");

        let config = self.config.read().await;
        if !config.enabled {
            log::warn!("Commander Unit is disabled in config");
            return Ok(());
        }
        drop(config);

        // Update status
        {
            let mut status = self.status.write().await;
            status.is_running = true;
        }

        // Create shutdown channel
        let (shutdown_tx, mut shutdown_rx) = mpsc::channel::<()>(1);
        self.shutdown_tx = Some(shutdown_tx);

        // Spawn the main loop
        let status = self.status.clone();
        let config = self.config.clone();
        let decision_engine = self.decision_engine.clone();
        let task_scheduler = self.task_scheduler.clone();
        let ckc_sync = self.ckc_sync.clone();
        let findings_tx = self.findings_tx.clone();

        tokio::spawn(async move {
            let start_time = Utc::now();

            loop {
                tokio::select! {
                    _ = shutdown_rx.recv() => {
                        log::info!("Commander Unit shutting down...");
                        break;
                    }
                    _ = tokio::time::sleep(tokio::time::Duration::from_secs(60)) => {
                        // Main operation loop
                        let cfg = config.read().await;
                        let scan_interval = cfg.scan_interval_minutes as u64 * 60;
                        drop(cfg);

                        // Update uptime
                        {
                            let mut s = status.write().await;
                            s.uptime_seconds = (Utc::now() - start_time).num_seconds() as u64;
                        }

                        // Process pending tasks
                        if let Some(task) = task_scheduler.get_next_task().await {
                            log::debug!("Processing task: {:?}", task);

                            // Execute task and get signal
                            let signal = task_scheduler.execute_task(&task).await;

                            // Make decision based on signal
                            if let Some(sig) = signal {
                                let decision = decision_engine.process_signal(sig).await;

                                // Update status
                                {
                                    let mut s = status.write().await;
                                    s.last_decision_at = Some(Utc::now());
                                    s.tasks_completed += 1;
                                }

                                // Handle decision action
                                match decision.action {
                                    Action::DeepAnalyze => {
                                        log::info!("Deep analysis triggered");
                                    }
                                    Action::QueueForReview => {
                                        log::info!("Queued for human review");
                                    }
                                    Action::ImmediateAlert => {
                                        log::warn!("Immediate alert: {}", decision.rationale);
                                    }
                                    Action::Archive => {
                                        log::debug!("Archived finding");
                                    }
                                    _ => {}
                                }
                            }
                        }

                        // Sync with CKC if connected
                        let sync_status = ckc_sync.get_status().await;
                        {
                            let mut s = status.write().await;
                            s.sync_status = sync_status;
                        }
                    }
                }
            }
        });

        log::info!("Commander Unit started successfully");
        Ok(())
    }

    /// Stop the Commander Unit
    pub async fn stop(&mut self) -> Result<(), CommanderError> {
        log::info!("Stopping Commander Unit...");

        if let Some(tx) = self.shutdown_tx.take() {
            let _ = tx.send(()).await;
        }

        {
            let mut status = self.status.write().await;
            status.is_running = false;
        }

        Ok(())
    }

    /// Get current status
    pub async fn get_status(&self) -> CommanderStatus {
        self.status.read().await.clone()
    }

    /// Update configuration
    pub async fn update_config(&self, new_config: CommanderConfig) {
        let mut config = self.config.write().await;
        *config = new_config;
    }

    /// Add a research task manually
    pub async fn add_research_task(&self, topic: String, priority: super::TaskPriority) {
        let task = super::ResearchTask::new(topic, priority);
        self.task_scheduler.add_task(task).await;

        let mut status = self.status.write().await;
        status.tasks_pending += 1;
    }

    /// Get recent findings
    pub async fn get_recent_findings(&self, limit: usize) -> Vec<ResearchFinding> {
        self.task_scheduler.get_recent_findings(limit).await
    }

    /// Force sync with CKC
    pub async fn force_sync(&self) -> Result<(), CommanderError> {
        self.ckc_sync.sync_now().await
            .map(|_| ())
            .map_err(|e| CommanderError::SyncError(e.to_string()))
    }

    /// Get current configuration
    pub async fn get_config(&self) -> CommanderConfig {
        self.config.read().await.clone()
    }

    /// Get task queue status
    pub async fn get_queue_status(&self) -> super::task_scheduler::QueueStatus {
        self.task_scheduler.get_queue_status().await
    }

    /// Get sync statistics
    pub async fn get_sync_stats(&self) -> super::sync::SyncStats {
        self.ckc_sync.get_stats().await
    }
}

/// Commander Unit errors
#[derive(Debug, thiserror::Error)]
pub enum CommanderError {
    #[error("Commander is not running")]
    NotRunning,

    #[error("Configuration error: {0}")]
    ConfigError(String),

    #[error("Sync error: {0}")]
    SyncError(String),

    #[error("Task error: {0}")]
    TaskError(String),
}
