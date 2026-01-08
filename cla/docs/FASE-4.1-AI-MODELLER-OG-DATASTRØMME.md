# FASE 4.1: Lokale AI-opgaver og Datastrømme
## Cirkelline Local Agent (CLA) Implementation

**Version:** 1.0
**Dato:** 2025-12-08
**Status:** Specifikation Komplet

---

## 4.1.1: IDENTIFICERING AF LETVÆGTS-AI-MODELLER TIL LOKAL UDFØRELSE

### Analyse af Cirkelline's Nuværende AI-arkitektur

Cirkelline bruger pt. følgende AI-kapaciteter i cloud:

| Komponent | Cloud Model | API Kald/Request | Latency |
|-----------|-------------|------------------|---------|
| **Main Orchestrator** | Gemini 2.5 Flash | 1-3 kald | 1-3s |
| **Research Team** | Gemini 2.5 Flash | 2-5 kald | 3-10s |
| **Law Team** | Gemini 2.5 Flash | 2-4 kald | 3-8s |
| **Audio Specialist** | Gemini 2.5 Flash (multimodal) | 1-2 kald | 2-5s |
| **Video Specialist** | Gemini 2.5 Flash (multimodal) | 1-2 kald | 3-8s |
| **Image Specialist** | Gemini 2.5 Flash (multimodal) | 1-2 kald | 1-3s |
| **Document Specialist** | Gemini 2.5 Flash | 1-2 kald | 2-5s |
| **Embeddings** | GeminiEmbedder | 1 kald/chunk | 0.5-1s |
| **Memory Manager** | Gemini 2.5 Flash | 1 kald/session | 1-2s |

---

### Udvalgte Lokale AI-modeller

Baseret på analysen anbefaler jeg følgende modeller til lokal udførelse:

## TIER 1: CORE LOKALE MODELLER (Altid Installeret)

### 1.1 Embeddings: all-MiniLM-L6-v2

| Parameter | Værdi |
|-----------|-------|
| **Model ID** | `sentence-transformers/all-MiniLM-L6-v2` |
| **ONNX Format** | `all-MiniLM-L6-v2.onnx` |
| **Størrelse** | 23 MB |
| **Dimensions** | 384-dim (vs 768-dim Gemini) |
| **Performance** | ~100 embeddings/sekund (CPU) |
| **Quantized** | INT8 tilgængelig (12 MB) |

**Begrundelse for lokal udførelse:**
- Cirkelline laver embedding-opslag ved hver knowledge search
- Lokal embedding = 0ms latency vs 500-1000ms cloud
- Bruges til: Memory search, knowledge search, semantic similarity
- **Besparelse:** ~50% af embedding API kald

**Konvertering til ONNX:**
```python
from optimum.onnxruntime import ORTModelForFeatureExtraction
model = ORTModelForFeatureExtraction.from_pretrained(
    "sentence-transformers/all-MiniLM-L6-v2",
    export=True
)
model.save_pretrained("./models/embedding")
```

**Mapping fra Gemini 768-dim til MiniLM 384-dim:**
```typescript
// CLA vil bruge 384-dim lokalt men kan konvertere ved sync
interface EmbeddingConfig {
  localModel: 'all-MiniLM-L6-v2';
  localDimensions: 384;
  cloudModel: 'GeminiEmbedder';
  cloudDimensions: 768;
  syncStrategy: 'dual_index';  // Gemmer begge for kompatibilitet
}
```

---

### 1.2 Voice-to-Text: Whisper Tiny (English)

| Parameter | Værdi |
|-----------|-------|
| **Model ID** | `openai/whisper-tiny.en` |
| **ONNX Format** | `whisper-tiny-en.onnx` |
| **Størrelse** | 39 MB |
| **Sprog** | Kun engelsk |
| **Real-time Factor** | ~0.5x (2 sek audio = 1 sek processing) |
| **Accuracy** | WER ~7% på LibriSpeech |

