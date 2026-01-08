// Test setup for Vitest
// Mocks Tauri APIs and IndexedDB for browser-less testing

import { vi } from 'vitest';
import 'fake-indexeddb/auto';

// Mock Tauri API
vi.mock('@tauri-apps/api/core', () => ({
  invoke: vi.fn().mockImplementation((cmd: string, args?: unknown) => {
    console.log(`[Mock] invoke: ${cmd}`, args);

    switch (cmd) {
      case 'get_settings':
        return Promise.resolve({
          max_cpu_percent: 30,
          max_ram_percent: 20,
          max_gpu_percent: 30,
          max_disk_mb: 2000,
          idle_only: true,
          idle_threshold_seconds: 120,
          paused: false,
          auto_start: false,
          run_on_battery: false,
          min_battery_percent: 20,
          sync_interval_minutes: 15,
          sync_on_startup: true,
          offline_mode: false,
          enable_transcription: true,
          enable_ocr: true,
          enable_embeddings: true,
          download_tier2_models: false,
          download_tier3_models: false,
          ckc_endpoint: 'https://ckc.cirkelline.com',
          api_key: null,
        });

      case 'get_system_metrics':
        return Promise.resolve({
          cpu_usage_percent: 15,
          cpu_count: 8,
          ram_used_mb: 4096,
          ram_total_mb: 16384,
          ram_usage_percent: 25,
          gpu_available: false,
          gpu_usage_percent: null,
          gpu_memory_used_mb: null,
          gpu_memory_total_mb: null,
          disk_used_mb: 500,
          disk_available_mb: 100000,
          on_battery: false,
          battery_percent: null,
          idle_seconds: 150,
          is_idle: true,
          timestamp: new Date().toISOString(),
        });

      case 'get_sync_status':
        return Promise.resolve({
          is_syncing: false,
          last_sync: null,
          last_sync_result: null,
          pending_uploads: 0,
          pending_downloads: 0,
          conflicts: [],
          bytes_uploaded: 0,
          bytes_downloaded: 0,
        });

      case 'get_model_status':
        return Promise.resolve([
          {
            id: 'all-minilm-l6-v2',
            name: 'MiniLM Embeddings',
            size_mb: 23,
            tier: 1,
            capabilities: ['embeddings'],
            downloaded: true,
            download_progress: null,
            version: '1.0.0',
          },
        ]);

      default:
        return Promise.resolve(null);
    }
  }),
}));

// Mock Tauri event API
vi.mock('@tauri-apps/api/event', () => ({
  listen: vi.fn().mockImplementation((event: string, _handler: (e: unknown) => void) => {
    console.log(`[Mock] listening to: ${event}`);
    return Promise.resolve(() => {});
  }),
  emit: vi.fn(),
}));

// Mock window.__TAURI__
Object.defineProperty(window, '__TAURI__', {
  value: {
    invoke: vi.fn(),
  },
});

// Suppress console during tests (optional)
// vi.spyOn(console, 'log').mockImplementation(() => {});
// vi.spyOn(console, 'warn').mockImplementation(() => {});

// Global test utilities
export function createMockMemory(overrides = {}) {
  return {
    id: `mem-${Date.now()}`,
    content: 'Test memory',
    memory_type: 'fact',
    topics: ['test'],
    embedding_local: null,
    importance: 0.5,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    synced_at: null,
    cloud_id: null,
    pending_sync: true,
    ...overrides,
  };
}

export function createMockSession(overrides = {}) {
  return {
    id: `sess-${Date.now()}`,
    session_type: 'chat',
    context: {},
    messages: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    synced_at: null,
    cloud_id: null,
    ...overrides,
  };
}

export function createMockTask(overrides = {}) {
  return {
    id: `task-${Date.now()}`,
    task_type: 'GenerateEmbedding',
    priority: 5,
    payload: {},
    created_at: new Date().toISOString(),
    retry_count: 0,
    max_retries: 3,
    status: 'Queued',
    ...overrides,
  };
}
