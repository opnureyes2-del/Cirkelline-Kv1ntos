#!/bin/bash
# CLA Model Download Script
# Downloads ONNX models for local AI inference
#
# Models:
# - all-MiniLM-L6-v2: Text embeddings (384-dim)
# - Whisper Tiny EN: Audio transcription
#
# Usage: ./scripts/download-models.sh [--tier 1|2|3]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MODELS_DIR="$PROJECT_DIR/src-tauri/models"

# Model URLs (Hugging Face - GRATIS)
# Using ONNX-optimized models from Hugging Face Hub
MINILM_URL="https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/onnx/model.onnx"
MINILM_VOCAB_URL="https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/vocab.txt"

# Whisper Tiny EN - Using Xenova's optimized ONNX export
WHISPER_ENCODER_URL="https://huggingface.co/Xenova/whisper-tiny.en/resolve/main/onnx/encoder_model.onnx"
WHISPER_DECODER_URL="https://huggingface.co/Xenova/whisper-tiny.en/resolve/main/onnx/decoder_model_merged.onnx"

# Expected checksums (SHA256)
MINILM_CHECKSUM="expected_checksum_here"  # Will be updated after first download
MINILM_VOCAB_CHECKSUM="expected_checksum_here"

# Parse arguments
TIER=1
while [[ $# -gt 0 ]]; do
    case $1 in
        --tier)
            TIER="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--tier 1|2|3]"
            echo ""
            echo "Tiers:"
            echo "  1 - Essential (81MB): MiniLM + Whisper Tiny"
            echo "  2 - Standard (602MB): + Whisper Small + Better OCR"
            echo "  3 - Professional (2.4GB): + Whisper Medium + BGE-Large"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

download_file() {
    local url="$1"
    local dest="$2"
    local name="$3"

    if [[ -f "$dest" ]]; then
        log_warning "$name already exists, skipping..."
        return 0
    fi

    log_info "Downloading $name..."

    # Create directory if needed
    mkdir -p "$(dirname "$dest")"

    # Download with progress
    if command -v curl &> /dev/null; then
        curl -L --progress-bar -o "$dest" "$url" || {
            log_error "Failed to download $name"
            rm -f "$dest"
            return 1
        }
    elif command -v wget &> /dev/null; then
        wget --show-progress -q -O "$dest" "$url" || {
            log_error "Failed to download $name"
            rm -f "$dest"
            return 1
        }
    else
        log_error "Neither curl nor wget found. Please install one."
        exit 1
    fi

    log_success "$name downloaded successfully"
    return 0
}

verify_checksum() {
    local file="$1"
    local expected="$2"
    local name="$3"

    if [[ "$expected" == "expected_checksum_here" ]]; then
        log_warning "Checksum not configured for $name, computing..."
        local actual=$(sha256sum "$file" | cut -d' ' -f1)
        echo "  SHA256: $actual"
        return 0
    fi

    local actual=$(sha256sum "$file" | cut -d' ' -f1)
    if [[ "$actual" == "$expected" ]]; then
        log_success "$name checksum verified"
        return 0
    else
        log_error "$name checksum mismatch!"
        echo "  Expected: $expected"
        echo "  Actual:   $actual"
        return 1
    fi
}

get_file_size() {
    local file="$1"
    if [[ -f "$file" ]]; then
        local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        echo "$((size / 1024 / 1024))MB"
    else
        echo "N/A"
    fi
}

# Main
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Cirkelline Local Agent - Model Download${NC}"
echo -e "${BLUE}  Tier: $TIER | Destination: $MODELS_DIR${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Create models directory
mkdir -p "$MODELS_DIR"
mkdir -p "$MODELS_DIR/whisper-tiny-en"

# Check disk space
AVAILABLE_SPACE=$(df -BM "$MODELS_DIR" | tail -1 | awk '{print $4}' | tr -d 'M')
REQUIRED_SPACE=100  # MB for Tier 1

if [[ $TIER -eq 2 ]]; then
    REQUIRED_SPACE=700
elif [[ $TIER -eq 3 ]]; then
    REQUIRED_SPACE=2500
fi

if [[ $AVAILABLE_SPACE -lt $REQUIRED_SPACE ]]; then
    log_error "Insufficient disk space. Need ${REQUIRED_SPACE}MB, have ${AVAILABLE_SPACE}MB"
    exit 1
fi

log_info "Disk space check passed (${AVAILABLE_SPACE}MB available)"
echo ""

# ═══════════════════════════════════════════════════════════════
# TIER 1 - Essential Models (81MB)
# ═══════════════════════════════════════════════════════════════

echo -e "${GREEN}▸ Tier 1: Essential Models${NC}"
echo ""

# 1. MiniLM Embedding Model
download_file \
    "$MINILM_URL" \
    "$MODELS_DIR/all-minilm-l6-v2.onnx" \
    "all-MiniLM-L6-v2 (Embeddings)"

# 2. MiniLM Vocabulary
download_file \
    "$MINILM_VOCAB_URL" \
    "$MODELS_DIR/vocab.txt" \
    "MiniLM Vocabulary"

# 3. Whisper Tiny EN Encoder
download_file \
    "$WHISPER_ENCODER_URL" \
    "$MODELS_DIR/whisper-tiny-en/encoder.onnx" \
    "Whisper Tiny EN Encoder"

# 4. Whisper Tiny EN Decoder
download_file \
    "$WHISPER_DECODER_URL" \
    "$MODELS_DIR/whisper-tiny-en/decoder.onnx" \
    "Whisper Tiny EN Decoder"

echo ""

# ═══════════════════════════════════════════════════════════════
# TIER 2 - Standard Models (602MB additional)
# ═══════════════════════════════════════════════════════════════

if [[ $TIER -ge 2 ]]; then
    echo -e "${GREEN}▸ Tier 2: Standard Models${NC}"
    echo ""
    log_warning "Tier 2 models not yet configured - skipping"
    echo ""
fi

# ═══════════════════════════════════════════════════════════════
# TIER 3 - Professional Models (2.4GB additional)
# ═══════════════════════════════════════════════════════════════

if [[ $TIER -ge 3 ]]; then
    echo -e "${GREEN}▸ Tier 3: Professional Models${NC}"
    echo ""
    log_warning "Tier 3 models not yet configured - skipping"
    echo ""
fi

# ═══════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Download Complete!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Models installed:"
echo ""

# List downloaded files with sizes
if [[ -f "$MODELS_DIR/all-minilm-l6-v2.onnx" ]]; then
    SIZE=$(get_file_size "$MODELS_DIR/all-minilm-l6-v2.onnx")
    echo -e "  ${GREEN}✓${NC} all-minilm-l6-v2.onnx ($SIZE)"
fi

if [[ -f "$MODELS_DIR/vocab.txt" ]]; then
    SIZE=$(get_file_size "$MODELS_DIR/vocab.txt")
    echo -e "  ${GREEN}✓${NC} vocab.txt ($SIZE)"
fi

if [[ -f "$MODELS_DIR/whisper-tiny-en/encoder.onnx" ]]; then
    SIZE=$(get_file_size "$MODELS_DIR/whisper-tiny-en/encoder.onnx")
    echo -e "  ${GREEN}✓${NC} whisper-tiny-en/encoder.onnx ($SIZE)"
fi

if [[ -f "$MODELS_DIR/whisper-tiny-en/decoder.onnx" ]]; then
    SIZE=$(get_file_size "$MODELS_DIR/whisper-tiny-en/decoder.onnx")
    echo -e "  ${GREEN}✓${NC} whisper-tiny-en/decoder.onnx ($SIZE)"
fi

echo ""

# Total size
TOTAL_SIZE=$(du -sh "$MODELS_DIR" 2>/dev/null | cut -f1)
echo "Total models size: $TOTAL_SIZE"
echo ""
echo "You can now run: pnpm tauri dev"
echo ""
