import { useEffect, useState } from "react";
import { useCommanderStore, AutonomyLevel, SyncStatus } from "../../stores/commanderStore";
import {
  Brain,
  Play,
  Pause,
  RefreshCw,
  Wifi,
  WifiOff,
  Clock,
  ListTodo,
  Shield,
  Zap,
  ChevronDown,
  Plus,
  Search,
  ExternalLink,
} from "lucide-react";
import clsx from "clsx";

const autonomyLevels: { value: AutonomyLevel; label: string; description: string }[] = [
  { value: "Supervised", label: "Overvaget", description: "Alle beslutninger kræver godkendelse" },
  { value: "Assisted", label: "Assisteret", description: "Kun kritiske beslutninger kræver godkendelse" },
  { value: "Autonomous", label: "Autonom", description: "De fleste beslutninger er automatiske" },
  { value: "FullAutonomy", label: "Fuld Autonomi", description: "24/7 operation uden tilsyn" },
];

export function CommanderPage() {
  const {
    status,
    queueStatus,
    syncStats,
    findings,
    isLoading,
    error,
    refreshAll,
    startCommander,
    stopCommander,
    setAutonomyLevel,
    addResearchTask,
    forceSync,
  } = useCommanderStore();

  const [showAutonomyDropdown, setShowAutonomyDropdown] = useState(false);
  const [newTaskTopic, setNewTaskTopic] = useState("");
  const [newTaskPriority, setNewTaskPriority] = useState("normal");

  useEffect(() => {
    refreshAll();
    const interval = setInterval(refreshAll, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [refreshAll]);

  const handleAddTask = async () => {
    if (!newTaskTopic.trim()) return;
    try {
      await addResearchTask(newTaskTopic, newTaskPriority);
      setNewTaskTopic("");
    } catch (e) {
      console.error("Failed to add task:", e);
    }
  };

  const formatUptime = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${hours}t ${mins}m`;
  };

  const getSyncStatusText = (syncStatus: SyncStatus | undefined): string => {
    if (!syncStatus) return "Ukendt";
    if (syncStatus === "Connected") return "Forbundet";
    if (syncStatus === "Syncing") return "Synkroniserer...";
    if (syncStatus === "Disconnected") return "Frakoblet";
    if (typeof syncStatus === "object" && "Error" in syncStatus) return `Fejl: ${syncStatus.Error}`;
    return "Ukendt";
  };

  const currentAutonomy = autonomyLevels.find((a) => a.value === status?.autonomy_level) || autonomyLevels[0];

  return (
    <div className="space-y-4">
      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-3 text-red-700 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Main Status Card */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div
              className={clsx(
                "w-3 h-3 rounded-full",
                status?.is_running
                  ? "bg-green-500 animate-pulse"
                  : "bg-gray-400"
              )}
            />
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <Brain className="w-5 h-5 text-cirkelline-500" />
                Commander Unit
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {status?.is_running ? "Kører autonome forskningsopgaver" : "Stoppet"}
              </p>
            </div>
          </div>
          <button
            onClick={status?.is_running ? stopCommander : startCommander}
            disabled={isLoading}
            className={clsx(
              "p-2 rounded-lg transition-colors",
              status?.is_running
                ? "bg-red-100 text-red-600 hover:bg-red-200"
                : "bg-green-100 text-green-600 hover:bg-green-200",
              isLoading && "opacity-50 cursor-not-allowed"
            )}
          >
            {status?.is_running ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
          </button>
        </div>

        {/* Autonomy Level Selector */}
        <div className="relative mb-4">
          <button
            onClick={() => setShowAutonomyDropdown(!showAutonomyDropdown)}
            className="w-full flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg text-left"
          >
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-cirkelline-500" />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {currentAutonomy.label}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {currentAutonomy.description}
                </p>
              </div>
            </div>
            <ChevronDown className={clsx("w-4 h-4 transition-transform", showAutonomyDropdown && "rotate-180")} />
          </button>

          {showAutonomyDropdown && (
            <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
              {autonomyLevels.map((level) => (
                <button
                  key={level.value}
                  onClick={() => {
                    setAutonomyLevel(level.value.toLowerCase());
                    setShowAutonomyDropdown(false);
                  }}
                  className={clsx(
                    "w-full p-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 first:rounded-t-lg last:rounded-b-lg",
                    status?.autonomy_level === level.value && "bg-cirkelline-50 dark:bg-cirkelline-900/20"
                  )}
                >
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{level.label}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{level.description}</p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-2">
          <StatItem
            icon={<Clock className="w-4 h-4" />}
            label="Oppetid"
            value={formatUptime(status?.uptime_seconds || 0)}
          />
          <StatItem
            icon={<ListTodo className="w-4 h-4" />}
            label="Opgaver fuldført"
            value={String(status?.tasks_completed || 0)}
          />
          <StatItem
            icon={<Zap className="w-4 h-4" />}
            label="Ventende"
            value={String(status?.tasks_pending || 0)}
          />
          <StatItem
            icon={status?.sync_status === "Connected" ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
            label="CKC Sync"
            value={getSyncStatusText(status?.sync_status)}
          />
        </div>
      </div>

      {/* Task Queue */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
        <h3 className="font-medium text-gray-900 dark:text-white mb-3 flex items-center gap-2">
          <ListTodo className="w-4 h-4" />
          Opgavekø
        </h3>

        {queueStatus && (
          <div className="grid grid-cols-5 gap-1 mb-4 text-center text-xs">
            <PriorityBadge label="Kritisk" count={queueStatus.by_priority.critical} color="red" />
            <PriorityBadge label="Høj" count={queueStatus.by_priority.high} color="orange" />
            <PriorityBadge label="Normal" count={queueStatus.by_priority.normal} color="blue" />
            <PriorityBadge label="Lav" count={queueStatus.by_priority.low} color="gray" />
            <PriorityBadge label="Baggrund" count={queueStatus.by_priority.background} color="gray" />
          </div>
        )}

        {/* Add Task Form */}
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Tilføj forskningsemne..."
            value={newTaskTopic}
            onChange={(e) => setNewTaskTopic(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAddTask()}
            className="flex-1 px-3 py-2 text-sm bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-cirkelline-500"
          />
          <select
            value={newTaskPriority}
            onChange={(e) => setNewTaskPriority(e.target.value)}
            className="px-2 py-2 text-sm bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-cirkelline-500"
          >
            <option value="critical">Kritisk</option>
            <option value="high">Høj</option>
            <option value="normal">Normal</option>
            <option value="low">Lav</option>
            <option value="background">Baggrund</option>
          </select>
          <button
            onClick={handleAddTask}
            disabled={!newTaskTopic.trim()}
            className="p-2 bg-cirkelline-500 text-white rounded-lg hover:bg-cirkelline-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Plus className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Recent Findings */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-medium text-gray-900 dark:text-white flex items-center gap-2">
            <Search className="w-4 h-4" />
            Seneste Fund
          </h3>
          <button
            onClick={forceSync}
            disabled={isLoading}
            className="p-1.5 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <RefreshCw className={clsx("w-4 h-4", isLoading && "animate-spin")} />
          </button>
        </div>

        {findings.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
            Ingen fund endnu. Start Commander for at begynde forskning.
          </p>
        ) : (
          <div className="space-y-2">
            {findings.slice(0, 5).map((finding) => (
              <div
                key={finding.id}
                className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {finding.title}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">
                      {finding.summary}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className="text-xs px-2 py-0.5 bg-cirkelline-100 dark:bg-cirkelline-900/30 text-cirkelline-700 dark:text-cirkelline-300 rounded">
                        {finding.source}
                      </span>
                      <span className="text-xs text-gray-400">
                        {(finding.relevance_score * 100).toFixed(0)}% relevant
                      </span>
                    </div>
                  </div>
                  {finding.url && (
                    <a
                      href={finding.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Sync Stats */}
      {syncStats && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
          <h3 className="font-medium text-gray-900 dark:text-white mb-3 flex items-center gap-2">
            <RefreshCw className="w-4 h-4" />
            Sync Status
          </h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-gray-500 dark:text-gray-400">Status</p>
              <p className="font-medium text-gray-900 dark:text-white">
                {getSyncStatusText(syncStats.status)}
              </p>
            </div>
            <div>
              <p className="text-gray-500 dark:text-gray-400">I kø</p>
              <p className="font-medium text-gray-900 dark:text-white">
                {syncStats.queue_size} elementer
              </p>
            </div>
            <div className="col-span-2">
              <p className="text-gray-500 dark:text-gray-400">Sidste sync</p>
              <p className="font-medium text-gray-900 dark:text-white">
                {syncStats.last_sync
                  ? new Date(syncStats.last_sync).toLocaleString("da-DK")
                  : "Aldrig"}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatItem({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-700 rounded-lg">
      <div className="text-cirkelline-500">{icon}</div>
      <div>
        <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
        <p className="text-sm font-medium text-gray-900 dark:text-white">{value}</p>
      </div>
    </div>
  );
}

function PriorityBadge({
  label,
  count,
  color,
}: {
  label: string;
  count: number;
  color: string;
}) {
  const colorClasses = {
    red: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
    orange: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
    blue: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
    gray: "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-400",
  };

  return (
    <div className={clsx("py-1 px-1 rounded", colorClasses[color as keyof typeof colorClasses])}>
      <p className="font-medium">{count}</p>
      <p className="text-[10px]">{label}</p>
    </div>
  );
}
