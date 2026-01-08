// Task Scheduler - Research task queue management

use super::{ResearchFinding, ResearchSource, Signal};
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use std::collections::VecDeque;
use tokio::sync::RwLock;

/// Task priority levels
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub enum TaskPriority {
    Critical = 4,
    High = 3,
    Normal = 2,
    Low = 1,
    Background = 0,
}

/// Task status
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum TaskStatus {
    Pending,
    Running,
    Completed,
    Failed(String),
    Cancelled,
}

/// A research task
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResearchTask {
    pub id: String,
    pub topic: String,
    pub priority: TaskPriority,
    pub status: TaskStatus,
    pub source: Option<ResearchSource>,
    pub created_at: DateTime<Utc>,
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub retry_count: u32,
    pub max_retries: u32,
}

impl ResearchTask {
    pub fn new(topic: String, priority: TaskPriority) -> Self {
        Self {
            id: uuid::Uuid::new_v4().to_string(),
            topic,
            priority,
            status: TaskStatus::Pending,
            source: None,
            created_at: Utc::now(),
            started_at: None,
            completed_at: None,
            retry_count: 0,
            max_retries: 3,
        }
    }

    pub fn with_source(mut self, source: ResearchSource) -> Self {
        self.source = Some(source);
        self
    }
}

/// The Task Scheduler
pub struct TaskScheduler {
    queue: RwLock<VecDeque<ResearchTask>>,
    recent_findings: RwLock<Vec<ResearchFinding>>,
    max_queue_size: usize,
    max_findings_cache: usize,
}

impl TaskScheduler {
    pub fn new() -> Self {
        Self {
            queue: RwLock::new(VecDeque::new()),
            recent_findings: RwLock::new(Vec::new()),
            max_queue_size: 100,
            max_findings_cache: 50,
        }
    }

    /// Add a task to the queue
    pub async fn add_task(&self, task: ResearchTask) {
        let mut queue = self.queue.write().await;

        // Maintain max queue size
        if queue.len() >= self.max_queue_size {
            // Remove lowest priority task
            if let Some(idx) = queue.iter().position(|t| t.priority == TaskPriority::Background) {
                queue.remove(idx);
            } else {
                queue.pop_front();
            }
        }

        // Insert based on priority
        let insert_idx = queue
            .iter()
            .position(|t| t.priority < task.priority)
            .unwrap_or(queue.len());

        queue.insert(insert_idx, task);
        log::debug!("Task added to queue. Queue size: {}", queue.len());
    }

    /// Get the next task to process
    pub async fn get_next_task(&self) -> Option<ResearchTask> {
        let mut queue = self.queue.write().await;

        // Find first pending task
        if let Some(idx) = queue.iter().position(|t| t.status == TaskStatus::Pending) {
            let mut task = queue.remove(idx)?;
            task.status = TaskStatus::Running;
            task.started_at = Some(Utc::now());
            Some(task)
        } else {
            None
        }
    }

    /// Execute a task using research adapters
    pub async fn execute_task(&self, task: &ResearchTask) -> Option<Signal> {
        use crate::research::{ResearchAdapterRegistry, traits::{SearchOptions, SortOrder}};
        use crate::research::processors::SignalProcessor;

        log::info!("Executing research task: {} - {}", task.id, task.topic);

        // Create adapter registry with defaults
        let registry = match ResearchAdapterRegistry::with_defaults().await {
            Ok(r) => r,
            Err(e) => {
                log::error!("Failed to create adapter registry: {}", e);
                return None;
            }
        };

        // Determine which adapter to use
        let adapter = if let Some(source) = &task.source {
            registry.get_by_source(source).await
        } else {
            // Default to GitHub if no source specified
            registry.get("GitHub").await
        };

        let adapter = match adapter {
            Some(a) => a,
            None => {
                log::warn!("No adapter available for task: {}", task.topic);
                return None;
            }
        };

        // Configure search options
        let options = SearchOptions {
            limit: Some(10),
            min_relevance: Some(0.5),
            sort_by: Some(SortOrder::Relevance),
            ..Default::default()
        };

        // Execute search
        let findings = match adapter.search(&task.topic, &options).await {
            Ok(f) => f,
            Err(e) => {
                log::error!("Research search failed for '{}': {}", task.topic, e);
                return None;
            }
        };

        log::info!(
            "Research task '{}' found {} results from {}",
            task.topic,
            findings.len(),
            adapter.name()
        );

        if findings.is_empty() {
            return None;
        }

        // Store all findings
        for finding in &findings {
            self.add_finding(finding.clone()).await;
        }

        // Process the best finding into a signal
        let processor = SignalProcessor::default();
        let best_finding = findings.into_iter().next()?;
        let signal = processor.process(&best_finding);

        if signal.is_none() {
            // Generate fallback signal for low-scoring findings
            log::debug!("No signal generated, creating fallback");
            Some(Signal::NewTechnologyDetected {
                name: best_finding.title,
                relevance_score: best_finding.relevance_score,
                source: format!("{:?}", best_finding.source),
            })
        } else {
            signal
        }
    }

    /// Add a finding to the cache
    pub async fn add_finding(&self, finding: ResearchFinding) {
        let mut findings = self.recent_findings.write().await;

        findings.insert(0, finding);

        // Maintain cache size
        if findings.len() > self.max_findings_cache {
            findings.truncate(self.max_findings_cache);
        }
    }

    /// Get recent findings
    pub async fn get_recent_findings(&self, limit: usize) -> Vec<ResearchFinding> {
        let findings = self.recent_findings.read().await;
        findings.iter().take(limit).cloned().collect()
    }

    /// Get queue status
    pub async fn get_queue_status(&self) -> QueueStatus {
        let queue = self.queue.read().await;

        let pending = queue.iter().filter(|t| t.status == TaskStatus::Pending).count();
        let running = queue.iter().filter(|t| matches!(t.status, TaskStatus::Running)).count();

        QueueStatus {
            total: queue.len(),
            pending,
            running,
            by_priority: PriorityBreakdown {
                critical: queue.iter().filter(|t| t.priority == TaskPriority::Critical).count(),
                high: queue.iter().filter(|t| t.priority == TaskPriority::High).count(),
                normal: queue.iter().filter(|t| t.priority == TaskPriority::Normal).count(),
                low: queue.iter().filter(|t| t.priority == TaskPriority::Low).count(),
                background: queue.iter().filter(|t| t.priority == TaskPriority::Background).count(),
            },
        }
    }

    /// Clear completed tasks from queue
    pub async fn clear_completed(&self) {
        let mut queue = self.queue.write().await;
        queue.retain(|t| !matches!(t.status, TaskStatus::Completed | TaskStatus::Failed(_)));
    }

    /// Cancel a task by ID
    pub async fn cancel_task(&self, task_id: &str) -> bool {
        let mut queue = self.queue.write().await;
        if let Some(task) = queue.iter_mut().find(|t| t.id == task_id) {
            task.status = TaskStatus::Cancelled;
            true
        } else {
            false
        }
    }
}

impl Default for TaskScheduler {
    fn default() -> Self {
        Self::new()
    }
}

/// Queue status summary
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QueueStatus {
    pub total: usize,
    pub pending: usize,
    pub running: usize,
    pub by_priority: PriorityBreakdown,
}

/// Tasks by priority
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PriorityBreakdown {
    pub critical: usize,
    pub high: usize,
    pub normal: usize,
    pub low: usize,
    pub background: usize,
}
