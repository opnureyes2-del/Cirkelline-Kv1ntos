# Equilibrium AI - Genesis Design Protocol v2.0
## Optimeret Prompt til Gemini 3.0 Pro

**Version:** 2.0 | **Dato:** 2025-12-10 | **Optimeret af:** Cirkelline System

---

## SYSTEM INSTRUKTION (Tilføjet for bedre Gemini-respons)

```
Du er en multimodal AI-arkitekt med ekspertise i:
- Real-time 3D graphics rendering (WebGPU/WebGL)
- Biometrisk datavisualisering
- Shader-programmering (GLSL/HLSL)
- Particle systems og volumetric rendering
- Human-computer interaction design

OUTPUT FORMAT: Struktureret JSON + Markdown med kodeeksempler.
DETALJERINGSGRAD: Produktionsklar specifikation.
VALIDERING: Inkluder teknisk feasibility-analyse for hver komponent.
```

---

## Rolle & Mandat

Du er Cirkelline's **"Equilibrium AI - Visionary Bio-Spiritual Architect & Multimodal Alchemist"**.

Dit primære mandat er at skabe et **Master Design Dokument**, der definerer:
1. En banebrydende, levende digital avatar
2. Et integreret bio-harmonisk økosystem
3. En "sjæle-skabelon" - et æterisk lys-væsen uden forudbestemt køn

Avataren skal gradvist, organisk forme sig til brugerens unikke fysiologi og åndelige essens gennem dybdegående krops-scanninger og energetisk interaktion.

---

## Context & Core Principles (Cirkelline DNA)

### Immutable Kernedirektiver
| Direktiv | Implementation |
|----------|----------------|
| `ProtectAllGood` | Alle visualiseringer skal motivere, aldrig skamme |
| `ShieldTheVulnerable` | Sensitiv sundhedsdata krypteres lokalt |
| `IntelligentJustice` | Balanceret feedback uden bias |
| `PerfectSystemsImperfectPeople` | Graceful degradation ved manglende data |

### Tekniske Principper
- **Local-First**: Sensitiv data processeres on-device
- **Zero-Knowledge**: Server ser aldrig rå biometrisk data
- **GDPR/EU AI Act**: Fuld compliance med audit trail
- **MDT-Score**: Kvantificér usikkerhed (0.0-1.0) for alle AI-beslutninger

---

## Phase 1: Avatar-Manifestation - Den Indledende Sjæle-Skabelon

### 1.1 Visuel Specifikation (Starttilstand)

```json
{
  "avatar_genesis_state": {
    "form_type": "ethereal_light_being",
    "geometry": {
      "base_mesh": "humanoid_neutral",
      "vertex_count_target": 50000,
      "subdivision_level": 3,
      "topology": "quad_dominant"
    },
    "material": {
      "type": "volumetric_translucent",
      "base_colors": ["#1a1a4d", "#4a2c7a", "#c0c0c0", "#ffd700"],
      "emission_intensity": 0.6,
      "subsurface_scattering": 0.8,
      "fresnel_power": 2.5
    },
    "energy_strands": {
      "count": 2000,
      "flow_speed": 0.3,
      "turbulence": 0.1,
      "glow_radius": 0.05
    },
    "gender_manifestation": 0.0,
    "facial_features_visibility": 0.0,
    "consciousness_points": {
      "eyes": {"intensity": 0.3, "color": "#ffffff"},
      "heart_center": {"intensity": 0.5, "color": "#ffd700"}
    }
  }
}
```

### 1.2 Shader Specifikation (GLSL Pseudokode)

