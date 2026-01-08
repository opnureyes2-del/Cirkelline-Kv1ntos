// Authentication module for CLA-CKC communication
// Handles token management and session security

use chrono::{DateTime, Duration, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::RwLock;

/// Authentication token
#[derive(Clone, Serialize, Deserialize)]
pub struct AuthToken {
    /// JWT or opaque token
    pub token: String,
    /// Token type (Bearer, etc.)
    pub token_type: String,
    /// Expiration time
    pub expires_at: DateTime<Utc>,
    /// Refresh token (if available)
    pub refresh_token: Option<String>,
    /// User email/ID
    pub user_id: String,
    /// Granted scopes
    pub scopes: Vec<String>,
}

impl AuthToken {
    /// Check if token is expired
    pub fn is_expired(&self) -> bool {
        Utc::now() >= self.expires_at
    }

    /// Check if token will expire within given duration
    pub fn will_expire_in(&self, duration: Duration) -> bool {
        Utc::now() + duration >= self.expires_at
    }

    /// Get remaining lifetime in seconds
    pub fn remaining_seconds(&self) -> i64 {
        (self.expires_at - Utc::now()).num_seconds().max(0)
    }
}

/// Authentication manager
pub struct AuthManager {
    current_token: RwLock<Option<AuthToken>>,
    failed_attempts: RwLock<HashMap<String, FailedAttempts>>,
    config: AuthConfig,
}

#[derive(Clone)]
pub struct AuthConfig {
    pub max_attempts: u32,
    pub lockout_duration: Duration,
    pub token_refresh_threshold: Duration,
}

impl Default for AuthConfig {
    fn default() -> Self {
        Self {
            max_attempts: 5,
            lockout_duration: Duration::minutes(5),
            token_refresh_threshold: Duration::minutes(5),
        }
    }
}

struct FailedAttempts {
    count: u32,
    first_attempt: DateTime<Utc>,
    locked_until: Option<DateTime<Utc>>,
}

impl AuthManager {
    pub fn new(config: AuthConfig) -> Self {
        Self {
            current_token: RwLock::new(None),
            failed_attempts: RwLock::new(HashMap::new()),
            config,
        }
    }

    /// Set current authentication token
    pub fn set_token(&self, token: AuthToken) {
        let mut current = self.current_token.write().unwrap();
        *current = Some(token);
    }

    /// Get current token if valid
    pub fn get_token(&self) -> Option<AuthToken> {
        let current = self.current_token.read().unwrap();
        current.clone().filter(|t| !t.is_expired())
    }

    /// Check if authenticated
    pub fn is_authenticated(&self) -> bool {
        self.get_token().is_some()
    }

    /// Check if token needs refresh
    pub fn needs_refresh(&self) -> bool {
        if let Some(token) = self.get_token() {
            token.will_expire_in(self.config.token_refresh_threshold)
        } else {
            false
        }
    }

    /// Clear authentication
    pub fn logout(&self) {
        let mut current = self.current_token.write().unwrap();
        *current = None;
    }

    /// Record failed login attempt
    pub fn record_failed_attempt(&self, identifier: &str) -> Result<(), AuthError> {
        let mut attempts = self.failed_attempts.write().unwrap();
        let now = Utc::now();

        let entry = attempts.entry(identifier.to_string()).or_insert(FailedAttempts {
            count: 0,
            first_attempt: now,
            locked_until: None,
        });

        // Check if currently locked
        if let Some(locked_until) = entry.locked_until {
            if now < locked_until {
                let remaining = (locked_until - now).num_seconds();
                return Err(AuthError::AccountLocked {
                    remaining_seconds: remaining as u32,
                });
            } else {
                // Lockout expired, reset
                entry.count = 0;
                entry.locked_until = None;
            }
        }

        // Reset if first attempt was too long ago
        if (now - entry.first_attempt) > self.config.lockout_duration {
            entry.count = 0;
            entry.first_attempt = now;
        }

        entry.count += 1;

        // Check if should lock
        if entry.count >= self.config.max_attempts {
            entry.locked_until = Some(now + self.config.lockout_duration);
            return Err(AuthError::AccountLocked {
                remaining_seconds: self.config.lockout_duration.num_seconds() as u32,
            });
        }

        Ok(())
    }

    /// Clear failed attempts on successful login
    pub fn clear_failed_attempts(&self, identifier: &str) {
        let mut attempts = self.failed_attempts.write().unwrap();
        attempts.remove(identifier);
    }

    /// Check if identifier is locked
    pub fn is_locked(&self, identifier: &str) -> bool {
        let attempts = self.failed_attempts.read().unwrap();
        if let Some(entry) = attempts.get(identifier) {
            if let Some(locked_until) = entry.locked_until {
                return Utc::now() < locked_until;
            }
        }
        false
    }

    /// Get remaining lockout time
    pub fn lockout_remaining(&self, identifier: &str) -> Option<u32> {
        let attempts = self.failed_attempts.read().unwrap();
        if let Some(entry) = attempts.get(identifier) {
            if let Some(locked_until) = entry.locked_until {
                let remaining = (locked_until - Utc::now()).num_seconds();
                if remaining > 0 {
                    return Some(remaining as u32);
                }
            }
        }
        None
    }

    /// Validate token format
    pub fn validate_token_format(token: &str) -> Result<(), AuthError> {
        // Basic JWT format validation
        let parts: Vec<&str> = token.split('.').collect();
        if parts.len() != 3 {
            return Err(AuthError::InvalidToken);
        }

        // Check each part is valid base64
        for part in parts {
            base64::engine::general_purpose::URL_SAFE_NO_PAD
                .decode(part)
                .map_err(|_| AuthError::InvalidToken)?;
        }

        Ok(())
    }
}

/// Authentication errors
#[derive(Debug, Clone)]
pub enum AuthError {
    InvalidCredentials,
    InvalidToken,
    TokenExpired,
    AccountLocked { remaining_seconds: u32 },
    NetworkError(String),
    ServerError(String),
}

impl std::fmt::Display for AuthError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::InvalidCredentials => write!(f, "Invalid email or password"),
            Self::InvalidToken => write!(f, "Invalid authentication token"),
            Self::TokenExpired => write!(f, "Authentication token has expired"),
            Self::AccountLocked { remaining_seconds } => {
                write!(f, "Account locked. Try again in {} seconds", remaining_seconds)
            }
            Self::NetworkError(msg) => write!(f, "Network error: {}", msg),
            Self::ServerError(msg) => write!(f, "Server error: {}", msg),
        }
    }
}

