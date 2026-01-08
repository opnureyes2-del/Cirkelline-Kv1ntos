import { useSettingsStore } from "../../stores/settingsStore";
import {
  Cpu,
  Zap,
  Clock,
  Battery,
  Wifi,
  RefreshCw,
  Download
} from "lucide-react";

export function SettingsPage() {
  const settings = useSettingsStore((state) => state.settings);
  const updateSettings = useSettingsStore((state) => state.updateSettings);
  const resetSettings = useSettingsStore((state) => state.resetSettings);

  return (
    <div className="space-y-4">
      {/* Resource Limits */}
      <SettingsSection title="Ressourcegrænser" icon={<Cpu className="w-5 h-5" />}>
        <SliderSetting
          label="Maksimal CPU-brug"
          value={settings.max_cpu_percent}
          min={10}
          max={80}
          step={5}
          unit="%"
          onChange={(value) => updateSettings({ max_cpu_percent: value })}
        />
        <SliderSetting
          label="Maksimal RAM-brug"
          value={settings.max_ram_percent}
          min={10}
          max={50}
          step={5}
          unit="%"
          onChange={(value) => updateSettings({ max_ram_percent: value })}
        />
        <SliderSetting
          label="Maksimal GPU-brug"
          value={settings.max_gpu_percent}
          min={10}
          max={80}
          step={5}
          unit="%"
          onChange={(value) => updateSettings({ max_gpu_percent: value })}
        />
        <SliderSetting
          label="Maksimal diskplads"
          value={settings.max_disk_mb}
          min={500}
          max={10000}
          step={500}
          unit=" MB"
          onChange={(value) => updateSettings({ max_disk_mb: value })}
        />
      </SettingsSection>

      {/* Behavior */}
      <SettingsSection title="Adfærd" icon={<Clock className="w-5 h-5" />}>
        <ToggleSetting
          label="Kun ved idle"
          description="Kør kun opgaver når computeren er inaktiv"
          checked={settings.idle_only}
          onChange={(checked) => updateSettings({ idle_only: checked })}
        />
        {settings.idle_only && (
          <SliderSetting
            label="Idle-tærskel"
            value={settings.idle_threshold_seconds}
            min={30}
            max={600}
            step={30}
            unit=" sek"
            onChange={(value) => updateSettings({ idle_threshold_seconds: value })}
          />
        )}
        <ToggleSetting
          label="Start automatisk"
          description="Start CLA ved computer-opstart"
          checked={settings.auto_start}
          onChange={(checked) => updateSettings({ auto_start: checked })}
        />
      </SettingsSection>

      {/* Power */}
      <SettingsSection title="Strøm" icon={<Battery className="w-5 h-5" />}>
        <ToggleSetting
          label="Kør på batteri"
          description="Tillad opgaver at køre på batteri"
          checked={settings.run_on_battery}
          onChange={(checked) => updateSettings({ run_on_battery: checked })}
        />
        {settings.run_on_battery && (
          <SliderSetting
            label="Minimum batteri"
            value={settings.min_battery_percent}
            min={10}
            max={50}
            step={5}
            unit="%"
            onChange={(value) => updateSettings({ min_battery_percent: value })}
          />
        )}
      </SettingsSection>

      {/* Sync */}
      <SettingsSection title="Synkronisering" icon={<RefreshCw className="w-5 h-5" />}>
        <SliderSetting
          label="Sync-interval"
          value={settings.sync_interval_minutes}
          min={5}
          max={60}
          step={5}
          unit=" min"
          onChange={(value) => updateSettings({ sync_interval_minutes: value })}
        />
        <ToggleSetting
          label="Sync ved opstart"
          description="Synkroniser automatisk ved opstart"
          checked={settings.sync_on_startup}
          onChange={(checked) => updateSettings({ sync_on_startup: checked })}
        />
        <ToggleSetting
          label="Offline-tilstand"
          description="Deaktiver al netværkskommunikation"
          checked={settings.offline_mode}
          onChange={(checked) => updateSettings({ offline_mode: checked })}
        />
      </SettingsSection>

      {/* AI Features */}
      <SettingsSection title="AI-funktioner" icon={<Zap className="w-5 h-5" />}>
        <ToggleSetting
          label="Transskription"
          description="Aktiver lokal lyd-til-tekst"
          checked={settings.enable_transcription}
          onChange={(checked) => updateSettings({ enable_transcription: checked })}
        />
        <ToggleSetting
          label="OCR"
          description="Aktiver lokal tekstgenkendelse fra billeder"
          checked={settings.enable_ocr}
          onChange={(checked) => updateSettings({ enable_ocr: checked })}
        />
        <ToggleSetting
          label="Embeddings"
          description="Aktiver lokal semantisk søgning"
          checked={settings.enable_embeddings}
          onChange={(checked) => updateSettings({ enable_embeddings: checked })}
        />
      </SettingsSection>

      {/* Models */}
      <SettingsSection title="Modeller" icon={<Download className="w-5 h-5" />}>
        <ToggleSetting
          label="Download Tier 2 modeller"
          description="Større modeller med bedre kvalitet (~600MB)"
          checked={settings.download_tier2_models}
          onChange={(checked) => updateSettings({ download_tier2_models: checked })}
        />
        <ToggleSetting
          label="Download Tier 3 modeller"
          description="Store LLM-modeller for lokal inferens (~2.4GB)"
          checked={settings.download_tier3_models}
          onChange={(checked) => updateSettings({ download_tier3_models: checked })}
        />
      </SettingsSection>

      {/* Connection */}
      <SettingsSection title="Forbindelse" icon={<Wifi className="w-5 h-5" />}>
        <TextSetting
          label="CKC Endpoint"
          value={settings.ckc_endpoint}
          placeholder="https://ckc.cirkelline.com"
          onChange={(value) => updateSettings({ ckc_endpoint: value })}
        />
      </SettingsSection>

      {/* Reset */}
      <div className="pt-4">
        <button
          onClick={resetSettings}
          className="w-full py-2 text-red-600 dark:text-red-400 text-sm font-medium hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
        >
          Nulstil alle indstillinger
        </button>
      </div>
    </div>
  );
}

