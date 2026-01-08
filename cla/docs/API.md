# CLA API Reference

## Tauri Commands

All commands are invoked via `@tauri-apps/api/core`:

```typescript
import { invoke } from '@tauri-apps/api/core';
const result = await invoke<ReturnType>('command_name', { args });
```

---

## Settings Commands

### `get_settings`

Get current application settings.

**Returns:** `Settings`

```typescript
interface Settings {
  max_cpu_percent: number;       // 0-100
  max_ram_percent: number;       // 0-100
  max_gpu_percent: number;       // 0-100
  max_disk_mb: number;           // Megabytes
  idle_only: boolean;            // Only run when idle
  idle_threshold_seconds: number; // Seconds until considered idle
  paused: boolean;               // Processing paused
  auto_start: boolean;           // Start with OS
  run_on_battery: boolean;       // Allow battery operation
  min_battery_percent: number;   // Minimum battery level
  sync_interval_minutes: number; // Auto-sync interval
  sync_on_startup: boolean;      // Sync when app starts
  offline_mode: boolean;         // Force offline
  enable_transcription: boolean; // Enable Whisper
  enable_ocr: boolean;           // Enable OCR
  enable_embeddings: boolean;    // Enable embeddings
  download_tier2_models: boolean;
  download_tier3_models: boolean;
  ckc_endpoint: string;          // CKC server URL
  api_key: string | null;        // API key if needed
}
```

### `save_settings`

Save updated settings.

**Arguments:**
- `settings: Settings` - Complete settings object

**Returns:** `void`

### `reset_settings`

Reset all settings to defaults.

**Returns:** `Settings`

---

## Resource Commands

### `get_system_metrics`

Get current system resource usage.

**Returns:** `SystemMetrics`

```typescript
interface SystemMetrics {
  cpu_usage_percent: number;
  cpu_count: number;
  ram_used_mb: number;
  ram_total_mb: number;
  ram_usage_percent: number;
  gpu_available: boolean;
  gpu_usage_percent: number | null;
  gpu_memory_used_mb: number | null;
  gpu_memory_total_mb: number | null;
  disk_used_mb: number;
  disk_available_mb: number;
  on_battery: boolean;
  battery_percent: number | null;
  idle_seconds: number;
  is_idle: boolean;
  timestamp: string;  // ISO 8601
}
```

### `can_execute_task`

Check if a task can be executed with current resources.

**Arguments:**
- `cpu_estimate: number` - Estimated CPU usage (%)
- `ram_estimate_mb: number` - Estimated RAM usage (MB)
- `requires_gpu: boolean` - Whether GPU is needed

**Returns:** `ExecutionPermission`

```typescript
interface ExecutionPermission {
  granted: boolean;
  reason?: string;  // If denied
  suggested_wait_seconds?: number;  // If temporary
}
```

---

## Sync Commands

### `get_sync_status`

Get current synchronization status.

**Returns:** `SyncStatus`

```typescript
interface SyncStatus {
  is_syncing: boolean;
  last_sync: string | null;      // ISO 8601
  last_sync_result: 'success' | 'error' | null;
  pending_uploads: number;
  pending_downloads: number;
  conflicts: SyncConflict[];
  bytes_uploaded: number;
  bytes_downloaded: number;
}

interface SyncConflict {
  id: string;
  type: 'memory' | 'session' | 'knowledge';
  local_version: string;
  remote_version: string;
  conflict_at: string;
}
```

### `start_sync`

Start a synchronization with CKC.

**Returns:** `SyncResult`

```typescript
interface SyncResult {
  success: boolean;
  uploaded: number;
  downloaded: number;
  conflicts: number;
  duration_ms: number;
  error?: string;
}
```

### `resolve_conflict`

Resolve a sync conflict.

**Arguments:**
- `conflict_id: string`
- `resolution: 'keep_local' | 'keep_remote' | 'keep_both'`

**Returns:** `void`

---

## Model Commands

### `get_model_status`

Get status of all AI models.

**Returns:** `ModelInfo[]`

```typescript
interface ModelInfo {
  id: string;
  name: string;
  size_mb: number;
  tier: 1 | 2 | 3;
  capabilities: string[];
  downloaded: boolean;
  download_progress: number | null;  // 0-100
  version: string;
}
```

### `download_model`

Download a specific model.

**Arguments:**
- `model_id: string`

**Returns:** `void` (emits progress events)

### `delete_model`

Delete a downloaded model.

**Arguments:**
- `model_id: string`

**Returns:** `void`

---

## Inference Commands

### `generate_embedding`

