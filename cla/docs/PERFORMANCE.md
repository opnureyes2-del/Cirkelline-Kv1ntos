# CLA Performance Optimization Guide

## Performance Targets

| Metric | Target | Priority |
|--------|--------|----------|
| App startup time | < 2 seconds | High |
| Embedding generation | < 100ms | High |
| Audio transcription | < 5x realtime | Medium |
| OCR per page | < 500ms | Medium |
| Memory usage (idle) | < 150MB | High |
| Memory usage (active) | < 500MB | Medium |
| Disk space (Tier 1) | < 200MB | Low |

## Optimization Strategies

### 1. Model Loading Optimization

#### Lazy Loading
Models are loaded only when first needed:

```rust
pub struct ModelManager {
    models: HashMap<String, LazyModel>,
}

impl ModelManager {
    pub async fn get_model(&mut self, id: &str) -> Result<&Model> {
        if !self.models.contains_key(id) {
            let model = load_model(id).await?;
            self.models.insert(id.to_string(), model);
        }
        Ok(self.models.get(id).unwrap())
    }
}
```

#### Model Caching
Keep recently used models in memory with LRU eviction:

```rust
const MAX_CACHED_MODELS: usize = 3;
const MODEL_CACHE_TTL: Duration = Duration::from_secs(300);
```

#### Preloading
Preload Tier 1 models during idle time after startup.

### 2. Inference Optimization

#### Batch Processing
Group multiple embeddings into batches:

```rust
const MAX_BATCH_SIZE: usize = 32;
const BATCH_WAIT_MS: u64 = 50;

pub async fn batch_embeddings(texts: Vec<String>) -> Vec<Vec<f32>> {
    let batches = texts.chunks(MAX_BATCH_SIZE);
    let results = Vec::new();

    for batch in batches {
        let batch_result = model.run_batch(batch).await?;
        results.extend(batch_result);
    }

    results
}
```

#### ONNX Optimizations
- Use ONNX Runtime execution providers (CPU, CUDA, CoreML)
- Enable graph optimization level 99
- Use float16 quantization where supported

```rust
let session_options = SessionBuilder::new()
    .with_optimization_level(GraphOptimizationLevel::Level99)?
    .with_intra_threads(num_cpus::get() / 2)?;
```

### 3. Memory Optimization

#### Embedding Storage
Store embeddings as compressed binary, not JSON:

```rust
// Instead of storing as Vec<f32> (4 bytes per dimension)
// Use f16 (2 bytes) or quantized i8 (1 byte)

fn compress_embedding(embedding: &[f32]) -> Vec<u8> {
    embedding.iter()
        .map(|&f| half::f16::from_f32(f))
        .flat_map(|f| f.to_le_bytes())
        .collect()
}
```

#### Memory Pools
Pre-allocate buffers for inference:

```rust
struct InferencePool {
    input_buffer: Vec<f32>,
    output_buffer: Vec<f32>,
}

impl InferencePool {
    fn new(max_input_size: usize, output_size: usize) -> Self {
        Self {
            input_buffer: vec![0.0; max_input_size],
            output_buffer: vec![0.0; output_size],
        }
    }
}
```

### 4. Database Optimization

#### IndexedDB Performance

**Indexes:**
```typescript
// Ensure proper indexes for common queries
store.createIndex('by_topics', 'topics', { multiEntry: true });
store.createIndex('by_created', 'created_at');
store.createIndex('by_pending_sync', 'pending_sync');
```

**Batch Operations:**
```typescript
// Use transactions for bulk operations
const tx = db.transaction(['memories'], 'readwrite');
const store = tx.objectStore('memories');

for (const memory of memories) {
  store.put(memory);
}

await tx.done;
```

**Pagination:**
```typescript
// Use cursor-based pagination for large datasets
async function* iterateMemories(batchSize = 100) {
  let cursor = await store.openCursor();
  let batch = [];

  while (cursor) {
    batch.push(cursor.value);
    if (batch.length >= batchSize) {
      yield batch;
      batch = [];
    }
    cursor = await cursor.continue();
  }

  if (batch.length > 0) {
    yield batch;
  }
}
```

### 5. UI Optimization

#### Debouncing
Debounce rapid updates from backend:

```typescript
import { useDebouncedCallback } from 'use-debounce';

const debouncedUpdate = useDebouncedCallback(
  (metrics: SystemMetrics) => setMetrics(metrics),
  100
);

useEffect(() => {
  return listen('metrics-update', (e) => debouncedUpdate(e.payload));
}, []);
```

#### Virtualization
Use virtual lists for long data:

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