function SettingsSection({
  title,
  icon,
  children
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-cirkelline-500">{icon}</span>
        <h3 className="font-medium text-gray-900 dark:text-white">{title}</h3>
      </div>
      <div className="space-y-4">
        {children}
      </div>
    </div>
  );
}

function ToggleSetting({
  label,
  description,
  checked,
  onChange,
}: {
  label: string;
  description?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between cursor-pointer">
      <div>
        <p className="text-sm font-medium text-gray-900 dark:text-white">{label}</p>
        {description && (
          <p className="text-xs text-gray-500 dark:text-gray-400">{description}</p>
        )}
      </div>
      <div
        className={`relative w-11 h-6 rounded-full transition-colors ${
          checked ? 'bg-cirkelline-500' : 'bg-gray-300 dark:bg-gray-600'
        }`}
        onClick={() => onChange(!checked)}
      >
        <div
          className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
            checked ? 'translate-x-5' : ''
          }`}
        />
      </div>
    </label>
  );
}

function SliderSetting({
  label,
  value,
  min,
  max,
  step,
  unit,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  unit: string;
  onChange: (value: number) => void;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-900 dark:text-white">{label}</p>
        <span className="text-sm text-cirkelline-600 dark:text-cirkelline-400 font-medium">
          {value}{unit}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-cirkelline-500"
      />
    </div>
  );
}

function TextSetting({
  label,
  value,
  placeholder,
  onChange,
}: {
  label: string;
  value: string;
  placeholder?: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-2">
      <p className="text-sm font-medium text-gray-900 dark:text-white">{label}</p>
      <input
        type="text"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-cirkelline-500 focus:border-transparent"
      />
    </div>
  );
}
