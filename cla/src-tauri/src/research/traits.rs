// Research Adapter Trait - Core interface for research sources
// Each adapter (GitHub, ArXiv, etc.) implements this trait

use crate::commander::{ResearchFinding, ResearchSource};
use async_trait::async_trait;
use std::fmt::Debug;

/// Result type for research operations
pub type ResearchResult<T> = Result<T, ResearchError>;

/// Research errors
#[derive(Debug, Clone)]
pub enum ResearchError {
    /// Network/HTTP error
    NetworkError(String),
    /// API rate limit exceeded
    RateLimited { retry_after_secs: Option<u64> },
    /// API returned error
    ApiError { status: u16, message: String },
    /// Failed to parse response
    ParseError(String),
    /// Invalid configuration
    ConfigError(String),
    /// Adapter not available
    AdapterUnavailable(String),
    /// Search query invalid
    InvalidQuery(String),
}

impl std::fmt::Display for ResearchError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::NetworkError(msg) => write!(f, "Network error: {}", msg),
            Self::RateLimited { retry_after_secs } => {
                if let Some(secs) = retry_after_secs {
                    write!(f, "Rate limited, retry after {} seconds", secs)
                } else {
                    write!(f, "Rate limited")
                }
            }
            Self::ApiError { status, message } => {
                write!(f, "API error ({}): {}", status, message)
            }
            Self::ParseError(msg) => write!(f, "Parse error: {}", msg),
            Self::ConfigError(msg) => write!(f, "Config error: {}", msg),
            Self::AdapterUnavailable(name) => write!(f, "Adapter unavailable: {}", name),
            Self::InvalidQuery(msg) => write!(f, "Invalid query: {}", msg),
        }
    }
}

impl std::error::Error for ResearchError {}

/// Search options for research queries
#[derive(Debug, Clone, Default)]
pub struct SearchOptions {
    /// Maximum number of results
    pub limit: Option<usize>,
    /// Minimum relevance score (0.0-1.0)
    pub min_relevance: Option<f32>,
    /// Filter by date (Unix timestamp)
    pub since_timestamp: Option<i64>,
    /// Filter by specific tags/categories
    pub tags: Option<Vec<String>>,
    /// Sort order
    pub sort_by: Option<SortOrder>,
}

/// Sort order for search results
#[derive(Debug, Clone, Default)]
pub enum SortOrder {
    #[default]
    Relevance,
    DateDesc,
    DateAsc,
    PopularityDesc,
}

/// Core trait that all research adapters must implement
#[async_trait]
pub trait ResearchAdapter: Send + Sync + Debug {
    /// Get the adapter name (e.g., "GitHub", "ArXiv")
    fn name(&self) -> &str;

    /// Get the research source type
    fn source(&self) -> ResearchSource;

    /// Check if the adapter is configured and available
    async fn validate(&self) -> ResearchResult<()>;

    /// Search for research findings matching the query
    async fn search(
        &self,
        query: &str,
        options: &SearchOptions,
    ) -> ResearchResult<Vec<ResearchFinding>>;

    /// Get trending/recent topics (if supported)
    async fn get_trending(&self, limit: usize) -> ResearchResult<Vec<ResearchFinding>> {
        // Default implementation - not all sources support trending
        let _ = limit;
        Ok(vec![])
    }

    /// Check health/connectivity of the adapter
    async fn health_check(&self) -> bool {
        self.validate().await.is_ok()
    }
}
