# CLA Security Guide

## Security Philosophy

Cirkelline Local Agent (CLA) follows a **privacy-first, security-by-design** approach.
User data stays on the device unless explicitly synced with consent.

---

## Threat Model

### Assets to Protect

| Asset | Sensitivity | Storage |
|-------|-------------|---------|
| User memories | High | Local encrypted |
| API keys | Critical | OS keychain |
| Session data | Medium | Local encrypted |
| Model files | Low | Local plaintext |
| Telemetry | Low | Anonymous |

### Threat Actors

1. **Local attacker** - Physical access to device
2. **Network attacker** - Man-in-the-middle
3. **Malicious app** - Other apps on system
4. **CKC compromise** - Backend breach

---

## Security Architecture

### 1. Data Encryption

#### At Rest (Local Storage)

**Algorithm:** AES-256-GCM

```rust
use aes_gcm::{Aes256Gcm, Key, Nonce};
use aes_gcm::aead::{Aead, NewAead};

pub fn encrypt_data(plaintext: &[u8], key: &[u8; 32]) -> Result<Vec<u8>> {
    let cipher = Aes256Gcm::new(Key::from_slice(key));
    let nonce = generate_random_nonce(); // 12 bytes

    let ciphertext = cipher.encrypt(Nonce::from_slice(&nonce), plaintext)?;

    // Prepend nonce to ciphertext
    let mut result = nonce.to_vec();
    result.extend(ciphertext);
    Ok(result)
}
```

**Key Derivation:** Argon2id

```rust
use argon2::{Argon2, password_hash::SaltString};

pub fn derive_key(password: &str, salt: &[u8]) -> [u8; 32] {
    let argon2 = Argon2::default();
    let mut key = [0u8; 32];

    argon2.hash_password_into(
        password.as_bytes(),
        salt,
        &mut key
    ).expect("Key derivation failed");

    key
}
```

#### In Transit

- **Protocol:** TLS 1.3 (enforced)
- **Certificate:** Pinned for CKC endpoints
- **Fallback:** Refuse connection on TLS failure

### 2. Authentication

#### Device Authentication

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│   CLA   │────►│   JWT   │────►│   CKC   │
│ Device  │     │ + DevID │     │ Backend │
└─────────┘     └─────────┘     └─────────┘
```

**JWT Claims:**
```json
{
  "sub": "device_id",
  "iat": 1701234567,
  "exp": 1701320967,
  "scope": ["sync", "models", "telemetry"],
  "device_fingerprint": "sha256_hash"
}
```

**Token Refresh:**
- Tokens expire after 24 hours
- Refresh 1 hour before expiry
- Store refresh token in OS keychain

### 3. API Key Management

**Storage:**
- macOS: Keychain Services
- Windows: Credential Manager
- Linux: libsecret/Secret Service API

```rust
use keyring::Entry;

pub fn store_api_key(key: &str) -> Result<()> {
    let entry = Entry::new("cirkelline-cla", "api_key")?;
    entry.set_password(key)?;
    Ok(())
}

pub fn get_api_key() -> Result<String> {
    let entry = Entry::new("cirkelline-cla", "api_key")?;
    entry.get_password()
}
```

**NEVER:**
- Store keys in plaintext files
- Log API keys
- Include keys in error messages
- Commit keys to version control

### 4. Input Validation

#### IPC Arguments

```rust
use validator::Validate;

#[derive(Validate)]
pub struct SyncRequest {
    #[validate(length(min = 1, max = 1000))]
    pub content: String,

    #[validate(range(min = 0, max = 100))]
    pub priority: u8,

    #[validate(email)]
    pub user_email: Option<String>,
}

#[tauri::command]
pub async fn sync_data(request: SyncRequest) -> Result<(), String> {
    request.validate().map_err(|e| e.to_string())?;
    // Process validated request
    Ok(())
}
```

#### Path Traversal Prevention

```rust
pub fn safe_path_join(base: &Path, user_input: &str) -> Result<PathBuf> {
    let sanitized = user_input
        .replace("..", "")
        .replace("~", "")
        .trim_start_matches('/');

    let full_path = base.join(sanitized);

    // Verify path is still under base
    if !full_path.starts_with(base) {
        return Err(SecurityError::PathTraversal);
    }

    Ok(full_path)
}
```

### 5. Network Security

#### Endpoint Allowlist

```rust
const ALLOWED_HOSTS: &[&str] = &[
    "ckc.cirkelline.com",
    "api.cirkelline.com",
    "localhost",  // Development only
];

