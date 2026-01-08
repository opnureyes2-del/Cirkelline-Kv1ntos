// Security-focused tests for CLA
// Tests encryption, authentication, and input validation

#![cfg(test)]

use cla::security::{
    encryption::{Encryptor, generate_salt},
    validation::InputValidator,
    auth::{AuthManager, AuthConfig, AuthToken},
    rate_limiter::RateLimiter,
    SecurityConfig,
};
use chrono::{Duration, Utc};
use std::time::Duration as StdDuration;

mod encryption_tests {
    use super::*;

    #[test]
    fn test_generate_key_is_random() {
        let key1 = Encryptor::generate_key();
        let key2 = Encryptor::generate_key();

        assert_ne!(key1, key2, "Generated keys should be unique");
        assert_eq!(key1.len(), 32, "Key should be 256 bits");
    }

    #[test]
    fn test_encrypt_produces_different_ciphertext() {
        let encryptor = Encryptor::from_key(Encryptor::generate_key());
        let plaintext = "Same message";

        let encrypted1 = encryptor.encrypt_string(plaintext).unwrap();
        let encrypted2 = encryptor.encrypt_string(plaintext).unwrap();

        // Due to random nonce, ciphertexts should differ
        assert_ne!(encrypted1, encrypted2);
    }

    #[test]
    fn test_empty_string_encryption() {
        let encryptor = Encryptor::from_key(Encryptor::generate_key());

        let encrypted = encryptor.encrypt_string("").unwrap();
        let decrypted = encryptor.decrypt_string(&encrypted).unwrap();

        assert_eq!(decrypted, "");
    }

    #[test]
    fn test_large_data_encryption() {
        let encryptor = Encryptor::from_key(Encryptor::generate_key());
        let large_data = "A".repeat(1_000_000); // 1MB

        let encrypted = encryptor.encrypt_string(&large_data).unwrap();
        let decrypted = encryptor.decrypt_string(&encrypted).unwrap();

        assert_eq!(decrypted, large_data);
    }

    #[test]
    fn test_unicode_encryption() {
        let encryptor = Encryptor::from_key(Encryptor::generate_key());
        let unicode_text = "日本語テスト 🚀 Ñoño café";

        let encrypted = encryptor.encrypt_string(unicode_text).unwrap();
        let decrypted = encryptor.decrypt_string(&encrypted).unwrap();

        assert_eq!(decrypted, unicode_text);
    }

    #[test]
    fn test_password_different_salts() {
        let password = "secure_password123";
        let salt1 = generate_salt();
        let salt2 = generate_salt();

        let enc1 = Encryptor::from_password(password, &salt1).unwrap();
        let enc2 = Encryptor::from_password(password, &salt2).unwrap();

        let encrypted = enc1.encrypt_string("test").unwrap();
        let result = enc2.decrypt_string(&encrypted);

        assert!(result.is_err(), "Different salts should produce different keys");
    }

    #[test]
    fn test_tampered_ciphertext() {
        let encryptor = Encryptor::from_key(Encryptor::generate_key());

        let mut encrypted = encryptor.encrypt_string("secret").unwrap();

        // Tamper with the ciphertext
        if let Some(byte) = encrypted.ciphertext.get_mut(0) {
            *byte ^= 0xFF;
        }

        let result = encryptor.decrypt_string(&encrypted);
        assert!(result.is_err(), "Tampered data should fail decryption");
    }
}

mod validation_tests {
    use super::*;

    #[test]
    fn test_path_traversal_prevention() {
        let validator = InputValidator::default();

        let dangerous_paths = vec![
            "../../../etc/passwd",
            "..\\..\\windows\\system32",
            "/home/user/../../../root/.ssh/id_rsa",
            "file:///etc/passwd",
            "\\\\server\\share",
        ];

        for path in dangerous_paths {
            assert!(
                validator.validate_path(path).is_err(),
                "Should reject path traversal: {}",
                path
            );
        }
    }

    #[test]
    fn test_valid_paths() {
        let validator = InputValidator::default();

        let valid_paths = vec![
            "/home/user/documents/file.txt",
            "/tmp/cache/data.json",
            "/var/log/app.log",
            "C:\\Users\\User\\Documents\\file.txt",
        ];

        for path in valid_paths {
            assert!(
                validator.validate_path(path).is_ok(),
                "Should accept valid path: {}",
                path
            );
        }
    }

    #[test]
    fn test_null_byte_rejection() {
        let validator = InputValidator::default();

        assert!(validator.validate_path("/path/with\0null").is_err());
        assert!(validator.validate_string("text\0hidden").is_err());
    }

    #[test]
    fn test_email_validation_comprehensive() {
        let validator = InputValidator::default();

        // Valid emails
        let valid = vec![
            "user@example.com",
            "user.name@example.co.uk",
            "user+tag@example.org",
            "123@example.com",
        ];

        for email in valid {
            assert!(
                validator.validate_email(email).is_ok(),
                "Should accept: {}",
                email
            );
        }

        // Invalid emails
        let invalid = vec![
            "not-an-email",
            "@nodomain.com",
            "user@",
            "user@.com",
            "",
            "user@domain",
            "user name@example.com",
        ];

        for email in invalid {
            assert!(
                validator.validate_email(email).is_err(),
                "Should reject: {}",
                email
            );
        }
    }

