#!/usr/bin/env python3
"""
Load existing documents from Contents DB into Vector DB.
This creates the embeddings for semantic search.
"""

import sys
sys.path.insert(0, '/home/eenvy/Desktop/cirkelline')

import os
from dotenv import load_dotenv
load_dotenv()

from my_os import knowledge
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("=" * 80)
    print("LOADING DOCUMENTS INTO VECTOR DATABASE")
    print("=" * 80)

    try:
        # Load knowledge base into vector DB
        # This will:
        # 1. Read all documents from Contents DB (ai.agno_knowledge)
        # 2. Generate embeddings using GeminiEmbedder
        # 3. Store vectors in Vector DB (cirkelline_knowledge_vectors)

        logger.info("Starting knowledge.load()...")
        knowledge.load(recreate=False, upsert=True)

        print("\n" + "=" * 80)
        print("✅ VECTOR DATABASE LOADED SUCCESSFULLY!")
        print("=" * 80)
        print("\nDocuments are now searchable via semantic search.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