Generate text embedding locally.

**Arguments:**
- `text: string` - Text to embed
- `model_id?: string` - Model to use (default: tier 1)

**Returns:** `EmbeddingResult`

```typescript
interface EmbeddingResult {
  embedding: number[];  // 384 dimensions for MiniLM
  model_id: string;
  processing_time_ms: number;
}
```

### `transcribe_audio`

Transcribe audio file.

**Arguments:**
- `audio_path: string` - Path to audio file
- `language?: string` - Language code (auto-detect if omitted)

**Returns:** `TranscriptionResult`

```typescript
interface TranscriptionResult {
  text: string;
  language: string;
  confidence: number;
  segments: TranscriptSegment[];
  processing_time_ms: number;
}

interface TranscriptSegment {
  start_time: number;  // seconds
  end_time: number;
  text: string;
  confidence: number;
}
```

### `extract_text_ocr`

Extract text from image using OCR.

**Arguments:**
- `image_path: string` - Path to image file

**Returns:** `OcrResult`

```typescript
interface OcrResult {
  text: string;
  confidence: number;
  bounding_boxes: BoundingBox[];
  processing_time_ms: number;
}

interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  text: string;
  confidence: number;
}
```

---

## Task Queue Commands

### `queue_task`

Add a task to the processing queue.

**Arguments:**
- `task: PendingTask`

```typescript
interface PendingTask {
  id?: string;  // Generated if omitted
  task_type: 'GenerateEmbedding' | 'Transcribe' | 'OCR' | 'Custom';
  priority: number;  // 1-10, higher = more urgent
  payload: Record<string, unknown>;
  max_retries?: number;
}
```

**Returns:** `string` (task ID)

### `get_task_status`

Get status of a queued task.

**Arguments:**
- `task_id: string`

**Returns:** `TaskStatus`

```typescript
interface TaskStatus {
  id: string;
  status: 'Queued' | 'Running' | 'Completed' | 'Failed' | 'Cancelled';
  progress: number | null;  // 0-100
  result?: unknown;
  error?: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}
```

### `cancel_task`

Cancel a pending or running task.

**Arguments:**
- `task_id: string`

**Returns:** `boolean` (success)

---

## Telemetry Commands

### `get_telemetry_status`

Get telemetry configuration and consent status.

**Returns:** `TelemetryStatus`

```typescript
interface TelemetryStatus {
  enabled: boolean;
  consent_given: boolean;
  consent_timestamp: string | null;
  last_report: string | null;
}
```

### `set_telemetry_consent`

Update telemetry consent.

**Arguments:**
- `consented: boolean`

**Returns:** `void`

---

## Health Commands

### `get_health`

Get application health status.

**Returns:** `HealthStatus`

```typescript
interface HealthStatus {
  state: 'healthy' | 'degraded' | 'unhealthy';
  components: Record<string, ComponentHealth>;
  error_count: number;
  last_error: string | null;
  uptime_seconds: number;
}

interface ComponentHealth {
  state: 'healthy' | 'degraded' | 'unhealthy';
  message: string | null;
  last_check: string;
}
```

---

## Events

Listen to events via `@tauri-apps/api/event`:

```typescript
import { listen } from '@tauri-apps/api/event';

await listen('event-name', (event) => {
  console.log(event.payload);
});
```

### Available Events

| Event | Payload | Description |
|-------|---------|-------------|
| `metrics-update` | `SystemMetrics` | Resource usage update |
| `sync-progress` | `{ progress: number, stage: string }` | Sync progress |
| `sync-completed` | `SyncResult` | Sync finished |
| `model-download-progress` | `{ model_id: string, progress: number }` | Download progress |
| `task-progress` | `{ task_id: string, progress: number }` | Task progress |
| `task-completed` | `{ task_id: string, result: unknown }` | Task finished |
| `task-failed` | `{ task_id: string, error: string }` | Task failed |
| `health-changed` | `HealthStatus` | Health status change |

---

## Error Handling

All commands may throw errors with this structure:

```typescript
interface ClaError {
  type: string;  // Error category
  message: string;  // Human-readable message
  code?: string;  // Error code
  recoverable: boolean;
  recovery_hint?: string;
}
```

Example error handling:

```typescript
try {
  await invoke('start_sync');
} catch (error) {
  const claError = error as ClaError;
  if (claError.recoverable) {
    console.warn(`Recoverable error: ${claError.message}`);
    // Show notification, retry later
  } else {
    console.error(`Fatal error: ${claError.message}`);
    // Show error dialog
  }
}
```
