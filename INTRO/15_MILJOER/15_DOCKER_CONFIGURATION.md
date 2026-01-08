# Docker Configuration - cirkelline-kv1ntos

**Status:** Production-Ready (Local)
**Version:** Docker Compose v3.8+
**Last Updated:** 2025-12-20

---

## Overview

cirkelline-kv1ntos uses Docker to containerize PostgreSQL, Redis, and RabbitMQ services. The backend and frontend run locally (not in containers) for easier development.

```
┌──────────────────────────────────────────┐
│  Frontend (Next.js) - localhost:3000     │
│  Running in terminal (not containerized) │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│  Backend (FastAPI) - localhost:7777      │
│  Running in terminal (not containerized) │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│  Docker Containers (from docker-compose) │
├──────────────────────────────────────────┤
│  cirkelline-postgres:5532                │
│  redis:6381                              │
│  rabbitmq:5672 & 15672                  │
└──────────────────────────────────────────┘
```

---

## docker-compose.yml

### Basic Configuration

```yaml
version: '3.8'

services:
  # PostgreSQL Database with pgvector
  cirkelline-postgres:
    image: pgvector/pgvector:pg17
    container_name: cirkelline-postgres
    environment:
      POSTGRES_DB: cirkelline
      POSTGRES_USER: cirkelline
      POSTGRES_PASSWORD: cirkelline123
    ports:
      - "5532:5432"
    volumes:
      - cirkelline_postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U cirkelline"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - cirkelline_network

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: cirkelline-redis
    ports:
      - "6381:6379"
    volumes:
      - cirkelline_redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - cirkelline_network

  # RabbitMQ Message Queue
  rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: cirkelline-rabbitmq
    environment:
      RABBITMQ_DEFAULT_USER: guest
      RABBITMQ_DEFAULT_PASS: guest
    ports:
      - "5672:5672"        # AMQP
      - "15672:15672"      # Management UI
    volumes:
      - cirkelline_rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - cirkelline_network

volumes:
  cirkelline_postgres_data:
    driver: local
  cirkelline_redis_data:
    driver: local
  cirkelline_rabbitmq_data:
    driver: local

networks:
  cirkelline_network:
    driver: bridge
```

### Service Details

#### PostgreSQL 17
```yaml
cirkelline-postgres:
  image: pgvector/pgvector:pg17
  ports:
    - "5532:5432"
  environment:
    POSTGRES_DB: cirkelline
    POSTGRES_USER: cirkelline
    POSTGRES_PASSWORD: cirkelline123
```

- **Image:** pgvector/pgvector:pg17 (includes pgvector extension)
- **Port:** 5532 → 5432
- **Database:** cirkelline
- **User:** cirkelline
- **Password:** cirkelline123
- **Data Persistence:** `cirkelline_postgres_data` volume
- **Health Check:** pg_isready every 10s

#### Redis 7
```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6381:6379"
```

- **Image:** redis:7-alpine (lightweight)
- **Port:** 6381 → 6379
- **Data Persistence:** `cirkelline_redis_data` volume
- **Health Check:** redis-cli ping every 10s

#### RabbitMQ 3 Management
```yaml
rabbitmq:
  image: rabbitmq:3-management-alpine
  ports:
    - "5672:5672"      # AMQP protocol
    - "15672:15672"    # Management UI
```

- **Image:** rabbitmq:3-management-alpine
- **AMQP Port:** 5672 → 5672
- **Management Port:** 15672 → 15672
- **Default User:** guest / guest
- **Management UI:** http://localhost:15672
- **Health Check:** rabbitmq-diagnostics every 10s

---

## Docker Management Commands

### Starting Services

```bash
# Start all services
cd /home/rasmus/Desktop/projekts/projects/cirkelline-kv1ntos
docker-compose up -d

# Expected output:
#   Creating cirkelline-postgres ...
#   Creating cirkelline-redis ...
#   Creating cirkelline-rabbitmq ...

# Verify all running
docker-compose ps
# Should show 3 containers with status "Up"
```

### Checking Status

```bash
# List running containers
docker ps

# Show all services (including stopped)
docker ps -a

# View logs
docker-compose logs                    # All services
docker-compose logs cirkelline-postgres # PostgreSQL only
docker-compose logs -f redis           # Follow redis logs

# Check health
docker-compose ps  # Health status in "Status" column
```

### Database Management

```bash
# Connect to PostgreSQL
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline

# Inside psql:
\dt ai.*           # List tables in ai schema
\dt public.*       # List tables in public schema
\dx vector         # Check pgvector extension
SELECT 1;          # Test connection
\q                 # Exit

# Run SQL command without interactive shell
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline \
  -c "SELECT 1;"
```

### Redis Management

```bash
# Connect to Redis
docker exec -it cirkelline-redis redis-cli

# Inside redis-cli:
ping                # Test connection
info stats          # Statistics
dbsize              # Number of keys
keys *              # List all keys
flushdb             # Clear current database
exit                # Exit

# Quick commands
docker exec -it cirkelline-redis redis-cli ping
docker exec -it cirkelline-redis redis-cli dbsize
docker exec -it cirkelline-redis redis-cli flushall
```

### RabbitMQ Management

```bash
# Access Management UI
# Open browser: http://localhost:15672
# Username: guest
# Password: guest

# Via command line
docker exec -it cirkelline-rabbitmq rabbitmqctl status
docker exec -it cirkelline-rabbitmq rabbitmqctl list_users
docker exec -it cirkelline-rabbitmq rabbitmqctl list_queues
```

### Stopping & Cleanup

```bash
# Stop all services (data persists in volumes)
docker-compose down

# Stop and remove volumes (DELETES ALL DATA!)
docker-compose down -v

# Remove only containers, keep volumes
docker-compose rm -f

# Restart a specific service
docker-compose restart cirkelline-postgres
```

