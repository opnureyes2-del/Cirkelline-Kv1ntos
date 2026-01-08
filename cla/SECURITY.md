# Security Policy

**Project:** CLA (Cirkelline Local Agent) - Desktop Application
**Version:** 1.0.0
**Last Updated:** 2025-12-09
**Compliance:** OpenSSF Project Security Baseline

---

## Supported Versions

| Version | Supported          | Notes |
| ------- | ------------------ | ----- |
| 1.x.x   | :white_check_mark: | Current stable release |
| 0.x.x   | :x:                | Development versions - not supported |

---

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

**Email:** security@cirkelline.com

**Do NOT:**
- Create public GitHub issues for security vulnerabilities
- Post details on social media or public forums
- Exploit the vulnerability beyond necessary demonstration

### What to Include

1. **Description:** Clear description of the vulnerability
2. **Impact:** Potential impact if exploited
3. **Steps to Reproduce:** Detailed reproduction steps
4. **Platform:** Which OS/version affected
5. **Suggested Fix:** If you have one (optional)

### Response Timeline

| Stage | Timeline |
|-------|----------|
| Initial Response | Within 48 hours |
| Vulnerability Assessment | Within 7 days |
| Fix Development | Based on severity |
| Public Disclosure | After fix is deployed |

### Severity-Based Fix Timeline

| Severity | Fix Timeline | Examples |
|----------|--------------|----------|
| **Critical** | 24 hours | Local privilege escalation, RCE |
| **High** | 7 days | Data theft, unauthorized access |
| **Medium** | 30 days | Local info disclosure |
| **Low** | 90 days | Minor security improvements |

---

## Security Measures

### Local-First Security Model

CLA is designed with a "local-first" security approach:

- **No Cloud Storage:** User data stays on device
- **Minimal Network:** Only syncs when user initiates
- **Offline Capable:** Core features work without internet
- **User Control:** Full control over data and sync

### Application Security

- **Tauri Framework:** Rust-based security sandbox
- **Process Isolation:** Frontend/backend separation
- **IPC Security:** Validated inter-process communication
- **No Webview Exploits:** CSP and security headers

### Data Protection

- **Local Encryption:** User data encrypted at rest
- **Secure Storage:** OS keychain for credentials
- **Memory Safety:** Rust prevents buffer overflows
- **No Telemetry:** No data sent without consent

### Model Security

- **Local Inference:** AI models run locally (Candle)
- **Model Validation:** Checksums verified on download
- **Sandboxed Execution:** Models run in isolated context
- **No Model Uploads:** User data never sent to train models

### Sync Security

- **Authenticated Sync:** Device registration required
- **End-to-End Encryption:** Sync data encrypted in transit
- **Minimal Data:** Only necessary data synchronized
- **User Approval:** Explicit consent for each sync

---

## Platform-Specific Security

### Windows

- Code signing with trusted certificate
- Windows Defender compatibility
- UAC compliance for elevated operations
- Secure storage via DPAPI

### macOS

- Code signing and notarization
- App Sandbox enforcement
- Keychain integration
- Gatekeeper compliance

### Linux

- AppArmor/SELinux profiles
- XDG Base Directory compliance
- Secure credential storage
- Minimal privilege execution

---

## Security Dependencies

### Rust Dependencies

```toml
[dependencies]
tauri = "2.5.1"          # Secure app framework
candle-core = "0.8"      # Local AI inference
serde = "1.0"            # Secure serialization
tokio = "1.0"            # Async runtime
```

### Security Auditing

```bash
# Rust dependency audit
cargo audit

# Check for security advisories
cargo deny check advisories

# Memory safety check
cargo clippy --all-targets
```

---

## Secure Development Practices

### Code Review Requirements

- [ ] All IPC commands reviewed for security
- [ ] No hardcoded secrets in Rust or TypeScript
- [ ] Input validation on all Tauri commands
- [ ] Proper error handling (no info leakage)

### Build Security

- [ ] Reproducible builds
- [ ] Dependency pinning (Cargo.lock committed)
- [ ] No debug symbols in release builds
- [ ] Code signing for all platforms

### Testing Requirements

- [ ] Security-focused test cases
- [ ] IPC command fuzzing
- [ ] Memory safety verification (Miri where applicable)

---

## Known Security Considerations

### Current Limitations

1. **Sync Not Implemented:** Currently no cloud sync (planned)
2. **100+ Compiler Warnings:** Being addressed
3. **Model Download:** Uses HTTP (HTTPS planned)

### Planned Improvements

- [ ] Implement secure sync protocol
- [ ] Fix all compiler warnings
- [ ] Add model signature verification
- [ ] Implement auto-update with verification

---

## Security Contacts

| Role | Contact |
|------|---------|
| Security Team | security@cirkelline.com |
| Project Lead | rasmus@cirkelline.com |

---

## Related Documentation

- [Architecture](docs/ARCHITECTURE.md) - System architecture
- [Build Guide](docs/BUILD-GUIDE.md) - Secure build process
- [Local AI](docs/LOCAL-AI.md) - AI security model

---

*This security policy follows OpenSSF Security Policy guidelines.*
