#!/bin/bash
# CLA Build Script
# Builds the Cirkelline Local Agent for the current platform

set -e

echo "🔵 Building Cirkelline Local Agent"
echo "==================================="

cd "$(dirname "$0")/.."

# Check for required tools
if ! command -v cargo &> /dev/null; then
    echo "❌ Rust is not installed. Run ./scripts/setup.sh first."
    exit 1
fi

if ! command -v pnpm &> /dev/null; then
    echo "❌ pnpm is not installed. Run ./scripts/setup.sh first."
    exit 1
fi

# Build frontend
echo "📦 Building frontend..."
pnpm build

# Build Tauri app
echo "📦 Building Tauri app..."
pnpm tauri build

echo ""
echo "✅ Build complete!"
echo ""
echo "Output files are in: src-tauri/target/release/bundle/"
