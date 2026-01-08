# CLA Local AI Guide

Version: 1.0 | Opdateret: 2025-12-12

---

## Indhold

1. [Oversigt](#oversigt)
2. [Model Tiers](#model-tiers)
3. [Installation af Modeller](#installation-af-modeller)
4. [Inference Engine](#inference-engine)
5. [Resource Management](#resource-management)
6. [Offline Capabilities](#offline-capabilities)
7. [Performance Tuning](#performance-tuning)
8. [Troubleshooting](#troubleshooting)

---

## Oversigt

Cirkelline Local Agent (CLA) kører AI-modeller lokalt på brugerens enhed for at muliggøre:

- **Privacybevarende inferens** - Data forlader ikke enheden
- **Offline funktionalitet** - Fungerer uden internetforbindelse
- **Lavere latency** - Ingen netværksroundtrip
- **Ressourcerespekt** - Kører kun når systemet tillader det

### Arkitektur

```
┌──────────────────────────────────────────────────┐
│                  CLA Frontend                     │
│            (React + TypeScript)                   │
├──────────────────────────────────────────────────┤
│                 Tauri Bridge                      │
│              (IPC Commands)                       │
├──────────────────────────────────────────────────┤
│              Rust Inference Engine                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────┐  │
│  │  Embeddings  │ │   Whisper    │ │   OCR    │  │
│  │  (ONNX)      │ │   (ONNX)     │ │ (Paddle) │  │
│  └──────────────┘ └──────────────┘ └──────────┘  │
├──────────────────────────────────────────────────┤
│              Model Storage                        │
│        ~/.cirkelline/models/                      │
└──────────────────────────────────────────────────┘
```

---

## Model Tiers

CLA organiserer modeller i 3 tiers baseret på størrelse og funktionalitet.

### Tier 1 - Essential (81MB total)

Altid downloaded ved installation. Dækker kernefunktionalitet.

| Model | Størrelse | Funktion | Latency |
|-------|-----------|----------|---------|
| **all-MiniLM-L6-v2** | 23 MB | Tekst embeddings (384-dim) | < 50ms |
| **Whisper Tiny** | 39 MB | Audio transkription | < 5x realtime |
| **PaddleOCR Mobile** | 19 MB | OCR tekstudtrækning | < 300ms/side |

**Brug:**
- Hurtig søgning i lokale dokumenter
- Grundlæggende stemmetransskription
- OCR af billeder og PDF'er

### Tier 2 - Standard (602MB total)

Valgfri, forbedret kvalitet.

| Model | Størrelse | Funktion | Forbedring |
|-------|-----------|----------|------------|
| **Whisper Small** | 244 MB | Bedre transkription | +15% accuracy |
| **PaddleOCR Server** | 120 MB | Bedre OCR | +20% accuracy |
| **Sentence-T5-Base** | 238 MB | Bedre embeddings | +10% relevans |

**Anbefalet til:**
- Professionelle brugere
- Multilingual content
- Dokumenter med kompleks layout

### Tier 3 - Professional (2.4GB total)

Opt-in, højeste kvalitet. Kræver kraftigere hardware.

| Model | Størrelse | Funktion | Krav |
|-------|-----------|----------|------|
| **Whisper Medium** | 769 MB | Professionel transkription | 8GB RAM |
| **BGE-Large-EN** | 335 MB | Premium embeddings | 4GB RAM |
| **LayoutLM** | 430 MB | Dokumentforståelse | 6GB RAM |
| **LLaMA-2-7B-Q4** | 4 GB | Lokal LLM (valgfri) | 16GB RAM, GPU |

---

## Installation af Modeller

### Via UI (Anbefalet)

1. Åbn CLA
2. Gå til "AI-modeller" siden
3. Vælg tier og modeller
4. Klik download

### Via CLI

```bash
# List tilgængelige modeller
cirkelline-local-agent models list

# Download specifik model
cirkelline-local-agent models download all-minilm-l6-v2
cirkelline-local-agent models download whisper-tiny
cirkelline-local-agent models download paddleocr-mobile

# Download hele tier
cirkelline-local-agent models download --tier 1
cirkelline-local-agent models download --tier 2
```

### Filplacering

```
~/.cirkelline/
├── models/
│   ├── embeddings/
│   │   ├── all-minilm-l6-v2.onnx
│   │   └── sentence-t5-base.onnx
│   ├── whisper/
│   │   ├── whisper-tiny.onnx
│   │   └── whisper-small.onnx
│   └── ocr/
│       ├── paddleocr-mobile.onnx
│       └── paddleocr-server.onnx
├── config.json
└── device_id
```

### Verifikation

```bash
# Verificer modeller
cirkelline-local-agent models verify

# Output:
# ✓ all-minilm-l6-v2.onnx (23 MB, checksum OK)
# ✓ whisper-tiny.onnx (39 MB, checksum OK)
# ✓ paddleocr-mobile.onnx (19 MB, checksum OK)
```

---

## Inference Engine

### ONNX Runtime

CLA bruger ONNX Runtime til model execution:

- **Cross-platform** - Fungerer på Windows, macOS, Linux
- **Hardware acceleration** - CPU, GPU (CUDA, DirectML, CoreML)
- **Optimeret** - Grafoptimering og quantization support

### Embeddings

```rust
// Intern API (Rust)
pub async fn generate_embedding(text: &str) -> Result<Vec<f32>, InferenceError> {
    let model = load_model("all-minilm-l6-v2")?;
    let tokens = tokenize(text)?;
    let output = model.run(tokens)?;
    Ok(normalize(output))
}
```

**Specifikationer:**
- Output dimension: 384 (Tier 1) / 768 (Tier 2+)
- Max input: 512 tokens
- Batch size: 1-32

### Whisper Transkription

```rust
// Intern API (Rust)
pub async fn transcribe_audio(audio_path: &Path) -> Result<Transcript, InferenceError> {
    let model = load_model("whisper-tiny")?;
    let audio = load_audio(audio_path)?;
    let segments = model.transcribe(audio)?;
    Ok(Transcript::from_segments(segments))
}
```

**Specifikationer:**
- Understøttede formater: WAV, MP3, FLAC, OGG
- Max længde: 30 minutter (Tier 1), ubegrænset (Tier 2+)
- Sprog: 99 sprog understøttet

### OCR Processing

```rust
// Intern API (Rust)
pub async fn extract_text(image_path: &Path) -> Result<OcrResult, InferenceError> {
    let model = load_model("paddleocr-mobile")?;
    let image = load_image(image_path)?;
    let regions = model.detect(image)?;
    let text = model.recognize(regions)?;
    Ok(OcrResult::new(text, regions))
}
```

**Specifikationer:**
- Understøttede formater: PNG, JPEG, TIFF, PDF
- Sprog: Dansk, Engelsk, Tysk, Svensk, Arabisk
- Output: Tekst + bounding boxes

---

## Resource Management

### Konservative Defaults

CLA respekterer systemressourcer med konservative standardindstillinger:

| Ressource | Default | Max Konfigurerbar |
|-----------|---------|-------------------|
| CPU | 30% | 80% |
| RAM | 20% | 50% |
| GPU | 30% | 80% |
| Disk | 2 GB | Ubegrænset |

### Konfiguration

**Via UI:**
Settings → Ressourcer → Juster sliders

**Via config.json:**
```json
{
  "resources": {
    "cpu_limit_percent": 30,
    "ram_limit_percent": 20,
    "gpu_limit_percent": 30,
    "disk_quota_gb": 2,
    "allow_on_battery": false,
    "battery_threshold_percent": 20,
    "idle_only": true,
    "idle_timeout_seconds": 300
  }
}
```

### Execution Decision Matrix

| Idle | Batteri | Ressourcer | Resultat |
|------|---------|------------|----------|
| Ja | AC Power | Tilgængelige | Execute |
| Ja | Batteri (>20%) | Tilgængelige | Execute (hvis tilladt) |
| Ja | Batteri (<20%) | Tilgængelige | Afvist |
| Nej | Any | Any | Afvist (hvis idle_only) |
| Any | Any | Over grænse | Afvist |

### Resource Monitor

```bash
# Real-time monitoring
cirkelline-local-agent monitor

# Output:
# CPU:  ████░░░░░░ 23%
# RAM:  ██░░░░░░░░ 18%
# GPU:  ░░░░░░░░░░  0%
# Disk: 145 MB / 2 GB
# Status: Ready for inference
```

---

## Offline Capabilities

### Hvad Fungerer Offline

| Funktion | Offline | Online Only |
|----------|---------|-------------|
| Tekst embeddings | ✓ | |
| Audio transkription | ✓ | |
| OCR tekstudtrækning | ✓ | |
| Lokal søgning | ✓ | |
| Dokumentanalyse | ✓ | |
| Model download | | ✓ |
| Sync med CKC | | ✓ |
| Cloud AI (Gemini) | | ✓ |

### Offline Mode Aktivering

CLA skifter automatisk til offline mode når:
1. Ingen netværksforbindelse detekteret
2. CKC server ikke tilgængelig
3. Manuel aktivering via Settings

### Data Sync

```
Online → Offline:
1. Seneste data cached lokalt
2. Pending tasks queued
3. Offline indicator vises

Offline → Online:
1. Queue synkroniseres
2. Konflikter løses (nyeste vinder)
3. Fuldt sync gennemføres
```

---

## Performance Tuning

### Hardware Acceleration

**CPU Optimering:**
```json
{
  "inference": {
    "cpu_threads": 4,
    "use_avx2": true,
    "use_avx512": false
  }
}
```

**GPU Acceleration (valgfri):**
```json
{
  "inference": {
    "use_gpu": true,
    "gpu_device_id": 0,
    "gpu_memory_limit_mb": 2048
  }
}
```

### Batch Processing

For mange filer, brug batch processing:

```bash
# Batch embed alle dokumenter
cirkelline-local-agent embed --dir ./documents --batch-size 32

# Batch OCR alle billeder
cirkelline-local-agent ocr --dir ./images --workers 4
```

### Performance Targets

| Operation | Mål | Typisk |
|-----------|-----|--------|
| App startup | < 2s | 1.2s |
| Embedding (enkelt) | < 100ms | 45ms |
| Embedding (batch 32) | < 500ms | 320ms |
| Whisper (1 min audio) | < 15s | 8s |
| OCR (A4 side) | < 500ms | 280ms |
| Memory (idle) | < 150MB | 95MB |
| Memory (aktiv) | < 500MB | 320MB |

### Profiling

```bash
# Enable profiling
cirkelline-local-agent --profile

# Output til fil
cirkelline-local-agent --profile --profile-output ./profile.json

# Analyser
cat profile.json | jq '.operations | sort_by(.duration_ms) | reverse | .[0:5]'
```

---

## Troubleshooting

### Almindelige Problemer

| Problem | Årsag | Løsning |
|---------|-------|---------|
| Model fails to load | Korrupt download | `cirkelline-local-agent models verify --fix` |
| Slow inference | For mange threads | Reducer `cpu_threads` |
| Out of memory | Model for stor | Brug Tier 1 modeller |
| GPU not detected | Manglende drivers | Installer CUDA/DirectML |
| Timeout errors | Stor fil | Øg `inference_timeout_seconds` |

### Diagnostik

```bash
# System check
cirkelline-local-agent diagnostics

# Output:
# OS: Linux 6.14.0
# CPU: AMD Ryzen 9 5900X (24 threads)
# RAM: 32 GB (28 GB available)
# GPU: NVIDIA RTX 3080 (CUDA 12.0)
# Models: 3/3 verified
# Status: All systems operational
```

### Logs

```bash
# Se inference logs
tail -f ~/.cirkelline/logs/inference.log

# Debug mode
CLA_LOG=debug cirkelline-local-agent

# Log levels: error, warn, info, debug, trace
```

### Reset

```bash
# Reset all models
cirkelline-local-agent models reset

# Reset config
rm ~/.cirkelline/config.json

# Full reset (beholder device_id)
cirkelline-local-agent reset --keep-device-id
```

---

## API Reference

### Tauri Commands

| Command | Beskrivelse | Return |
|---------|-------------|--------|
| `get_model_status` | List alle modeller og status | `Vec<ModelInfo>` |
| `download_model` | Download specifik model | `Result<(), Error>` |
| `generate_embedding` | Generer embedding fra tekst | `Vec<f32>` |
| `transcribe_audio` | Transkriber lydfil | `Transcript` |
| `extract_text` | OCR på billede | `OcrResult` |
| `check_resources` | Check resource availability | `ResourceStatus` |

### Events

| Event | Payload | Beskrivelse |
|-------|---------|-------------|
| `model-download-progress` | `{model_id, progress, downloaded_mb, total_mb}` | Download fremgang |
| `inference-complete` | `{task_id, result}` | Inferens færdig |
| `resource-warning` | `{resource, current, limit}` | Ressource advarsel |

---

## Sikkerhed

### Model Integritet

- SHA-256 checksums verificeres ved download
- Modeller signeret af Cirkelline
- Automatisk re-download ved korruption

### Data Isolation

- Inference kører i sandboxed process
- Ingen netværksadgang under inferens
- Midlertidige filer slettes automatisk

### Privacy

Lokale modeller betyder:
- Ingen data sendes til eksterne servere
- Ingen cloud-processing af sensitiv data
- Fuld kontrol over egne data

---

*Maintained by Cirkelline Development Team*
*Last updated: 2025-12-12*
