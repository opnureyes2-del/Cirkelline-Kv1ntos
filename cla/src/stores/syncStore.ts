import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";

export interface SyncConflict {
  id: string;
  data_type: string;
  local_version: string;
  remote_version: string;
  description: string;
  resolution_options: string[];
}

export interface SyncStatus {
  is_syncing: boolean;
  last_sync: string | null;
  last_sync_result: {
    type: "Success" | "PartialSuccess" | "Failed";
    errors?: string[];
    error?: string;
  } | null;
  pending_uploads: number;
  pending_downloads: number;
  conflicts: SyncConflict[];
  bytes_uploaded: number;
  bytes_downloaded: number;
}

interface SyncState {
  status: SyncStatus;
  setStatus: (status: SyncStatus) => void;
  syncNow: () => Promise<void>;
  resolveConflict: (conflictId: string, resolution: string) => Promise<void>;
}

const defaultStatus: SyncStatus = {
  is_syncing: false,
  last_sync: null,
  last_sync_result: null,
  pending_uploads: 0,
  pending_downloads: 0,
  conflicts: [],
  bytes_uploaded: 0,
  bytes_downloaded: 0,
};

export const useSyncStore = create<SyncState>((set, _get) => ({
  status: defaultStatus,

  setStatus: (status) => set({ status }),

  syncNow: async () => {
    set((state) => ({
      status: { ...state.status, is_syncing: true },
    }));

    try {
      await invoke<{ type: string; errors?: string[]; error?: string }>("sync_now");
      const status = await invoke<SyncStatus>("get_sync_status");
      set({ status });
    } catch (error) {
      console.error("Sync failed:", error);
      set((state) => ({
        status: {
          ...state.status,
          is_syncing: false,
          last_sync_result: { type: "Failed", error: String(error) },
        },
      }));
    }
  },

  resolveConflict: async (conflictId, resolution) => {
    try {
      await invoke("resolve_conflict", {
        conflictId,
        resolution,
      });

      // Refresh status
      const status = await invoke<SyncStatus>("get_sync_status");
      set({ status });
    } catch (error) {
      console.error("Failed to resolve conflict:", error);
    }
  },
}));