**Begrundelse for lokal udførelse:**
- Audio Specialist bruger Gemini til transcription = dyr og langsom
- Lokal Whisper = instant transcription, ingen cloud kald
- Bruges til: Voice memos, meeting recordings, audio messages
- **Besparelse:** Eliminerer alle audio transcription API kald

**ONNX Model Split (for streaming):**
```
whisper-tiny-en/
├── encoder.onnx       (18 MB)
├── decoder.onnx       (21 MB)
└── tokenizer.json     (1 MB)
```

---

### 1.3 OCR: Tesseract WASM

| Parameter | Værdi |
|-----------|-------|
| **Library** | `tesseract.js` (WASM build) |
| **Størrelse** | ~15 MB (core + eng trained data) |
| **Sprog** | Engelsk + Dansk (tilføj flere on-demand) |
| **Performance** | ~1-2 sek per A4 side |

**Begrundelse for lokal udførelse:**
- Image Specialist bruger Gemini til OCR
- Lokal Tesseract = hurtigere for simple dokumenter
- Bruges til: Business cards, receipts, simple documents
- **Fallback:** Komplekse layouts sendes til Gemini

**Language Packs (on-demand download):**
```
tesseract-data/
├── eng.traineddata    (4 MB)
├── dan.traineddata    (3 MB)  # Download on first Danish text
├── deu.traineddata    (5 MB)  # German
└── fra.traineddata    (4 MB)  # French
```

---

## TIER 2: VALGFRIE LOKALE MODELLER (Bruger Vælger)

### 2.1 Multilingual Whisper: whisper-small

| Parameter | Værdi |
|-----------|-------|
| **Model ID** | `openai/whisper-small` |
| **ONNX Format** | `whisper-small.onnx` |
| **Størrelse** | 466 MB |
| **Sprog** | 99 sprog inkl. dansk |
| **Real-time Factor** | ~1.5x (behøver god CPU/GPU) |

**Hvornår tilbyde download:**
- Bruger beder om transcription på ikke-engelsk
- Bruger har >8 GB RAM og god CPU
- Bruger aktiverer "Extended Language Support"

---

### 2.2 Bedre Embeddings: bge-small-en-v1.5

| Parameter | Værdi |
|-----------|-------|
| **Model ID** | `BAAI/bge-small-en-v1.5` |
| **ONNX Format** | `bge-small-en.onnx` |
| **Størrelse** | 133 MB |
| **Dimensions** | 384-dim |
| **Performance** | Bedre semantic matching end MiniLM |

**Hvornår tilbyde download:**
- Bruger har meget knowledge base content
- Bruger rapporterer dårlige søgeresultater
- Power user setting aktiveret

---

## TIER 3: POWER USER MODELLER (Kræver Eksplicit Accept)

### 3.1 Lokal LLM: Phi-3-mini-4k-instruct

| Parameter | Værdi |
|-----------|-------|
| **Model ID** | `microsoft/Phi-3-mini-4k-instruct` |
| **ONNX Format** | `phi-3-mini-4k-instruct.onnx` |
| **Størrelse** | 2.4 GB (INT4 quantized) |
| **Context** | 4K tokens |
| **Performance** | ~10 tokens/sek (GPU), ~2 tokens/sek (CPU) |

**Hardware Krav:**
```typescript
interface Phi3Requirements {
  gpu: {
    vram: '4+ GB';  // NVIDIA, AMD, or Apple Silicon
    recommended: ['RTX 3060+', 'M1/M2/M3', 'RX 6700+'];
  };
  ram: '8+ GB';
  storage: '5+ GB free';
  os: ['Windows 10+', 'macOS 12+', 'Ubuntu 20.04+'];
}
```

**Anvendelse:**
- Simple queries lokalt (greetings, simple questions)
- Offline chat capability
- Privacy-sensitive requests
- Draft generation før cloud refinement

