"""
Cirkelline Knowledge Base Module
=================================
Knowledge base initialization with vector database.
"""

from agno.knowledge.knowledge import Knowledge
from cirkelline.database import db, vector_db
from cirkelline.config import logger

# Knowledge base
# ✅ v1.2.33: Added max_results (AGNO best practice for default retrieval limit)
knowledge = Knowledge(
    name="Cirkelline Knowledge Base",
    description="Information about the Cirkelline project",
    contents_db=db,
    vector_db=vector_db,
    max_results=5,  # ✅ v1.2.33: Default limit (custom tool can override to 20)
)

# Async knowledge loading function (for future use)
async def load_knowledge_async():
    """
    Load knowledge base asynchronously at startup.
    Uncomment the code below when you have documents to load.
    """
    try:
        logger.info("Loading knowledge base asynchronously...")

        # Example: Add documentation
        # await knowledge.add_content_async(
        #     name="Cirkelline Documentation",
        #     path="docs/",
        #     metadata={"type": "documentation", "version": "1.0"}
        # )

        # Example: Add from URL
        # await knowledge.add_content_async(
        #     name="API Reference",
        #     url="https://example.com/api-docs.pdf",
        #     metadata={"type": "reference"}
        # )

        # Load into vector database
        # await knowledge.aload(recreate=False)

        logger.info("Knowledge base loaded successfully")
    except Exception as e:
        logger.error(f"Error loading knowledge: {e}")

# Uncomment to load knowledge at startup:
# import asyncio
# asyncio.run(load_knowledge_async())

logger.info("✅ Knowledge base module loaded")
