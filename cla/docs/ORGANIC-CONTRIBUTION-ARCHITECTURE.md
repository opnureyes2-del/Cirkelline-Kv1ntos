# CLA Organisk Enhedsbidrag - Arkitekturdokumentation

## Version: 1.0.0
## Status: DESIGN FASE
## Dato: 2025-12-08

---

## 1. FILOSOFISK FUNDAMENT

### 1.1 Vision
Cirkelline Local Agent (CLA) skal udvikle evnen til proaktivt at bidrage med overskydende ressourcer til Cirkelline-økosystemet, mens den **UBETINGET** respekterer brugerens kontrol og privatliv.

### 1.2 Kerneprincipper

| Princip | Beskrivelse |
|---------|-------------|
| **Explicit Opt-In** | Enhedsbidrag er ALDRIG aktiveret som standard |
| **Brugeren har prioritet** | Lokale opgaver har ALTID forrang over netværksbidrag |
| **Fuld transparens** | Brugeren kan se præcis hvad der sker i realtid |
| **Granulær kontrol** | Brugeren styrer alle aspekter af bidrag |
| **Øjeblikkelig stop** | Bidrag kan stoppes på millisekunder |

---

## 2. SYSTEMARKITEKTUR

### 2.1 Overordnet Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    BRUGER KONTROL LAG                            │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐    │
│  │  Opt-In    │ │ Ressource  │ │ Tidsvindue │ │ Opgavetyper│    │
│  │  Toggle    │ │  Grænser   │ │   Filter   │ │   Filter   │    │
│  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘    │
└────────┼──────────────┼──────────────┼──────────────┼────────────┘
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   CONTRIBUTION       │
                    │   PERMISSION ENGINE   │
                    │   (Rust Backend)      │
                    └───────────┬───────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         │                      │                      │
┌────────▼────────┐    ┌───────▼───────┐    ┌────────▼────────┐
│  RESOURCE       │    │  CONTRIBUTION │    │  NETWORK        │
│  ANALYZER       │    │  SCHEDULER    │    │  COMMUNICATOR   │
│  (Avanceret)    │    │               │    │                 │
└────────┬────────┘    └───────┬───────┘    └────────┬────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   CKC BACKEND API   │
                    │   /api/contribution │
                    └─────────────────────┘
```

### 2.2 Komponent Hierarki

```
src-tauri/src/
├── contribution/
│   ├── mod.rs                    # Module exports
│   ├── settings.rs               # ContributionSettings struct
│   ├── permission_engine.rs      # Godkendelses-logik
│   ├── resource_analyzer.rs      # Avanceret ressourceanalyse
│   ├── scheduler.rs              # Opgave-scheduler
│   ├── task_types.rs             # Definitioner af bidragsopgaver
│   ├── network_client.rs         # Kommunikation med CKC
│   └── history.rs                # Bidragshistorik

src/
├── stores/
│   └── contributionStore.ts      # Zustand store for bidrag
├── components/
│   └── contribution/
│       ├── ContributionPanel.tsx  # Hovedpanel
│       ├── ContributionToggle.tsx # Opt-in toggle
│       ├── ResourceLimiters.tsx   # Granulære grænser
│       ├── TimeWindowPicker.tsx   # Tidsvindue-vælger
│       ├── TaskTypeSelector.tsx   # Opgavetype-filter
│       ├── ContributionStats.tsx  # Statistik og historik
│       └── ActiveTaskIndicator.tsx# Realtids-indikator
```

---

## 3. RUST BACKEND IMPLEMENTATION

### 3.1 ContributionSettings Struct

```rust
// src-tauri/src/contribution/settings.rs

use serde::{Deserialize, Serialize};

/// Bruger-kontrollerede indstillinger for enhedsbidrag
/// ALLE felter er opt-in og false/0 som standard
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ContributionSettings {
    // ========================================
    // MASTER CONTROL - EXPLICIT OPT-IN
    // ========================================
    /// Enhedsbidrag aktiveret (ALTID false som standard)
    pub enabled: bool,

    /// Brugeren har eksplicit accepteret vilkår
    pub user_acknowledged_terms: bool,

    /// Tidspunkt for accept af vilkår
    pub terms_accepted_at: Option<String>,

    // ========================================
    // RESSOURCE GRÆNSER (Overskrider IKKE systemgrænser)
    // ========================================
    /// Max CPU til bidrag (procent af TILGÆNGELIG headroom)
    /// Standard: 50% af headroom, max 30% absolut
    pub contribution_cpu_percent: u8,

    /// Max RAM til bidrag (MB)
    /// Standard: 512 MB, aldrig over system-headroom
    pub contribution_ram_mb: u32,

    /// Max GPU til bidrag (procent af tilgængelig)
    /// Standard: 40%, kun når GPU er idle
    pub contribution_gpu_percent: u8,

    /// Max netværksbåndbredde til bidrag (KB/s)
    /// Standard: 1024 KB/s (1 MB/s)
    pub contribution_bandwidth_kbps: u32,

    /// Max diskplads til midlertidig cache (MB)
    /// Standard: 500 MB
    pub contribution_disk_mb: u32,

    // ========================================
    // TIDSVINDUE KONTROL
    // ========================================
    /// Kun bidrag i specifikke tidsrum
    pub time_windows_enabled: bool,

    /// Tilladte tidsvinduer (f.eks. "00:00-06:00")
    pub allowed_time_windows: Vec<TimeWindow>,

    /// Bidrag kun på bestemte ugedage
    pub allowed_weekdays: Vec<Weekday>,

    // ========================================
    // BETINGELSER
    // ========================================
    /// Kun bidrag når system er idle
    /// Standard: true
    pub require_system_idle: bool,

    /// Minimum idle-tid før bidrag starter (sekunder)
    /// Standard: 300 (5 minutter)
    pub idle_before_contribution_seconds: u32,

    /// Kun bidrag når tilsluttet strøm
    /// Standard: true
    pub require_power_connected: bool,

    /// Minimum batteri for bidrag (hvis på batteri tilladt)
    /// Standard: 80%
    pub min_battery_for_contribution: u8,

    /// Stop bidrag ved brugeraktivitet
    /// Standard: true (ALTID respekteret)
    pub stop_on_user_activity: bool,

    /// Grace period efter brugeraktivitet (sekunder)
    /// Standard: 60
    pub activity_grace_period_seconds: u32,

    // ========================================
    // OPGAVETYPER (GRANULÆR KONTROL)
    // ========================================
    /// Tillad AI-inferens opgaver
    pub allow_ai_inference: bool,

    /// Tillad embedding-generering
    pub allow_embedding_generation: bool,

    /// Tillad data-preprocessing
    pub allow_data_preprocessing: bool,

    /// Tillad netværks-caching
    pub allow_network_caching: bool,

    /// Tillad model-distribution
    pub allow_model_distribution: bool,

    // ========================================
    // SIKKERHED OG PRIVATLIV
    // ========================================
    /// Kun anonymiserede opgaver
    pub anonymized_tasks_only: bool,

    /// Log alle bidragsaktiviteter lokalt
    pub log_all_activities: bool,

    /// Max opgavestørrelse (MB)
    pub max_task_size_mb: u32,
}