**IKKE egnet til:**
- Deep research (kræver web search)
- Complex reasoning (Gemini er bedre)
- Long context (kun 4K tokens)

---

### 3.2 Alternativ Lokal LLM: Llama-3.2-1B

| Parameter | Værdi |
|-----------|-------|
| **Model ID** | `meta-llama/Llama-3.2-1B-Instruct` |
| **ONNX Format** | `llama-3.2-1b-instruct.onnx` |
| **Størrelse** | 1.3 GB (INT4 quantized) |
| **Context** | 8K tokens |
| **Performance** | ~15 tokens/sek (GPU), ~4 tokens/sek (CPU) |

**Fordele vs Phi-3:**
- Mindre størrelse (1.3 GB vs 2.4 GB)
- Længere context (8K vs 4K)
- Hurtigere inference
- Nyere model (dec 2024)

---

## MODEL VALG MATRIX

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CLA MODEL SELECTION MATRIX                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  OPGAVE                    │ LOKAL MODEL           │ CLOUD FALLBACK        │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Embedding generation      │ all-MiniLM-L6-v2     │ GeminiEmbedder        │
│  Memory search             │ all-MiniLM-L6-v2     │ GeminiEmbedder        │
│  Knowledge search          │ all-MiniLM-L6-v2     │ GeminiEmbedder        │
│  Voice transcription (EN)  │ whisper-tiny.en      │ Gemini Audio          │
│  Voice transcription (DA)  │ whisper-small        │ Gemini Audio          │
│  Simple OCR                │ tesseract.js         │ Gemini Vision         │
│  Complex OCR               │ CLOUD                │ Gemini Vision         │
│  Simple chat               │ phi-3/llama-3.2      │ Gemini 2.5 Flash      │
│  Research queries          │ CLOUD                │ Research Team         │
│  Legal queries             │ CLOUD                │ Law Team              │
│  Image analysis            │ CLOUD                │ Image Specialist      │
│  Video analysis            │ CLOUD                │ Video Specialist      │
│  Document analysis         │ CLOUD                │ Document Specialist   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4.1.2: DATATYPER OG DATASTRØMME FOR LOKAL FORBEHANDLING

### Datatype Specifikationer

#### 1. Memories (Lokal Cache)

```typescript
interface LocalMemory {
  id: string;                    // UUID
  user_id: string;               // User identifier
  memory: string;                // Memory content
  topics: string[];              // Topic tags ["preferences", "family"]
  embedding_local: Float32Array; // 384-dim MiniLM embedding
  embedding_cloud?: Float32Array; // 768-dim Gemini embedding (synced)
  created_at: Date;
  updated_at: Date;
  synced_at?: Date;              // Last sync with cloud
  is_dirty: boolean;             // Needs sync
}

// IndexedDB Schema
const MEMORIES_STORE = {
  name: 'memories',
  keyPath: 'id',
  indexes: [
    { name: 'user_id', keyPath: 'user_id', unique: false },
    { name: 'topics', keyPath: 'topics', multiEntry: true },
    { name: 'synced_at', keyPath: 'synced_at', unique: false },
    { name: 'is_dirty', keyPath: 'is_dirty', unique: false },
  ]
};
```

#### 2. Sessions (Lokal Cache)

```typescript
interface LocalSession {
  session_id: string;            // UUID
  user_id: string;
  name: string;                  // Session name
  messages: LocalMessage[];      // Conversation history
  metadata: {
    created_at: Date;
    updated_at: Date;
    message_count: number;
    tokens_used: number;
  };
  synced_at?: Date;
  is_dirty: boolean;
}

interface LocalMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  attachments?: LocalAttachment[];
  timestamp: Date;
  tokens: number;
  processed_locally: boolean;    // Was this handled by local LLM?
}

interface LocalAttachment {
  id: string;
  type: 'audio' | 'image' | 'document' | 'video';
  filename: string;
  mime_type: string;
  size_bytes: number;
  local_path?: string;           // Path in local storage
  cloud_url?: string;            // Cloud storage URL
  processed_result?: string;     // OCR/transcription result
  processed_at?: Date;
}

// IndexedDB Schema
const SESSIONS_STORE = {
  name: 'sessions',
  keyPath: 'session_id',
  indexes: [
    { name: 'user_id', keyPath: 'user_id', unique: false },
    { name: 'updated_at', keyPath: 'metadata.updated_at', unique: false },
  ]
};
```

