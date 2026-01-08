import { useMetricsStore } from "../../stores/metricsStore";
import { useSyncStore } from "../../stores/syncStore";
import { useSettingsStore } from "../../stores/settingsStore";
import {
  Cpu,
  HardDrive,
  Wifi,
  WifiOff,
  Pause,
  Play,
  Battery,
  Clock,
  Zap
} from "lucide-react";
import clsx from "clsx";

export function StatusPage() {
  const metrics = useMetricsStore((state) => state.metrics);
  const syncStatus = useSyncStore((state) => state.status);
  const settings = useSettingsStore((state) => state.settings);
  const togglePause = useSettingsStore((state) => state.togglePause);

  const isActive = !settings.paused && metrics?.is_idle;
  const statusText = settings.paused
    ? "På pause"
    : metrics?.is_idle
      ? "Aktiv"
      : "Venter på idle";

  return (
    <div className="space-y-4">
      {/* Main Status Card */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div
              className={clsx(
                "w-3 h-3 rounded-full",
                settings.paused
                  ? "bg-yellow-500"
                  : isActive
                    ? "bg-green-500 animate-pulse"
                    : "bg-blue-500"
              )}
            />
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-white">
                {statusText}
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {settings.paused
                  ? "CLA er sat på pause"
                  : isActive
                    ? "Kører AI-opgaver i baggrunden"
                    : `Idle om ${settings.idle_threshold_seconds - (metrics?.idle_seconds || 0)}s`}
              </p>
            </div>
          </div>
          <button
            onClick={togglePause}
            className={clsx(
              "p-2 rounded-lg transition-colors",
              settings.paused
                ? "bg-green-100 text-green-600 hover:bg-green-200"
                : "bg-yellow-100 text-yellow-600 hover:bg-yellow-200"
            )}
          >
            {settings.paused ? <Play className="w-5 h-5" /> : <Pause className="w-5 h-5" />}
          </button>
        </div>

        {/* Resource Usage */}
        <div className="space-y-3">
          <ResourceBar
            icon={<Cpu className="w-4 h-4" />}
            label="CPU"
            value={metrics?.cpu_usage_percent || 0}
            max={settings.max_cpu_percent}
            unit="%"
          />
          <ResourceBar
            icon={<HardDrive className="w-4 h-4" />}
            label="RAM"
            value={metrics?.ram_usage_percent || 0}
            max={settings.max_ram_percent}
            unit="%"
          />
          {metrics?.gpu_available && (
            <ResourceBar
              icon={<Zap className="w-4 h-4" />}
              label="GPU"
              value={metrics?.gpu_usage_percent || 0}
              max={settings.max_gpu_percent}
              unit="%"
            />
          )}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 gap-3">
        <StatCard
          icon={<Clock className="w-5 h-5" />}
          label="Idle tid"
          value={formatIdleTime(metrics?.idle_seconds || 0)}
          color="blue"
        />
        <StatCard
          icon={metrics?.on_battery ? <Battery className="w-5 h-5" /> : <Zap className="w-5 h-5" />}
          label="Strøm"
          value={metrics?.on_battery
            ? `${metrics?.battery_percent || 0}%`
            : "Tilsluttet"}
          color={metrics?.on_battery ? "yellow" : "green"}
        />
        <StatCard
          icon={syncStatus?.is_syncing ? <Wifi className="w-5 h-5 animate-pulse" /> : <WifiOff className="w-5 h-5" />}
          label="Sync"
          value={syncStatus?.is_syncing
            ? "Synkroniserer..."
            : syncStatus?.last_sync
              ? formatLastSync(syncStatus.last_sync)
              : "Aldrig"}
          color={syncStatus?.is_syncing ? "blue" : "gray"}
        />
        <StatCard
          icon={<HardDrive className="w-5 h-5" />}
          label="Lokal data"
          value={`${(metrics?.disk_used_mb || 0).toLocaleString()} MB`}
          color="purple"
        />
      </div>

      {/* Recent Activity */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
        <h3 className="font-medium text-gray-900 dark:text-white mb-3">
          Seneste aktivitet
        </h3>
        <div className="space-y-2 text-sm text-gray-500 dark:text-gray-400">
          {syncStatus?.last_sync ? (
            <p>Sidste sync: {new Date(syncStatus.last_sync).toLocaleString('da-DK')}</p>
          ) : (
            <p>Ingen aktivitet endnu</p>
          )}
        </div>
      </div>
    </div>
  );
}

function ResourceBar({
  icon,
  label,
  value,
  max,
  unit
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  max: number;
  unit: string;
}) {
  const percentage = Math.min((value / max) * 100, 100);
  const isOverLimit = value > max;

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2 text-gray-600 dark:text-gray-300">
          {icon}
          <span>{label}</span>
        </div>
        <span className={clsx(
          "font-medium",
          isOverLimit ? "text-red-500" : "text-gray-900 dark:text-white"
        )}>
          {value.toFixed(0)}{unit} / {max}{unit}
        </span>
      </div>
      <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={clsx(
            "h-full rounded-full transition-all duration-300",
            isOverLimit
              ? "bg-red-500"
              : percentage > 70
                ? "bg-yellow-500"
                : "bg-cirkelline-500"
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  color
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
}) {
  const colorClasses = {
    blue: "bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400",
    green: "bg-green-50 text-green-600 dark:bg-green-900/20 dark:text-green-400",
    yellow: "bg-yellow-50 text-yellow-600 dark:bg-yellow-900/20 dark:text-yellow-400",
    gray: "bg-gray-50 text-gray-600 dark:bg-gray-700 dark:text-gray-400",
    purple: "bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400",
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-3 shadow-sm">
      <div className={clsx(
        "w-10 h-10 rounded-lg flex items-center justify-center mb-2",
        colorClasses[color as keyof typeof colorClasses]
      )}>
        {icon}
      </div>
      <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
      <p className="font-semibold text-gray-900 dark:text-white">{value}</p>
    </div>
  );
}

function formatIdleTime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  return `${Math.floor(seconds / 3600)}t`;
}

function formatLastSync(date: string): string {
  const diff = Date.now() - new Date(date).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "Nu";
  if (minutes < 60) return `${minutes}m siden`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}t siden`;
  return `${Math.floor(hours / 24)}d siden`;
}
