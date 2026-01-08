# Cirkelline Local Agent (CLA)

A lightweight desktop application for local AI processing that integrates with Cirkelline Knowledge Center (CKC).

## Features

- **Local AI Processing:** Run embeddings, transcription, and OCR locally
- **Resource-Aware:** Respects system resources and only runs when idle
- **Privacy-First:** Your data stays on your device, synced securely to CKC
- **Cross-Platform:** Windows, macOS, and Linux support
- **Offline-Capable:** Works without internet, syncs when connected

## Quick Start

### Prerequisites

- Rust 1.75+
- Node.js 20+
- pnpm

### Installation

```bash
# Clone the repository
git clone https://github.com/cirkelline/cla.git
cd cla

# Setup (installs dependencies and downloads models)
./scripts/setup.sh

# Run in development mode
pnpm tauri dev
```

### Building for Production

```bash
pnpm tauri build
```

## Architecture

```
┌──────────────────────────────────────────┐
│              User Interface              │
│           (React + TailwindCSS)          │
├──────────────────────────────────────────┤
│              Tauri Bridge                │
├──────────────────────────────────────────┤
│              Rust Backend                │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐    │
│  │Inference│ │  Sync   │ │Security │    │
│  │ Engine  │ │ Service │ │ Module  │    │
│  └─────────┘ └─────────┘ └─────────┘    │
├──────────────────────────────────────────┤
│            Storage Layer                 │
│     IndexedDB    │    Local Files        │
└──────────────────────────────────────────┘
```

## Configuration

Default settings (conservative):

| Setting | Default | Description |
|---------|---------|-------------|
| CPU Limit | 30% | Maximum CPU usage |
| RAM Limit | 20% | Maximum RAM usage |
| Idle Only | Yes | Only process when system is idle |
| Auto Start | No | Start with operating system |
| Run on Battery | No | Allow battery operation |

## Model Tiers

### Tier 1 - Essential (81MB)
Always installed:
- **MiniLM** - Text embeddings (384-dim)
- **Whisper Tiny** - Audio transcription
- **PaddleOCR Mobile** - Text extraction

### Tier 2 - Standard (602MB)
Optional, higher quality:
- **Whisper Small** - Better transcription
- **PaddleOCR Server** - Better OCR
- **Sentence-T5** - Better embeddings

### Tier 3 - Professional (2.4GB)
Opt-in, professional quality:
- **Whisper Medium** - Professional transcription
- **BGE-Large** - Premium embeddings
- **LayoutLM** - Document understanding

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design
- [Development](docs/DEVELOPMENT.md) - Development guide
- [API Reference](docs/API.md) - Tauri commands
- [Performance](docs/PERFORMANCE.md) - Optimization guide

## Security

- AES-256-GCM encryption for sensitive data
- Secure sync with CKC (HTTPS/TLS 1.3)
- Input validation and sanitization
- No data collection without consent

## Privacy

CLA is designed with privacy first:
- All processing happens locally
- Data is encrypted at rest
- Sync is optional and secure
- Telemetry is opt-in and anonymized

## License

Copyright © 2025 Cirkelline ApS. All rights reserved.

## Support

- Issues: [GitHub Issues](https://github.com/cirkelline/cla/issues)
- Docs: [Documentation](https://docs.cirkelline.com/cla)
- Email: support@cirkelline.com