#### 3. Knowledge Snippets (Lokal Cache)

```typescript
interface LocalKnowledgeChunk {
  chunk_id: string;              // UUID
  document_id: string;           // Parent document
  user_id: string;
  content: string;               // Text content (max 1000 chars)
  embedding_local: Float32Array; // 384-dim MiniLM
  metadata: {
    document_name: string;
    page_number?: number;
    chunk_index: number;
    source_type: 'pdf' | 'docx' | 'txt' | 'url';
  };
  created_at: Date;
  last_accessed: Date;           // For cache eviction
}

// IndexedDB Schema
const KNOWLEDGE_STORE = {
  name: 'knowledge_chunks',
  keyPath: 'chunk_id',
  indexes: [
    { name: 'document_id', keyPath: 'document_id', unique: false },
    { name: 'user_id', keyPath: 'user_id', unique: false },
    { name: 'last_accessed', keyPath: 'last_accessed', unique: false },
  ]
};
```

#### 4. Pending Tasks (Lokal Kø)

```typescript
interface PendingTask {
  task_id: string;
  type: TaskType;
  priority: 'low' | 'medium' | 'high' | 'critical';
  payload: any;                  // Task-specific data
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: Date;
  started_at?: Date;
  completed_at?: Date;
  error?: string;
  retry_count: number;
  max_retries: number;
}

enum TaskType {
  GENERATE_EMBEDDING = 'generate_embedding',
  TRANSCRIBE_AUDIO = 'transcribe_audio',
  OCR_IMAGE = 'ocr_image',
  SYNC_MEMORIES = 'sync_memories',
  SYNC_SESSIONS = 'sync_sessions',
  PRELOAD_KNOWLEDGE = 'preload_knowledge',
  LOCAL_INFERENCE = 'local_inference',
}
```

---

### Datastrømsdiagrammer

#### Strøm 1: Memory Search (Lokal First)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MEMORY SEARCH DATAFLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

User Query: "Hvad er mine præferencer for kodesprog?"
     │
     ▼
┌─────────────────────────────────────┐
│  1. LOKAL EMBEDDING GENERATION     │
│                                     │
│  Input: "præferencer kodesprog"     │
│  Model: all-MiniLM-L6-v2 (ONNX)    │
│  Output: [0.12, -0.34, ...] 384-dim │
│  Latency: <10ms                     │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│  2. LOKAL VECTOR SEARCH            │
│                                     │
│  Search: IndexedDB memories         │
│  Method: Cosine similarity          │
│  Filter: topics CONTAINS            │
│         ["preferences", "coding"]   │
│  Limit: 10 results                  │
│  Latency: <50ms                     │
└─────────────────────────────────────┘
     │
     ├─── Results Found (>0) ─────────────────────────────────────────┐
     │                                                                 │
     ▼                                                                 ▼
┌─────────────────────────────────────┐    ┌──────────────────────────────────┐
│  3a. RETURN LOCAL RESULTS          │    │  3b. FALLBACK TO CLOUD           │
│                                     │    │                                  │
│  Format memories for display        │    │  If: No local results OR         │
│  Mark as "from_local_cache"         │    │      Cache is stale (>24h)       │
│  Total latency: ~60ms               │    │                                  │
└─────────────────────────────────────┘    │  Call: CKC /api/memories/search  │
                                           │  Sync: Update local cache        │
                                           │  Total latency: ~500-1000ms      │
                                           └──────────────────────────────────┘
