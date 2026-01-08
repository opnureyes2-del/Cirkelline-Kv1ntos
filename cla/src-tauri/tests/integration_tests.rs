// Integration tests for Cirkelline Local Agent
// Tests complete workflows and component interactions

#![cfg(test)]

mod settings_tests {
    use cla::models::Settings;

    #[test]
    fn test_default_settings_are_conservative() {
        let settings = Settings::default();

        // Verify conservative defaults
        assert_eq!(settings.max_cpu_percent, 30);
        assert_eq!(settings.max_ram_percent, 20);
        assert_eq!(settings.max_gpu_percent, 30);
        assert!(settings.idle_only);
        assert_eq!(settings.idle_threshold_seconds, 120);
        assert!(!settings.auto_start);
        assert!(!settings.run_on_battery);
    }

    #[test]
    fn test_settings_validation() {
        let mut settings = Settings::default();

        // CPU limit validation
        settings.max_cpu_percent = 50;
        assert!(settings.max_cpu_percent <= 80, "CPU limit should be max 80%");

        // RAM limit validation
        settings.max_ram_percent = 30;
        assert!(settings.max_ram_percent <= 50, "RAM limit should be max 50%");
    }
}

mod resource_tests {
    use cla::utils::{ResourceLimiter, ResourceLimits, ExecutionPermission};
    use cla::utils::resource_limiter::SystemMetrics;

    #[tokio::test]
    async fn test_can_execute_when_idle() {
        let limits = ResourceLimits::default();
        let limiter = ResourceLimiter::new(limits);

        let metrics = SystemMetrics {
            cpu_usage_percent: 10.0,
            ram_usage_percent: 15.0,
            gpu_available: false,
            gpu_usage_percent: None,
            on_battery: false,
            battery_percent: None,
            idle_seconds: 150,
            is_idle: true,
        };

        let result = limiter.can_execute(10, 100, false, &metrics).await;
        assert!(matches!(result, ExecutionPermission::Granted { .. }));
    }

    #[tokio::test]
    async fn test_blocks_when_not_idle() {
        let limits = ResourceLimits::default();
        let limiter = ResourceLimiter::new(limits);

        let metrics = SystemMetrics {
            cpu_usage_percent: 10.0,
            ram_usage_percent: 15.0,
            gpu_available: false,
            gpu_usage_percent: None,
            on_battery: false,
            battery_percent: None,
            idle_seconds: 30, // Not idle enough
            is_idle: false,
        };

        let result = limiter.can_execute(10, 100, false, &metrics).await;
        assert!(matches!(result, ExecutionPermission::Denied { .. }));
    }

    #[tokio::test]
    async fn test_blocks_on_low_battery() {
        let limits = ResourceLimits {
            run_on_battery: true,
            min_battery_percent: 20,
            ..ResourceLimits::default()
        };
        let limiter = ResourceLimiter::new(limits);

        let metrics = SystemMetrics {
            cpu_usage_percent: 10.0,
            ram_usage_percent: 15.0,
            gpu_available: false,
            gpu_usage_percent: None,
            on_battery: true,
            battery_percent: Some(10), // Too low
            idle_seconds: 150,
            is_idle: true,
        };

        let result = limiter.can_execute(10, 100, false, &metrics).await;
        assert!(matches!(result, ExecutionPermission::Denied { .. }));
    }
}

mod security_tests {
    use cla::security::{hash_data, sanitize_input, is_endpoint_allowed, SecurityConfig};
    use cla::security::validation::InputValidator;

    #[test]
    fn test_hash_consistency() {
        let hash1 = hash_data(b"test_data");
        let hash2 = hash_data(b"test_data");
        let hash3 = hash_data(b"different_data");

        assert_eq!(hash1, hash2, "Same input should produce same hash");
        assert_ne!(hash1, hash3, "Different input should produce different hash");
    }

    #[test]
    fn test_input_sanitization() {
        let dangerous = "Hello\x00\x1fWorld\n";
        let sanitized = sanitize_input(dangerous);

        assert!(!sanitized.contains('\0'));
        assert!(sanitized.contains('\n')); // Newlines should be preserved
    }

    #[test]
    fn test_endpoint_allowlist() {
        let config = SecurityConfig::default();

        assert!(is_endpoint_allowed("https://ckc.cirkelline.com/api/v1", &config));
        assert!(is_endpoint_allowed("http://localhost:7779/health", &config));
        assert!(!is_endpoint_allowed("https://malicious.com/api", &config));
    }

    #[test]
    fn test_path_validation() {
        let validator = InputValidator::default();

        // Safe paths
        assert!(validator.validate_path("/home/user/document.txt").is_ok());
        assert!(validator.validate_path("/tmp/audio.wav").is_ok());

        // Dangerous paths
        assert!(validator.validate_path("../../etc/passwd").is_err());
        assert!(validator.validate_path("/path/with\0null").is_err());
    }

    #[test]
    fn test_email_validation() {
        let validator = InputValidator::default();

        assert!(validator.validate_email("user@cirkelline.com").is_ok());
        assert!(validator.validate_email("admin@sub.domain.com").is_ok());
        assert!(validator.validate_email("invalid").is_err());
        assert!(validator.validate_email("@nodomain").is_err());
    }
}

