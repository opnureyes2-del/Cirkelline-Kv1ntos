// Retry mechanism with exponential backoff
// Automatically retries failed operations based on error type

use std::future::Future;
use std::time::Duration;
use tokio::time::sleep;

use super::{ClaError, ClaResult, RecoveryAction};

/// Retry configuration
#[derive(Clone)]
pub struct RetryConfig {
    /// Maximum number of retry attempts
    pub max_attempts: u32,
    /// Initial delay between retries (milliseconds)
    pub initial_delay_ms: u64,
    /// Maximum delay between retries (milliseconds)
    pub max_delay_ms: u64,
    /// Backoff multiplier
    pub backoff_multiplier: f64,
    /// Jitter factor (0.0 to 1.0)
    pub jitter_factor: f64,
}

impl Default for RetryConfig {
    fn default() -> Self {
        Self {
            max_attempts: 3,
            initial_delay_ms: 1000,
            max_delay_ms: 30000,
            backoff_multiplier: 2.0,
            jitter_factor: 0.1,
        }
    }
}

impl RetryConfig {
    /// Config for aggressive retry (network issues)
    pub fn aggressive() -> Self {
        Self {
            max_attempts: 5,
            initial_delay_ms: 500,
            max_delay_ms: 10000,
            backoff_multiplier: 1.5,
            jitter_factor: 0.2,
        }
    }

    /// Config for gentle retry (resource constraints)
    pub fn gentle() -> Self {
        Self {
            max_attempts: 10,
            initial_delay_ms: 5000,
            max_delay_ms: 60000,
            backoff_multiplier: 1.5,
            jitter_factor: 0.1,
        }
    }

    /// Calculate delay for given attempt
    pub fn delay_for_attempt(&self, attempt: u32) -> Duration {
        let base_delay = self.initial_delay_ms as f64
            * self.backoff_multiplier.powi(attempt as i32);

        let capped_delay = base_delay.min(self.max_delay_ms as f64);

        // Add jitter
        let jitter_range = capped_delay * self.jitter_factor;
        let jitter = (rand::random::<f64>() - 0.5) * 2.0 * jitter_range;
        let final_delay = (capped_delay + jitter).max(0.0);

        Duration::from_millis(final_delay as u64)
    }
}

/// Retry an async operation
pub async fn retry<T, F, Fut>(
    config: &RetryConfig,
    mut operation: F,
) -> ClaResult<T>
where
    F: FnMut() -> Fut,
    Fut: Future<Output = ClaResult<T>>,
{
    let mut last_error = None;

    for attempt in 0..config.max_attempts {
        match operation().await {
            Ok(result) => return Ok(result),
            Err(error) => {
                if !error.should_retry() {
                    return Err(error);
                }

                last_error = Some(error);

                if attempt + 1 < config.max_attempts {
                    let delay = config.delay_for_attempt(attempt);
                    log::warn!(
                        "Attempt {} failed, retrying in {:?}",
                        attempt + 1,
                        delay
                    );
                    sleep(delay).await;
                }
            }
        }
    }

    Err(last_error.unwrap_or(ClaError::Internal("All retry attempts failed".to_string())))
}

/// Retry with custom predicate
pub async fn retry_if<T, F, Fut, P>(
    config: &RetryConfig,
    mut operation: F,
    should_retry: P,
) -> ClaResult<T>
where
    F: FnMut() -> Fut,
    Fut: Future<Output = ClaResult<T>>,
    P: Fn(&ClaError) -> bool,
{
    let mut last_error = None;

    for attempt in 0..config.max_attempts {
        match operation().await {
            Ok(result) => return Ok(result),
            Err(error) => {
                if !should_retry(&error) {
                    return Err(error);
                }

                last_error = Some(error);

                if attempt + 1 < config.max_attempts {
                    let delay = config.delay_for_attempt(attempt);
                    sleep(delay).await;
                }
            }
        }
    }

    Err(last_error.unwrap_or(ClaError::Internal("All retry attempts failed".to_string())))
}

/// Retry with timeout
pub async fn retry_with_timeout<T, F, Fut>(
    config: &RetryConfig,
    timeout: Duration,
    operation: F,
) -> ClaResult<T>
where
    F: FnMut() -> Fut + Clone,
    Fut: Future<Output = ClaResult<T>>,
{
    tokio::time::timeout(timeout, retry(config, operation))
        .await
        .map_err(|_| ClaError::Network(super::NetworkError::Timeout {
            url: "operation".to_string(),
            timeout_ms: timeout.as_millis() as u64,
        }))?
}

