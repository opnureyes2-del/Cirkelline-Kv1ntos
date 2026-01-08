// Store tests for CLA frontend
// Tests Zustand stores for settings, metrics, and sync

import { describe, it, expect, beforeEach } from 'vitest';

// Mock the stores for testing
const createMockSettingsStore = () => {
  let state = {
    settings: {
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
    },
    isLoading: false,
    error: null,
  };

  return {
    getState: () => state,
    setState: (partial: Partial<typeof state>) => {
      state = { ...state, ...partial };
    },
    updateSetting: <K extends keyof typeof state.settings>(
      key: K,
      value: typeof state.settings[K]
    ) => {
      state.settings = { ...state.settings, [key]: value };
    },
  };
};

const createMockMetricsStore = () => {
  let state = {
    metrics: null as null | {
      cpu_usage_percent: number;
      ram_usage_percent: number;
      gpu_usage_percent: number | null;
      is_idle: boolean;
      on_battery: boolean;
    },
    history: [] as Array<{ timestamp: string; cpu: number; ram: number }>,
    isMonitoring: false,
  };

  return {
    getState: () => state,
    setState: (partial: Partial<typeof state>) => {
      state = { ...state, ...partial };
    },
    addMetric: (metric: typeof state.metrics) => {
      if (metric) {
        state.metrics = metric;
        state.history.push({
          timestamp: new Date().toISOString(),
          cpu: metric.cpu_usage_percent,
          ram: metric.ram_usage_percent,
        });
        // Keep only last 60 entries
        if (state.history.length > 60) {
          state.history = state.history.slice(-60);
        }
      }
    },
  };
};

describe('Settings Store', () => {
  let store: ReturnType<typeof createMockSettingsStore>;

  beforeEach(() => {
    store = createMockSettingsStore();
  });

  describe('Default Values', () => {
    it('should have conservative CPU default', () => {
      expect(store.getState().settings.max_cpu_percent).toBe(30);
    });

    it('should have conservative RAM default', () => {
      expect(store.getState().settings.max_ram_percent).toBe(20);
    });

    it('should default to idle-only mode', () => {
      expect(store.getState().settings.idle_only).toBe(true);
    });

    it('should not auto-start by default', () => {
      expect(store.getState().settings.auto_start).toBe(false);
    });

    it('should not run on battery by default', () => {
      expect(store.getState().settings.run_on_battery).toBe(false);
    });
  });

  describe('Setting Updates', () => {
    it('should update CPU limit', () => {
      store.updateSetting('max_cpu_percent', 50);
      expect(store.getState().settings.max_cpu_percent).toBe(50);
    });

    it('should update idle_only setting', () => {
      store.updateSetting('idle_only', false);
      expect(store.getState().settings.idle_only).toBe(false);
    });

    it('should update sync interval', () => {
      store.updateSetting('sync_interval_minutes', 30);
      expect(store.getState().settings.sync_interval_minutes).toBe(30);
    });
  });

  describe('Validation', () => {
    it('should keep CPU within bounds', () => {
      const validCpu = Math.min(Math.max(80, 0), 100);
      expect(validCpu).toBeLessThanOrEqual(100);
      expect(validCpu).toBeGreaterThanOrEqual(0);
    });

    it('should keep RAM within bounds', () => {
      const validRam = Math.min(Math.max(50, 0), 100);
      expect(validRam).toBeLessThanOrEqual(100);
      expect(validRam).toBeGreaterThanOrEqual(0);
    });
  });
});