mod encryption_tests {
    use cla::security::encryption::{Encryptor, generate_salt};

    #[test]
    fn test_encrypt_decrypt_roundtrip() {
        let key = Encryptor::generate_key();
        let encryptor = Encryptor::from_key(key);

        let plaintext = "Sensitive user data";
        let encrypted = encryptor.encrypt_string(plaintext).unwrap();
        let decrypted = encryptor.decrypt_string(&encrypted).unwrap();

        assert_eq!(plaintext, decrypted);
    }

    #[test]
    fn test_wrong_key_fails() {
        let key1 = Encryptor::generate_key();
        let key2 = Encryptor::generate_key();

        let encryptor1 = Encryptor::from_key(key1);
        let encryptor2 = Encryptor::from_key(key2);

        let encrypted = encryptor1.encrypt_string("secret").unwrap();
        let result = encryptor2.decrypt_string(&encrypted);

        assert!(result.is_err());
    }

    #[test]
    fn test_password_derived_key() {
        let salt = generate_salt();
        let encryptor1 = Encryptor::from_password("my_password", &salt).unwrap();
        let encryptor2 = Encryptor::from_password("my_password", &salt).unwrap();

        let encrypted = encryptor1.encrypt_string("data").unwrap();
        let decrypted = encryptor2.decrypt_string(&encrypted).unwrap();

        assert_eq!("data", decrypted);
    }
}

mod auth_tests {
    use cla::security::auth::{AuthManager, AuthConfig, AuthToken};
    use chrono::{Duration, Utc};

    #[test]
    fn test_token_expiry_check() {
        let valid_token = AuthToken {
            token: "valid".to_string(),
            token_type: "Bearer".to_string(),
            expires_at: Utc::now() + Duration::hours(1),
            refresh_token: None,
            user_id: "user@test.com".to_string(),
            scopes: vec![],
        };

        let expired_token = AuthToken {
            token: "expired".to_string(),
            token_type: "Bearer".to_string(),
            expires_at: Utc::now() - Duration::hours(1),
            refresh_token: None,
            user_id: "user@test.com".to_string(),
            scopes: vec![],
        };

        assert!(!valid_token.is_expired());
        assert!(expired_token.is_expired());
    }

    #[test]
    fn test_login_lockout() {
        let config = AuthConfig {
            max_attempts: 3,
            lockout_duration: Duration::minutes(5),
            token_refresh_threshold: Duration::minutes(5),
        };
        let manager = AuthManager::new(config);

        // First attempts should succeed
        assert!(manager.record_failed_attempt("user1").is_ok());
        assert!(manager.record_failed_attempt("user1").is_ok());

        // Third attempt should trigger lockout
        let result = manager.record_failed_attempt("user1");
        assert!(result.is_err());
        assert!(manager.is_locked("user1"));
    }
}

mod error_tests {
    use cla::error::{ClaError, NetworkError, RecoveryAction};

    #[test]
    fn test_error_recovery_actions() {
        // Network timeout should retry
        let timeout_error = ClaError::Network(NetworkError::Timeout {
            url: "https://api.test.com".to_string(),
            timeout_ms: 5000,
        });
        assert!(matches!(
            timeout_error.recovery_action(),
            RecoveryAction::Retry { .. }
        ));

        // Offline should use fallback
        let offline_error = ClaError::Network(NetworkError::Offline);
        assert!(matches!(
            offline_error.recovery_action(),
            RecoveryAction::UseFallback { .. }
        ));
    }

    #[test]
    fn test_user_friendly_messages() {
        let error = ClaError::Network(NetworkError::Offline);
        let message = error.user_message();

        assert!(message.contains("offline") || message.contains("internet"));
    }
}

mod retry_tests {
    use cla::error::retry::{RetryConfig, retry};
    use cla::error::{ClaError, NetworkError};
    use std::sync::atomic::{AtomicU32, Ordering};
    use std::sync::Arc;

    #[tokio::test]
    async fn test_retry_succeeds_eventually() {
        let config = RetryConfig {
            max_attempts: 5,
            initial_delay_ms: 10,
            ..RetryConfig::default()
        };

        let attempts = Arc::new(AtomicU32::new(0));
        let attempts_clone = attempts.clone();

        let result = retry(&config, || {
            let attempts = attempts_clone.clone();
            async move {
                let count = attempts.fetch_add(1, Ordering::SeqCst);
                if count < 2 {
                    Err(ClaError::Network(NetworkError::Timeout {
                        url: "test".to_string(),
                        timeout_ms: 1000,
                    }))
                } else {
                    Ok(42)
                }
            }
        }).await;

        assert_eq!(result.unwrap(), 42);
        assert_eq!(attempts.load(Ordering::SeqCst), 3);
    }

    #[test]
    fn test_exponential_backoff() {
        let config = RetryConfig {
            initial_delay_ms: 1000,
            max_delay_ms: 30000,
            backoff_multiplier: 2.0,
            jitter_factor: 0.0,
            ..RetryConfig::default()
        };

        let d0 = config.delay_for_attempt(0).as_millis();
        let d1 = config.delay_for_attempt(1).as_millis();
        let d2 = config.delay_for_attempt(2).as_millis();

        assert_eq!(d0, 1000);
        assert_eq!(d1, 2000);
        assert_eq!(d2, 4000);
    }
}