impl std::error::Error for AuthError {}

use base64::Engine;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_token_expiry() {
        let token = AuthToken {
            token: "test".to_string(),
            token_type: "Bearer".to_string(),
            expires_at: Utc::now() + Duration::hours(1),
            refresh_token: None,
            user_id: "user@test.com".to_string(),
            scopes: vec!["read".to_string()],
        };

        assert!(!token.is_expired());
        assert!(token.remaining_seconds() > 0);
    }

    #[test]
    fn test_expired_token() {
        let token = AuthToken {
            token: "test".to_string(),
            token_type: "Bearer".to_string(),
            expires_at: Utc::now() - Duration::hours(1),
            refresh_token: None,
            user_id: "user@test.com".to_string(),
            scopes: vec![],
        };

        assert!(token.is_expired());
        assert_eq!(token.remaining_seconds(), 0);
    }

    #[test]
    fn test_auth_manager_failed_attempts() {
        let manager = AuthManager::new(AuthConfig {
            max_attempts: 3,
            lockout_duration: Duration::minutes(5),
            token_refresh_threshold: Duration::minutes(5),
        });

        // First 2 attempts should succeed
        assert!(manager.record_failed_attempt("user1").is_ok());
        assert!(manager.record_failed_attempt("user1").is_ok());

        // Third attempt should lock
        let result = manager.record_failed_attempt("user1");
        assert!(matches!(result, Err(AuthError::AccountLocked { .. })));

        // Should be locked
        assert!(manager.is_locked("user1"));
    }

    #[test]
    fn test_clear_failed_attempts() {
        let manager = AuthManager::new(AuthConfig::default());

        manager.record_failed_attempt("user1").unwrap();
        manager.record_failed_attempt("user1").unwrap();

        manager.clear_failed_attempts("user1");

        // Should be able to fail again
        assert!(manager.record_failed_attempt("user1").is_ok());
    }
}
