import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";

// Types matching Rust backend
export type AutonomyLevel = "Supervised" | "Assisted" | "Autonomous" | "FullAutonomy";
export type SyncStatus = "Connected" | "Syncing" | "Disconnected" | { Error: string };

export interface CommanderStatus {
  is_running: boolean;
  uptime_seconds: number;
  tasks_completed: number;
  tasks_pending: number;
  last_decision_at: string | null;
  sync_status: SyncStatus;
  autonomy_level: AutonomyLevel;
}

export interface CommanderConfig {
  enabled: boolean;
  autonomy_level: AutonomyLevel;
  scan_interval_minutes: number;
  max_concurrent_tasks: number;
  relevance_threshold: number;
  sources: string[];
  alert_on_critical: boolean;
  sync_to_cosmic_library: boolean;
  offline_mode_enabled: boolean;
}

export interface QueueStatus {
  total: number;
  pending: number;
  running: number;
  by_priority: {
    critical: number;
    high: number;
    normal: number;
    low: number;
    background: number;
  };
}

export interface SyncStats {
  status: SyncStatus;
  queue_size: number;
  last_sync: string | null;
}

export interface ResearchFinding {
  id: string;
  source: string;
  title: string;
  summary: string;
  relevance_score: number;
  discovered_at: string;
  tags: string[];
  url: string | null;
}

interface CommanderState {
  status: CommanderStatus | null;
  config: CommanderConfig | null;
  queueStatus: QueueStatus | null;
  syncStats: SyncStats | null;
  findings: ResearchFinding[];
  isLoading: boolean;
  error: string | null;

  // Actions
  loadStatus: () => Promise<void>;
  loadConfig: () => Promise<void>;
  loadQueueStatus: () => Promise<void>;
  loadSyncStats: () => Promise<void>;
  loadFindings: (limit?: number) => Promise<void>;
  startCommander: () => Promise<void>;
  stopCommander: () => Promise<void>;
  updateConfig: (config: CommanderConfig) => Promise<void>;
  setAutonomyLevel: (level: string) => Promise<void>;
  addResearchTask: (topic: string, priority: string) => Promise<string>;
  forceSync: () => Promise<void>;
  refreshAll: () => Promise<void>;
}

const defaultConfig: CommanderConfig = {
  enabled: true,
  autonomy_level: "Supervised",
  scan_interval_minutes: 30,
  max_concurrent_tasks: 5,
  relevance_threshold: 0.6,
  sources: ["GitHub", "ArXiv"],
  alert_on_critical: true,
  sync_to_cosmic_library: true,
  offline_mode_enabled: true,
};

export const useCommanderStore = create<CommanderState>((set, get) => ({
  status: null,
  config: null,
  queueStatus: null,
  syncStats: null,
  findings: [],
  isLoading: false,
  error: null,

  loadStatus: async () => {
    try {
      const status = await invoke<CommanderStatus>("get_commander_status");
      set({ status, error: null });
    } catch (error) {
      set({ error: String(error) });
      console.error("Failed to load commander status:", error);
    }
  },

  loadConfig: async () => {
    try {
      const config = await invoke<CommanderConfig>("get_commander_config");
      set({ config, error: null });
    } catch (error) {
      set({ config: defaultConfig, error: String(error) });
      console.error("Failed to load commander config:", error);
    }
  },

  loadQueueStatus: async () => {
    try {
      const queueStatus = await invoke<QueueStatus>("get_task_queue_status");
      set({ queueStatus, error: null });
    } catch (error) {
      console.error("Failed to load queue status:", error);
    }
  },

  loadSyncStats: async () => {
    try {
      const syncStats = await invoke<SyncStats>("get_sync_stats");
      set({ syncStats, error: null });
    } catch (error) {
      console.error("Failed to load sync stats:", error);
    }
  },

  loadFindings: async (limit = 10) => {
    try {
      const findings = await invoke<ResearchFinding[]>("get_recent_findings", { limit });
      set({ findings, error: null });
    } catch (error) {
      console.error("Failed to load findings:", error);
    }
  },

  startCommander: async () => {
    set({ isLoading: true, error: null });
    try {
      await invoke("start_commander");
      await get().loadStatus();
    } catch (error) {
      set({ error: String(error) });
      console.error("Failed to start commander:", error);
    } finally {
      set({ isLoading: false });
    }
  },

  stopCommander: async () => {
    set({ isLoading: true, error: null });
    try {
      await invoke("stop_commander");
      await get().loadStatus();
    } catch (error) {
      set({ error: String(error) });
      console.error("Failed to stop commander:", error);
    } finally {
      set({ isLoading: false });
    }
  },

  updateConfig: async (config) => {
    try {
      await invoke("update_commander_config", { newConfig: config });
      set({ config, error: null });
    } catch (error) {
      set({ error: String(error) });
      console.error("Failed to update config:", error);
    }
  },

  setAutonomyLevel: async (level) => {
    try {
      await invoke("set_autonomy_level", { level });
      await get().loadConfig();
      await get().loadStatus();
    } catch (error) {
      set({ error: String(error) });
      console.error("Failed to set autonomy level:", error);
    }
  },

  addResearchTask: async (topic, priority) => {
    try {
      const taskId = await invoke<string>("add_research_task", { topic, priority });
      await get().loadQueueStatus();
      return taskId;
    } catch (error) {
      set({ error: String(error) });
      console.error("Failed to add research task:", error);
      throw error;
    }
  },

  forceSync: async () => {
    set({ isLoading: true, error: null });
    try {
      await invoke("force_commander_sync");
      await get().loadSyncStats();
    } catch (error) {
      set({ error: String(error) });
      console.error("Failed to force sync:", error);
    } finally {
      set({ isLoading: false });
    }
  },

  refreshAll: async () => {
    set({ isLoading: true });
    await Promise.all([
      get().loadStatus(),
      get().loadConfig(),
      get().loadQueueStatus(),
      get().loadSyncStats(),
      get().loadFindings(),
    ]);
    set({ isLoading: false });
  },
}));