```

#### Strøm 2: Audio Transcription (Lokal First)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AUDIO TRANSCRIPTION DATAFLOW                            │
└─────────────────────────────────────────────────────────────────────────────┘

User uploads: meeting_recording.mp3 (5 min, 8 MB)
     │
     ▼
┌─────────────────────────────────────┐
│  1. AUDIO PREPROCESSING            │
│                                     │
│  Decode: MP3 → PCM 16kHz mono       │
│  Split: 30-second chunks            │
│  Store: Local temp storage          │
│  Latency: ~500ms                    │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│  2. LANGUAGE DETECTION             │
│                                     │
│  Sample: First 10 seconds           │
│  Detect: English/Danish/Other       │
│  Method: Whisper encoder analysis   │
│  Latency: ~200ms                    │
└─────────────────────────────────────┘
     │
     ├─── English ─────────────────────────────────────┐
     │                                                  │
     ├─── Danish (whisper-small installed) ────────────┤
     │                                                  │
     ├─── Danish (NOT installed) ──────────────────────┼───┐
     │                                                  │   │
     ▼                                                  │   │
┌─────────────────────────────────────┐                │   │
│  3a. LOCAL TRANSCRIPTION           │◄───────────────┘   │
│                                     │                     │
│  Model: whisper-tiny.en OR          │                     │
│         whisper-small               │                     │
│  Process: Streaming per chunk       │                     │
│  Output: Text + timestamps          │                     │
│  Latency: ~2.5 min for 5 min audio │                     │
└─────────────────────────────────────┘                     │
                                                            │
     ┌──────────────────────────────────────────────────────┘
     ▼
┌─────────────────────────────────────┐
│  3b. CLOUD FALLBACK                │
│                                     │
│  Upload: Audio to cloud storage     │
│  Call: Gemini Audio API             │
│  Reason: Language not supported     │
│          OR user preference         │
│  Latency: ~10-30 sec                │
└─────────────────────────────────────┘
```

#### Strøm 3: Knowledge Preloading (Background)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   KNOWLEDGE PRELOADING DATAFLOW                            │
└─────────────────────────────────────────────────────────────────────────────┘

Trigger: User logs in / App starts
     │
     ▼
┌─────────────────────────────────────┐
│  1. CHECK SYNC STATUS              │
│                                     │
│  Compare: Local last_sync vs Cloud  │
│  Identify: Missing or stale chunks  │
│  Priority: Recently accessed first  │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│  2. FETCH MISSING CHUNKS           │
│  (Background, idle-only)            │
│                                     │
│  API: GET /api/knowledge/chunks     │
│  Params: user_id, since=last_sync   │
│  Batch: 50 chunks at a time         │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│  3. GENERATE LOCAL EMBEDDINGS      │
│  (Background task queue)            │
│                                     │
│  For each chunk:                    │
│    - Generate 384-dim embedding     │
│    - Store in IndexedDB             │
│    - Update last_accessed           │
└─────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────┐
│  4. CACHE MANAGEMENT               │
│                                     │
│  If storage > 100 MB:               │
│    - Evict least recently accessed  │
│    - Keep metadata for re-fetch     │
└─────────────────────────────────────┘
```

---

## 4.1.3: INTERAKTIONER MED LOKALE DATA OG OS

### IndexedDB Interaktioner

```typescript
// CLA Database Manager
class CLADatabase {
  private db: IDBDatabase;
  private readonly DB_NAME = 'cirkelline_local';
  private readonly DB_VERSION = 1;

  async initialize(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.DB_NAME, this.DB_VERSION);

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Memories store
        if (!db.objectStoreNames.contains('memories')) {
          const store = db.createObjectStore('memories', { keyPath: 'id' });
          store.createIndex('user_id', 'user_id', { unique: false });
          store.createIndex('topics', 'topics', { multiEntry: true });
          store.createIndex('is_dirty', 'is_dirty', { unique: false });
        }