---

## Dockerfile for Backend

Used for AWS ECS Fargate deployment (not for local development).

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 7777

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7777/health || exit 1

# Run application
CMD ["uvicorn", "my_os:app", "--host", "0.0.0.0", "--port", "7777"]
```

**Important Features:**
- Includes `curl` for health checks (required for ECS)
- PostgreSQL client for database migrations
- Slim Python image to reduce size
- Health check endpoint configured

---

## Network & Connectivity

### Internal Docker Network
All containers connect via `cirkelline_network` bridge:
- `cirkelline-postgres:5432` → accessible as `postgres:5432` from other containers
- `redis:6379` → accessible as `redis:6379`
- `rabbitmq:5672` → accessible as `rabbitmq:5672`

### Backend Connection Strings

```python
# From backend (running locally, not in container)
DATABASE_URL = "postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline"
REDIS_URL = "redis://localhost:6381"
RABBITMQ_URL = "amqp://guest:guest@localhost:5672/"

# If backend was in container:
DATABASE_URL = "postgresql+psycopg://cirkelline:cirkelline123@cirkelline-postgres:5432/cirkelline"
REDIS_URL = "redis://redis:6379"
RABBITMQ_URL = "amqp://guest:guest@rabbitmq:5672/"
```

---

## Environment Variables for Docker

### PostgreSQL
```yaml
environment:
  POSTGRES_DB: cirkelline         # Database name
  POSTGRES_USER: cirkelline       # Username
  POSTGRES_PASSWORD: cirkelline123 # Password
```

### RabbitMQ
```yaml
environment:
  RABBITMQ_DEFAULT_USER: guest    # Username
  RABBITMQ_DEFAULT_PASS: guest    # Password
```

### For Backend (.env)
```bash
DATABASE_URL=postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline
REDIS_URL=redis://localhost:6381/0
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
```

---

## Volumes & Persistence

### Docker Volumes
```yaml
volumes:
  cirkelline_postgres_data:    # PostgreSQL data
  cirkelline_redis_data:       # Redis data
  cirkelline_rabbitmq_data:    # RabbitMQ data
```

### Backup & Restore Data

```bash
# Backup PostgreSQL
docker exec cirkelline-postgres pg_dump -U cirkelline cirkelline \
  > cirkelline_backup.sql

# Restore PostgreSQL
docker exec -i cirkelline-postgres psql -U cirkelline cirkelline \
  < cirkelline_backup.sql

# Backup Redis
docker exec cirkelline-redis redis-cli --rdb /tmp/dump.rdb
docker cp cirkelline-redis:/tmp/dump.rdb ./redis_backup.rdb

# Clear databases completely
docker-compose down -v  # ⚠️ DELETES ALL DATA
docker-compose up -d    # Fresh start
```

---

## Production Docker Configuration (AWS)

### AWS ECR Image Building

```bash
# Build for production
docker build --platform linux/amd64 \
  -t 710504360116.dkr.ecr.eu-north-1.amazonaws.com/cirkelline-system-backend:v1.3.5 \
  -f Dockerfile .

# Login to ECR
aws ecr get-login-password --region eu-north-1 | \
  docker login --username AWS --password-stdin \
  710504360116.dkr.ecr.eu-north-1.amazonaws.com

# Push to ECR
docker push 710504360116.dkr.ecr.eu-north-1.amazonaws.com/cirkelline-system-backend:v1.3.5
```

### AWS RDS PostgreSQL
Production uses AWS RDS instead of Docker PostgreSQL:

```python
# Production connection
DATABASE_URL = "postgresql+psycopg://cirkelline:PASSWORD@cirkelline-system-db.crm4mi2uozbi.eu-north-1.rds.amazonaws.com:5432/cirkelline"
```

---

## Troubleshooting Docker Issues

### Port Already in Use

```bash
# Find process using port
lsof -i :5532    # PostgreSQL
lsof -i :6381    # Redis
lsof -i :5672    # RabbitMQ

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
# "5532:5432" → "5533:5432"
```

### Container Won't Start

```bash
# Check logs
docker-compose logs cirkelline-postgres
# or
docker logs cirkelline-postgres

# Common issues:
# - Port already in use
# - Volume permission issues
# - Image pull failed

# Solution: Clean and restart
docker-compose down -v
docker-compose pull
docker-compose up -d
```

### Database Connection Issues

```bash
# Test connection from host
psql -h localhost -p 5532 -U cirkelline -d cirkelline -c "SELECT 1;"

# From container
docker exec -it cirkelline-postgres psql -U cirkelline -d cirkelline -c "SELECT 1;"

# Check environment
docker-compose config | grep -A 10 cirkelline-postgres
```

### Volume Issues

```bash
# List volumes
docker volume ls | grep cirkelline

# Inspect volume
docker volume inspect cirkelline_postgres_data

# Clean unused volumes
docker volume prune

# Force remove volume
docker volume rm cirkelline_postgres_data
```

---

## Health Checks

### All Services Healthy

```bash
# Check all services
docker-compose ps

# Status should be "Up (healthy)" or similar

# Individual checks
docker exec -it cirkelline-postgres pg_isready -U cirkelline
docker exec -it cirkelline-redis redis-cli ping
docker exec -it cirkelline-rabbitmq rabbitmqctl status
```

---

## CHANGELOG

| Date | Time | Description | Author |
|------|------|-------------|--------|
| 2026-01-01 | 23:50 | Initial DOCKER_CONFIGURATION.md created with MEDIUM detail | Kv1nt |

---

**Last Updated:** 2026-01-01
**Status:** MEDIUM Detail Level Complete
**Document Type:** INTRO Documentation
