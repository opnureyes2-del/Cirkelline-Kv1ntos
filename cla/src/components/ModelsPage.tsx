import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import {
  Database,
  Download,
  Check,
  Loader2,
  HardDrive,
  Cpu,
  Mic,
  FileText
} from "lucide-react";
import clsx from "clsx";

interface ModelInfo {
  id: string;
  name: string;
  size_mb: number;
  tier: number;
  capabilities: string[];
  downloaded: boolean;
  download_progress: number | null;
  version: string;
}

interface DownloadProgress {
  model_id: string;
  progress: number;
  downloaded_mb: number;
  total_mb: number;
}

export function ModelsPage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [downloadProgress, setDownloadProgress] = useState<Record<string, number>>({});

  useEffect(() => {
    // Load model status
    loadModels();

    // Listen for download progress
    const unlisten = listen<DownloadProgress>("model-download-progress", (event) => {
      setDownloadProgress((prev) => ({
        ...prev,
        [event.payload.model_id]: event.payload.progress,
      }));
    });

    return () => {
      unlisten.then((fn) => fn());
    };
  }, []);

  async function loadModels() {
    try {
      const result = await invoke<ModelInfo[]>("get_model_status");
      setModels(result);
    } catch (error) {
      console.error("Failed to load models:", error);
    }
  }

  async function downloadModel(modelId: string) {
    setDownloading(modelId);
    setDownloadProgress((prev) => ({ ...prev, [modelId]: 0 }));

    try {
      await invoke("download_model", { modelId });
      await loadModels();
    } catch (error) {
      console.error("Download failed:", error);
    } finally {
      setDownloading(null);
      setDownloadProgress((prev) => {
        const { [modelId]: _, ...rest } = prev;
        return rest;
      });
    }
  }

  const tierGroups = {
    1: models.filter((m) => m.tier === 1),
    2: models.filter((m) => m.tier === 2),
    3: models.filter((m) => m.tier === 3),
  };

  const tierDescriptions = {
    1: "Kernefunktioner (81MB total)",
    2: "Udvidede funktioner (602MB total)",
    3: "Power-funktioner (2.4GB total)",
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center">
            <Database className="w-5 h-5 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h2 className="font-semibold text-gray-900 dark:text-white">
              AI-modeller
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Administrer lokale modeller til offline inferens
            </p>
          </div>
        </div>
      </div>

      {/* Model Tiers */}
      {([1, 2, 3] as const).map((tier) => (
        <div key={tier} className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="font-medium text-gray-900 dark:text-white">
                Tier {tier}
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {tierDescriptions[tier]}
              </p>
            </div>
            <TierBadge tier={tier} />
          </div>

          <div className="space-y-3">
            {tierGroups[tier].map((model) => (
              <ModelCard
                key={model.id}
                model={model}
                isDownloading={downloading === model.id}
                progress={downloadProgress[model.id]}
                onDownload={() => downloadModel(model.id)}
              />
            ))}
          </div>
        </div>
      ))}

      {/* Storage Info */}
      <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
        <div className="flex items-center gap-3 mb-3">
          <HardDrive className="w-5 h-5 text-gray-500" />
          <span className="font-medium text-gray-900 dark:text-white">
            Lagerbrug
          </span>
        </div>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-500 dark:text-gray-400">Downloadede modeller</span>
            <span className="text-gray-900 dark:text-white">
              {models.filter((m) => m.downloaded).reduce((acc, m) => acc + m.size_mb, 0)} MB
            </span>
          </div>
          <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-purple-500 rounded-full"
              style={{
                width: `${
                  (models.filter((m) => m.downloaded).reduce((acc, m) => acc + m.size_mb, 0) /
                    models.reduce((acc, m) => acc + m.size_mb, 0)) *
                  100
                }%`,
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function TierBadge({ tier }: { tier: number }) {
  const colors = {
    1: "bg-green-100 text-green-600 dark:bg-green-900/20 dark:text-green-400",
    2: "bg-blue-100 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400",
    3: "bg-purple-100 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400",
  };

  const labels = {
    1: "Anbefalet",
    2: "Valgfri",
    3: "Avanceret",
  };

  return (
    <span className={clsx("px-2 py-1 text-xs font-medium rounded-full", colors[tier as keyof typeof colors])}>
      {labels[tier as keyof typeof labels]}
    </span>
  );
}

function ModelCard({
  model,
  isDownloading,
  progress,
  onDownload,
}: {
  model: ModelInfo;
  isDownloading: boolean;
  progress?: number;
  onDownload: () => void;
}) {
  const capabilityIcons: Record<string, React.ReactNode> = {
    embeddings: <Cpu className="w-4 h-4" />,
    transcription: <Mic className="w-4 h-4" />,
    ocr: <FileText className="w-4 h-4" />,
    llm: <Database className="w-4 h-4" />,
  };

  return (
    <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium text-gray-900 dark:text-white">
              {model.name}
            </span>
            {model.downloaded && (
              <Check className="w-4 h-4 text-green-500" />
            )}
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {model.size_mb} MB • v{model.version}
          </p>
          <div className="flex items-center gap-2 mt-2">
            {model.capabilities.map((cap) => (
              <span
                key={cap}
                className="flex items-center gap-1 px-2 py-0.5 text-xs bg-gray-200 dark:bg-gray-600 rounded-full text-gray-600 dark:text-gray-300"
              >
                {capabilityIcons[cap] || null}
                {cap}
              </span>
            ))}
          </div>
        </div>
        {!model.downloaded && (
          <button
            onClick={onDownload}
            disabled={isDownloading}
            className={clsx(
              "p-2 rounded-lg transition-colors",
              isDownloading
                ? "bg-gray-200 dark:bg-gray-600 cursor-not-allowed"
                : "bg-cirkelline-100 text-cirkelline-600 hover:bg-cirkelline-200 dark:bg-cirkelline-900/20 dark:text-cirkelline-400"
            )}
          >
            {isDownloading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Download className="w-5 h-5" />
            )}
          </button>
        )}
      </div>

      {/* Download Progress */}
      {isDownloading && progress !== undefined && (
        <div className="mt-3">
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
            <span>Downloader...</span>
            <span>{progress.toFixed(0)}%</span>
          </div>
          <div className="h-1.5 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
            <div
              className="h-full bg-cirkelline-500 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