    #[test]
    fn test_string_length_limits() {
        let validator = InputValidator::default();

        let short = "a".repeat(100);
        let long = "a".repeat(100_000);

        assert!(validator.validate_string(&short).is_ok());
        assert!(validator.validate_string(&long).is_err());
    }
}

mod auth_tests {
    use super::*;

    #[test]
    fn test_token_expiry_grace_period() {
        // Token about to expire (within refresh threshold)
        let token = AuthToken {
            token: "test".to_string(),
            token_type: "Bearer".to_string(),
            expires_at: Utc::now() + Duration::minutes(3),
            refresh_token: Some("refresh".to_string()),
            user_id: "user@test.com".to_string(),
            scopes: vec![],
        };

        assert!(!token.is_expired());
        assert!(token.should_refresh());
    }

    #[test]
    fn test_lockout_timing() {
        let config = AuthConfig {
            max_attempts: 3,
            lockout_duration: Duration::seconds(10),
            token_refresh_threshold: Duration::minutes(5),
        };
        let manager = AuthManager::new(config);

        // Trigger lockout
        for _ in 0..3 {
            let _ = manager.record_failed_attempt("user1");
        }

        assert!(manager.is_locked("user1"));

        // Different user should not be locked
        assert!(!manager.is_locked("user2"));
    }

    #[test]
    fn test_successful_login_clears_attempts() {
        let config = AuthConfig::default();
        let manager = AuthManager::new(config);

        // Record some failed attempts
        let _ = manager.record_failed_attempt("user1");
        let _ = manager.record_failed_attempt("user1");

        // Successful login
        manager.record_success("user1");

        // Should be able to fail again
        assert!(manager.record_failed_attempt("user1").is_ok());
    }

    #[test]
    fn test_token_scopes() {
        let token = AuthToken {
            token: "test".to_string(),
            token_type: "Bearer".to_string(),
            expires_at: Utc::now() + Duration::hours(1),
            refresh_token: None,
            user_id: "user@test.com".to_string(),
            scopes: vec!["read".to_string(), "write".to_string()],
        };

        assert!(token.has_scope("read"));
        assert!(token.has_scope("write"));
        assert!(!token.has_scope("admin"));
    }
}

mod rate_limiter_tests {
    use super::*;

    #[test]
    fn test_rate_limit_basic() {
        let limiter = RateLimiter::new(5, StdDuration::from_secs(60));

        // First 5 requests should succeed
        for _ in 0..5 {
            assert!(limiter.check("key1").is_ok());
        }

        // 6th should fail
        assert!(limiter.check("key1").is_err());
    }

    #[test]
    fn test_rate_limit_per_key() {
        let limiter = RateLimiter::new(2, StdDuration::from_secs(60));

        assert!(limiter.check("key1").is_ok());
        assert!(limiter.check("key1").is_ok());
        assert!(limiter.check("key1").is_err());

        // Different key should work
        assert!(limiter.check("key2").is_ok());
    }

    #[test]
    fn test_remaining_requests() {
        let limiter = RateLimiter::new(5, StdDuration::from_secs(60));

        assert_eq!(limiter.remaining("key1"), 5);

        limiter.check("key1").unwrap();
        assert_eq!(limiter.remaining("key1"), 4);

        limiter.check("key1").unwrap();
        limiter.check("key1").unwrap();
        assert_eq!(limiter.remaining("key1"), 2);
    }
}

mod endpoint_security_tests {
    use super::*;
    use cla::security::is_endpoint_allowed;

    #[test]
    fn test_allowed_endpoints() {
        let config = SecurityConfig::default();

        let allowed = vec![
            "https://ckc.cirkelline.com/api/v1/sync",
            "https://ckc.cirkelline.com/api/v1/auth",
            "http://localhost:7779/health",
            "http://127.0.0.1:8080/api",
        ];

        for endpoint in allowed {
            assert!(
                is_endpoint_allowed(endpoint, &config),
                "Should allow: {}",
                endpoint
            );
        }
    }

    #[test]
    fn test_blocked_endpoints() {
        let config = SecurityConfig::default();

        let blocked = vec![
            "https://malicious.com/steal",
            "http://evil.org/api",
            "https://phishing.net/login",
            "file:///etc/passwd",
            "ftp://files.example.com",
        ];

        for endpoint in blocked {
            assert!(
                !is_endpoint_allowed(endpoint, &config),
                "Should block: {}",
                endpoint
            );
        }
    }

    #[test]
    fn test_custom_allowlist() {
        let mut config = SecurityConfig::default();
        config.allowed_endpoints.push("https://custom.api.com".to_string());

        assert!(is_endpoint_allowed("https://custom.api.com/v1", &config));
    }
}
