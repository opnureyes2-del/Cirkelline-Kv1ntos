# Changelog

All notable changes to Cirkelline Local Agent (CLA) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- OCR model integration (PaddleOCR)
- Full bidirectional sync
- Organic Device Contribution system
- I18N support (DA, EN, DE)

---

## [0.1.0] - 2025-12-08

### Added

#### Core Infrastructure
- Tauri 2.0 desktop application framework
- React 18 + TypeScript frontend
- Rust backend with async support
- Cross-platform build support (Linux .deb, macOS, Windows)

#### AI Inference
- ONNX Runtime integration (ort 2.0.0-rc.10)
- MiniLM L6 v2 embedding model (384-dim, 87MB)
- Whisper Tiny EN transcription model (146MB)
- Model download script (`scripts/download-models.sh`)
- Lazy model loading for memory efficiency

#### CKC Integration
- Device registration endpoint (`POST /api/cla/devices/register`)
- Health check endpoint (`GET /api/cla/health`)
- Models catalog endpoint (`GET /api/cla/models`)
- Sync endpoint (`POST /api/cla/sync`)
- Telemetry endpoint (`POST /api/cla/telemetry`)
- JWT-based device authentication
- Rate limiting (60 sync/hr, 100 models/hr, 10 telemetry/hr)

#### Resource Management
- System metrics monitoring (CPU, RAM, GPU, disk)
- Idle detection system
- Battery awareness
- Configurable resource limits

#### Settings
- Conservative default settings
- Offline mode toggle
- Sync interval configuration
- Model tier selection (Tier 1/2/3)

#### Documentation
- README.md with quick start
- API.md with full command reference
- ARCHITECTURE.md with system design
- DEVELOPMENT.md with contribution guide
- PERFORMANCE.md with optimization strategies
- CLA-CKC-INTEGRATION.md with API specs
- ORGANIC-CONTRIBUTION-ARCHITECTURE.md
- FASE-4.1 and FASE-4.2 specification documents

### Technical Details
- Binary size: 8.7MB (release)
- Package size: 83MB (.deb with models)
- Models total: 231MB (Tier 1)
- Supported platforms: Linux (primary), macOS, Windows

### Known Issues
- 100 compiler warnings (dead code, unused variables)
- OCR model not yet integrated
- Sync conflict resolution UI pending
- No auto-update mechanism

---

## Version Naming Convention

- **Major (X.0.0):** Breaking changes, major features
- **Minor (0.X.0):** New features, backward compatible
- **Patch (0.0.X):** Bug fixes, minor improvements

## Links

- [Roadmap](./docs/ROADMAP.md)
- [Documentation](./docs/)
- [Issues](https://github.com/cirkelline/cla/issues)

---

[Unreleased]: https://github.com/cirkelline/cla/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/cirkelline/cla/releases/tag/v0.1.0