/// Retry context for tracking progress
pub struct RetryContext {
    pub attempt: u32,
    pub max_attempts: u32,
    pub last_error: Option<ClaError>,
    pub total_delay_ms: u64,
}

impl RetryContext {
    pub fn new(max_attempts: u32) -> Self {
        Self {
            attempt: 0,
            max_attempts,
            last_error: None,
            total_delay_ms: 0,
        }
    }

    pub fn remaining_attempts(&self) -> u32 {
        self.max_attempts.saturating_sub(self.attempt)
    }

    pub fn progress(&self) -> f32 {
        self.attempt as f32 / self.max_attempts as f32
    }
}

/// Callback for retry progress
pub type RetryCallback = Box<dyn Fn(&RetryContext) + Send + Sync>;

/// Retry with progress callback
pub async fn retry_with_callback<T, F, Fut>(
    config: &RetryConfig,
    mut operation: F,
    callback: RetryCallback,
) -> ClaResult<T>
where
    F: FnMut() -> Fut,
    Fut: Future<Output = ClaResult<T>>,
{
    let mut context = RetryContext::new(config.max_attempts);

    for attempt in 0..config.max_attempts {
        context.attempt = attempt + 1;
        callback(&context);

        match operation().await {
            Ok(result) => return Ok(result),
            Err(error) => {
                if !error.should_retry() {
                    return Err(error);
                }

                context.last_error = Some(error);

                if attempt + 1 < config.max_attempts {
                    let delay = config.delay_for_attempt(attempt);
                    context.total_delay_ms += delay.as_millis() as u64;
                    sleep(delay).await;
                }
            }
        }
    }

    Err(context.last_error.unwrap_or(ClaError::Internal("All retry attempts failed".to_string())))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicU32, Ordering};
    use std::sync::Arc;

    #[tokio::test]
    async fn test_retry_success_first_try() {
        let config = RetryConfig::default();
        let result = retry(&config, || async { Ok::<_, ClaError>(42) }).await;
        assert_eq!(result.unwrap(), 42);
    }

    #[tokio::test]
    async fn test_retry_success_after_failures() {
        let config = RetryConfig {
            max_attempts: 5,
            initial_delay_ms: 10,
            ..Default::default()
        };

        let attempts = Arc::new(AtomicU32::new(0));
        let attempts_clone = attempts.clone();

        let result = retry(&config, || {
            let attempts = attempts_clone.clone();
            async move {
                let count = attempts.fetch_add(1, Ordering::SeqCst);
                if count < 2 {
                    Err(ClaError::Network(super::super::NetworkError::Timeout {
                        url: "test".to_string(),
                        timeout_ms: 1000,
                    }))
                } else {
                    Ok(42)
                }
            }
        })
        .await;

        assert_eq!(result.unwrap(), 42);
        assert_eq!(attempts.load(Ordering::SeqCst), 3);
    }

    #[tokio::test]
    async fn test_retry_non_retryable_error() {
        let config = RetryConfig::default();

        let result = retry(&config, || async {
            Err::<i32, _>(ClaError::Security(super::super::SecurityError::Unauthorized))
        })
        .await;

        assert!(result.is_err());
    }

    #[test]
    fn test_delay_calculation() {
        let config = RetryConfig {
            initial_delay_ms: 1000,
            max_delay_ms: 10000,
            backoff_multiplier: 2.0,
            jitter_factor: 0.0,
            ..Default::default()
        };

        let delay0 = config.delay_for_attempt(0);
        let delay1 = config.delay_for_attempt(1);
        let delay2 = config.delay_for_attempt(2);

        assert_eq!(delay0.as_millis(), 1000);
        assert_eq!(delay1.as_millis(), 2000);
        assert_eq!(delay2.as_millis(), 4000);
    }

    #[test]
    fn test_delay_capping() {
        let config = RetryConfig {
            initial_delay_ms: 1000,
            max_delay_ms: 5000,
            backoff_multiplier: 10.0,
            jitter_factor: 0.0,
            ..Default::default()
        };

        let delay = config.delay_for_attempt(5);
        assert!(delay.as_millis() <= 5000);
    }
}
