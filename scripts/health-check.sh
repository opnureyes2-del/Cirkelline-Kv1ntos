#!/bin/bash
# Cirkelline Health Check Script
# Run: ./scripts/health-check.sh

echo "CIRKELLINE HEALTH CHECK"
echo "======================="

# Backend
curl -s http://localhost:7777/config > /dev/null && echo "Backend:   OK" || echo "Backend:   DOWN"

# Database
docker exec cirkelline-postgres psql -U cirkelline -d cirkelline -c "SELECT 1;" > /dev/null 2>&1 && echo "Database:  OK" || echo "Database:  DOWN"

# pgvector
docker exec cirkelline-postgres psql -U cirkelline -d cirkelline -c "\dx vector" 2>&1 | grep -q "0\." && echo "pgvector:  OK" || echo "pgvector:  MISSING"

# Frontend
curl -s http://localhost:3000 > /dev/null && echo "Frontend:  OK" || echo "Frontend:  DOWN"

# API Key
[[ ! -z "$GOOGLE_API_KEY" ]] && echo "API Key:   OK" || echo "API Key:   MISSING"

echo "======================="