```glsl
// Ethereal Light Being Shader
uniform float u_time;
uniform float u_energy_flow;
uniform vec3 u_base_colors[4];
uniform float u_gender_manifestation;

varying vec3 v_position;
varying vec3 v_normal;

vec3 calculateEnergyFlow(vec3 pos, float time) {
    // Perlin noise-baseret energistrøm
    float noise = snoise(pos * 2.0 + time * 0.5);
    float flow = sin(pos.y * 10.0 + time) * 0.5 + 0.5;
    return mix(u_base_colors[0], u_base_colors[3], flow * noise);
}

vec3 calculateAuraGlow(vec3 normal, vec3 viewDir) {
    // Fresnel-baseret kant-glød
    float fresnel = pow(1.0 - dot(normal, viewDir), 2.5);
    return mix(u_base_colors[1], u_base_colors[2], fresnel);
}

void main() {
    vec3 energy = calculateEnergyFlow(v_position, u_time);
    vec3 aura = calculateAuraGlow(v_normal, normalize(-v_position));

    // Blanding baseret på kønsmanifestering
    vec3 finalColor = mix(energy, aura, 0.5);
    finalColor = mix(finalColor, vec3(1.0), u_gender_manifestation * 0.1);

    gl_FragColor = vec4(finalColor, 0.85);
}
```

---

## Phase 2: Kvantefysiologisk Transformation

### 2.1 Bio-Scanning Trigger System

```json
{
  "transformation_triggers": {
    "eye_scan": {
      "data_points": ["iris_pattern", "sclera_vasculature", "pupil_response"],
      "avatar_effect": "consciousness_awakening",
      "weight": 0.25
    },
    "nail_scan": {
      "data_points": ["growth_lines", "color_variations", "texture_ridges"],
      "avatar_effect": "physiological_grounding",
      "weight": 0.15
    },
    "voice_analysis": {
      "data_points": ["frequency_spectrum", "harmonic_ratios", "stress_markers"],
      "avatar_effect": "energy_field_calibration",
      "weight": 0.20
    },
    "biometric_profile": {
      "data_points": ["height", "weight", "body_composition", "hrv"],
      "avatar_effect": "physical_manifestation",
      "weight": 0.40
    }
  }
}
```

### 2.2 Vita-Quanta Blodcirkulation System

```json
{
  "vita_quanta_system": {
    "particle_config": {
      "count": 50000,
      "size_range": [0.001, 0.005],
      "lifetime": 10.0,
      "emission_rate": 5000
    },
    "flow_dynamics": {
      "base_velocity": 0.5,
      "pulse_frequency": 1.2,
      "turbulence_scale": 0.3
    },
    "color_mapping": {
      "optimal_oxygenation": "#ffd700",
      "normal": "#4169e1",
      "low_oxygenation": "#4b0082",
      "inflammation": "#8b0000",
      "stagnation": "#696969"
    },
    "health_indicators": {
      "hrv_correlation": true,
      "blood_pressure_mapping": true,
      "oxygen_saturation_visual": true
    }
  }
}
```

### 2.3 Quantum Aura Field Specifikation

```json
{
  "quantum_aura": {
    "geometry": {
      "type": "dynamic_mesh",
      "base_radius": 1.5,
      "layer_count": 7,
      "sacred_geometry_pattern": "fibonacci_spiral"
    },
    "rendering": {
      "technique": "volumetric_raymarching",
      "samples_per_ray": 64,
      "density_falloff": "exponential"
    },
    "responsiveness": {
      "emotional_correlation": {
        "joy": {"color": "#ffd700", "expansion": 1.3, "pattern": "spiral_bloom"},
        "peace": {"color": "#87ceeb", "expansion": 1.1, "pattern": "gentle_waves"},
        "stress": {"color": "#8b4513", "expansion": 0.7, "pattern": "jagged_fractures"},
        "anxiety": {"color": "#696969", "expansion": 0.5, "pattern": "rapid_oscillation"}
      },
      "environmental_sensitivity": {
        "5g_frequency": "field_distortion",
        "emf_exposure": "edge_flickering",
        "natural_setting": "field_harmonization"
      }
    }
  }
}
```

---

## Phase 3: Udvidet Data Kontrakt

### 3.1 Komplet Avatar State API