impl Default for ContributionSettings {
    fn default() -> Self {
        Self {
            // MASTER CONTROL - ALDRIG AKTIVERET SOM DEFAULT
            enabled: false,
            user_acknowledged_terms: false,
            terms_accepted_at: None,

            // KONSERVATIVE RESSOURCEGRÆNSER
            contribution_cpu_percent: 50,  // 50% af headroom
            contribution_ram_mb: 512,
            contribution_gpu_percent: 40,
            contribution_bandwidth_kbps: 1024,
            contribution_disk_mb: 500,

            // TIDSVINDUE - DEAKTIVERET SOM DEFAULT
            time_windows_enabled: false,
            allowed_time_windows: Vec::new(),
            allowed_weekdays: vec![
                Weekday::Monday,
                Weekday::Tuesday,
                Weekday::Wednesday,
                Weekday::Thursday,
                Weekday::Friday,
                Weekday::Saturday,
                Weekday::Sunday,
            ],

            // STRENGE BETINGELSER SOM DEFAULT
            require_system_idle: true,
            idle_before_contribution_seconds: 300,
            require_power_connected: true,
            min_battery_for_contribution: 80,
            stop_on_user_activity: true,
            activity_grace_period_seconds: 60,

            // ALLE OPGAVETYPER DEAKTIVERET SOM DEFAULT
            allow_ai_inference: false,
            allow_embedding_generation: false,
            allow_data_preprocessing: false,
            allow_network_caching: false,
            allow_model_distribution: false,

            // SIKKERHED
            anonymized_tasks_only: true,
            log_all_activities: true,
            max_task_size_mb: 100,
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TimeWindow {
    pub start_hour: u8,
    pub start_minute: u8,
    pub end_hour: u8,
    pub end_minute: u8,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub enum Weekday {
    Monday,
    Tuesday,
    Wednesday,
    Thursday,
    Friday,
    Saturday,
    Sunday,
}
```

### 3.2 Permission Engine

```rust
// src-tauri/src/contribution/permission_engine.rs

use super::settings::ContributionSettings;
use crate::utils::resource_limiter::SystemMetrics;
use chrono::{Datelike, Local, Timelike, Weekday as ChronoWeekday};

/// Resultat af tilladelsescheck
#[derive(Debug, Clone)]
pub enum ContributionPermission {
    /// Bidrag tilladt
    Granted {
        max_cpu_percent: u8,
        max_ram_mb: u32,
        max_duration_seconds: u64,
        allowed_task_types: Vec<ContributionTaskType>,
    },
    /// Bidrag ikke tilladt
    Denied {
        reason: DenialReason,
        retry_after_seconds: Option<u32>,
    },
}

#[derive(Debug, Clone)]
pub enum DenialReason {
    NotEnabled,
    TermsNotAccepted,
    SystemNotIdle,
    InsufficientIdleTime { current: u32, required: u32 },
    OnBattery,
    BatteryTooLow { current: u8, required: u8 },
    OutsideTimeWindow,
    WrongWeekday,
    ResourcesInUse,
    LocalTaskPriority,
    UserActivity,
    Paused,
}

#[derive(Debug, Clone, PartialEq)]
pub enum ContributionTaskType {
    AIInference,
    EmbeddingGeneration,
    DataPreprocessing,
    NetworkCaching,
    ModelDistribution,
}

pub struct ContributionPermissionEngine {
    settings: ContributionSettings,
}

impl ContributionPermissionEngine {
    pub fn new(settings: ContributionSettings) -> Self {
        Self { settings }
    }

    /// HOVEDMETODE: Check om bidrag er tilladt
    pub fn can_contribute(&self, metrics: &SystemMetrics) -> ContributionPermission {
        // ========================================
        // CHECKPOINT 1: MASTER SWITCH
        // ========================================
        if !self.settings.enabled {
            return ContributionPermission::Denied {
                reason: DenialReason::NotEnabled,
                retry_after_seconds: None,
            };
        }

        if !self.settings.user_acknowledged_terms {
            return ContributionPermission::Denied {
                reason: DenialReason::TermsNotAccepted,
                retry_after_seconds: None,
            };
        }

        // ========================================
        // CHECKPOINT 2: BRUGERAKTIVITET (HØJESTE PRIORITET)
        // ========================================
        if self.settings.stop_on_user_activity {
            if !metrics.is_idle {
                return ContributionPermission::Denied {
                    reason: DenialReason::UserActivity,
                    retry_after_seconds: Some(self.settings.activity_grace_period_seconds),
                };
            }
        }

        // ========================================
        // CHECKPOINT 3: IDLE KRAV
        // ========================================
        if self.settings.require_system_idle {
            if metrics.idle_seconds < self.settings.idle_before_contribution_seconds {
                return ContributionPermission::Denied {
                    reason: DenialReason::InsufficientIdleTime {
                        current: metrics.idle_seconds,
                        required: self.settings.idle_before_contribution_seconds,
                    },
                    retry_after_seconds: Some(
                        self.settings.idle_before_contribution_seconds - metrics.idle_seconds
                    ),
                };
            }
        }

        // ========================================
        // CHECKPOINT 4: STRØM/BATTERI
        // ========================================
        if metrics.on_battery {
            if self.settings.require_power_connected {
                return ContributionPermission::Denied {
                    reason: DenialReason::OnBattery,
                    retry_after_seconds: None,
                };
            }

            if let Some(battery) = metrics.battery_percent {
                if battery < self.settings.min_battery_for_contribution {
                    return ContributionPermission::Denied {
                        reason: DenialReason::BatteryTooLow {
                            current: battery,
                            required: self.settings.min_battery_for_contribution,
                        },
                        retry_after_seconds: None,
                    };
                }
            }
        }

        // ========================================
        // CHECKPOINT 5: TIDSVINDUE
        // ========================================
        if self.settings.time_windows_enabled {
            if !self.is_within_time_window() {
                return ContributionPermission::Denied {
                    reason: DenialReason::OutsideTimeWindow,
                    retry_after_seconds: Some(self.seconds_until_next_window()),
                };
            }
        }

        if !self.is_allowed_weekday() {
            return ContributionPermission::Denied {
                reason: DenialReason::WrongWeekday,
                retry_after_seconds: Some(self.seconds_until_allowed_day()),
            };
        }

        // ========================================
        // CHECKPOINT 6: RESSOURCE TILGÆNGELIGHED
        // ========================================
        let available_cpu = self.calculate_available_cpu(metrics);
        let available_ram = self.calculate_available_ram(metrics);

        if available_cpu == 0 || available_ram == 0 {
            return ContributionPermission::Denied {
                reason: DenialReason::ResourcesInUse,
                retry_after_seconds: Some(60),
            };
        }

        // ========================================
        // ALLE CHECKS BESTÅET - BIDRAG TILLADT
        // ========================================
        ContributionPermission::Granted {
            max_cpu_percent: available_cpu,
            max_ram_mb: available_ram,
            max_duration_seconds: self.calculate_max_duration(),
            allowed_task_types: self.get_allowed_task_types(),
        }
    }

    /// Beregn tilgængelig CPU til bidrag
    fn calculate_available_cpu(&self, metrics: &SystemMetrics) -> u8 {
        // System max (fra ResourceLimiter)
        let system_max = 30; // Fra FASE 4 konservative defaults
        let current_usage = metrics.cpu_usage_percent as u8;
        let headroom = system_max.saturating_sub(current_usage);

        // Bidrag må kun bruge % af headroom
        let contribution_cap = (headroom as f32 * (self.settings.contribution_cpu_percent as f32 / 100.0)) as u8;

        // Aldrig mere end absolut max
        contribution_cap.min(self.settings.contribution_cpu_percent)
    }

    /// Beregn tilgængelig RAM til bidrag
    fn calculate_available_ram(&self, metrics: &SystemMetrics) -> u32 {
        let system_max_percent = 20; // Fra FASE 4
        let current_percent = metrics.ram_usage_percent as u8;

        if current_percent >= system_max_percent {
            return 0;
        }

        // Aldrig mere end konfigureret max
        self.settings.contribution_ram_mb
    }

    fn is_within_time_window(&self) -> bool {
        if self.settings.allowed_time_windows.is_empty() {
            return true;
        }

        let now = Local::now();
        let current_minutes = now.hour() * 60 + now.minute();

        for window in &self.settings.allowed_time_windows {
            let start = (window.start_hour as u32) * 60 + (window.start_minute as u32);
            let end = (window.end_hour as u32) * 60 + (window.end_minute as u32);

            if current_minutes >= start && current_minutes < end {
                return true;
            }
        }

        false
    }

    fn is_allowed_weekday(&self) -> bool {
        let now = Local::now();
        let weekday = match now.weekday() {
            ChronoWeekday::Mon => super::settings::Weekday::Monday,
            ChronoWeekday::Tue => super::settings::Weekday::Tuesday,
            ChronoWeekday::Wed => super::settings::Weekday::Wednesday,
            ChronoWeekday::Thu => super::settings::Weekday::Thursday,
            ChronoWeekday::Fri => super::settings::Weekday::Friday,
            ChronoWeekday::Sat => super::settings::Weekday::Saturday,
            ChronoWeekday::Sun => super::settings::Weekday::Sunday,
        };

        self.settings.allowed_weekdays.contains(&weekday)
    }

    fn seconds_until_next_window(&self) -> u32 {
        // Placeholder - beregn tid til næste vindue
        3600
    }

    fn seconds_until_allowed_day(&self) -> u32 {
        // Placeholder - beregn tid til næste tilladte dag
        86400
    }

    fn calculate_max_duration(&self) -> u64 {
        // Max 30 minutter per bidragssession
        1800
    }

    fn get_allowed_task_types(&self) -> Vec<ContributionTaskType> {
        let mut types = Vec::new();

        if self.settings.allow_ai_inference {
            types.push(ContributionTaskType::AIInference);
        }
        if self.settings.allow_embedding_generation {
            types.push(ContributionTaskType::EmbeddingGeneration);
        }
        if self.settings.allow_data_preprocessing {
            types.push(ContributionTaskType::DataPreprocessing);
        }
        if self.settings.allow_network_caching {
            types.push(ContributionTaskType::NetworkCaching);
        }
        if self.settings.allow_model_distribution {
            types.push(ContributionTaskType::ModelDistribution);
        }

        types
    }
}
```

### 3.3 Avanceret Ressource Analyzer

```rust
// src-tauri/src/contribution/resource_analyzer.rs

use std::collections::VecDeque;
use std::time::{Duration, Instant};
use sysinfo::{System, SystemExt, CpuExt, DiskExt, NetworkExt};

/// Avanceret ressourceanalyse med historik og forudsigelse
pub struct AdvancedResourceAnalyzer {
    system: System,
    cpu_history: VecDeque<CpuSample>,
    ram_history: VecDeque<RamSample>,
    network_history: VecDeque<NetworkSample>,
    history_size: usize,
    sample_interval: Duration,
    last_sample: Instant,
}

#[derive(Clone)]
struct CpuSample {
    timestamp: Instant,
    usage_percent: f32,
    per_core: Vec<f32>,
}

#[derive(Clone)]
struct RamSample {
    timestamp: Instant,
    used_mb: u64,
    available_mb: u64,
    usage_percent: f32,
}

#[derive(Clone)]
struct NetworkSample {
    timestamp: Instant,
    bytes_sent: u64,
    bytes_received: u64,
    bandwidth_usage_percent: f32,
}

/// Detaljeret snapshot af systemressourcer
#[derive(Debug, Clone, serde::Serialize)]
pub struct DetailedResourceSnapshot {
    // CPU
    pub cpu_usage_percent: f32,
    pub cpu_per_core: Vec<f32>,
    pub cpu_frequency_mhz: u64,
    pub cpu_cores: usize,

    // RAM
    pub ram_total_mb: u64,
    pub ram_used_mb: u64,
    pub ram_available_mb: u64,
    pub ram_usage_percent: f32,

    // GPU (hvis tilgængelig)
    pub gpu_available: bool,
    pub gpu_name: Option<String>,
    pub gpu_usage_percent: Option<f32>,
    pub gpu_memory_used_mb: Option<u64>,
    pub gpu_memory_total_mb: Option<u64>,

    // Disk
    pub disk_total_mb: u64,
    pub disk_available_mb: u64,
    pub disk_io_read_kbps: f32,
    pub disk_io_write_kbps: f32,

    // Netværk
    pub network_up_kbps: f32,
    pub network_down_kbps: f32,
    pub network_latency_ms: Option<u32>,

    // Strøm
    pub on_battery: bool,
    pub battery_percent: Option<u8>,
    pub power_saving_mode: bool,

    // Idle
    pub idle_seconds: u32,
    pub idle_depth: IdleDepth,

    // Forudsigelser
    pub predicted_available_cpu: f32,
    pub predicted_available_ram_mb: u64,
    pub contribution_feasibility: ContributionFeasibility,
}

/// Idle dybde - hvor "dybt" systemet er i idle
#[derive(Debug, Clone, serde::Serialize)]
pub enum IdleDepth {
    /// Ikke idle - aktiv brugeraktivitet
    Active,
    /// Let idle - ingen input, men processer kører
    Light,
    /// Medium idle - minimal aktivitet
    Medium,
    /// Dyb idle - systemet er i ro
    Deep,
    /// Søvn-klar - systemet kan gå i dvale snart
    SleepReady,
}

/// Vurdering af om bidrag er fornuftigt
#[derive(Debug, Clone, serde::Serialize)]
pub struct ContributionFeasibility {
    pub is_feasible: bool,
    pub confidence: f32,
    pub max_recommended_cpu: u8,
    pub max_recommended_ram_mb: u32,
    pub recommended_duration_seconds: u64,
    pub warnings: Vec<String>,
}

impl AdvancedResourceAnalyzer {
    pub fn new() -> Self {
        Self {
            system: System::new_all(),
            cpu_history: VecDeque::with_capacity(60),
            ram_history: VecDeque::with_capacity(60),
            network_history: VecDeque::with_capacity(60),
            history_size: 60, // 5 minutters historik ved 5s interval
            sample_interval: Duration::from_secs(5),
            last_sample: Instant::now(),
        }
    }

    /// Tag en ny sample og opdater historik
    pub fn sample(&mut self) {
        self.system.refresh_all();

        let now = Instant::now();

        // CPU sample
        let cpu_usage = self.system.global_cpu_info().cpu_usage();
        let per_core: Vec<f32> = self.system.cpus()
            .iter()
            .map(|cpu| cpu.cpu_usage())
            .collect();

        self.cpu_history.push_back(CpuSample {
            timestamp: now,
            usage_percent: cpu_usage,
            per_core,
        });

        if self.cpu_history.len() > self.history_size {
            self.cpu_history.pop_front();
        }

        // RAM sample
        let ram_used = self.system.used_memory() / 1024 / 1024;
        let ram_total = self.system.total_memory() / 1024 / 1024;
        let ram_available = ram_total - ram_used;

        self.ram_history.push_back(RamSample {
            timestamp: now,
            used_mb: ram_used,
            available_mb: ram_available,
            usage_percent: (ram_used as f32 / ram_total as f32) * 100.0,
        });

        if self.ram_history.len() > self.history_size {
            self.ram_history.pop_front();
        }

        self.last_sample = now;
    }

    /// Få detaljeret ressource-snapshot
    pub fn get_detailed_snapshot(&mut self) -> DetailedResourceSnapshot {
        // Opdater hvis nødvendigt
        if self.last_sample.elapsed() > self.sample_interval {
            self.sample();
        }

        let cpu_usage = self.system.global_cpu_info().cpu_usage();
        let per_core: Vec<f32> = self.system.cpus()
            .iter()
            .map(|cpu| cpu.cpu_usage())
            .collect();

        let ram_used = self.system.used_memory() / 1024 / 1024;
        let ram_total = self.system.total_memory() / 1024 / 1024;

        // Beregn idle dybde
        let idle_depth = self.calculate_idle_depth(cpu_usage);

        // Forudsig tilgængelige ressourcer
        let (predicted_cpu, predicted_ram) = self.predict_available_resources();

        // Vurder bidragsmulighed
        let feasibility = self.assess_contribution_feasibility(
            cpu_usage,
            ram_used,
            ram_total,
            &idle_depth,
        );

        DetailedResourceSnapshot {
            cpu_usage_percent: cpu_usage,
            cpu_per_core: per_core,
            cpu_frequency_mhz: 0, // Platform-specifik
            cpu_cores: self.system.cpus().len(),

            ram_total_mb: ram_total,
            ram_used_mb: ram_used,
            ram_available_mb: ram_total - ram_used,
            ram_usage_percent: (ram_used as f32 / ram_total as f32) * 100.0,

            gpu_available: false, // TODO: Implementer GPU detection
            gpu_name: None,
            gpu_usage_percent: None,
            gpu_memory_used_mb: None,
            gpu_memory_total_mb: None,

            disk_total_mb: self.get_disk_total_mb(),
            disk_available_mb: self.get_disk_available_mb(),
            disk_io_read_kbps: 0.0,
            disk_io_write_kbps: 0.0,

            network_up_kbps: 0.0,
            network_down_kbps: 0.0,
            network_latency_ms: None,

            on_battery: false, // TODO: Platform-specifik
            battery_percent: None,
            power_saving_mode: false,

            idle_seconds: 0, // Fra IdleDetector
            idle_depth,

            predicted_available_cpu: predicted_cpu,
            predicted_available_ram_mb: predicted_ram,
            contribution_feasibility: feasibility,
        }
    }

    /// Beregn idle dybde baseret på CPU historik
    fn calculate_idle_depth(&self, current_cpu: f32) -> IdleDepth {
        if current_cpu > 30.0 {
            return IdleDepth::Active;
        }

        // Tjek historik for konsistent lav aktivitet
        let recent_avg = self.get_recent_cpu_average(12); // Sidste minut

        if recent_avg > 20.0 {
            IdleDepth::Light
        } else if recent_avg > 10.0 {
            IdleDepth::Medium
        } else if recent_avg > 5.0 {
            IdleDepth::Deep
        } else {
            IdleDepth::SleepReady
        }
    }

    fn get_recent_cpu_average(&self, samples: usize) -> f32 {
        let recent: Vec<f32> = self.cpu_history
            .iter()
            .rev()
            .take(samples)
            .map(|s| s.usage_percent)
            .collect();

        if recent.is_empty() {
            return 100.0;
        }

        recent.iter().sum::<f32>() / recent.len() as f32
    }

    fn predict_available_resources(&self) -> (f32, u64) {
        // Simpel forudsigelse baseret på historik
        let avg_cpu = self.get_recent_cpu_average(12);
        let predicted_available_cpu = 30.0 - avg_cpu; // 30% er system max

        let avg_ram = if !self.ram_history.is_empty() {
            let sum: f32 = self.ram_history.iter().map(|s| s.usage_percent).sum();
            sum / self.ram_history.len() as f32
        } else {
            50.0
        };

        let ram_total = self.system.total_memory() / 1024 / 1024;
        let predicted_available_ram = ((20.0 - avg_ram).max(0.0) / 100.0 * ram_total as f32) as u64;

        (predicted_available_cpu.max(0.0), predicted_available_ram)
    }

    fn assess_contribution_feasibility(
        &self,
        cpu_usage: f32,
        ram_used: u64,
        ram_total: u64,
        idle_depth: &IdleDepth,
    ) -> ContributionFeasibility {
        let mut warnings = Vec::new();

        let is_deep_enough = matches!(idle_depth, IdleDepth::Deep | IdleDepth::SleepReady);

        if !is_deep_enough {
            warnings.push("System er ikke dybt nok i idle".to_string());
        }

        let cpu_headroom = 30.0 - cpu_usage;
        if cpu_headroom < 10.0 {
            warnings.push(format!("Begrænset CPU headroom: {:.1}%", cpu_headroom));
        }

        let ram_percent = (ram_used as f32 / ram_total as f32) * 100.0;
        if ram_percent > 15.0 {
            warnings.push(format!("RAM brug over 15%: {:.1}%", ram_percent));
        }

        let is_feasible = is_deep_enough && cpu_headroom >= 5.0 && ram_percent < 20.0;

        ContributionFeasibility {
            is_feasible,
            confidence: if is_feasible { 0.85 } else { 0.2 },
            max_recommended_cpu: (cpu_headroom * 0.5).min(15.0) as u8,
            max_recommended_ram_mb: 512.min((ram_total - ram_used) / 4) as u32,
            recommended_duration_seconds: if is_feasible { 1800 } else { 0 },
            warnings,
        }
    }

    fn get_disk_total_mb(&self) -> u64 {
        self.system.disks()
            .iter()
            .map(|d| d.total_space() / 1024 / 1024)
            .sum()
    }

    fn get_disk_available_mb(&self) -> u64 {
        self.system.disks()
            .iter()
            .map(|d| d.available_space() / 1024 / 1024)
            .sum()
    }
}
```

---

## 4. FRONTEND IMPLEMENTATION

### 4.1 Contribution Store (TypeScript)

```typescript
// src/stores/contributionStore.ts

import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";

export interface ContributionSettings {
  // Master control
  enabled: boolean;
  userAcknowledgedTerms: boolean;
  termsAcceptedAt: string | null;

  // Resource limits
  contributionCpuPercent: number;
  contributionRamMb: number;
  contributionGpuPercent: number;
  contributionBandwidthKbps: number;
  contributionDiskMb: number;

  // Time windows
  timeWindowsEnabled: boolean;
  allowedTimeWindows: TimeWindow[];
  allowedWeekdays: Weekday[];

  // Conditions
  requireSystemIdle: boolean;
  idleBeforeContributionSeconds: number;
  requirePowerConnected: boolean;
  minBatteryForContribution: number;
  stopOnUserActivity: boolean;
  activityGracePeriodSeconds: number;

  // Task types
  allowAiInference: boolean;
  allowEmbeddingGeneration: boolean;
  allowDataPreprocessing: boolean;
  allowNetworkCaching: boolean;
  allowModelDistribution: boolean;

  // Security
  anonymizedTasksOnly: boolean;
  logAllActivities: boolean;
  maxTaskSizeMb: number;
}

export interface TimeWindow {
  startHour: number;
  startMinute: number;
  endHour: number;
  endMinute: number;
}

export type Weekday =
  | "Monday" | "Tuesday" | "Wednesday"
  | "Thursday" | "Friday" | "Saturday" | "Sunday";

export interface ContributionStatus {
  isContributing: boolean;
  currentTask: ContributionTask | null;
  sessionStats: SessionStats;
  lifetimeStats: LifetimeStats;
}

export interface ContributionTask {
  id: string;
  taskType: string;
  progress: number;
  cpuUsage: number;
  ramUsageMb: number;
  startedAt: string;
  estimatedCompletionSeconds: number;
}

export interface SessionStats {
  tasksCompleted: number;
  cpuSecondsContributed: number;
  dataProcessedMb: number;
  sessionDurationSeconds: number;
}

export interface LifetimeStats {
  totalTasksCompleted: number;
  totalCpuHoursContributed: number;
  totalDataProcessedGb: number;
  firstContributionAt: string | null;
  lastContributionAt: string | null;
  contributionScore: number;
}

interface ContributionState {
  settings: ContributionSettings;
  status: ContributionStatus;
  history: ContributionHistoryEntry[];
  loading: boolean;
  error: string | null;

  // Actions
  loadSettings: () => Promise<void>;
  updateSettings: (updates: Partial<ContributionSettings>) => Promise<void>;
  enableContribution: (acceptTerms: boolean) => Promise<void>;
  disableContribution: () => Promise<void>;
  loadStatus: () => Promise<void>;
  loadHistory: (limit: number) => Promise<void>;
}

export interface ContributionHistoryEntry {
  id: string;
  taskType: string;
  completedAt: string;
  cpuSecondsUsed: number;
  ramMbUsed: number;
  dataProcessedMb: number;
  success: boolean;
  errorMessage: string | null;
}

const defaultSettings: ContributionSettings = {
  // ALDRIG AKTIVERET SOM DEFAULT
  enabled: false,
  userAcknowledgedTerms: false,
  termsAcceptedAt: null,

  // Konservative grænser
  contributionCpuPercent: 50,
  contributionRamMb: 512,
  contributionGpuPercent: 40,
  contributionBandwidthKbps: 1024,
  contributionDiskMb: 500,

  // Tidsvindue deaktiveret
  timeWindowsEnabled: false,
  allowedTimeWindows: [],
  allowedWeekdays: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],

  // Strenge betingelser
  requireSystemIdle: true,
  idleBeforeContributionSeconds: 300,
  requirePowerConnected: true,
  minBatteryForContribution: 80,
  stopOnUserActivity: true,
  activityGracePeriodSeconds: 60,

  // Alle opgavetyper deaktiveret
  allowAiInference: false,
  allowEmbeddingGeneration: false,
  allowDataPreprocessing: false,
  allowNetworkCaching: false,
  allowModelDistribution: false,

  // Sikkerhed
  anonymizedTasksOnly: true,
  logAllActivities: true,
  maxTaskSizeMb: 100,
};

const defaultStatus: ContributionStatus = {
  isContributing: false,
  currentTask: null,
  sessionStats: {
    tasksCompleted: 0,
    cpuSecondsContributed: 0,
    dataProcessedMb: 0,
    sessionDurationSeconds: 0,
  },
  lifetimeStats: {
    totalTasksCompleted: 0,
    totalCpuHoursContributed: 0,
    totalDataProcessedGb: 0,
    firstContributionAt: null,
    lastContributionAt: null,
    contributionScore: 0,
  },
};

export const useContributionStore = create<ContributionState>((set, get) => ({
  settings: defaultSettings,
  status: defaultStatus,
  history: [],
  loading: false,
  error: null,

  loadSettings: async () => {
    set({ loading: true, error: null });
    try {
      const settings = await invoke<ContributionSettings>("get_contribution_settings");
      set({ settings, loading: false });
    } catch (error) {
      console.error("Failed to load contribution settings:", error);
      set({ error: String(error), loading: false });
    }
  },

  updateSettings: async (updates) => {
    set({ loading: true, error: null });
    try {
      const newSettings = await invoke<ContributionSettings>("update_contribution_settings", {
        updates,
      });
      set({ settings: newSettings, loading: false });
    } catch (error) {
      console.error("Failed to update contribution settings:", error);
      set({ error: String(error), loading: false });
    }
  },

  enableContribution: async (acceptTerms: boolean) => {
    if (!acceptTerms) {
      set({ error: "Du skal acceptere vilkårene for at aktivere enhedsbidrag" });
      return;
    }

    set({ loading: true, error: null });
    try {
      await invoke("enable_contribution", { acceptTerms });
      await get().loadSettings();
    } catch (error) {
      console.error("Failed to enable contribution:", error);
      set({ error: String(error), loading: false });
    }
  },

  disableContribution: async () => {
    set({ loading: true, error: null });
    try {
      await invoke("disable_contribution");
      await get().loadSettings();
    } catch (error) {
      console.error("Failed to disable contribution:", error);
      set({ error: String(error), loading: false });
    }
  },

  loadStatus: async () => {
    try {
      const status = await invoke<ContributionStatus>("get_contribution_status");
      set({ status });
    } catch (error) {
      console.error("Failed to load contribution status:", error);
    }
  },

  loadHistory: async (limit: number) => {
    try {
      const history = await invoke<ContributionHistoryEntry[]>("get_contribution_history", {
        limit,
      });
      set({ history });
    } catch (error) {
      console.error("Failed to load contribution history:", error);
    }
  },
}));
```

### 4.2 Contribution Panel Component

```tsx
// src/components/contribution/ContributionPanel.tsx

import React, { useEffect, useState } from "react";
import { useContributionStore } from "../../stores/contributionStore";
import {
  Power,
  Cpu,
  HardDrive,
  Wifi,
  Clock,
  Shield,
  BarChart3,
  AlertTriangle,
  CheckCircle2,
  Settings2
} from "lucide-react";

export const ContributionPanel: React.FC = () => {
  const {
    settings,
    status,
    history,
    loading,
    error,
    loadSettings,
    updateSettings,
    enableContribution,
    disableContribution,
    loadStatus,
    loadHistory,
  } = useContributionStore();

  const [showTermsModal, setShowTermsModal] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);

  useEffect(() => {
    loadSettings();
    loadStatus();
    loadHistory(20);

    // Poll status hvert 5. sekund
    const interval = setInterval(() => {
      if (settings.enabled) {
        loadStatus();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleEnableToggle = async () => {
    if (settings.enabled) {
      await disableContribution();
    } else {
      setShowTermsModal(true);
    }
  };

  const handleAcceptTerms = async () => {
    if (termsAccepted) {
      await enableContribution(true);
      setShowTermsModal(false);
    }
  };

  return (
    <div className="contribution-panel p-6 bg-gray-900 rounded-lg">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${settings.enabled ? 'bg-green-500/20' : 'bg-gray-700'}`}>
            <Power className={`w-6 h-6 ${settings.enabled ? 'text-green-400' : 'text-gray-400'}`} />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-white">Enhedsbidrag</h2>
            <p className="text-sm text-gray-400">
              Bidrag til Cirkelline-netværket med overskydende ressourcer
            </p>
          </div>
        </div>

        {/* Master Toggle */}
        <button
          onClick={handleEnableToggle}
          disabled={loading}
          className={`
            px-4 py-2 rounded-lg font-medium transition-all
            ${settings.enabled
              ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
              : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'}
          `}
        >
          {settings.enabled ? 'Deaktiver' : 'Aktiver'}
        </button>
      </div>

      {/* Status Indikator */}
      {settings.enabled && (
        <div className={`
          p-4 rounded-lg mb-6
          ${status.isContributing ? 'bg-green-500/10 border border-green-500/30' : 'bg-yellow-500/10 border border-yellow-500/30'}
        `}>
          <div className="flex items-center gap-3">
            {status.isContributing ? (
              <>
                <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse" />
                <span className="text-green-400 font-medium">Aktivt bidrag</span>
              </>
            ) : (
              <>
                <div className="w-3 h-3 bg-yellow-400 rounded-full" />
                <span className="text-yellow-400 font-medium">Venter på betingelser</span>
              </>
            )}
          </div>

          {status.currentTask && (
            <div className="mt-3 p-3 bg-black/20 rounded-lg">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-400">Opgave: {status.currentTask.taskType}</span>
                <span className="text-gray-400">{status.currentTask.progress}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className="bg-green-400 h-2 rounded-full transition-all"
                  style={{ width: `${status.currentTask.progress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Ressource Grænser */}
      {settings.enabled && (
        <div className="grid grid-cols-2 gap-4 mb-6">
          <ResourceSlider
            icon={<Cpu className="w-4 h-4" />}
            label="CPU Bidrag"
            value={settings.contributionCpuPercent}
            max={50}
            unit="%"
            onChange={(v) => updateSettings({ contributionCpuPercent: v })}
          />
          <ResourceSlider
            icon={<HardDrive className="w-4 h-4" />}
            label="RAM Bidrag"
            value={settings.contributionRamMb}
            max={2048}
            unit=" MB"
            onChange={(v) => updateSettings({ contributionRamMb: v })}
          />
          <ResourceSlider
            icon={<Wifi className="w-4 h-4" />}
            label="Båndbredde"
            value={settings.contributionBandwidthKbps}
            max={10240}
            unit=" KB/s"
            onChange={(v) => updateSettings({ contributionBandwidthKbps: v })}
          />
          <ResourceSlider
            icon={<Clock className="w-4 h-4" />}
            label="Min Idle Tid"
            value={settings.idleBeforeContributionSeconds}
            max={900}
            unit="s"
            onChange={(v) => updateSettings({ idleBeforeContributionSeconds: v })}
          />
        </div>
      )}

      {/* Statistik */}
      {settings.enabled && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <StatCard
            icon={<CheckCircle2 className="w-5 h-5 text-green-400" />}
            label="Opgaver Fuldført"
            value={status.lifetimeStats.totalTasksCompleted.toString()}
          />
          <StatCard
            icon={<Cpu className="w-5 h-5 text-blue-400" />}
            label="CPU Timer"
            value={status.lifetimeStats.totalCpuHoursContributed.toFixed(1)}
          />
          <StatCard
            icon={<BarChart3 className="w-5 h-5 text-purple-400" />}
            label="Bidragsscore"
            value={status.lifetimeStats.contributionScore.toString()}
          />
        </div>
      )}

      {/* Vilkår Modal */}
      {showTermsModal && (
        <TermsModal
          onAccept={handleAcceptTerms}
          onDecline={() => setShowTermsModal(false)}
          accepted={termsAccepted}
          setAccepted={setTermsAccepted}
        />
      )}

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
          <div className="flex items-center gap-2 text-red-400">
            <AlertTriangle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        </div>
      )}
    </div>
  );
};

// Helper Components
const ResourceSlider: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: number;
  max: number;
  unit: string;
  onChange: (value: number) => void;
}> = ({ icon, label, value, max, unit, onChange }) => (
  <div className="p-3 bg-gray-800 rounded-lg">
    <div className="flex items-center gap-2 mb-2">
      {icon}
      <span className="text-sm text-gray-400">{label}</span>
    </div>
    <input
      type="range"
      min={0}
      max={max}
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
      className="w-full"
    />
    <div className="text-right text-sm text-white mt-1">
      {value}{unit}
    </div>
  </div>
);

const StatCard: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: string;
}> = ({ icon, label, value }) => (
  <div className="p-4 bg-gray-800 rounded-lg text-center">
    <div className="flex justify-center mb-2">{icon}</div>
    <div className="text-2xl font-bold text-white">{value}</div>
    <div className="text-xs text-gray-400">{label}</div>
  </div>
);

const TermsModal: React.FC<{
  onAccept: () => void;
  onDecline: () => void;
  accepted: boolean;
  setAccepted: (v: boolean) => void;
}> = ({ onAccept, onDecline, accepted, setAccepted }) => (
  <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
    <div className="bg-gray-900 rounded-xl p-6 max-w-lg mx-4">
      <h3 className="text-xl font-bold text-white mb-4">
        Vilkår for Enhedsbidrag
      </h3>

      <div className="prose prose-invert text-sm mb-6">
        <p>Ved at aktivere enhedsbidrag accepterer du følgende:</p>
        <ul>
          <li>CLA vil kun bruge ressourcer inden for dine konfigurerede grænser</li>
          <li>Lokale opgaver har ALTID prioritet over netværksbidrag</li>
          <li>Bidrag stopper øjeblikkeligt ved brugeraktivitet</li>
          <li>Alle data der behandles er anonymiserede</li>
          <li>Du kan til enhver tid deaktivere bidrag</li>
        </ul>
      </div>

      <label className="flex items-center gap-3 mb-6 cursor-pointer">
        <input
          type="checkbox"
          checked={accepted}
          onChange={(e) => setAccepted(e.target.checked)}
          className="w-5 h-5"
        />
        <span className="text-gray-300">
          Jeg har læst og accepterer vilkårene
        </span>
      </label>

      <div className="flex gap-3">
        <button
          onClick={onDecline}
          className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600"
        >
          Annuller
        </button>
        <button
          onClick={onAccept}
          disabled={!accepted}
          className={`
            flex-1 px-4 py-2 rounded-lg font-medium
            ${accepted
              ? 'bg-green-500 text-white hover:bg-green-600'
              : 'bg-gray-700 text-gray-500 cursor-not-allowed'}
          `}
        >
          Aktiver Bidrag
        </button>
      </div>
    </div>
  </div>
);
```

---

## 5. CKC BACKEND API INTEGRATION

### 5.1 Contribution API Endpoints (CKC)

```python
# CKC Backend - api/contribution.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/contribution", tags=["Contribution"])

class ContributionPotential(BaseModel):
    """Rapporteret bidragspotentiale fra en CLA"""
    device_id: str
    available_cpu_percent: float
    available_ram_mb: int
    available_gpu_percent: Optional[float]
    available_bandwidth_kbps: int
    idle_depth: str  # "light", "medium", "deep", "sleep_ready"
    allowed_task_types: List[str]
    max_duration_seconds: int
    estimated_availability_hours: float

class ContributionTask(BaseModel):
    """Opgave tildelt til en CLA"""
    task_id: str
    task_type: str
    payload_url: str
    payload_size_mb: float
    expected_cpu_percent: int
    expected_ram_mb: int
    expected_duration_seconds: int
    priority: int
    deadline: Optional[datetime]

class TaskResult(BaseModel):
    """Resultat fra en fuldført opgave"""
    task_id: str
    device_id: str
    success: bool
    result_url: Optional[str]
    error_message: Optional[str]
    cpu_seconds_used: float
    ram_mb_peak: int
    processing_time_seconds: float

@router.post("/register")
async def register_contribution_potential(potential: ContributionPotential):
    """
    CLA rapporterer sit bidragspotentiale til CKC.
    Kaldes periodisk (hvert 30 sekund) når bidrag er aktivt.
    """
    # TODO: Gem i Redis med TTL
    # TODO: Opdater device registry
    return {"status": "registered", "device_id": potential.device_id}

@router.get("/tasks/{device_id}")
async def get_assigned_tasks(device_id: str) -> List[ContributionTask]:
    """
    CLA henter tildelte opgaver baseret på rapporteret potentiale.
    """
    # TODO: Match opgaver til device baseret på capabilities
    return []

@router.post("/tasks/{task_id}/accept")
async def accept_task(task_id: str, device_id: str):
    """
    CLA accepterer en opgave og starter behandling.
    """
    return {"status": "accepted", "task_id": task_id}

@router.post("/tasks/{task_id}/result")
async def submit_task_result(task_id: str, result: TaskResult):
    """
    CLA rapporterer resultat af fuldført opgave.
    """
    # TODO: Gem resultat
    # TODO: Opdater device score
    return {"status": "received", "task_id": task_id}

@router.post("/tasks/{task_id}/abort")
async def abort_task(task_id: str, device_id: str, reason: str):
    """
    CLA afbryder en opgave (f.eks. ved brugeraktivitet).
    """
    return {"status": "aborted", "task_id": task_id}

@router.get("/stats/{device_id}")
async def get_device_stats(device_id: str):
    """
    Hent statistik for en specifik enhed.
    """
    return {
        "device_id": device_id,
        "total_tasks_completed": 0,
        "total_cpu_hours": 0.0,
        "contribution_score": 0,
        "rank": None,
    }

@router.get("/network/stats")
async def get_network_stats():
    """
    Hent overordnet netværksstatistik.
    """
    return {
        "active_contributors": 0,
        "total_capacity_gflops": 0.0,
        "tasks_pending": 0,
        "tasks_completed_24h": 0,
    }
```

---

## 6. IMPLEMENTERINGSPLAN

### Fase 1: Fundament (Uge 1-2)
- [ ] Opret `contribution/` modul i Rust backend
- [ ] Implementer `ContributionSettings` struct
- [ ] Implementer `ContributionPermissionEngine`
- [ ] Tilføj Tauri commands til settings

### Fase 2: Ressourceanalyse (Uge 3-4)
- [ ] Implementer `AdvancedResourceAnalyzer`
- [ ] Tilføj idle depth beregning
- [ ] Implementer ressource-forudsigelse
- [ ] Integrer med eksisterende `ResourceLimiter`

### Fase 3: Frontend (Uge 5-6)
- [ ] Opret `contributionStore.ts`
- [ ] Implementer `ContributionPanel` komponent
- [ ] Tilføj vilkårs-modal
- [ ] Implementer realtids-statusvisning

### Fase 4: Netværk (Uge 7-8)
- [ ] Implementer CKC API endpoints
- [ ] Implementer CLA network client
- [ ] Tilføj opgave-scheduler
- [ ] Implementer resultat-rapportering

### Fase 5: Test & Sikkerhed (Uge 9-10)
- [ ] Enhedstest for alle komponenter
- [ ] Integrationstest med CKC
- [ ] Sikkerhedsaudit af dataflow
- [ ] Performance-test under load

---

## 7. SIKKERHEDSOVERVEJELSER

### 7.1 Datahåndtering
- Alle opgavedata krypteres under transit (TLS 1.3)
- Ingen personlige data forlader enheden uden eksplicit samtykke
- Anonymisering af alle behandlede data

### 7.2 Brugerbeskyttelse
- Opt-in er **obligatorisk** og kan aldrig omgås
- Øjeblikkelig stop-mekanisme ved brugeraktivitet
- Fuld audit trail af alle bidrag

### 7.3 Ressourcebeskyttelse
- Hårde grænser der aldrig kan overskrides
- Fallback til konservative defaults ved fejl
- Automatisk stop ved systembelastning

---

## 8. FREMTIDIGE MULIGHEDER

### 8.1 Belønningsmekanismer (Ikke implementeret endnu)
- Contribution score tracking
- Potentielle token-baserede belønninger
- Tier-baserede fordele for aktive bidragydere

### 8.2 Avancerede Opgavetyper
- Distribueret model-træning
- Federated learning
- Edge AI inference network

---

*Dokument oprettet: 2025-12-08*
*Sidste opdatering: 2025-12-08*
*Ansvarlig: Claude Code / Cirkelline Team*