function MemoryList({ memories }: { memories: Memory[] }) {
  const virtualizer = useVirtualizer({
    count: memories.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 72,
  });

  return (
    <div ref={parentRef} style={{ height: '400px', overflow: 'auto' }}>
      <div style={{ height: virtualizer.getTotalSize() }}>
        {virtualizer.getVirtualItems().map((item) => (
          <MemoryItem key={item.key} memory={memories[item.index]} />
        ))}
      </div>
    </div>
  );
}
```

#### Code Splitting
Split routes and heavy components:

```typescript
const SettingsPage = lazy(() => import('./components/SettingsPage'));
const ModelsPage = lazy(() => import('./components/ModelsPage'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/models" element={<ModelsPage />} />
      </Routes>
    </Suspense>
  );
}
```

### 6. Network Optimization

#### Request Batching
Batch sync operations:

```rust
const SYNC_BATCH_SIZE: usize = 100;

async fn sync_memories(memories: Vec<Memory>) -> Result<()> {
    for batch in memories.chunks(SYNC_BATCH_SIZE) {
        client.post("/api/cla/sync/batch")
            .json(&SyncBatch { memories: batch })
            .send()
            .await?;
    }
    Ok(())
}
```

#### Delta Sync
Only sync changed data:

```rust
struct SyncDelta {
    last_sync: DateTime<Utc>,
    changed_ids: Vec<String>,
    checksums: HashMap<String, String>,
}
```

#### Compression
Compress large payloads:

```rust
let compressed = flate2::write::GzEncoder::new(Vec::new(), Compression::fast());
compressed.write_all(&json_data)?;
let bytes = compressed.finish()?;

client.post("/api/cla/sync")
    .header("Content-Encoding", "gzip")
    .body(bytes)
    .send()
    .await?;
```

### 7. Startup Optimization

#### Cold Start Improvements

1. **Minimize initial bundle:**
   ```javascript
   // vite.config.ts
   build: {
     rollupOptions: {
       output: {
         manualChunks: {
           vendor: ['react', 'react-dom'],
           store: ['zustand', 'idb'],
         }
       }
     }
   }
   ```

2. **Defer non-critical initialization:**
   ```rust
   // Start UI immediately, load models in background
   #[tauri::command]
   async fn init_app(app: AppHandle) {
       // Return immediately
       spawn(async move {
           // Load models in background
           preload_tier1_models().await;
       });
   }
   ```

3. **Use splash screen:**
   ```rust
   // Show native splash while React loads
   let splash = tauri::WindowBuilder::new(&app, "splash")
       .decorations(false)
       .build()?;
   ```

## Benchmarking

### Performance Tests

```rust
#[bench]
fn bench_embedding_generation(b: &mut Bencher) {
    let model = load_model_sync("all-minilm-l6-v2");
    let text = "This is a test sentence for benchmarking.";

    b.iter(|| {
        model.generate_embedding(black_box(text))
    });
}

#[bench]
fn bench_batch_embeddings(b: &mut Bencher) {
    let model = load_model_sync("all-minilm-l6-v2");
    let texts: Vec<_> = (0..32).map(|i| format!("Test sentence {}", i)).collect();

    b.iter(|| {
        model.generate_embeddings_batch(black_box(&texts))
    });
}
```

### Profiling

```bash
# CPU profiling
cargo flamegraph --bin cla

# Memory profiling
valgrind --tool=massif ./target/release/cla

# Frontend profiling
pnpm build --profile
# Then use Chrome DevTools Performance tab
```

## Monitoring

### Key Metrics to Track

```rust
// Track in telemetry
metrics.record("embedding_latency_ms", duration.as_millis());
metrics.record("model_load_time_ms", load_time.as_millis());
metrics.record("memory_usage_mb", process_memory_mb());
metrics.record("inference_queue_depth", queue.len());
```

### Alerts

Set up alerts for:
- Embedding latency > 500ms
- Memory usage > 1GB
- Queue depth > 100 tasks
- Error rate > 5%

## Future Optimizations

### Planned Improvements

1. **WebGPU Support**
   - Faster inference using GPU compute shaders
   - Better cross-platform GPU support

2. **Model Quantization**
   - INT8 quantization for smaller models
   - Mixed precision inference

3. **Streaming Inference**
   - Stream transcription results as they're generated
   - Reduce perceived latency

4. **Intelligent Scheduling**
   - Predict idle periods
   - Pre-process likely-needed content

5. **Edge Caching**
   - Cache embeddings for common queries
   - Bloom filters for quick lookups
