# CLA Development Guide

## Prerequisites

### Required

- **Rust:** 1.75+ with `cargo`
- **Node.js:** 20+ with `pnpm`
- **System Libraries:**
  - Linux: `libgtk-3-dev`, `libwebkit2gtk-4.1-dev`, `libayatana-appindicator3-dev`
  - macOS: Xcode Command Line Tools
  - Windows: Microsoft C++ Build Tools

### Optional

- **ONNX Runtime:** For testing inference locally
- **Docker:** For containerized development

## Quick Start

```bash
# Clone and setup
cd /path/to/cla
./scripts/setup.sh

# Start development
pnpm tauri dev
```

## Project Structure

```
cla/
├── src/                    # Frontend source
│   ├── components/         # React components
│   ├── stores/            # Zustand stores
│   ├── services/          # Business logic
│   └── tests/             # Vitest tests
├── src-tauri/             # Backend source
│   ├── src/               # Rust code
│   └── tests/             # Integration tests
├── docs/                  # Documentation
└── scripts/               # Build scripts
```

## Development Workflow

### Frontend Development

```bash
# Run frontend only (without Tauri)
pnpm dev

# Run tests
pnpm test

# Type checking
pnpm type-check

# Lint
pnpm lint
```

### Backend Development

```bash
# Run Rust tests
cd src-tauri
cargo test

# Check formatting
cargo fmt --check

# Run clippy
cargo clippy --all-targets --all-features

# Build release
cargo build --release
```

### Full Application

```bash
# Development mode (hot reload)
pnpm tauri dev

# Production build
pnpm tauri build
```

## Adding New Features

### 1. Adding a Tauri Command

```rust
// src-tauri/src/commands/your_feature.rs

use tauri::command;
use crate::error::ClaResult;

#[command]
pub async fn your_command(arg: String) -> ClaResult<String> {
    // Implementation
    Ok(format!("Result: {}", arg))
}
```

Register in `main.rs`:

```rust
.invoke_handler(tauri::generate_handler![
    // ... existing commands
    commands::your_feature::your_command,
])
```

Call from frontend:

```typescript
import { invoke } from '@tauri-apps/api/core';

const result = await invoke<string>('your_command', { arg: 'test' });
```

### 2. Adding a UI Component

```tsx
// src/components/YourComponent.tsx

import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';

export function YourComponent() {
  const [data, setData] = useState<string | null>(null);

  useEffect(() => {
    invoke<string>('your_command', { arg: 'init' })
      .then(setData)
      .catch(console.error);
  }, []);

  return (
    <div className="p-4">
      <h2 className="text-lg font-semibold">Your Feature</h2>
      <p>{data ?? 'Loading...'}</p>
    </div>
  );
}
```

### 3. Adding a Zustand Store

```typescript
// src/stores/yourStore.ts

import { create } from 'zustand';

interface YourState {
  value: string;
  setValue: (value: string) => void;
}

export const useYourStore = create<YourState>((set) => ({
  value: '',
  setValue: (value) => set({ value }),
}));
```

### 4. Adding a Database Entity

```typescript
// src/services/database.ts

export interface YourEntity {
  id: string;
  name: string;
  created_at: string;
}

export async function saveYourEntity(entity: YourEntity): Promise<void> {
  const db = await getDatabase();
  await db.put('your_entities', entity);
}

export async function getYourEntity(id: string): Promise<YourEntity | undefined> {
  const db = await getDatabase();
  return db.get('your_entities', id);
}
```

## Testing

### Frontend Tests (Vitest)

```typescript
// src/tests/your_feature.test.ts

import { describe, it, expect, vi } from 'vitest';
import { yourFunction } from '../services/your_feature';

describe('Your Feature', () => {
  it('should work correctly', () => {
    const result = yourFunction('input');
    expect(result).toBe('expected output');
  });
});
```

Run tests:

```bash
pnpm test        # Watch mode
pnpm test:ci     # Single run with coverage
```

### Backend Tests (Rust)

```rust
// src-tauri/tests/your_feature_tests.rs

#[cfg(test)]
mod tests {
    use cla::your_module::*;

    #[test]
    fn test_your_function() {
        let result = your_function("input");
        assert_eq!(result, "expected");
    }

    #[tokio::test]
    async fn test_async_function() {
        let result = async_function().await;
        assert!(result.is_ok());
    }
}
```

Run tests:

```bash
cd src-tauri
cargo test
cargo test --test your_feature_tests  # Specific test file
```

## Debugging

### Frontend

1. Use Chrome DevTools (F12 in dev mode)
2. React DevTools extension
3. Console logging

### Backend

1. Enable logging:
   ```rust
   log::info!("Debug message: {:?}", value);
   ```

2. Run with debug output:
   ```bash
   RUST_LOG=debug pnpm tauri dev
   ```

3. Use `dbg!()` macro:
   ```rust
   let result = dbg!(some_function());
   ```

## Common Issues

### Build Failures

