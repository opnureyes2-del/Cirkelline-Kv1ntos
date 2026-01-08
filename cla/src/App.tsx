import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useEffect } from "react";
import { listen } from "@tauri-apps/api/event";
import { Layout } from "./components/Layout";
import { StatusPage } from "./components/status/StatusPage";
import { SettingsPage } from "./components/settings/SettingsPage";
import { SyncPage } from "./components/sync/SyncPage";
import { ModelsPage } from "./components/ModelsPage";
import { CommanderPage } from "./components/commander/CommanderPage";
import { useSettingsStore } from "./stores/settingsStore";
import { useMetricsStore } from "./stores/metricsStore";
import { useSyncStore } from "./stores/syncStore";

function App() {
  const setMetrics = useMetricsStore((state) => state.setMetrics);
  const setSyncStatus = useSyncStore((state) => state.setStatus);
  const loadSettings = useSettingsStore((state) => state.loadSettings);

  useEffect(() => {
    // Load initial settings
    loadSettings();

    // Listen for system metrics updates
    const unlistenMetrics = listen("system-metrics", (event) => {
      setMetrics(event.payload as any);
    });

    // Listen for sync status updates
    const unlistenSync = listen("sync-completed", (event) => {
      setSyncStatus(event.payload as any);
    });

    // Listen for navigation events from tray
    const unlistenNav = listen("navigate", (event) => {
      window.location.hash = event.payload as string;
    });

    return () => {
      unlistenMetrics.then((fn) => fn());
      unlistenSync.then((fn) => fn());
      unlistenNav.then((fn) => fn());
    };
  }, [setMetrics, setSyncStatus, loadSettings]);

  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<StatusPage />} />
          <Route path="/commander" element={<CommanderPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/sync" element={<SyncPage />} />
          <Route path="/models" element={<ModelsPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
