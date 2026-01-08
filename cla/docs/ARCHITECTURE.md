# CLA Architecture Documentation

## Overview

Cirkelline Local Agent (CLA) is a lightweight desktop application that enables local AI processing while respecting system resources and user privacy. It integrates with Cirkelline Knowledge Center (CKC) for cloud synchronization.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                    (React + TailwindCSS)                        │
├─────────────────────────────────────────────────────────────────┤
│                        Tauri Bridge                             │
│                    (IPC Communication)                          │
├─────────────────────────────────────────────────────────────────┤
│                       Rust Backend                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Commands   │  │  Inference  │  │    Sync     │             │
│  │   Layer     │  │   Engine    │  │   Service   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Resource   │  │  Security   │  │  Telemetry  │             │
│  │  Manager    │  │   Module    │  │   Service   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
├─────────────────────────────────────────────────────────────────┤
│                      Storage Layer                              │
│      ┌─────────────┐              ┌─────────────┐              │
│      │  IndexedDB  │              │ Local Files │              │
│      │  (Frontend) │              │  (Models)   │              │
│      └─────────────┘              └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Frontend (React/TypeScript)

**Location:** `src/`

- **Components:** UI components for settings, status, models management
- **Stores:** Zustand stores for state management
- **Services:** Database operations, Tauri bridge communication
- **Types:** TypeScript type definitions

### 2. Backend (Rust/Tauri)

**Location:** `src-tauri/src/`

- **Commands:** Tauri command handlers for IPC
- **Models:** Data structures and domain models
- **Utils:** Resource monitoring, idle detection
- **Inference:** ONNX-based AI model execution
- **Security:** Encryption, authentication, validation
- **Error:** Comprehensive error handling and retry logic
- **Telemetry:** Privacy-respecting usage analytics

### 3. Storage

**IndexedDB (Frontend):**
- Memories, sessions, knowledge base
- Task queue, sync log
- Local embeddings cache

**File System (Backend):**
- AI model files (.onnx)
- Settings configuration
- Encryption keys

## Data Flow

### Local Processing Flow

```
User Action → Frontend → Tauri Command → Resource Check
                                              ↓
                                         [Permission?]
                                              ↓
                              ┌──────────────┴──────────────┐
                              │                             │
                            [Yes]                         [No]
                              ↓                             ↓
                        Queue Task                    Return Denial
                              ↓                      (with reason)
                        Load Model
                              ↓
                        Run Inference
                              ↓
                        Store Result
                              ↓
                        Emit Event → Frontend Update
```

### Sync Flow

```
Sync Trigger (manual/scheduled)
        ↓
  Check Connectivity
        ↓
   ┌────┴────┐
   │         │
[Online]  [Offline]
   ↓         ↓
Get Changes  Queue for later
   ↓
Resolve Conflicts (if any)
   ↓
Apply Changes (both directions)
   ↓
Update Sync Log
   ↓
Emit Completion Event
```

## Resource Management

### Conservative Defaults

| Resource | Default Limit | Max Configurable |
|----------|--------------|------------------|
| CPU | 30% | 80% |
| RAM | 20% | 50% |
| GPU | 30% | 80% |
| Disk | 2GB | Unlimited |

### Execution Decision Matrix

| Idle | Battery | Resources | Action |
|------|---------|-----------|--------|
| ✓ | AC | Available | Execute |
| ✓ | Battery (>20%) | Available | Execute (if allowed) |
| ✓ | Battery (<20%) | Available | Deny |
| ✗ | Any | Any | Deny (if idle_only) |
| Any | Any | Exceeded | Deny |

## Model Tiers

### Tier 1 - Essential (81MB total)

Always downloaded, core functionality:

| Model | Size | Capabilities |
|-------|------|--------------|
| all-MiniLM-L6-v2 | 23MB | Text embeddings (384-dim) |
| Whisper Tiny | 39MB | Audio transcription |
| PaddleOCR Mobile | 19MB | OCR text extraction |