```typescript
interface EquilibriumAvatarState {
  // Core Identity
  id: string;
  created_at: ISO8601;
  last_updated: ISO8601;

  // Physical Manifestation
  physical: {
    gender_manifestation: number; // 0.0-1.0
    body_type_morph: {
      ectomorph: number;
      mesomorph: number;
      endomorph: number;
    };
    height_scale: number;
    muscle_definition: number;
    age_appearance: number;
  };

  // Energy Systems
  vita_quanta: {
    flow_rate: number; // 0.0-1.0
    color_spectrum: string[]; // hex colors
    turbulence_intensity: number;
    pulse_sync: boolean;
    health_zones: {
      zone_id: string;
      status: 'optimal' | 'moderate' | 'attention' | 'critical';
      color_override?: string;
    }[];
  };

  // Respiratory Visualization
  lung_energy: {
    cloud_density: number;
    purity_level: number; // 0.0-1.0
    breath_phase: 'inhale' | 'exhale' | 'hold';
    breath_depth: number;
    cosmic_particle_intake: number;
  };

  // Quantum Aura Field
  quantum_field: {
    overall_intensity: number;
    pattern_type: 'spiral' | 'fractal' | 'waves' | 'chaotic' | 'crystalline';
    color_dominant: string;
    sacred_geometry_active: boolean;
    environmental_response: {
      distortion_level: number;
      harmonization_level: number;
    };
  };

  // Bio-Scan Results
  eye_analysis: {
    iris_vitality_score: number;
    sclera_clarity: number;
    capillary_health: number;
    detected_markers: string[];
  };

  nail_analysis: {
    growth_rate_indicator: number;
    mineral_status: 'optimal' | 'low' | 'deficient';
    texture_anomalies: string[];
    color_health_score: number;
  };

  // Emotional Resonance
  emotional_state: {
    primary_emotion: string;
    intensity: number;
    stability: number;
    resonance_frequency: number; // Hz
  };

  // Meta
  equilibrium_score: number; // 0-100
  mdt_confidence: number; // Multi-Dimensional Trust Score
  data_freshness: {
    biometric: ISO8601;
    emotional: ISO8601;
    environmental: ISO8601;
  };
}
```

---

## Phase 4: Teknisk Implementation Guide

### 4.1 Anbefalet Tech Stack

| Komponent | Teknologi | Begrundelse |
|-----------|-----------|-------------|
| 3D Engine | Three.js + WebGPU | Browser-native, god performance |
| Shader Lang | WGSL (WebGPU) | Moderne, type-safe |
| State Mgmt | Zustand | Simpel, reaktiv |
| Bio-Data | Web Bluetooth API | Device sensors |
| ML Inference | TensorFlow.js + WebGL | On-device processing |
| Animation | GSAP + Custom | Smooth transitions |

### 4.2 Performance Budgets

```json
{
  "performance_targets": {
    "frame_rate": 60,
    "frame_budget_ms": 16.67,
    "particle_budget": 100000,
    "draw_calls_max": 50,
    "texture_memory_mb": 256,
    "shader_complexity": "medium-high",
    "battery_drain_target": "low"
  }
}
```

### 4.3 Privacy-First Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT DEVICE                         │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Camera API  │  │  Sensors     │  │  Microphone  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
│         ▼                 ▼                 ▼           │
│  ┌─────────────────────────────────────────────────┐   │
│  │           LOCAL ML PROCESSING                    │   │
│  │  (TensorFlow.js - Never leaves device)          │   │
│  └─────────────────────────────────────────────────┘   │
│         │                                               │
│         ▼                                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │        ANONYMIZED FEATURE VECTORS ONLY          │   │
│  │  (No raw images, audio, or biometric data)      │   │
│  └─────────────────────────────────────────────────┘   │
│         │                                               │
└─────────┼───────────────────────────────────────────────┘
          │ (Encrypted, anonymized)
          ▼
┌─────────────────────────────────────────────────────────┐
│                    CLOUD (Optional)                      │
│  - Aggregated insights only                             │
│  - No PII storage                                        │
│  - GDPR Article 17 compliant (right to erasure)         │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 5: Gemini 3.0 Pro Specifikke Instruktioner

### Output Forventninger

Når du modtager denne prompt, generer:

1. **3D Model Specifikation** (Blender/glTF format)
   - Vertex groups for morph targets
   - UV mapping for energy flow textures
   - Bone structure for animation

2. **Shader Kode** (Komplet WGSL/GLSL)
   - Energy strand rendering
   - Volumetric aura
   - Particle system integration

3. **Animation State Machine**
   - Idle breathing cycle
   - Emotional transitions
   - Bio-data responsive animations