pub fn validate_url(url: &str) -> Result<()> {
    let parsed = Url::parse(url)?;
    let host = parsed.host_str().ok_or(SecurityError::InvalidUrl)?;

    if !ALLOWED_HOSTS.contains(&host) {
        return Err(SecurityError::UnauthorizedHost);
    }

    // Require HTTPS in production
    #[cfg(not(debug_assertions))]
    if parsed.scheme() != "https" {
        return Err(SecurityError::InsecureProtocol);
    }

    Ok(())
}
```

#### Rate Limiting (Client-side)

```rust
pub struct RateLimiter {
    requests: HashMap<String, Vec<Instant>>,
    limits: HashMap<String, (usize, Duration)>,
}

impl RateLimiter {
    pub fn check(&mut self, endpoint: &str) -> bool {
        let (max_requests, window) = self.limits
            .get(endpoint)
            .unwrap_or(&(100, Duration::from_secs(3600)));

        let now = Instant::now();
        let requests = self.requests.entry(endpoint.to_string()).or_default();

        // Remove old requests
        requests.retain(|&t| now.duration_since(t) < *window);

        if requests.len() >= *max_requests {
            return false;
        }

        requests.push(now);
        true
    }
}
```

---

## Security Checklist

### Development

- [ ] Run `cargo audit` before release
- [ ] Run `pnpm audit` before release
- [ ] No hardcoded secrets in codebase
- [ ] All user input validated
- [ ] Error messages don't leak sensitive info
- [ ] Logging doesn't include secrets

### Build

- [ ] Release builds strip debug symbols
- [ ] Code signing enabled (macOS/Windows)
- [ ] Dependencies pinned to specific versions

### Runtime

- [ ] TLS certificate validation enabled
- [ ] API keys stored in OS keychain
- [ ] Sensitive data encrypted at rest
- [ ] Memory cleared after use (secrets)

---

## Vulnerability Reporting

**Security issues should be reported privately to:**

Email: security@cirkelline.com

**Do NOT:**
- Open public GitHub issues for security bugs
- Share vulnerability details publicly before fix

**Response Timeline:**
- Acknowledgment: 24 hours
- Initial assessment: 72 hours
- Fix timeline: Based on severity

---

## Incident Response

### Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| Critical | Active exploit, data breach | Immediate |
| High | Exploitable vulnerability | 24 hours |
| Medium | Potential vulnerability | 7 days |
| Low | Hardening opportunity | 30 days |

### Response Procedure

1. **Contain:** Disable affected features if needed
2. **Assess:** Determine scope and impact
3. **Fix:** Develop and test patch
4. **Deploy:** Push update to users
5. **Notify:** Inform affected users if data compromised
6. **Review:** Post-incident analysis

---

## Compliance

### GDPR Considerations

- **Data Minimization:** Only collect necessary data
- **Purpose Limitation:** Clear purpose for all data
- **User Control:** Export, delete on request
- **Consent:** Explicit opt-in for telemetry
- **Transparency:** Privacy policy accessible

### Data Retention

| Data Type | Retention | Deletion |
|-----------|-----------|----------|
| Memories | User-controlled | On request |
| Sessions | User-controlled | On request |
| Telemetry | 90 days | Automatic |
| Logs | 30 days | Automatic |

---

## Audit Log

All security-relevant actions should be logged:

```rust
pub fn audit_log(event: SecurityEvent) {
    let entry = AuditEntry {
        timestamp: Utc::now(),
        event_type: event.event_type,
        user_id: event.user_id,
        action: event.action,
        resource: event.resource,
        outcome: event.outcome,
        ip_address: None,  // Privacy: don't log IPs
    };

    // Write to secure audit log
    append_to_audit_log(&entry);
}
```

---

## Updates

This document should be reviewed and updated:
- After any security incident
- When adding new features
- At least quarterly

**Last Updated:** 2025-12-08
**Next Review:** 2026-03-08
