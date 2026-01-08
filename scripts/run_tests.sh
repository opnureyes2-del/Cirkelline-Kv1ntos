#!/bin/bash

echo ">ê CIRKELLINE COMPREHENSIVE TEST SUITE"
echo "========================================"
echo ""

# Activate virtual environment
source .venv/bin/activate

# Load environment variables
export $(cat .env | xargs)

# Run pytest with coverage
echo "Running all tests..."
echo ""

pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo " ALL TESTS PASSED!"
    echo ""
    echo "Coverage report generated in htmlcov/index.html"
    echo "Open it with: firefox htmlcov/index.html"
else
    echo ""
    echo "L SOME TESTS FAILED"
    echo "Review the output above for details"
    exit 1
fi
