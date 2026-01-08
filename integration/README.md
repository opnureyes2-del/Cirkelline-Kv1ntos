# ELLE Unified Integration System

This directory contains the unified integration system for ELLE.md, providing:

## Features

### 1. Event Bus (RabbitMQ)
- Publish/subscribe messaging
- Topic-based routing
- Persistent messages
- Full database logging

### 2. Cache Manager
- Multi-layer caching (Memory + Redis)
- Automatic cache invalidation
- 4-8x query speedup

### 3. Unified Query API
- Cross-database queries (INTRO + ELLE)
- Full-text search with relevance ranking
- REST API endpoints
- No sudo requirements (better than PostgreSQL FDW)

### 4. Master Orchestrator
- Central event coordinator
- Agent lifecycle management
- Failure recovery

### 5. Cross-DB Sync
- Bidirectional INTRO ↔ ELLE synchronization
- Content-based change detection
- Cache integration

### 6. File Watcher
- Real-time file change detection
- inotify-based monitoring
- Automatic sync triggers

## Usage

```python
from integration import UnifiedQueryAPI, EventBus

# Search knowledge bases
api = UnifiedQueryAPI()
await api.connect_databases()
results = await api.search_all("query", limit=10)

# Event bus
bus = EventBus()
bus.connect()
await bus.publish('event.type', {'data': 'value'})
```

See `examples.py` for complete examples.

## Configuration

Edit `config.py` to customize database connections and paths.

## Requirements

- Python 3.8+
- PostgreSQL (multiple databases)
- RabbitMQ
- Redis

## Documentation

Full documentation: `/home/rasmus/Desktop/ELLE.md/REPORTS/`
