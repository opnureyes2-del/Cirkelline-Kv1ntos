#!/usr/bin/env python3
"""
Create vector embeddings for existing documents that are in Contents DB but not in Vector DB.
This is a one-time migration script.
"""

import sys
sys.path.insert(0, '/home/eenvy/Desktop/cirkelline')

import os
from dotenv import load_dotenv
load_dotenv()

from my_os import knowledge, vector_db
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    print("=" * 80)
    print("CREATING VECTOR EMBEDDINGS FOR EXISTING DOCUMENTS")
    print("=" * 80)

    try:
        # Get all content from Contents DB
        logger.info("Fetching all documents from Contents DB...")

        # Use contents_db to query all documents
        from sqlalchemy import text
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session

        db_url = os.getenv("DATABASE_URL", "postgresql+psycopg://cirkelline:cirkelline123@localhost:5532/cirkelline")
        engine = create_engine(db_url)

        with Session(engine) as session:
            result = session.execute(
                text("SELECT name FROM ai.agno_knowledge")
            )
            all_docs = result.fetchall()

        logger.info(f"Found {len(all_docs)} documents in Contents DB")

        if not all_docs:
            print("\n⚠️  No documents found in Contents DB")
            return

        # Get all content from Knowledge (returns list of Content objects)
        all_content, total = knowledge.get_content()
        logger.info(f"Retrieved {len(all_content)} Content objects from Knowledge")

        if not all_content:
            print("\n⚠️  No content objects found")
            return

        # Process each document
        created_count = 0
        for content_obj in all_content:
            doc_name = content_obj.name
            logger.info(f"\n📄 Processing: {doc_name}")

            try:
                # Create vector embeddings using vector_db directly
                await vector_db.async_create(documents=[content_obj])
                logger.info(f"   ✅ Created embeddings for: {doc_name}")
                created_count += 1

            except Exception as e:
                logger.error(f"   ❌ Error processing {doc_name}: {e}")
                import traceback
                traceback.print_exc()

        print("\n" + "=" * 80)
        print(f"✅ COMPLETED! Created embeddings for {created_count}/{len(all_docs)} documents")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
