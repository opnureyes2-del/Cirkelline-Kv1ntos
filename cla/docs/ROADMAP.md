# CLA Development Roadmap

## Version History & Planning

**Current Version:** 0.1.0 (Alpha)
**Last Updated:** 2025-12-08

---

## Completed Milestones

### v0.1.0 - Foundation (December 2025)

- [x] Tauri 2.0 project setup
- [x] React + TypeScript frontend scaffolding
- [x] Rust backend structure
- [x] ONNX Runtime integration
- [x] MiniLM embedding model (Tier 1)
- [x] Whisper Tiny EN transcription (Tier 1)
- [x] CKC API endpoints implementation
- [x] Device registration flow
- [x] Sync protocol (basic)
- [x] Telemetry system (anonymous)
- [x] Resource monitoring
- [x] Settings management
- [x] Build pipeline (.deb package)

---

## Current Sprint

### v0.2.0 - Documentation & Quality (Q1 2025)

| Task | Status | Priority |
|------|--------|----------|
| CHANGELOG.md | In Progress | P1 |
| I18N/L10N setup | Pending | P1 |
| SECURITY.md | Pending | P1 |
| TEST.md | Pending | P2 |
| Automated doc checks | Pending | P3 |

---

## Planned Releases

### v0.3.0 - Enhanced Inference (Q1 2025)

- [ ] OCR model integration (PaddleOCR)
- [ ] Batch embedding processing
- [ ] Model download progress UI
- [ ] Tier 2 model support (opt-in)
- [ ] Inference queue management
- [ ] Background task processing

### v0.4.0 - Sync & Offline (Q2 2025)

- [ ] Full bidirectional sync
- [ ] Conflict resolution UI
- [ ] Offline mode improvements
- [ ] Delta sync (changed-only)
- [ ] Sync queue persistence
- [ ] Network status awareness

### v0.5.0 - Organic Contribution (Q2 2025)

- [ ] Contribution permission engine
- [ ] Resource analyzer (advanced)
- [ ] Time window scheduling
- [ ] Task type filtering
- [ ] Contribution statistics
- [ ] Real-time contribution indicator

### v0.6.0 - UX Polish (Q3 2025)

- [ ] System tray integration
- [ ] Native notifications
- [ ] Keyboard shortcuts
- [ ] Dark/light theme
- [ ] Onboarding wizard
- [ ] Tutorial tooltips

### v1.0.0 - Production Release (Q3 2025)

- [ ] Full I18N (DA, EN, DE)
- [ ] Auto-update system
- [ ] Crash reporting
- [ ] Performance profiling
- [ ] Security audit
- [ ] App Store submissions (macOS)
- [ ] Microsoft Store submission

---

## Technical Debt

| Item | Impact | Effort |
|------|--------|--------|
| Remove dead code warnings (100+) | Low | Low |
| Add comprehensive unit tests | Medium | High |
| Improve error messages | Medium | Medium |
| Database migration system | High | Medium |
| CI/CD pipeline setup | High | Medium |

---

## Architecture Evolution

### Phase 1: Current (v0.1.x)
```
CLA ─────► CKC Backend
  │
  └── Local ONNX Models
```

### Phase 2: Enhanced (v0.5.x)
```
CLA ─────► CKC Backend
  │            │
  │            ▼
  │        CKC Task Queue
  │            │
  └── Local ONNX Models
           │
           ▼
      Contribution Pool
```

### Phase 3: Production (v1.0.x)
```
┌──────────────────────────────────────┐
│           CLA Network                │
│  ┌─────┐  ┌─────┐  ┌─────┐          │
│  │CLA 1│  │CLA 2│  │CLA n│          │
│  └──┬──┘  └──┬──┘  └──┬──┘          │
│     └────────┼────────┘              │
│              ▼                       │
│      CKC Load Balancer               │
│              │                       │
│     ┌────────┼────────┐              │
│     ▼        ▼        ▼              │
│   CKC 1    CKC 2    CKC n            │
└──────────────────────────────────────┘
```

---

## Quality Gates

### Before v0.5.0
- [ ] 80%+ test coverage
- [ ] All P1 documentation complete
- [ ] Security review passed
- [ ] Performance benchmarks met

### Before v1.0.0
- [ ] 90%+ test coverage
- [ ] I18N complete (3 languages)
- [ ] Accessibility audit (WCAG 2.1 AA)
- [ ] External security audit
- [ ] Load testing (1000+ concurrent users)

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| ONNX model compatibility | Medium | High | Pin versions, test matrix |
| Cross-platform issues | Medium | Medium | CI testing on all platforms |
| CKC API changes | Low | Medium | Versioned API, deprecation warnings |
| Model size bloat | Medium | Low | Tier system, optional downloads |

---

## Dependencies

### Critical
- `ort` 2.0.0 - ONNX Runtime
- `tauri` 2.0.0 - Desktop framework
- `reqwest` - HTTP client

### Monitor for Updates
- `tokenizers` - HuggingFace tokenization
- `serde` - Serialization
- React 18 - Frontend framework

---

## Contributing

See [DEVELOPMENT.md](./DEVELOPMENT.md) for contribution guidelines.

## Contact

- **Product Owner:** Rasmus
- **Tech Lead:** TBD
- **Repository:** cirkelline-system/cla
