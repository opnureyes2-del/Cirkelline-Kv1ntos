import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";

export interface Settings {
  // Resource limits
  max_cpu_percent: number;
  max_ram_percent: number;
  max_gpu_percent: number;
  max_disk_mb: number;

  // Behavior
  idle_only: boolean;
  idle_threshold_seconds: number;
  paused: boolean;
  auto_start: boolean;
  run_on_battery: boolean;
  min_battery_percent: number;

  // Sync settings
  sync_interval_minutes: number;
  sync_on_startup: boolean;
  offline_mode: boolean;

  // Model settings
  enable_transcription: boolean;
  enable_ocr: boolean;
  enable_embeddings: boolean;
  download_tier2_models: boolean;
  download_tier3_models: boolean;

  // Connection
  ckc_endpoint: string;
  api_key: string | null;
}

interface SettingsState {
  settings: Settings;
  loading: boolean;
  error: string | null;
  loadSettings: () => Promise<void>;
  updateSettings: (updates: Partial<Settings>) => Promise<void>;
  resetSettings: () => Promise<void>;
  togglePause: () => Promise<void>;
}

const defaultSettings: Settings = {
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
  ckc_endpoint: "https://ckc.cirkelline.com",
  api_key: null,
};

export const useSettingsStore = create<SettingsState>((set, get) => ({
  settings: defaultSettings,
  loading: false,
  error: null,

  loadSettings: async () => {
    set({ loading: true, error: null });
    try {
      const settings = await invoke<Settings>("get_settings");
      set({ settings, loading: false });
    } catch (error) {
      console.error("Failed to load settings:", error);
      set({ error: String(error), loading: false });
    }
  },

  updateSettings: async (updates) => {
    set({ loading: true, error: null });
    try {
      const newSettings = await invoke<Settings>("update_settings", {
        newSettings: updates,
      });
      set({ settings: newSettings, loading: false });
    } catch (error) {
      console.error("Failed to update settings:", error);
      set({ error: String(error), loading: false });
    }
  },

  resetSettings: async () => {
    set({ loading: true, error: null });
    try {
      const settings = await invoke<Settings>("reset_settings");
      set({ settings, loading: false });
    } catch (error) {
      console.error("Failed to reset settings:", error);
      set({ error: String(error), loading: false });
    }
  },

  togglePause: async () => {
    const { settings, updateSettings } = get();
    await updateSettings({ paused: !settings.paused });
  },
}));