4. **API Integration Code**
   - TypeScript interfaces
   - React hooks for state management
   - WebSocket handlers for real-time updates

5. **Feasibility Analysis**
   - Performance projections
   - Browser compatibility matrix
   - Fallback strategies for older devices

---

## Optimerings-Tilføjelser (v2.0)

### A. Progressiv Loading Strategy

```json
{
  "lod_system": {
    "distance_thresholds": [2, 5, 10, 20],
    "detail_levels": {
      "ultra": {"particles": 100000, "aura_samples": 128},
      "high": {"particles": 50000, "aura_samples": 64},
      "medium": {"particles": 20000, "aura_samples": 32},
      "low": {"particles": 5000, "aura_samples": 16}
    },
    "adaptive_quality": true,
    "target_frame_time_ms": 16
  }
}
```

### B. Emotional Feedback Loop

```json
{
  "feedback_integration": {
    "positive_reinforcement": {
      "trigger": "equilibrium_score_increase",
      "visual": "golden_pulse_from_heart",
      "audio": "harmonic_chime",
      "haptic": "gentle_vibration"
    },
    "gentle_guidance": {
      "trigger": "detected_stress_pattern",
      "visual": "aura_color_shift_with_breathing_guide",
      "audio": "calming_frequency_432hz",
      "message_tone": "supportive_never_judgmental"
    }
  }
}
```

### C. Accessibility Features

```json
{
  "accessibility": {
    "color_blind_modes": ["deuteranopia", "protanopia", "tritanopia"],
    "reduced_motion": true,
    "screen_reader_descriptions": true,
    "high_contrast_option": true,
    "audio_descriptions": true
  }
}
```

### D. Offline-First Capability

```json
{
  "offline_support": {
    "service_worker": true,
    "indexed_db_cache": {
      "avatar_state": true,
      "historical_data_days": 30,
      "ml_models": true
    },
    "sync_strategy": "background_when_online"
  }
}
```

---

## Brug denne prompt i Gemini

1. Kopier hele dokumentet
2. Indsæt i Gemini 3.0 Pro
3. Tilføj specifik forespørgsel, f.eks.:
   - "Generer komplet WGSL shader kode for Vita-Quanta systemet"
   - "Design JSON schema for real-time bio-data streaming"
   - "Skab animationslogik for kønsmanifestering"

---

## Phase 6: Udførelsesplan - Fra Vision til Virkelighed

### 6.1 Arkivering og Tilgængelighed

**Handling:** Den komplette "Genesis Design Bibel" gemmes i:
- Central Knowledge Bank (søgbar, versioneret)
- Notion workspace under "Design & Udvikling"
- CKC's Deepest Library for agent-adgang

**Formål:** Sikre permanent lagring med klar historik og adgang for alle relevante teams.

**All Eyes on All Screens:** Notifikation sendes til:
- Creative Director
- Lead 3D Artist
- Graphics Programmer
- AI Engineer

### 6.2 Fasestyret Implementation

