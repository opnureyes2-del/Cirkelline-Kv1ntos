// Security module for Cirkelline Local Agent
// Handles authentication, encryption, and secure communication

pub mod encryption;
pub mod auth;
pub mod validation;

pub use encryption::{Encryptor, EncryptedData};
pub use auth::{AuthManager, AuthToken, AuthError};
pub use validation::{InputValidator, ValidationError};

use sha2::{Sha256, Digest};
use base64::{Engine as _, engine::general_purpose::STANDARD as BASE64};

/// Security configuration
#[derive(Clone)]
pub struct SecurityConfig {
    /// Minimum password length
    pub min_password_length: usize,
    /// Token expiry in seconds
    pub token_expiry_seconds: u64,
    /// Maximum failed login attempts before lockout
    pub max_login_attempts: u32,
    /// Lockout duration in seconds
    pub lockout_duration_seconds: u64,
    /// Enable encryption for local storage
    pub encrypt_local_storage: bool,
    /// Allowed CKC endpoints
    pub allowed_endpoints: Vec<String>,
}

impl Default for SecurityConfig {
    fn default() -> Self {
        Self {
            min_password_length: 8,
            token_expiry_seconds: 3600, // 1 hour
            max_login_attempts: 5,
            lockout_duration_seconds: 300, // 5 minutes
            encrypt_local_storage: true,
            allowed_endpoints: vec![
                "https://ckc.cirkelline.com".to_string(),
                "https://api.cirkelline.com".to_string(),
                "http://localhost:7779".to_string(), // Dev
            ],
        }
    }
}

/// Hash sensitive data using SHA-256
pub fn hash_data(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    let result = hasher.finalize();
    BASE64.encode(result)
}

/// Generate a secure random token
pub fn generate_token(length: usize) -> String {
    use rand::Rng;
    let mut rng = rand::thread_rng();
    let bytes: Vec<u8> = (0..length).map(|_| rng.gen()).collect();
    BASE64.encode(&bytes)
}

/// Sanitize user input to prevent injection attacks
pub fn sanitize_input(input: &str) -> String {
    input
        .chars()
        .filter(|c| !c.is_control() || *c == '\n' || *c == '\t')
        .collect::<String>()
        .trim()
        .to_string()
}

/// Validate URL against allowed endpoints
pub fn is_endpoint_allowed(url: &str, config: &SecurityConfig) -> bool {
    config.allowed_endpoints.iter().any(|allowed| {
        url.starts_with(allowed)
    })
}

/// Rate limiter for API calls
pub struct RateLimiter {
    requests: std::sync::Mutex<std::collections::HashMap<String, Vec<std::time::Instant>>>,
    max_requests: usize,
    window_seconds: u64,
}

impl RateLimiter {
    pub fn new(max_requests: usize, window_seconds: u64) -> Self {
        Self {
            requests: std::sync::Mutex::new(std::collections::HashMap::new()),
            max_requests,
            window_seconds,
        }
    }

    /// Check if request is allowed
    pub fn check(&self, key: &str) -> bool {
        let mut requests = self.requests.lock().unwrap();
        let now = std::time::Instant::now();
        let window = std::time::Duration::from_secs(self.window_seconds);

        let entry = requests.entry(key.to_string()).or_insert_with(Vec::new);

        // Remove old requests outside window
        entry.retain(|&t| now.duration_since(t) < window);

        if entry.len() < self.max_requests {
            entry.push(now);
            true
        } else {
            false
        }
    }

    /// Get remaining requests in window
    pub fn remaining(&self, key: &str) -> usize {
        let requests = self.requests.lock().unwrap();
        let now = std::time::Instant::now();
        let window = std::time::Duration::from_secs(self.window_seconds);

        if let Some(entry) = requests.get(key) {
            let valid_count = entry.iter()
                .filter(|&&t| now.duration_since(t) < window)
                .count();
            self.max_requests.saturating_sub(valid_count)
        } else {
            self.max_requests
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hash_data() {
        let hash1 = hash_data(b"test");
        let hash2 = hash_data(b"test");
        let hash3 = hash_data(b"different");

        assert_eq!(hash1, hash2);
        assert_ne!(hash1, hash3);
    }

    #[test]
    fn test_sanitize_input() {
        let input = "  hello\x00world\x1f  ";
        let sanitized = sanitize_input(input);
        assert_eq!(sanitized, "helloworld");
    }

    #[test]
    fn test_rate_limiter() {
        let limiter = RateLimiter::new(3, 60);

        assert!(limiter.check("user1"));
        assert!(limiter.check("user1"));
        assert!(limiter.check("user1"));
        assert!(!limiter.check("user1")); // Should be blocked
        assert!(limiter.check("user2")); // Different user OK
    }

    #[test]
    fn test_endpoint_validation() {
        let config = SecurityConfig::default();

        assert!(is_endpoint_allowed("https://ckc.cirkelline.com/api/v1", &config));
        assert!(is_endpoint_allowed("http://localhost:7779/health", &config));
        assert!(!is_endpoint_allowed("https://evil.com/api", &config));
    }
}