**Linux - Missing libraries:**
```bash
sudo apt-get install libgtk-3-dev libwebkit2gtk-4.1-dev libayatana-appindicator3-dev librsvg2-dev
```

**macOS - Xcode:**
```bash
xcode-select --install
```

**Windows - MSVC:**
Download and install Visual Studio Build Tools.

### Runtime Issues

**Tauri IPC not working:**
- Check command is registered in `invoke_handler`
- Verify command name matches exactly
- Check for serialization errors in command arguments

**IndexedDB errors:**
- Clear browser data in dev mode
- Check schema migrations

## Code Style

### TypeScript

- Use functional components with hooks
- Prefer `const` over `let`
- Use TypeScript strict mode
- Format with Prettier

### Rust

- Follow Rust API Guidelines
- Use `clippy` with all warnings
- Format with `rustfmt`
- Document public APIs

## Performance Considerations

1. **Lazy Loading:** Load AI models on demand
2. **Debouncing:** Debounce UI updates from backend events
3. **Pagination:** Use cursor-based pagination for large datasets
4. **Caching:** Cache inference results with content hashes
5. **Background Processing:** Use Tauri events for long-running tasks

## Security Best Practices

1. **Never trust frontend input:** Validate all IPC arguments
2. **Use parameterized queries:** Avoid SQL injection
3. **Sanitize paths:** Prevent path traversal
4. **Encrypt sensitive data:** Use the security module
5. **Audit dependencies:** Run `cargo audit` and `pnpm audit`

---

## Internationalization (I18N) & Localization (L10N)

CLA is designed for global deployment. Follow these guidelines for I18N-ready code.

### Supported Languages (Planned)

| Code | Language | Status |
|------|----------|--------|
| `da` | Danish | Primary |
| `en` | English | Secondary |
| `de` | German | Planned |

### Frontend I18N Setup

**Using react-i18next:**

```bash
pnpm add react-i18next i18next i18next-browser-languagedetector
```

**Directory Structure:**
```
src/
├── locales/
│   ├── da/
│   │   └── translation.json
│   ├── en/
│   │   └── translation.json
│   └── index.ts
```

**Translation File Example:**
```json
// src/locales/da/translation.json
{
  "settings": {
    "title": "Indstillinger",
    "cpu_limit": "CPU grænse",
    "ram_limit": "RAM grænse",
    "save": "Gem",
    "cancel": "Annuller"
  },
  "sync": {
    "syncing": "Synkroniserer...",
    "last_sync": "Sidst synkroniseret: {{time}}",
    "offline": "Offline tilstand"
  }
}
```

**Usage in Components:**
```tsx
import { useTranslation } from 'react-i18next';

export function SettingsPage() {
  const { t } = useTranslation();

  return (
    <div>
      <h1>{t('settings.title')}</h1>
      <button>{t('settings.save')}</button>
    </div>
  );
}
```

### Backend I18N (Rust)

**Using rust-i18n:**

```toml
# Cargo.toml
[dependencies]
rust-i18n = "3"
```

**Setup:**
```rust
// src/main.rs
rust_i18n::i18n!("locales");

// Usage
let message = t!("error.network_failed");
let formatted = t!("sync.progress", count = 5, total = 10);
```

**Locale Files:**
```yaml
# locales/da.yml
error:
  network_failed: "Netværksforbindelse fejlede"
  file_not_found: "Fil ikke fundet: {path}"
sync:
  progress: "Synkroniserer {count} af {total}"
```

### I18N Best Practices

1. **Never hardcode user-facing strings**
   ```tsx
   // Bad
   <button>Save Settings</button>

   // Good
   <button>{t('settings.save')}</button>
   ```

2. **Use ICU message format for plurals**
   ```json
   {
     "items": "{count, plural, =0 {Ingen elementer} one {# element} other {# elementer}}"
   }
   ```

3. **Handle date/time localization**
   ```tsx
   import { formatDate } from 'date-fns';
   import { da } from 'date-fns/locale';

   formatDate(date, 'PPP', { locale: da });
   ```

4. **RTL-ready layout (future)**
   ```css
   /* Use logical properties */
   margin-inline-start: 1rem;  /* Instead of margin-left */
   padding-inline-end: 1rem;   /* Instead of padding-right */
   ```

5. **Extract strings during development**
   ```bash
   # Use i18next-parser to find missing translations
   pnpm i18next-parser
   ```

### Testing Translations

```typescript
// src/tests/i18n.test.ts
import { describe, it, expect } from 'vitest';
import da from '../locales/da/translation.json';
import en from '../locales/en/translation.json';

describe('Translations', () => {
  it('should have matching keys in all languages', () => {
    const daKeys = Object.keys(flattenObject(da));
    const enKeys = Object.keys(flattenObject(en));

    expect(daKeys).toEqual(enKeys);
  });

  it('should not have empty translations', () => {
    const daValues = Object.values(flattenObject(da));
    daValues.forEach(value => {
      expect(value).not.toBe('');
    });
  });
});
```

### Locale Detection Priority

1. User preference (stored in settings)
2. Browser/OS language
3. Default to Danish (`da`)
