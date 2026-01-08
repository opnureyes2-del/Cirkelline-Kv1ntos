#!/bin/bash
# CLA Setup Script
# This script installs all dependencies for the Cirkelline Local Agent

set -e

echo "🔵 Cirkelline Local Agent Setup"
echo "================================"

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "📦 Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
fi

echo "✅ Rust version: $(rustc --version)"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

echo "✅ Node.js version: $(node --version)"

# Check if pnpm is installed
if ! command -v pnpm &> /dev/null; then
    echo "📦 Installing pnpm..."
    npm install -g pnpm
fi

echo "✅ pnpm version: $(pnpm --version)"

# Install Tauri CLI
echo "📦 Installing Tauri CLI..."
cargo install tauri-cli --version "^2.0"

# Install system dependencies (Linux)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "📦 Installing Linux system dependencies..."
    sudo apt update
    sudo apt install -y \
        libwebkit2gtk-4.1-dev \
        libappindicator3-dev \
        librsvg2-dev \
        patchelf \
        libssl-dev \
        libgtk-3-dev \
        libayatana-appindicator3-dev
fi

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd "$(dirname "$0")/.."
pnpm install

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start development:"
echo "  pnpm tauri dev"
echo ""
echo "To build for production:"
echo "  pnpm tauri build"