### Tier 2 - Standard (602MB total)

Optional, better quality:

| Model | Size | Capabilities |
|-------|------|--------------|
| Whisper Small | 244MB | Better transcription |
| PaddleOCR Server | 120MB | Better OCR |
| Sentence-T5-Base | 238MB | Better embeddings |

### Tier 3 - Professional (2.4GB total)

Opt-in, highest quality:

| Model | Size | Capabilities |
|-------|------|--------------|
| Whisper Medium | 769MB | Professional transcription |
| BGE-Large-EN | 335MB | Premium embeddings |
| LayoutLM | 430MB | Document understanding |
| LLaMA-2-7B-Q4 | 4GB | Local LLM (optional) |

## Security Architecture

### Encryption

- **At Rest:** AES-256-GCM for sensitive data
- **Key Derivation:** Argon2id from user password
- **In Transit:** HTTPS/TLS 1.3 to CKC

### Authentication

- JWT-based authentication with CKC
- Token refresh before expiry
- Login attempt lockout (3 failures)

### Input Validation

- Path traversal prevention
- Null byte injection protection
- Email format validation
- String length limits

### Endpoint Security

- Allowlist-based URL validation
- Only CKC endpoints allowed
- localhost for development

## Error Handling

### Error Categories

| Category | Retry | Fallback |
|----------|-------|----------|
| Network | Yes (exponential backoff) | Offline mode |
| Storage | Yes (limited) | Report to user |
| Inference | Yes (once) | Skip task |
| Security | No | Deny operation |
| Config | No | Use defaults |

### Recovery Actions

1. **Retry:** Automatic with exponential backoff
2. **UseFallback:** Switch to offline/cached data
3. **RequireUserAction:** Show dialog, wait for user
4. **Fatal:** Terminate operation, log error

## Telemetry (Opt-in)

### Collected (when enabled)

- Performance metrics (latency percentiles)
- Error type counts (anonymized)
- Feature usage counts
- Resource utilization averages

### Never Collected

- Personal information
- File contents or paths
- IP addresses
- Conversation content
- Memory contents

## Directory Structure

```
cla/
├── src/                          # Frontend (React/TypeScript)
│   ├── components/               # UI components
│   ├── stores/                   # Zustand state stores
│   ├── services/                 # Database, Tauri bridge
│   ├── tests/                    # Frontend tests
│   └── types/                    # TypeScript definitions
├── src-tauri/                    # Backend (Rust)
│   ├── src/
│   │   ├── commands/             # Tauri command handlers
│   │   ├── models/               # Data models
│   │   ├── utils/                # Resource monitoring
│   │   ├── inference/            # AI model execution
│   │   ├── security/             # Encryption, auth
│   │   ├── error/                # Error handling
│   │   └── telemetry/            # Analytics
│   └── tests/                    # Rust tests
├── docs/                         # Documentation
└── .github/workflows/            # CI/CD pipelines
```

## Integration with CKC

### API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /api/cla/health` | Health check (no auth) |
| `POST /api/cla/devices/register` | Device registration |
| `POST /api/cla/sync` | Bidirectional sync |
| `GET /api/cla/models` | Model catalog |
| `POST /api/cla/telemetry` | Anonymous telemetry |

See `docs/CLA-CKC-INTEGRATION.md` for detailed API documentation.

### Sync Protocol

1. CLA sends local changes with timestamps
2. CKC responds with remote changes
3. Conflicts resolved by latest timestamp
4. Both sides confirm completion

## Performance Targets

| Metric | Target |
|--------|--------|
| App startup | < 2 seconds |
| Embedding generation | < 100ms (Tier 1) |
| Audio transcription | < 5x realtime |
| OCR processing | < 500ms per page |
| Memory usage (idle) | < 150MB |
| Memory usage (active) | < 500MB |
| Disk space (Tier 1) | < 200MB |
