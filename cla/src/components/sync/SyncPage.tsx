import { useSyncStore } from "../../stores/syncStore";
import {
  RefreshCw,
  Upload,
  Download,
  AlertTriangle,
  CheckCircle,
  XCircle
} from "lucide-react";
import clsx from "clsx";

export function SyncPage() {
  const { status, syncNow, resolveConflict } = useSyncStore();

  return (
    <div className="space-y-4">
      {/* Sync Status */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div
              className={clsx(
                "w-10 h-10 rounded-lg flex items-center justify-center",
                status.is_syncing
                  ? "bg-blue-100 text-blue-600"
                  : status.last_sync_result?.type === "Success"
                    ? "bg-green-100 text-green-600"
                    : "bg-gray-100 text-gray-600"
              )}
            >
              <RefreshCw
                className={clsx(
                  "w-5 h-5",
                  status.is_syncing && "animate-spin"
                )}
              />
            </div>
            <div>
              <h2 className="font-semibold text-gray-900 dark:text-white">
                {status.is_syncing ? "Synkroniserer..." : "Sync-status"}
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {status.last_sync
                  ? `Sidst: ${new Date(status.last_sync).toLocaleString('da-DK')}`
                  : "Aldrig synkroniseret"}
              </p>
            </div>
          </div>
          <button
            onClick={syncNow}
            disabled={status.is_syncing}
            className={clsx(
              "px-4 py-2 rounded-lg font-medium transition-colors",
              status.is_syncing
                ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                : "bg-cirkelline-500 text-white hover:bg-cirkelline-600"
            )}
          >
            {status.is_syncing ? "Vent..." : "Sync nu"}
          </button>
        </div>

        {/* Progress */}
        {status.is_syncing && (
          <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div className="h-full bg-cirkelline-500 animate-progress-indeterminate w-1/3" />
          </div>
        )}
      </div>

      {/* Pending Changes */}
      <div className="grid grid-cols-3 gap-3">
        <StatCard
          icon={<Upload className="w-5 h-5" />}
          label="Upload"
          value={status.pending_uploads}
          color="blue"
        />
        <StatCard
          icon={<Download className="w-5 h-5" />}
          label="Download"
          value={status.pending_downloads}
          color="green"
        />
        <StatCard
          icon={<AlertTriangle className="w-5 h-5" />}
          label="Konflikter"
          value={status.conflicts.length}
          color={status.conflicts.length > 0 ? "yellow" : "gray"}
        />
      </div>

      {/* Conflicts */}
      {status.conflicts.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
          <h3 className="font-medium text-gray-900 dark:text-white mb-3 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-500" />
            Konflikter ({status.conflicts.length})
          </h3>
          <div className="space-y-3">
            {status.conflicts.map((conflict) => (
              <div
                key={conflict.id}
                className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg"
              >
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {conflict.description}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Type: {conflict.data_type} | Lokal: {new Date(conflict.local_version).toLocaleString('da-DK')}
                </p>
                <div className="flex gap-2 mt-2">
                  <button
                    onClick={() => resolveConflict(conflict.id, "KeepLocal")}
                    className="px-3 py-1 text-xs bg-blue-100 text-blue-600 rounded-lg hover:bg-blue-200"
                  >
                    Behold lokal
                  </button>
                  <button
                    onClick={() => resolveConflict(conflict.id, "KeepRemote")}
                    className="px-3 py-1 text-xs bg-green-100 text-green-600 rounded-lg hover:bg-green-200"
                  >
                    Behold remote
                  </button>
                  <button
                    onClick={() => resolveConflict(conflict.id, "Merge")}
                    className="px-3 py-1 text-xs bg-purple-100 text-purple-600 rounded-lg hover:bg-purple-200"
                  >
                    Flet
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Last Sync Result */}
      {status.last_sync_result && (
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
          <h3 className="font-medium text-gray-900 dark:text-white mb-3">
            Sidste sync-resultat
          </h3>
          <div className="flex items-center gap-3">
            {status.last_sync_result.type === "Success" ? (
              <>
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-green-600 dark:text-green-400">
                  Sync gennemført
                </span>
              </>
            ) : status.last_sync_result.type === "PartialSuccess" ? (
              <>
                <AlertTriangle className="w-5 h-5 text-yellow-500" />
                <span className="text-yellow-600 dark:text-yellow-400">
                  Delvis gennemført
                </span>
              </>
            ) : (
              <>
                <XCircle className="w-5 h-5 text-red-500" />
                <span className="text-red-600 dark:text-red-400">
                  Fejl: {status.last_sync_result.error || "Ukendt fejl"}
                </span>
              </>
            )}
          </div>
        </div>
      )}

      {/* Data Transfer Stats */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
        <h3 className="font-medium text-gray-900 dark:text-white mb-3">
          Dataoverførsel
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">Uploadet</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {formatBytes(status.bytes_uploaded)}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400">Downloadet</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {formatBytes(status.bytes_downloaded)}
            </p>
          </div>
        </div>
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
  value: number;
  color: string;
}) {
  const colorClasses = {
    blue: "bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400",
    green: "bg-green-50 text-green-600 dark:bg-green-900/20 dark:text-green-400",
    yellow: "bg-yellow-50 text-yellow-600 dark:bg-yellow-900/20 dark:text-yellow-400",
    gray: "bg-gray-50 text-gray-600 dark:bg-gray-700 dark:text-gray-400",
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-3 shadow-sm text-center">
      <div
        className={clsx(
          "w-10 h-10 rounded-lg flex items-center justify-center mx-auto mb-2",
          colorClasses[color as keyof typeof colorClasses]
        )}
      >
        {icon}
      </div>
      <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
      <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
    </div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}
