# Tests Directory

This directory contains all test files for the Cirkelline backend.

## Test Files

### Knowledge Base Tests
- **test_knowledge_retriever.py** - Unit tests for custom knowledge retriever (v1.1.25+)
- **test_retrieval.py** - Integration tests for document retrieval
- **test_upload.py** - Tests for document upload functionality

### Legacy Tests
- **test_cirkelline.py** - Main Cirkelline agent tests
- **test_hybrid_search.py** - Hybrid vector search tests

## Test Data

### test_documents/
Contains sample documents for testing document permissions:
- **ivo_private.txt** - Ivo's private test document
- **rasmus_private.txt** - Rasmus's private test document
- **regular_user_private.txt** - Regular user's private test document

### test_data/
Legacy test data directory.

## Running Tests

### Run All Tests
```bash
cd /home/eenvy/Desktop/cirkelline
source .venv/bin/activate
python -m pytest tests/
```

### Run Specific Test
```bash
python -m pytest tests/test_knowledge_retriever.py -v
```

### Run Knowledge Base Tests
```bash
# Test retriever
python tests/test_knowledge_retriever.py

# Test document retrieval
python tests/test_retrieval.py

# Test document upload
python tests/test_upload.py
```

## Test Coverage

- ✅ Custom knowledge retriever (user permissions)
- ✅ Document upload (private & admin-shared)
- ✅ Document retrieval (filtering by user)
- ✅ Vector search
- ✅ Hybrid search (semantic + BM25)
- ✅ Cirkelline agent functionality

## Notes

- Tests use local PostgreSQL database (localhost:5532)
- Database must be running before running tests
- Tests create and clean up their own test data
- Test documents are uploaded to `ai.agno_knowledge` table
