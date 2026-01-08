# Scripts Directory

This directory contains utility scripts for database management, migrations, and setup.

## Current Scripts

### Vector Database Management
- **create_missing_vectors.py** - Creates vector embeddings for documents missing them
- **load_vectors.py** - Loads and validates vector embeddings
- **setup_test_documents.py** - Sets up test documents in knowledge base

### Knowledge Base Management
- **check_agno_table_name.py** - Verifies Agno table naming conventions
- **check_knowledge_db.py** - Checks knowledge base database structure
- **check_knowledge_methods.py** - Tests knowledge base methods
- **check_uploaded_files.py** - Validates uploaded files in database
- **fix_knowledge_properly.py** - Fixes knowledge base issues
- **initialize_knowledge_base.py** - Initializes the knowledge base
- **initialize_contents_db.py** - Initializes the contents database
- **create_contents_table_manual.py** - Manually creates contents table
- **reupload_with_contents_db.py** - Re-uploads documents with contents DB

### Memory Migration
- **migrate_memories.py** - Migrates memories between databases
- **migrate_memories.sql** - SQL script for memory migration
- **prepare_for_memory_migration.py** - Prepares data for memory migration

### Investigation & Debugging
- **investigate_rasmus.py** - Debugging script for Rasmus-specific issues

## Usage

### Vector Management
```bash
# Create missing vectors for documents
python scripts/create_missing_vectors.py

# Load and validate vectors
python scripts/load_vectors.py
```

### Test Setup
```bash
# Set up test documents
python scripts/setup_test_documents.py
```

### Memory Migration
```bash
# Migrate memories from old to new database
python scripts/migrate_memories.py
```

## Database Connection

Most scripts connect to:
- **Local DB:** `localhost:5532`
- **Database:** `cirkelline`
- **User:** `cirkelline`
- **Password:** Set in script or environment variable

## Notes

- Scripts assume PostgreSQL with pgvector extension
- Some scripts are for one-time use (migrations)
- Always backup database before running migration scripts
- Check script contents before running to verify connection details
