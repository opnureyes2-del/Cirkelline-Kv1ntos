// Re-export all types from stores
export type { Settings } from "../stores/settingsStore";
export type { SystemMetrics } from "../stores/metricsStore";
export type { SyncStatus, SyncConflict } from "../stores/syncStore";

// Additional types

export interface LocalMemory {
  id: string;
  content: string;
  memory_type: string;
  topics: string[];
  embedding_local: number[] | null;
  importance: number;
  created_at: string;
  updated_at: string;
  synced_at: string | null;
  cloud_id: string | null;
  pending_sync: boolean;
}

export interface LocalSession {
  id: string;
  session_type: string;
  context: Record<string, unknown>;
  messages: LocalMessage[];
  created_at: string;
  updated_at: string;
  synced_at: string | null;
  cloud_id: string | null;
}

export interface LocalMessage {
  role: string;
  content: string;
  timestamp: string;
}

export interface LocalKnowledgeChunk {
  id: string;
  source_id: string;
  content: string;
  embedding_local: number[];
  metadata: Record<string, unknown>;
  priority: number;
  expires_at: string | null;
}

export interface PendingTask {
  id: string;
  task_type: TaskType;
  priority: number;
  payload: Record<string, unknown>;
  created_at: string;
  retry_count: number;
  max_retries: number;
  status: TaskStatus;
}

export type TaskType =
  | "GenerateEmbedding"
  | "TranscribeAudio"
  | "ExtractText"
  | "SyncMemory"
  | "PreloadKnowledge";

export type TaskStatus =
  | "Queued"
  | "Running"
  | "Completed"
  | { Failed: { error: string } }
  | "Cancelled";

export interface ModelInfo {
  id: string;
  name: string;
  size_mb: number;
  tier: number;
  capabilities: string[];
  downloaded: boolean;
  download_progress: number | null;
  version: string;
}

export interface EmbeddingResult {
  embedding: number[];
  model_used: string;
  processing_time_ms: number;
}

export interface TranscriptionResult {
  text: string;
  language: string | null;
  confidence: number;
  segments: TranscriptionSegment[];
  processing_time_ms: number;
}

export interface TranscriptionSegment {
  start_ms: number;
  end_ms: number;
  text: string;
  confidence: number;
}

export interface TextExtractionResult {
  text: string;
  confidence: number;
  regions: TextRegion[];
  processing_time_ms: number;
}

export interface TextRegion {
  text: string;
  bbox: BoundingBox;
  confidence: number;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface ConnectionStatus {
  connected: boolean;
  endpoint: string;
  latency_ms: number | null;
  last_check: string;
  error: string | null;
}
