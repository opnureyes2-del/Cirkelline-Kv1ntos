// Research Adapters Module - CLA FASE 6
// Concrete implementations of ResearchAdapter trait

mod common;
mod github;
mod arxiv;

pub use common::{AdapterConfig, HttpHelper, RateLimiter};
pub use github::GitHubAdapter;
pub use arxiv::ArXivAdapter;

use crate::commander::ResearchSource;
use crate::research::traits::{ResearchAdapter, ResearchResult, ResearchError};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

/// Registry for managing multiple research adapters
#[derive(Debug)]
pub struct ResearchAdapterRegistry {
    adapters: RwLock<HashMap<String, Arc<dyn ResearchAdapter>>>,
}

impl ResearchAdapterRegistry {
    /// Create a new empty registry
    pub fn new() -> Self {
        Self {
            adapters: RwLock::new(HashMap::new()),
        }
    }

    /// Create a registry with default adapters configured
    pub async fn with_defaults() -> ResearchResult<Self> {
        let registry = Self::new();

        // Add GitHub adapter (no API key required for basic search)
        let github = GitHubAdapter::new(None);
        registry.register(github).await?;

        // Add ArXiv adapter (no API key required)
        let arxiv = ArXivAdapter::new();
        registry.register(arxiv).await?;

        Ok(registry)
    }

    /// Register an adapter
    pub async fn register<A: ResearchAdapter + 'static>(&self, adapter: A) -> ResearchResult<()> {
        let name = adapter.name().to_string();
        let mut adapters = self.adapters.write().await;
        adapters.insert(name, Arc::new(adapter));
        Ok(())
    }

    /// Unregister an adapter by name
    pub async fn unregister(&self, name: &str) -> ResearchResult<()> {
        let mut adapters = self.adapters.write().await;
        adapters.remove(name).ok_or_else(|| {
            ResearchError::AdapterUnavailable(name.to_string())
        })?;
        Ok(())
    }

    /// Get an adapter by name
    pub async fn get(&self, name: &str) -> Option<Arc<dyn ResearchAdapter>> {
        let adapters = self.adapters.read().await;
        adapters.get(name).cloned()
    }

    /// Get adapter by source type
    pub async fn get_by_source(&self, source: &ResearchSource) -> Option<Arc<dyn ResearchAdapter>> {
        let adapters = self.adapters.read().await;
        for adapter in adapters.values() {
            if adapter.source() == *source {
                return Some(adapter.clone());
            }
        }
        None
    }

    /// Get all registered adapters
    pub async fn all(&self) -> Vec<Arc<dyn ResearchAdapter>> {
        let adapters = self.adapters.read().await;
        adapters.values().cloned().collect()
    }

    /// Get all available (validated) adapters
    pub async fn available(&self) -> Vec<Arc<dyn ResearchAdapter>> {
        let adapters = self.adapters.read().await;
        let mut available = Vec::new();

        for adapter in adapters.values() {
            if adapter.health_check().await {
                available.push(adapter.clone());
            }
        }

        available
    }

    /// List all adapter names
    pub async fn list_names(&self) -> Vec<String> {
        let adapters = self.adapters.read().await;
        adapters.keys().cloned().collect()
    }

    /// Validate all adapters and return health status
    pub async fn health_check(&self) -> HashMap<String, bool> {
        let adapters = self.adapters.read().await;
        let mut health = HashMap::new();

        for (name, adapter) in adapters.iter() {
            health.insert(name.clone(), adapter.health_check().await);
        }

        health
    }
}

impl Default for ResearchAdapterRegistry {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_registry_create() {
        let registry = ResearchAdapterRegistry::new();
        assert!(registry.list_names().await.is_empty());
    }

    #[tokio::test]
    async fn test_registry_register() {
        let registry = ResearchAdapterRegistry::new();
        let github = GitHubAdapter::new(None);

        registry.register(github).await.unwrap();

        let names = registry.list_names().await;
        assert!(names.contains(&"GitHub".to_string()));
    }
}