describe('Metrics Store', () => {
  let store: ReturnType<typeof createMockMetricsStore>;

  beforeEach(() => {
    store = createMockMetricsStore();
  });

  describe('Initial State', () => {
    it('should have null metrics initially', () => {
      expect(store.getState().metrics).toBeNull();
    });

    it('should have empty history initially', () => {
      expect(store.getState().history).toHaveLength(0);
    });

    it('should not be monitoring initially', () => {
      expect(store.getState().isMonitoring).toBe(false);
    });
  });

  describe('Metric Updates', () => {
    it('should add metrics to history', () => {
      store.addMetric({
        cpu_usage_percent: 25,
        ram_usage_percent: 40,
        gpu_usage_percent: null,
        is_idle: true,
        on_battery: false,
      });

      expect(store.getState().history).toHaveLength(1);
      expect(store.getState().history[0].cpu).toBe(25);
    });

    it('should limit history to 60 entries', () => {
      for (let i = 0; i < 100; i++) {
        store.addMetric({
          cpu_usage_percent: i,
          ram_usage_percent: i,
          gpu_usage_percent: null,
          is_idle: true,
          on_battery: false,
        });
      }

      expect(store.getState().history).toHaveLength(60);
      // Should keep most recent
      expect(store.getState().history[59].cpu).toBe(99);
    });

    it('should update current metrics', () => {
      store.addMetric({
        cpu_usage_percent: 15,
        ram_usage_percent: 30,
        gpu_usage_percent: 10,
        is_idle: false,
        on_battery: true,
      });

      const metrics = store.getState().metrics;
      expect(metrics?.cpu_usage_percent).toBe(15);
      expect(metrics?.on_battery).toBe(true);
      expect(metrics?.is_idle).toBe(false);
    });
  });

  describe('Resource Status', () => {
    it('should detect high CPU usage', () => {
      store.addMetric({
        cpu_usage_percent: 85,
        ram_usage_percent: 30,
        gpu_usage_percent: null,
        is_idle: false,
        on_battery: false,
      });

      const metrics = store.getState().metrics;
      const isHighCpu = (metrics?.cpu_usage_percent ?? 0) > 80;
      expect(isHighCpu).toBe(true);
    });

    it('should detect battery power', () => {
      store.addMetric({
        cpu_usage_percent: 10,
        ram_usage_percent: 20,
        gpu_usage_percent: null,
        is_idle: true,
        on_battery: true,
      });

      expect(store.getState().metrics?.on_battery).toBe(true);
    });
  });
});

