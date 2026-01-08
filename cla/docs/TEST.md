# CLA Testing Strategy

## Test Philosophy

**Quality from Start:** Testing is not an afterthought but integral to development.
Every feature must have tests before merge.

---

## Test Pyramid

```
         ╱╲
        ╱  ╲
       ╱ E2E╲        (10%) - Full user flows
      ╱──────╲
     ╱        ╲
    ╱Integration╲    (30%) - Component interactions
   ╱──────────────╲
  ╱                ╲
 ╱   Unit Tests     ╲  (60%) - Individual functions
╱────────────────────╲
```

---

## Test Categories

### 1. Unit Tests

**Frontend (Vitest)**

```typescript
// src/tests/utils.test.ts
import { describe, it, expect } from 'vitest';
import { formatBytes, truncateText } from '../lib/utils';

describe('formatBytes', () => {
  it('formats bytes to human readable', () => {
    expect(formatBytes(0)).toBe('0 B');
    expect(formatBytes(1024)).toBe('1 KB');
    expect(formatBytes(1048576)).toBe('1 MB');
    expect(formatBytes(1073741824)).toBe('1 GB');
  });

  it('handles negative values', () => {
    expect(formatBytes(-1)).toBe('0 B');
  });
});

describe('truncateText', () => {
  it('truncates long text with ellipsis', () => {
    const text = 'This is a very long text that needs truncation';
    expect(truncateText(text, 20)).toBe('This is a very lo...');
  });

  it('returns original if shorter than limit', () => {
    expect(truncateText('Short', 20)).toBe('Short');
  });
});
```

**Backend (Rust)**

```rust
// src-tauri/src/utils/tests.rs
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_cpu_limit() {
        assert!(validate_cpu_limit(0).is_ok());
        assert!(validate_cpu_limit(50).is_ok());
        assert!(validate_cpu_limit(100).is_ok());
        assert!(validate_cpu_limit(101).is_err());
    }

    #[test]
    fn test_sanitize_path() {
        assert_eq!(
            sanitize_path("../../../etc/passwd"),
            "etc/passwd"
        );
        assert_eq!(
            sanitize_path("normal/path/file.txt"),
            "normal/path/file.txt"
        );
    }

    #[test]
    fn test_generate_device_id() {
        let id1 = generate_device_id();
        let id2 = generate_device_id();
        assert_ne!(id1, id2);
        assert_eq!(id1.len(), 36); // UUID format
    }
}
```

### 2. Integration Tests

**Tauri Command Tests**

```rust
// src-tauri/tests/commands_test.rs
use cla::commands::*;
use cla::AppState;
use std::sync::Arc;
use tokio::sync::RwLock;

async fn create_test_state() -> AppState {
    AppState {
        settings: Arc::new(RwLock::new(Settings::default())),
        sync_status: Arc::new(RwLock::new(SyncStatus::default())),
        // ... other fields
    }
}

#[tokio::test]
async fn test_get_settings_returns_defaults() {
    let state = create_test_state();
    let settings = get_settings(state.into()).await.unwrap();

    assert_eq!(settings.max_cpu_percent, 30);
    assert_eq!(settings.idle_only, true);
}

#[tokio::test]
async fn test_save_settings_persists() {
    let state = create_test_state();

    let mut new_settings = Settings::default();
    new_settings.max_cpu_percent = 50;

    save_settings(state.clone().into(), new_settings.clone())
        .await
        .unwrap();

    let loaded = get_settings(state.into()).await.unwrap();
    assert_eq!(loaded.max_cpu_percent, 50);
}
```

**API Integration Tests**

```rust
// src-tauri/tests/api_integration.rs
use wiremock::{MockServer, Mock, ResponseTemplate};
use wiremock::matchers::{method, path, header};

#[tokio::test]
async fn test_sync_with_ckc() {
    let mock_server = MockServer::start().await;

    Mock::given(method("POST"))
        .and(path("/api/cla/sync"))
        .and(header("Authorization", "Bearer test_token"))
        .respond_with(ResponseTemplate::new(200)
            .set_body_json(serde_json::json!({
                "success": true,
                "sync_token": "abc123",
                "id_mappings": {}
            })))
        .mount(&mock_server)
        .await;

    let client = CkcClient::new(&mock_server.uri(), "test_token");
    let result = client.sync(SyncRequest::default()).await;

    assert!(result.is_ok());
    assert_eq!(result.unwrap().sync_token, "abc123");
}
```

### 3. End-to-End Tests

**Using Playwright + Tauri**

```typescript
// tests/e2e/settings.spec.ts
import { test, expect } from '@playwright/test';
import { spawn, ChildProcess } from 'child_process';

let app: ChildProcess;

test.beforeAll(async () => {
  // Start Tauri app in test mode
  app = spawn('pnpm', ['tauri', 'dev', '--', '--test-mode'], {
    stdio: 'pipe',
    env: { ...process.env, TAURI_TEST: '1' }
  });

  // Wait for app to start
  await new Promise(resolve => setTimeout(resolve, 5000));
});

test.afterAll(async () => {
  app.kill();
});

test('user can change CPU limit', async ({ page }) => {
  await page.goto('tauri://localhost');

  // Navigate to settings
  await page.click('[data-testid="settings-button"]');

  // Change CPU limit
  const slider = page.locator('[data-testid="cpu-limit-slider"]');
  await slider.fill('50');

  // Save settings
  await page.click('[data-testid="save-button"]');

  // Verify saved
  await expect(page.locator('[data-testid="save-success"]')).toBeVisible();

  // Reload and verify persistence
  await page.reload();
  await expect(slider).toHaveValue('50');
});

test('sync flow works correctly', async ({ page }) => {
  await page.goto('tauri://localhost');

  // Trigger sync
  await page.click('[data-testid="sync-button"]');

  // Wait for sync to complete
  await expect(page.locator('[data-testid="sync-status"]'))
    .toContainText('Synkroniseret', { timeout: 10000 });

  // Verify no errors
  await expect(page.locator('[data-testid="sync-error"]')).not.toBeVisible();
});
```