        // Sessions store
        if (!db.objectStoreNames.contains('sessions')) {
          const store = db.createObjectStore('sessions', { keyPath: 'session_id' });
          store.createIndex('user_id', 'user_id', { unique: false });
          store.createIndex('updated_at', 'metadata.updated_at', { unique: false });
        }

        // Knowledge chunks store
        if (!db.objectStoreNames.contains('knowledge_chunks')) {
          const store = db.createObjectStore('knowledge_chunks', { keyPath: 'chunk_id' });
          store.createIndex('document_id', 'document_id', { unique: false });
          store.createIndex('user_id', 'user_id', { unique: false });
          store.createIndex('last_accessed', 'last_accessed', { unique: false });
        }

        // Pending tasks store
        if (!db.objectStoreNames.contains('pending_tasks')) {
          const store = db.createObjectStore('pending_tasks', { keyPath: 'task_id' });
          store.createIndex('status', 'status', { unique: false });
          store.createIndex('priority', 'priority', { unique: false });
        }

        // Models metadata store
        if (!db.objectStoreNames.contains('models')) {
          const store = db.createObjectStore('models', { keyPath: 'model_id' });
        }

        // Settings store
        if (!db.objectStoreNames.contains('settings')) {
          const store = db.createObjectStore('settings', { keyPath: 'key' });
        }
      };

      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onerror = () => {
        reject(request.error);
      };
    });
  }
}
```

### OS Integration (Tauri Commands)

```rust
// src-tauri/src/commands.rs

use tauri::command;
use sysinfo::{System, SystemExt, ProcessorExt, DiskExt};

/// Get current system resource usage
#[command]
pub fn get_system_metrics() -> Result<SystemMetrics, String> {
    let mut sys = System::new_all();
    sys.refresh_all();

    Ok(SystemMetrics {
        cpu_usage: sys.global_processor_info().cpu_usage(),
        memory_used: sys.used_memory(),
        memory_total: sys.total_memory(),
        gpu_available: check_gpu_availability(),
        battery_level: get_battery_level(),
        is_charging: is_battery_charging(),
        disk_available: get_available_disk_space(),
    })
}

#[derive(serde::Serialize)]
pub struct SystemMetrics {
    cpu_usage: f32,
    memory_used: u64,
    memory_total: u64,
    gpu_available: bool,
    battery_level: Option<f32>,
    is_charging: bool,
    disk_available: u64,
}

/// Check if user is idle (no keyboard/mouse activity)
#[command]
pub fn get_idle_time() -> u64 {
    #[cfg(target_os = "windows")]
    {
        use windows::Win32::UI::Input::KeyboardAndMouse::GetLastInputInfo;
        // Windows implementation
    }

    #[cfg(target_os = "macos")]
    {
        use core_graphics::event_source::CGEventSourceSecondsSinceLastEventType;
        // macOS implementation
    }

    #[cfg(target_os = "linux")]
    {
        use x11::xss::XScreenSaverQueryInfo;
        // Linux implementation
    }
}

/// Read file for processing (with security sandbox)
#[command]
pub fn read_file_for_processing(path: String) -> Result<Vec<u8>, String> {
    // Validate path is in allowed directory
    if !is_path_allowed(&path) {
        return Err("Path not in allowed directories".to_string());
    }

    std::fs::read(&path).map_err(|e| e.to_string())
}

