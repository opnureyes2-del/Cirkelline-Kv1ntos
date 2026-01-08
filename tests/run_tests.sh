#!/bin/bash

echo "🧪 Running Cirkelline Test Suite"
echo "================================"
echo ""

# Activate virtual environment
source .venv/bin/activate

# Run tests
python tests/test_cirkelline.py

echo ""
echo "Tests complete!"