### 4. Performance Tests

```rust
// src-tauri/benches/inference_bench.rs
use criterion::{criterion_group, criterion_main, Criterion};
use cla::inference::*;

fn benchmark_embedding_generation(c: &mut Criterion) {
    let model = load_embedding_model().unwrap();
    let text = "This is a test sentence for embedding generation.";

    c.bench_function("generate_embedding", |b| {
        b.iter(|| model.generate_embedding(text))
    });
}

fn benchmark_batch_embeddings(c: &mut Criterion) {
    let model = load_embedding_model().unwrap();
    let texts: Vec<_> = (0..32)
        .map(|i| format!("Test sentence number {}", i))
        .collect();

    c.bench_function("batch_embeddings_32", |b| {
        b.iter(|| model.generate_embeddings_batch(&texts))
    });
}

criterion_group!(benches, benchmark_embedding_generation, benchmark_batch_embeddings);
criterion_main!(benches);
```

### 5. Security Tests

```rust
// src-tauri/tests/security_tests.rs

#[test]
fn test_path_traversal_blocked() {
    let malicious_paths = vec![
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32",
        "/etc/passwd",
        "C:\\Windows\\System32",
        "file:///etc/passwd",
    ];

    for path in malicious_paths {
        let result = safe_path_join(Path::new("/app/data"), path);
        assert!(result.is_err(), "Path traversal not blocked: {}", path);
    }
}

#[test]
fn test_sql_injection_blocked() {
    let malicious_inputs = vec![
        "'; DROP TABLE users; --",
        "1 OR 1=1",
        "' UNION SELECT * FROM secrets --",
    ];

    for input in malicious_inputs {
        let sanitized = sanitize_search_query(input);
        assert!(!sanitized.contains("DROP"));
        assert!(!sanitized.contains("UNION"));
        assert!(!sanitized.contains("--"));
    }
}

#[test]
fn test_api_key_not_logged() {
    let api_key = "sk-secret-api-key-12345";
    let log_output = format!("Request with key: {}", mask_sensitive(api_key));

    assert!(!log_output.contains("sk-secret"));
    assert!(log_output.contains("***"));
}
```

---

## Running Tests

### Frontend

```bash
# Run all tests
pnpm test

# Watch mode
pnpm test:watch

# With coverage
pnpm test:coverage

# Specific file
pnpm test src/tests/utils.test.ts
```

### Backend

```bash
cd src-tauri

# Run all tests
cargo test

# With output
cargo test -- --nocapture

# Specific test
cargo test test_validate_cpu_limit

# Integration tests only
cargo test --test '*'

# Benchmarks
cargo bench
```

### E2E

```bash
# Run E2E tests
pnpm test:e2e

# With headed browser
pnpm test:e2e --headed

# Specific test file
pnpm test:e2e tests/e2e/settings.spec.ts
```

---

## Coverage Requirements

| Category | Minimum | Target |
|----------|---------|--------|
| Unit Tests | 70% | 90% |
| Integration | 50% | 70% |
| Critical Paths | 95% | 100% |

### Critical Paths (Must be 100%)

- [ ] Authentication flow
- [ ] Data encryption/decryption
- [ ] Sync conflict resolution
- [ ] API key storage
- [ ] Settings persistence

---

## Test Data Management

### Fixtures

```typescript
// src/tests/fixtures/memories.ts
export const mockMemories = [
  {
    id: 'mem_001',
    content: 'Test memory content',
    topics: ['test', 'development'],
    created_at: '2025-01-01T00:00:00Z',
  },
  // ... more fixtures
];
```

### Factory Functions

```rust
// src-tauri/tests/factories.rs
pub fn create_test_memory() -> Memory {
    Memory {
        id: Uuid::new_v4().to_string(),
        content: "Test memory".to_string(),
        topics: vec!["test".to_string()],
        created_at: Utc::now(),
        updated_at: Utc::now(),
    }
}

pub fn create_test_settings() -> Settings {
    Settings {
        max_cpu_percent: 30,
        max_ram_percent: 20,
        idle_only: true,
        ..Settings::default()
    }
}
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - run: pnpm install
      - run: pnpm test:ci
      - uses: codecov/codecov-action@v3

  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo test --all-features
      - run: cargo clippy -- -D warnings

  test-e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - run: pnpm install
      - run: pnpm build
      - run: pnpm test:e2e
```

---

## Test Naming Convention

```
test_[unit]_[what]_[condition]_[expected]

Examples:
- test_validate_cpu_limit_negative_value_returns_error
- test_sync_request_with_conflicts_returns_conflict_list
- test_encrypt_data_with_valid_key_succeeds
```

---

## Mocking Guidelines

### When to Mock

- External APIs (CKC Backend)
- File system operations (for unit tests)
- Time-dependent operations
- Random number generation

### When NOT to Mock

- Core business logic
- Data transformations
- Validation functions

---

## Test Review Checklist

- [ ] Tests cover happy path
- [ ] Tests cover error cases
- [ ] Tests cover edge cases
- [ ] Tests are deterministic (no flaky tests)
- [ ] Tests are fast (< 100ms per unit test)
- [ ] Tests have clear assertions
- [ ] Tests use meaningful names
- [ ] No hardcoded test data in production paths
