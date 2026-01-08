// Tauri API wrapper for type-safe invocations

import { invoke } from "@tauri-apps/api/core";
import type {
  Settings,
  SystemMetrics,
  SyncStatus,
  ModelInfo,
  EmbeddingResult,
  TranscriptionResult,
  TextExtractionResult,
  ConnectionStatus,
} from "../types";

// Settings commands
export async function getSettings(): Promise<Settings> {
  return invoke<Settings>("get_settings");
}

export async function updateSettings(updates: Partial<Settings>): Promise<Settings> {
  return invoke<Settings>("update_settings", { newSettings: updates });
}

export async function resetSettings(): Promise<Settings> {
  return invoke<Settings>("reset_settings");
}

export async function getConnectionStatus(): Promise<ConnectionStatus> {
  return invoke<ConnectionStatus>("get_connection_status");
}

export async function testConnection(endpoint: string): Promise<ConnectionStatus> {
  return invoke<ConnectionStatus>("test_connection", { endpoint });
}

// Resource commands
export async function getSystemMetrics(): Promise<SystemMetrics> {
  return invoke<SystemMetrics>("get_system_metrics");
}

export async function canExecuteTask(
  estimatedCpuPercent: number,
  estimatedRamMb: number,
  requiresGpu: boolean
): Promise<{ can_execute: boolean; reason: string | null; estimated_wait_seconds: number | null }> {
  return invoke("can_execute_task", {
    estimatedCpuPercent,
    estimatedRamMb,
    requiresGpu,
  });
}

export interface ResourceLimits {
  max_cpu_percent: number;
  max_ram_percent: number;
  max_gpu_percent: number;
  max_disk_mb: number;
  idle_only: boolean;
  idle_threshold_seconds: number;
}

export async function getResourceLimits(): Promise<ResourceLimits> {
  return invoke<ResourceLimits>("get_resource_limits");
}

export async function setResourceLimits(limits: ResourceLimits): Promise<void> {
  return invoke("set_resource_limits", { limits });
}

// Sync commands
export async function getSyncStatus(): Promise<SyncStatus> {
  return invoke<SyncStatus>("get_sync_status");
}

export async function syncNow(): Promise<{ type: string; error?: string }> {
  return invoke("sync_now");
}

export async function getPendingChanges(): Promise<{
  uploads: number;
  downloads: number;
  conflicts: number;
}> {
  return invoke("get_pending_changes");
}

export async function resolveConflict(conflictId: string, resolution: string): Promise<void> {
  return invoke("resolve_conflict", { conflictId, resolution });
}

// AI inference commands
export async function generateEmbedding(text: string): Promise<EmbeddingResult> {
  return invoke<EmbeddingResult>("generate_embedding", { text });
}

export async function transcribeAudio(
  audioPath: string,
  language?: string
): Promise<TranscriptionResult> {
  return invoke<TranscriptionResult>("transcribe_audio", { audioPath, language });
}

export async function extractText(imagePath: string): Promise<TextExtractionResult> {
  return invoke<TextExtractionResult>("extract_text", { imagePath });
}

export async function getModelStatus(): Promise<ModelInfo[]> {
  return invoke<ModelInfo[]>("get_model_status");
}

export async function downloadModel(modelId: string): Promise<void> {
  return invoke("download_model", { modelId });
}
