# CLA-CKC Integration Guide

## Overview

Cirkelline Local Agent (CLA) integrates with Cirkelline Knowledge Center (CKC) backend via REST API.

## Architecture

```
┌────────────────────┐              ┌────────────────────┐
│   CLA Desktop      │    HTTPS     │   CKC Backend      │
│   (Tauri + Rust)   │◄────────────►│   (FastAPI)        │
│                    │              │                    │
│  - Local AI        │   /api/cla/* │  - User Auth       │
│  - Embeddings      │              │  - Data Storage    │
│  - Transcription   │              │  - Model Catalog   │
│  - Sync Engine     │              │  - Rate Limiting   │
└────────────────────┘              └────────────────────┘
```

## Endpoints

Base URL: `http://localhost:7779/api/cla` (dev) | `https://ckc.cirkelline.com/api/cla` (prod)

### 1. Health Check
```
GET /health
```

No authentication required.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-08T22:30:00Z",
  "services": {
    "database": "healthy",
    "storage": "healthy",
    "models": "healthy"
  }
}
```

### 2. Device Registration
```
POST /devices/register
Authorization: Bearer <user_jwt_token>
```

Registers a new CLA device for a user.

**Request:**
```json
{
  "device_name": "Rasmus MacBook Pro",
  "device_type": "macos",
  "hardware_fingerprint": "<unique_hash>",
  "cla_version": "0.1.0",
  "capabilities": ["embeddings", "transcription"]
}
```

**Response:**
```json
{
  "device_id": "34d55bd2-17b5-4d2a-8e3e-e15baf76843e",
  "api_key": "14ab0c898560ee2120f19819dfacc613...",
  "sync_interval_seconds": 900,
  "features_enabled": ["sync", "inference", "telemetry"]
}
```

### 3. Get Available Models
```
GET /models
Authorization: Bearer <api_key>
X-Device-ID: <device_id>
X-CLA-Version: <version>
```

**Query Parameters:**
- `tier` (optional): Filter by tier (1, 2, or 3)
- `capability` (optional): Filter by capability (embeddings, transcription, ocr)

**Response:**
```json
{
  "models": [
    {
      "id": "all-minilm-l6-v2",
      "name": "MiniLM L6 v2",
      "version": "1.0.0",
      "size_mb": 87,
      "tier": 1,
      "download_url": "https://huggingface.co/...",
      "checksum_sha256": "",
      "capabilities": ["embeddings"]
    }
  ],
  "last_updated": "2025-12-08T22:30:00Z"
}
```

### 4. Bidirectional Sync
```
POST /sync
Authorization: Bearer <api_key>
X-Device-ID: <device_id>
X-CLA-Version: <version>
Content-Type: application/json
```

**Request:**
```json
{
  "device_id": "34d55bd2-...",
  "last_sync_token": null,
  "memories": [
    {
      "local_id": "mem_001",
      "content": "<encrypted_content>",
      "topics": ["personal", "notes"],
      "embedding": [0.1, 0.2, ...],
      "created_at": "2025-12-08T22:30:00Z"
    }
  ],
  "sessions": [
    {
      "local_id": "sess_001",
      "name": "Chat Session",
      "messages_count": 15,
      "created_at": "2025-12-08T22:30:00Z"
    }
  ],
  "inference_results": [
    {
      "model_id": "all-minilm-l6-v2",
      "input_tokens": 150,
      "processing_time_ms": 45
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "server_memories": [],
  "server_sessions": [],
  "conflicts": [],
  "sync_token": "9c99340e70fc31ee28fc9ba2fc3924aa",
  "id_mappings": {
    "mem_001": "a0bb7802-3f4a-4efe-8491-83bd4eaf72ac"
  },
  "timestamp": "2025-12-08T22:30:00Z"
}
```

### 5. Anonymous Telemetry
```
POST /telemetry
Content-Type: application/json
```

No authentication required (anonymous).

**Request:**
```json
{
  "session_id": "anon_session_123",
  "version": "0.1.0",
  "platform": "linux",
  "metrics": {
    "inference_count": 15,
    "avg_latency_ms": 42,
    "error_count": 0
  },
  "events": [
    {
      "type": "model_loaded",
      "timestamp": "2025-12-08T22:30:00Z",
      "data": {"model_id": "all-minilm-l6-v2"}
    }
  ]
}
```

**Response:**
```json
{
  "accepted": true,
  "config_updates": {
    "report_interval_seconds": 3600,
    "enabled_metrics": ["inference_count", "avg_latency_ms", "error_count"]
  }
}
```

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| /sync | 60 req | 1 hour |
| /models | 100 req | 1 hour |
| /telemetry | 10 req | 1 hour |

Exceeded limits return `429 Too Many Requests`:
```json
{
  "code": "RATE_LIMITED",
  "message": "Too many requests",
  "retry_after": 60
}
```

## Security

### Authentication Flow
1. User logs in via CKC web interface
2. CLA registers device with user's JWT token
3. CLA receives device-specific API key
4. All subsequent requests use API key + Device ID

### Headers
```
Authorization: Bearer <api_key>
X-Device-ID: <device_id>
X-CLA-Version: <version>
```

### Data Encryption
- All sync data should be encrypted client-side
- Use AES-256-GCM for local storage
- TLS 1.3 enforced at infrastructure level

## Rust Integration

### Tauri Command Example
```rust
#[tauri::command]
pub async fn sync_now(state: State<'_, AppState>) -> Result<SyncResult, String> {
    let settings = state.settings.read().await;

    let client = reqwest::Client::new();
    let response = client
        .post(format!("{}/api/cla/sync", settings.ckc_endpoint))
        .header("Authorization", format!("Bearer {}", settings.api_key))
        .header("X-Device-ID", &settings.device_id)
        .json(&sync_request)
        .send()
        .await?;

    Ok(response.json().await?)
}
```

### Frontend Call
```typescript
import { invoke } from '@tauri-apps/api/core';

const result = await invoke<SyncResult>('sync_now');
```

## Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| AUTH_MISSING | 401 | Authorization header required |
| AUTH_INVALID | 401 | Invalid or expired token |
| DEVICE_ID_MISSING | 400 | X-Device-ID header required |
| RATE_LIMITED | 429 | Too many requests |

## Testing

### Manual Test
```bash
# Register device
curl -X POST http://localhost:7779/api/cla/devices/register \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{"device_name":"Test","device_type":"linux","hardware_fingerprint":"abc123","cla_version":"0.1.0"}'

# Get models
curl http://localhost:7779/api/cla/models \
  -H "Authorization: Bearer <api_key>" \
  -H "X-Device-ID: <device_id>"

# Sync
curl -X POST http://localhost:7779/api/cla/sync \
  -H "Authorization: Bearer <api_key>" \
  -H "X-Device-ID: <device_id>" \
  -H "Content-Type: application/json" \
  -d '{"device_id":"<device_id>","memories":[],"sessions":[]}'
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-08 | Initial release with 5 endpoints |

## Files

- CKC Backend: `Cosmic-Library-main/backend/api/cla_endpoints.py`
- CLA Rust: `cirkelline-system/cla/src-tauri/src/commands/sync.rs`
- Device Config: `/tmp/cla-register.json` (dev)