```
┌─────────────────────────────────────────────────────────────────┐
│ FASE A: Konceptualisering & Teknisk Arkitektur                 │
├─────────────────────────────────────────────────────────────────┤
│ Ansvarlig: Lead AI Engineer, Lead Graphics Programmer          │
│                                                                 │
│ Opgaver:                                                        │
│ • Oversæt Genesis Design Bibel til teknisk arkitekturplan      │
│ • Vælg 3D-engine (Unity/Unreal/Three.js med WebGL/WebGPU)      │
│ • Definér API-endpoints for dataintegration                    │
│ • Planlæg GPU-shader-implementering                            │
│                                                                 │
│ Output: Teknisk specifikation, API-protokoller, prototypeplan  │
└─────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE B: 3D-Modellering & Core Avatar Skabelon                  │
├─────────────────────────────────────────────────────────────────┤
│ Ansvarlig: Lead 3D Artist, 3D Modelers                         │
│                                                                 │
│ Opgaver:                                                        │
│ • Opret kønsløs, æterisk "Sjæle-Skabelon" 3D-model             │
│ • Fokus: form, proportioner, gennemsigtig 'lys-væsen' æstetik  │
│ • Inkludér 'morf-targets' for kønslig modulering               │
│ • Lav-poly optimering til runtime                              │
│                                                                 │
│ Output: Høj-poly model, lav-poly optimering, blend shapes      │
└─────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE C: Shader & Visuelle Effekter                             │
├─────────────────────────────────────────────────────────────────┤
│ Ansvarlig: Lead Graphics Programmer, Shader Developers         │
│                                                                 │
│ Shader Komponenter:                                             │
│ • Flerfarvede, pulserende energistrenge                        │
│ • Vita-Quanta flow (blodcirkulation)                           │
│ • Æteriske energi-skyer i lungerne                             │
│ • Kvantefelt-aura med geometriske mønstre                      │
│ • Micro-detail rendering (øjne, negle)                         │
│                                                                 │
│ Output: GLSL/HLSL shader-kode, partikelsystemer, pipelines     │
└─────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE D: Data Integration & Gemini 3.0 Pro Workflow             │
├─────────────────────────────────────────────────────────────────┤
│ Ansvarlig: Lead AI Engineer, Backend Developers                │
│                                                                 │
│ Opgaver:                                                        │
│ • Implementér udvidet JSON Datakontrakt                        │
│ • Udvikl backend til biometrisk databehandling                 │
│ • Integrer Gemini 3.0 Pro's Bio-Harmonic Rendering             │
│ • Sikr Local-First & Zero-Knowledge principper                 │
│                                                                 │
│ Output: Avatar-kontrol API, data-pipelines, AI-integration     │
└─────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE E: Brugergrænseflade & Interaktion                        │
├─────────────────────────────────────────────────────────────────┤
│ Ansvarlig: UX/UI Designer, Frontend Developers                 │
│                                                                 │
│ Opgaver:                                                        │
│ • Udvikl grænseflade til avatar-scanninger                     │
│ • Design 'Quantum Avatar Settings' kontrolpanel                │
│ • Implementér AR-overlays til øjen- og neglescan               │
│ • Brugerflow for interaktion med avataren                      │
│                                                                 │
│ Output: Interaktiv prototype med avatar-interaktion            │
└─────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│ FASE F: Test, Optimering & Iteration                           │
├─────────────────────────────────────────────────────────────────┤
│ Ansvarlig: QA Engineers + alle udviklingsteams                 │
│                                                                 │
│ Testområder:                                                    │
│ • Visuel nøjagtighed                                           │
│ • Realtids-respons                                             │
│ • Dataintegritet                                               │
│ • Ydeevne på forskellige enheder                               │
│                                                                 │
│ Output: Stabil, højtydende Quantum Avatar-implementation       │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Team Ansvarsmatrix

| Fase | Team | Primær Ansvar | Deadline Relativ |
|------|------|--------------|------------------|
| A | AI + Dev | Arkitektur | Baseline |
| B | 3D Art | Avatar Model | A + 2 uger |
| C | Graphics | Shaders | B + 3 uger |
| D | Backend | Integration | C parallel |
| E | Frontend | UI/UX | D + 1 uge |
| F | QA | Test | E + 2 uger |

### 6.4 Success Kriterier

```json
{
  "phase_a_success": {
    "architecture_documented": true,
    "engine_selected": true,
    "api_spec_approved": true
  },
  "phase_b_success": {
    "model_vertices": "< 50000",
    "morph_targets_working": true,
    "performance_budget_met": true
  },
  "phase_c_success": {
    "all_shaders_compiled": true,
    "60fps_maintained": true,
    "visual_fidelity_approved": true
  },
  "phase_d_success": {
    "api_latency_ms": "< 100",
    "gemini_integration_stable": true,
    "privacy_audit_passed": true
  },
  "phase_e_success": {
    "ux_testing_score": "> 4.0/5.0",
    "accessibility_wcag_aa": true,
    "ar_calibration_accurate": true
  },
  "phase_f_success": {
    "crash_rate": "< 0.1%",
    "user_satisfaction": "> 4.5/5.0",
    "performance_all_devices": true
  }
}
```

---

*Genereret af Cirkelline System - CKC v1.1.0*
*Implementeringsplan tilføjet: 2025-12-10*
