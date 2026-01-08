# CLA-CKC API Integration Specification

## Version 1.0.0 | December 2024

---

## 1. Oversigt

CLA (Cirkelline Local Agent) kommunikerer med CKC (Cirkelline Knowledge Center) via REST API for at:
- Synkronisere lokale hukommelser og sessioner
- Validere bruger-tokens
- Hente model-opdateringer
- Rapportere telemetri (opt-in)

---

## 2. Base URLs

| Miljø | URL |
|-------|-----|
| Production | `https://ckc.cirkelline.com/api/cla` |
| Staging | `https://staging-ckc.cirkelline.com/api/cla` |
| Development | `http://localhost:7777/api/cla` |

---

## 3. Authentication

### 3.1 Token Format

CLA bruger JWT tokens udstedt af CKC:

```json
{
  "sub": "user-uuid",
  "iss": "ckc.cirkelline.com",
  "aud": "cla",
  "exp": 1735689600,
  "iat": 1735603200,
  "device_id": "device-fingerprint",
  "tier": "premium"
}
```

### 3.2 Header Format

```
Authorization: Bearer <jwt-token>
X-CLA-Version: 0.1.0
X-Device-ID: <device-fingerprint>
```

---

## 4. Endpoints

### 4.1 Device Registration

**POST /api/cla/devices/register**

Registrer en ny CLA-enhed.

Request:
```json
{
  "device_name": "Rasmus MacBook",
  "device_type": "macos",
  "hardware_fingerprint": "sha256-hash",
  "cla_version": "0.1.0",
  "capabilities": ["embeddings", "transcription", "ocr"]
}
```

Response:
```json
{
  "device_id": "uuid",
  "api_key": "device-specific-key",
  "sync_interval_seconds": 900,
  "features_enabled": ["sync", "inference", "telemetry"]
}
```

---

### 4.2 Sync - Pull

**GET /api/cla/sync/pull**

Hent ændringer fra CKC siden sidste sync.

Query params:
- `since`: ISO timestamp for sidste sync
- `types`: Kommasepareret liste (memories, sessions, knowledge)
- `limit`: Max antal records (default 100)

Response:
```json
{
  "memories": [
    {
      "id": "uuid",
      "content": "encrypted-content",
      "topics": ["family", "preferences"],
      "created_at": "2024-12-08T12:00:00Z",
      "updated_at": "2024-12-08T15:30:00Z"
    }
  ],
  "sessions": [...],
  "knowledge_chunks": [...],
  "sync_token": "opaque-cursor",
  "has_more": false
}
```

---

### 4.3 Sync - Push

**POST /api/cla/sync/push**

Upload lokale ændringer til CKC.

Request:
```json
{
  "memories": [
    {
      "local_id": "local-uuid",
      "content": "encrypted-content",
      "topics": ["work"],
      "embedding": [0.1, 0.2, ...],
      "created_locally_at": "2024-12-08T10:00:00Z"
    }
  ],
  "sessions": [...],
  "inference_results": [...]
}
```

Response:
```json
{
  "accepted": 15,
  "rejected": 0,
  "conflicts": [],
  "id_mappings": {
    "local-uuid-1": "server-uuid-1"
  }
}
```

---

### 4.4 Model Updates

**GET /api/cla/models/available**

Hent liste over tilgængelige modeller.

Response:
```json
{
  "models": [
    {
      "id": "all-minilm-l6-v2",
      "version": "1.0.0",
      "size_mb": 23,
      "tier": 1,
      "download_url": "https://models.cirkelline.com/...",
      "checksum_sha256": "abc123..."
    }
  ]
}
```

**GET /api/cla/models/{model_id}/download**

Download model fil (streamed).

---

### 4.5 Telemetry

**POST /api/cla/telemetry**

Send anonymiseret telemetri.

Request:
```json
{
  "session_id": "anonymous-session",
  "version": "0.1.0",
  "platform": "linux",
  "metrics": {
    "inference_count": 150,
    "avg_latency_ms": 45,
    "error_count": 2,
    "sync_count": 10
  },
  "events": [
    {"type": "app_start", "timestamp": "..."},
    {"type": "model_loaded", "model": "whisper-tiny", "timestamp": "..."}
  ]
}
```

Response:
```json
{
  "accepted": true,
  "config_updates": {
    "report_interval_seconds": 3600
  }
}
```

---

### 4.6 Health Check

**GET /api/cla/health**

Tjek CKC tilgængelighed.

Response:
```json
{
  "status": "healthy",
  "version": "1.2.34",
  "timestamp": "2024-12-08T12:00:00Z"
}
```

---

## 5. Error Handling

### 5.1 Error Response Format

```json
{
  "error": {
    "code": "SYNC_CONFLICT",
    "message": "Version conflict detected",
    "details": {...},
    "retry_after": 60
  }
}
```

### 5.2 Error Codes

| Code | HTTP Status | Beskrivelse |
|------|-------------|-------------|
| AUTH_EXPIRED | 401 | Token udløbet |
| AUTH_INVALID | 401 | Ugyldig token |
| DEVICE_REVOKED | 403 | Enhed deaktiveret |
| RATE_LIMITED | 429 | For mange requests |
| SYNC_CONFLICT | 409 | Version konflikt |
| SERVER_ERROR | 500 | Intern fejl |

---

## 6. Rate Limits

| Endpoint | Limit |
|----------|-------|
| /sync/pull | 60/time |
| /sync/push | 30/time |
| /models/download | 10/dag |
| /telemetry | 10/time |

---

## 7. Security Considerations

### 7.1 Data i Transit
- TLS 1.3 påkrævet
- Certificate pinning til CKC cert

### 7.2 Data at Rest
- Alle content felter krypteres med brugerens nøgle
- Server ser kun krypteret data
- Embeddings er ikke krypteret (tillader server-side søgning)

### 7.3 Device Trust
- Hardware fingerprint valideres
- Max 5 enheder per bruger
- Enheder kan revokeres fra CKC dashboard

---

## 8. Implementation Notes

### 8.1 Sync Strategy

1. **Initial sync**: Pull alle data ved første start
2. **Incremental sync**: Kun delta-ændringer
3. **Conflict resolution**: Server wins, client notificeres
4. **Offline queue**: Lokale ændringer køes til næste online

### 8.2 Retry Policy

```rust
let retry_delays = [1, 2, 4, 8, 16, 32]; // sekunder
let max_retries = 6;
```

### 8.3 Batch Sizes

- Max 100 memories per push
- Max 50 sessions per push
- Max 1000 embeddings per push