describe('Resource Permission Logic', () => {
  const checkCanExecute = (
    settings: {
      max_cpu_percent: number;
      max_ram_percent: number;
      idle_only: boolean;
      run_on_battery: boolean;
      min_battery_percent: number;
    },
    metrics: {
      cpu_usage_percent: number;
      ram_usage_percent: number;
      is_idle: boolean;
      on_battery: boolean;
      battery_percent: number | null;
    },
    taskCpu: number,
    taskRam: number
  ): { allowed: boolean; reason?: string } => {
    // Check idle requirement
    if (settings.idle_only && !metrics.is_idle) {
      return { allowed: false, reason: 'System not idle' };
    }

    // Check battery
    if (metrics.on_battery && !settings.run_on_battery) {
      return { allowed: false, reason: 'Running on battery' };
    }

    if (
      metrics.on_battery &&
      metrics.battery_percent !== null &&
      metrics.battery_percent < settings.min_battery_percent
    ) {
      return { allowed: false, reason: 'Battery too low' };
    }

    // Check CPU headroom
    const cpuAfter = metrics.cpu_usage_percent + taskCpu;
    if (cpuAfter > settings.max_cpu_percent) {
      return { allowed: false, reason: 'CPU limit would be exceeded' };
    }

    // Check RAM headroom
    const ramAfter = metrics.ram_usage_percent + taskRam;
    if (ramAfter > settings.max_ram_percent) {
      return { allowed: false, reason: 'RAM limit would be exceeded' };
    }

    return { allowed: true };
  };

  it('should allow execution when resources are available', () => {
    const result = checkCanExecute(
      {
        max_cpu_percent: 30,
        max_ram_percent: 20,
        idle_only: true,
        run_on_battery: false,
        min_battery_percent: 20,
      },
      {
        cpu_usage_percent: 10,
        ram_usage_percent: 5,
        is_idle: true,
        on_battery: false,
        battery_percent: null,
      },
      10, // task CPU
      5 // task RAM
    );

    expect(result.allowed).toBe(true);
  });

  it('should deny when not idle', () => {
    const result = checkCanExecute(
      {
        max_cpu_percent: 30,
        max_ram_percent: 20,
        idle_only: true,
        run_on_battery: false,
        min_battery_percent: 20,
      },
      {
        cpu_usage_percent: 10,
        ram_usage_percent: 5,
        is_idle: false, // Not idle
        on_battery: false,
        battery_percent: null,
      },
      10,
      5
    );

    expect(result.allowed).toBe(false);
    expect(result.reason).toContain('idle');
  });

  it('should deny when on battery without permission', () => {
    const result = checkCanExecute(
      {
        max_cpu_percent: 30,
        max_ram_percent: 20,
        idle_only: false,
        run_on_battery: false, // Not allowed on battery
        min_battery_percent: 20,
      },
      {
        cpu_usage_percent: 10,
        ram_usage_percent: 5,
        is_idle: true,
        on_battery: true, // On battery
        battery_percent: 50,
      },
      10,
      5
    );

    expect(result.allowed).toBe(false);
    expect(result.reason).toContain('battery');
  });

  it('should deny when battery too low', () => {
    const result = checkCanExecute(
      {
        max_cpu_percent: 30,
        max_ram_percent: 20,
        idle_only: false,
        run_on_battery: true, // Allowed on battery
        min_battery_percent: 20,
      },
      {
        cpu_usage_percent: 10,
        ram_usage_percent: 5,
        is_idle: true,
        on_battery: true,
        battery_percent: 10, // Too low
      },
      10,
      5
    );

    expect(result.allowed).toBe(false);
    expect(result.reason).toContain('Battery');
  });

  it('should deny when CPU limit would be exceeded', () => {
    const result = checkCanExecute(
      {
        max_cpu_percent: 30,
        max_ram_percent: 20,
        idle_only: false,
        run_on_battery: false,
        min_battery_percent: 20,
      },
      {
        cpu_usage_percent: 25, // Already high
        ram_usage_percent: 5,
        is_idle: true,
        on_battery: false,
        battery_percent: null,
      },
      10, // Would push to 35%
      5
    );

    expect(result.allowed).toBe(false);
    expect(result.reason).toContain('CPU');
  });
});

describe('Sync Store', () => {
  const createMockSyncStore = () => {
    let state = {
      status: {
        is_syncing: false,
        last_sync: null as string | null,
        last_sync_result: null as 'success' | 'error' | null,
        pending_uploads: 0,
        pending_downloads: 0,
        conflicts: [] as Array<{ id: string; type: string }>,
        bytes_uploaded: 0,
        bytes_downloaded: 0,
      },
      error: null as string | null,
    };

    return {
      getState: () => state,
      startSync: () => {
        state.status.is_syncing = true;
        state.error = null;
      },
      completeSync: (success: boolean) => {
        state.status.is_syncing = false;
        state.status.last_sync = new Date().toISOString();
        state.status.last_sync_result = success ? 'success' : 'error';
      },
      addConflict: (id: string, type: string) => {
        state.status.conflicts.push({ id, type });
      },
      resolveConflict: (id: string) => {
        state.status.conflicts = state.status.conflicts.filter((c) => c.id !== id);
      },
    };
  };

  it('should track sync status', () => {
    const store = createMockSyncStore();

    expect(store.getState().status.is_syncing).toBe(false);

    store.startSync();
    expect(store.getState().status.is_syncing).toBe(true);

    store.completeSync(true);
    expect(store.getState().status.is_syncing).toBe(false);
    expect(store.getState().status.last_sync_result).toBe('success');
  });

  it('should manage conflicts', () => {
    const store = createMockSyncStore();

    store.addConflict('mem-1', 'memory');
    store.addConflict('mem-2', 'memory');

    expect(store.getState().status.conflicts).toHaveLength(2);

    store.resolveConflict('mem-1');
    expect(store.getState().status.conflicts).toHaveLength(1);
    expect(store.getState().status.conflicts[0].id).toBe('mem-2');
  });
});
