// Common utilities for research adapters
// Shared HTTP helper, rate limiting, and configuration

use crate::research::traits::{ResearchResult, ResearchError};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, Instant};
use tokio::sync::Mutex;

/// Common configuration for adapters
#[derive(Debug, Clone)]
pub struct AdapterConfig {
    /// Base URL for the API
    pub base_url: String,
    /// Optional API key for authentication
    pub api_key: Option<String>,
    /// Request timeout in seconds
    pub timeout_secs: u64,
    /// Maximum results per request
    pub max_results: usize,
    /// User agent string
    pub user_agent: String,
}

impl Default for AdapterConfig {
    fn default() -> Self {
        Self {
            base_url: String::new(),
            api_key: None,
            timeout_secs: 30,
            max_results: 50,
            user_agent: "CLA-ResearchAdapter/1.0 (Cirkelline Local Agent)".to_string(),
        }
    }
}

/// Rate limiter for API requests
#[derive(Debug)]
pub struct RateLimiter {
    /// Maximum requests per window
    max_requests: u32,
    /// Window duration
    window: Duration,
    /// Current request count
    request_count: AtomicU64,
    /// Window start time
    window_start: Mutex<Instant>,
}

impl RateLimiter {
    /// Create a new rate limiter
    pub fn new(max_requests: u32, window_secs: u64) -> Self {
        Self {
            max_requests,
            window: Duration::from_secs(window_secs),
            request_count: AtomicU64::new(0),
            window_start: Mutex::new(Instant::now()),
        }
    }

    /// Check if a request can be made (non-blocking)
    pub async fn check(&self) -> bool {
        let mut start = self.window_start.lock().await;
        let now = Instant::now();

        // Reset window if expired
        if now.duration_since(*start) >= self.window {
            *start = now;
            self.request_count.store(0, Ordering::SeqCst);
        }

        let count = self.request_count.load(Ordering::SeqCst);
        count < self.max_requests as u64
    }

    /// Record a request
    pub fn record(&self) {
        self.request_count.fetch_add(1, Ordering::SeqCst);
    }

    /// Wait until a request can be made (blocking)
    pub async fn acquire(&self) -> ResearchResult<()> {
        let mut attempts = 0;
        const MAX_ATTEMPTS: u32 = 60;

        while !self.check().await {
            if attempts >= MAX_ATTEMPTS {
                return Err(ResearchError::RateLimited {
                    retry_after_secs: Some(self.window.as_secs()),
                });
            }
            tokio::time::sleep(Duration::from_secs(1)).await;
            attempts += 1;
        }

        self.record();
        Ok(())
    }
}

/// HTTP helper for making API requests
#[derive(Debug)]
pub struct HttpHelper {
    client: reqwest::Client,
    config: AdapterConfig,
    rate_limiter: RateLimiter,
}

impl HttpHelper {
    /// Create a new HTTP helper
    pub fn new(config: AdapterConfig, rate_limit: Option<(u32, u64)>) -> ResearchResult<Self> {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(config.timeout_secs))
            .user_agent(&config.user_agent)
            .build()
            .map_err(|e| ResearchError::NetworkError(e.to_string()))?;

        let (max_req, window) = rate_limit.unwrap_or((60, 60));
        let rate_limiter = RateLimiter::new(max_req, window);

        Ok(Self {
            client,
            config,
            rate_limiter,
        })
    }

    /// Make a GET request
    pub async fn get(&self, url: &str) -> ResearchResult<reqwest::Response> {
        self.rate_limiter.acquire().await?;

        let mut request = self.client.get(url);

        if let Some(ref key) = self.config.api_key {
            request = request.header("Authorization", format!("Bearer {}", key));
        }

        request
            .send()
            .await
            .map_err(|e| ResearchError::NetworkError(e.to_string()))
    }

    /// Make a GET request with custom headers
    pub async fn get_with_headers(
        &self,
        url: &str,
        headers: &[(String, String)],
    ) -> ResearchResult<reqwest::Response> {
        self.rate_limiter.acquire().await?;

        let mut request = self.client.get(url);

        if let Some(ref key) = self.config.api_key {
            request = request.header("Authorization", format!("Bearer {}", key));
        }

        for (key, value) in headers {
            request = request.header(key.as_str(), value.as_str());
        }

        request
            .send()
            .await
            .map_err(|e| ResearchError::NetworkError(e.to_string()))
    }

    /// Get the base URL
    pub fn base_url(&self) -> &str {
        &self.config.base_url
    }

    /// Get max results setting
    pub fn max_results(&self) -> usize {
        self.config.max_results
    }
}

/// Parse relevance score from various formats
pub fn parse_relevance(score: Option<f64>, max_score: f64) -> f32 {
    match score {
        Some(s) if max_score > 0.0 => (s / max_score).min(1.0) as f32,
        Some(s) => s.min(1.0) as f32,
        None => 0.5,
    }
}

/// Sanitize search query for API
pub fn sanitize_query(query: &str) -> String {
    query
        .chars()
        .filter(|c| c.is_alphanumeric() || c.is_whitespace() || *c == '-' || *c == '_')
        .collect::<String>()
        .trim()
        .to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sanitize_query() {
        assert_eq!(sanitize_query("hello world"), "hello world");
        assert_eq!(sanitize_query("rust-lang"), "rust-lang");
        assert_eq!(sanitize_query("test<script>"), "testscript");
    }

    #[test]
    fn test_parse_relevance() {
        assert_eq!(parse_relevance(Some(5.0), 10.0), 0.5);
        assert_eq!(parse_relevance(Some(10.0), 10.0), 1.0);
        assert_eq!(parse_relevance(None, 10.0), 0.5);
    }

    #[tokio::test]
    async fn test_rate_limiter() {
        let limiter = RateLimiter::new(2, 1);
        
        assert!(limiter.check().await);
        limiter.record();
        
        assert!(limiter.check().await);
        limiter.record();
        
        // Third request should fail
        assert!(!limiter.check().await);
    }
}