/// Store processed result
#[command]
pub fn store_processed_result(
    filename: String,
    data: Vec<u8>,
) -> Result<String, String> {
    let cache_dir = get_cache_directory();
    let path = cache_dir.join(&filename);

    std::fs::write(&path, data).map_err(|e| e.to_string())?;

    Ok(path.to_string_lossy().to_string())
}
```

### File System Struktur

```
~/.cirkelline/                         # Linux/macOS
%APPDATA%\Cirkelline\                  # Windows
├── config/
│   ├── settings.json                  # User preferences
│   └── permissions.json               # Granted permissions
├── models/
│   ├── embedding/
│   │   └── all-MiniLM-L6-v2.onnx     # 23 MB
│   ├── whisper/
│   │   ├── whisper-tiny-en.onnx      # 39 MB
│   │   └── whisper-small.onnx        # 466 MB (optional)
│   ├── ocr/
│   │   ├── tesseract-core.wasm       # 15 MB
│   │   ├── eng.traineddata           # 4 MB
│   │   └── dan.traineddata           # 3 MB (optional)
│   └── llm/
│       └── phi-3-mini-4k.onnx        # 2.4 GB (optional)
├── cache/
│   ├── audio/                        # Temporary audio files
│   ├── images/                       # Processed images
│   └── documents/                    # Cached document previews
├── data/
│   └── cirkelline.db                 # SQLite backup of IndexedDB
└── logs/
    ├── cla.log                       # Application logs
    └── telemetry.json                # Anonymous usage data
```

---

## STORAGE BUDGET

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CLA STORAGE BUDGET                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TIER 1 (Required):                                                        │
│  ─────────────────                                                         │
│  • all-MiniLM-L6-v2.onnx      23 MB                                       │
│  • whisper-tiny-en.onnx       39 MB                                       │
│  • tesseract-core.wasm        15 MB                                       │
│  • eng.traineddata             4 MB                                       │
│  ──────────────────────────────────                                       │
│  TIER 1 TOTAL:                81 MB                                       │
│                                                                             │
│  TIER 2 (Optional):                                                        │
│  ─────────────────                                                         │
│  • whisper-small.onnx        466 MB                                       │
│  • bge-small-en.onnx         133 MB                                       │
│  • dan.traineddata             3 MB                                       │
│  ──────────────────────────────────                                       │
│  TIER 2 TOTAL:               602 MB                                       │
│                                                                             │
│  TIER 3 (Power User):                                                      │
│  ────────────────────                                                      │
│  • phi-3-mini-4k.onnx       2400 MB                                       │
│  • OR llama-3.2-1b.onnx     1300 MB                                       │
│  ──────────────────────────────────                                       │
│  TIER 3 TOTAL:        1300-2400 MB                                       │
│                                                                             │
│  DATA CACHE:                                                               │
│  ───────────                                                               │
│  • IndexedDB (memories)       ~50 MB (est. 10k memories)                  │
│  • IndexedDB (sessions)      ~100 MB (est. 1000 sessions)                 │
│  • IndexedDB (knowledge)     ~200 MB (est. 50k chunks)                    │
│  • Temp files (audio/img)     ~50 MB (auto-cleanup)                       │
│  ──────────────────────────────────                                       │
│  DATA CACHE TOTAL:           ~400 MB                                      │
│                                                                             │
│  ═══════════════════════════════════                                      │
│  MINIMUM (Tier 1 + Cache):   ~500 MB                                      │
│  TYPICAL (Tier 1+2 + Cache): ~1.1 GB                                      │
│  MAXIMUM (All tiers):        ~3.5 GB                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## NÆSTE SKRIDT

FASE 4.1 er nu komplet. Dokumentet definerer:

1. **AI-modeller** identificeret med størrelse, performance og anvendelse
2. **Datatyper** specificeret med TypeScript interfaces og IndexedDB schemas
3. **Datastrømme** visualiseret med flow diagrammer
4. **OS-integration** beskrevet med Tauri Rust commands
5. **Storage budget** beregnet for alle tiers

Klar til **FASE 4.2: API'er, Protokoller og Synkronisering**.

---

*Dokument oprettet: 2025-12-08*
*Forfatter: Claude (Opus 4.5)*
*Status: KOMPLET*
