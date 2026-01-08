# CLA Build Guide

**Version:** 1.0.0
**Last Updated:** 2025-12-09
**Platforms:** Windows, macOS, Linux

---

## Overview

This guide covers building CLA (Cirkelline Local Agent) from source for all supported platforms.

---

## Prerequisites

### All Platforms

| Requirement | Version | Purpose |
|-------------|---------|---------|
| **Node.js** | 18+ | Frontend build |
| **pnpm** | 9+ | Package manager |
| **Rust** | 1.70+ | Backend build |
| **Git** | 2.x | Source control |

### Platform-Specific

#### Windows

```powershell
# Install Visual Studio Build Tools
winget install Microsoft.VisualStudio.2022.BuildTools

# Install Rust
winget install Rustlang.Rustup

# Install Node.js
winget install OpenJS.NodeJS.LTS

# Install pnpm
npm install -g pnpm
```

#### macOS

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install Node.js
brew install node@18

# Install pnpm
npm install -g pnpm
```

#### Linux (Ubuntu/Debian)

```bash
# System dependencies
sudo apt update
sudo apt install -y \
    build-essential \
    curl \
    wget \
    libssl-dev \
    libgtk-3-dev \
    libwebkit2gtk-4.1-dev \
    libappindicator3-dev \
    librsvg2-dev \
    patchelf

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Install Node.js (via nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 18
nvm use 18

# Install pnpm
npm install -g pnpm
```

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/cirkelline/cirkelline-system.git
cd cirkelline-system/cla
```

### 2. Install Dependencies

```bash
# Frontend dependencies
pnpm install

# Rust dependencies (automatic on build)
```

### 3. Development Build

```bash
# Start development server
pnpm tauri dev
```

### 4. Production Build

```bash
# Build for current platform
pnpm tauri build
```

---

## Detailed Build Process

### Frontend Build

```bash
# Install dependencies
pnpm install

# Type check
pnpm typecheck

# Lint
pnpm lint

# Build frontend only
pnpm build
```

**Output:** `dist/` directory with compiled frontend assets.

### Rust Backend Build

```bash
cd src-tauri

# Check for errors
cargo check

# Build debug
cargo build

# Build release
cargo build --release
```

**Output:** `target/release/cirkelline-local-agent`

### Full Tauri Build

```bash
# From project root
pnpm tauri build

# Or with verbose output
pnpm tauri build --verbose
```

**Output locations:**

| Platform | Location |
|----------|----------|
| Windows | `src-tauri/target/release/bundle/msi/` |
| macOS | `src-tauri/target/release/bundle/dmg/` |
| Linux | `src-tauri/target/release/bundle/deb/` |

---

## Build Configuration

### Tauri Configuration

`src-tauri/tauri.conf.json`:

```json
{
  "productName": "Cirkelline Local Agent",
  "version": "1.0.0",
  "identifier": "com.cirkelline.cla",
  "build": {
    "beforeBuildCommand": "pnpm build",
    "beforeDevCommand": "pnpm dev",
    "devUrl": "http://localhost:5173",
    "frontendDist": "../dist"
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": [
      "icons/32x32.png",
      "icons/128x128.png",
      "icons/128x128@2x.png",
      "icons/icon.icns",
      "icons/icon.ico"
    ],
    "resources": ["resources/*"],
    "windows": {
      "certificateThumbprint": null,
      "wix": {
        "language": ["da-DK", "en-US"]
      }
    },
    "macOS": {
      "entitlements": null,
      "minimumSystemVersion": "10.15"
    },
    "linux": {
      "deb": {
        "depends": ["libwebkit2gtk-4.1-0"]
      }
    }
  }
}
```

### Cargo Configuration

`src-tauri/Cargo.toml`:

```toml
[package]
name = "cirkelline-local-agent"
version = "1.0.0"
edition = "2021"

[build-dependencies]
tauri-build = { version = "2.5", features = [] }

[dependencies]
tauri = { version = "2.5", features = ["protocol-asset"] }
tauri-plugin-shell = "2.5"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tokio = { version = "1.0", features = ["full"] }
candle-core = "0.8"
candle-transformers = "0.8"
rusqlite = { version = "0.32", features = ["bundled"] }
reqwest = { version = "0.12", features = ["json"] }
keyring = "3.0"
chrono = { version = "0.4", features = ["serde"] }
dirs = "5.0"

[features]
default = ["custom-protocol"]
custom-protocol = ["tauri/custom-protocol"]

[profile.release]
strip = true
lto = true
codegen-units = 1
panic = "abort"
```

---

## Platform-Specific Builds

### Windows

```powershell
# Ensure Visual Studio Build Tools are installed

# Build MSI installer
pnpm tauri build

# Output: src-tauri/target/release/bundle/msi/Cirkelline Local Agent_1.0.0_x64_en-US.msi
```

**Code Signing (optional):**

```powershell
# Set certificate thumbprint in tauri.conf.json
# Or use environment variable:
$env:TAURI_SIGNING_PRIVATE_KEY = "path/to/key"
$env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD = "password"
```

### macOS

```bash
# Build DMG
pnpm tauri build

# Output: src-tauri/target/release/bundle/dmg/Cirkelline Local Agent_1.0.0_aarch64.dmg
```

**Universal Binary (Intel + Apple Silicon):**

```bash
# Add targets
rustup target add x86_64-apple-darwin
rustup target add aarch64-apple-darwin

# Build universal
pnpm tauri build --target universal-apple-darwin
```

**Code Signing & Notarization:**

```bash
# Set up signing identity
export APPLE_SIGNING_IDENTITY="Developer ID Application: Your Name (XXXXXXXXXX)"
export APPLE_ID="your@email.com"
export APPLE_PASSWORD="app-specific-password"
export APPLE_TEAM_ID="XXXXXXXXXX"

# Build with signing
pnpm tauri build
```

### Linux

```bash
# Build .deb package
pnpm tauri build

# Output: src-tauri/target/release/bundle/deb/cirkelline-local-agent_1.0.0_amd64.deb

# Build AppImage
pnpm tauri build --bundles appimage

# Output: src-tauri/target/release/bundle/appimage/cirkelline-local-agent_1.0.0_amd64.AppImage
```

---

## Cross-Compilation

### From macOS to Windows

```bash
# Install cross-compilation tools
brew install mingw-w64

# Add target
rustup target add x86_64-pc-windows-gnu

# Build (frontend must be pre-built)
cd src-tauri
cargo build --release --target x86_64-pc-windows-gnu
```

### Using Docker

```bash
# Build Linux binary from any platform
docker run --rm -v $(pwd):/app -w /app \
    ghcr.io/aspect-build/gcc-toolchain:18-bookworm \
    bash -c "pnpm install && pnpm tauri build"
```

---

## AI Models

### Downloading Models

```bash
# Run model download script
./scripts/download-models.sh

# Or manually download
mkdir -p ~/.cla/models
wget -O ~/.cla/models/gemma-2b.gguf \
    https://huggingface.co/google/gemma-2b-it-GGUF/resolve/main/gemma-2b-it.gguf
```

### Model Verification

```bash
# Verify model checksum
sha256sum ~/.cla/models/gemma-2b.gguf
# Expected: <checksum from manifest>
```

### Including Models in Build

```json
// tauri.conf.json - Include models in bundle
{
  "bundle": {
    "resources": [
      "resources/*",
      "../models/*.gguf"
    ]
  }
}
```

---

## Troubleshooting

### Common Issues

#### Build fails with "linker not found"

**Windows:**
```powershell
# Install Visual Studio Build Tools with C++ workload
winget install Microsoft.VisualStudio.2022.BuildTools --override "--wait --quiet --add Microsoft.VisualStudio.Workload.VCTools"
```

**Linux:**
```bash
sudo apt install build-essential
```

#### "webkit2gtk not found" (Linux)

```bash
sudo apt install libwebkit2gtk-4.1-dev
```

#### "candle" build fails

```bash
# Ensure you have OpenBLAS (optional, for CPU acceleration)
sudo apt install libopenblas-dev  # Linux
brew install openblas             # macOS
```

#### Out of memory during build

```bash
# Reduce parallel compilation
export CARGO_BUILD_JOBS=2

# Or increase swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### TypeScript errors

```bash
# Clear cache and rebuild
rm -rf node_modules dist
pnpm install
pnpm build
```

### Debug Build

```bash
# Build with debug symbols
cd src-tauri
cargo build

# Run with debug logging
RUST_LOG=debug ./target/debug/cirkelline-local-agent
```

### Verbose Build Output

```bash
pnpm tauri build --verbose 2>&1 | tee build.log
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/build.yml
name: Build CLA

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    strategy:
      matrix:
        platform: [ubuntu-22.04, windows-latest, macos-latest]

    runs-on: ${{ matrix.platform }}

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 18

      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable

      - name: Install pnpm
        run: npm install -g pnpm

      - name: Install dependencies (Linux)
        if: matrix.platform == 'ubuntu-22.04'
        run: |
          sudo apt update
          sudo apt install -y libgtk-3-dev libwebkit2gtk-4.1-dev libappindicator3-dev

      - name: Install frontend dependencies
        working-directory: cla
        run: pnpm install

      - name: Build
        working-directory: cla
        run: pnpm tauri build

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: cla-${{ matrix.platform }}
          path: |
            cla/src-tauri/target/release/bundle/**/*
```

---

## Development Tips

### Hot Reload

```bash
# Frontend changes hot reload automatically with:
pnpm tauri dev
```

### Rust Changes

```bash
# Rust changes require restart, but `tauri dev` watches for changes
# For faster iteration on Rust:
cd src-tauri
cargo watch -x check  # Just type checking
cargo watch -x run    # Full rebuild
```

### Testing

```bash
# Frontend tests
pnpm test

# Rust tests
cd src-tauri
cargo test

# Integration tests
pnpm test:e2e
```

---

## Release Checklist

- [ ] Update version in `package.json`
- [ ] Update version in `src-tauri/Cargo.toml`
- [ ] Update version in `src-tauri/tauri.conf.json`
- [ ] Update CHANGELOG
- [ ] Run full test suite
- [ ] Build for all platforms
- [ ] Test installers on clean machines
- [ ] Code sign (production releases)
- [ ] Create GitHub release
- [ ] Upload artifacts

---

## Related Documentation

- [Architecture](ARCHITECTURE.md) - System architecture
- [Security](../SECURITY.md) - Security policy
- [Tauri Docs](https://tauri.app/v1/guides/) - Official Tauri documentation

---

*This documentation is part of the Cirkelline FASE 2 Documentation Initiative.*
