import { create } from "zustand";

export interface SystemMetrics {
  // CPU
  cpu_usage_percent: number;
  cpu_count: number;

  // Memory
  ram_used_mb: number;
  ram_total_mb: number;
  ram_usage_percent: number;

  // GPU
  gpu_available: boolean;
  gpu_usage_percent: number | null;
  gpu_memory_used_mb: number | null;
  gpu_memory_total_mb: number | null;

  // Disk
  disk_used_mb: number;
  disk_available_mb: number;

  // Power
  on_battery: boolean;
  battery_percent: number | null;

  // Idle
  idle_seconds: number;
  is_idle: boolean;

  // Timestamp
  timestamp: string;
}

interface MetricsState {
  metrics: SystemMetrics | null;
  history: SystemMetrics[];
  setMetrics: (metrics: SystemMetrics) => void;
  clearHistory: () => void;
}

const MAX_HISTORY = 60; // Keep last 60 data points (5 minutes at 5s intervals)

export const useMetricsStore = create<MetricsState>((set) => ({
  metrics: null,
  history: [],

  setMetrics: (metrics) =>
    set((state) => ({
      metrics,
      history: [...state.history.slice(-(MAX_HISTORY - 1)), metrics],
    })),

  clearHistory: () => set({ history: [] }),
}));
