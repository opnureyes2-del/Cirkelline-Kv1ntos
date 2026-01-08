"""
Intelligent Memory Search Tool
==============================
Uses database-level topic filtering to retrieve ONLY relevant memories.
Does NOT load all memories - filters at SQL level.

v1.2.34: Created to fix token bloat from loading all memories.
v1.2.34.4: Fixed to use Gemini model for agentic search.
v1.2.34.5: FIXED - Now uses db.get_user_memories(topics=[...]) for SQL-level filtering.
           No longer loads all memories. Agent extracts topic keywords from conversation.
"""

from typing import List
from agno.tools import Toolkit
from cirkelline.config import logger


class IntelligentMemoryTool(Toolkit):
    """Tool for intelligent memory search using database-level topic filtering."""

    def __init__(self, database):
        super().__init__(name="memory_tools")
        self.database = database
        self.register(self.search_memories)
        self.register(self.get_recent_memories)

    def search_memories(self, topics: List[str], user_id: str, limit: int = 10) -> str:
        """
        Search for memories by topic keywords using SQL-level filtering.
        Only memories matching the topics are returned - NOT all memories.

        Args:
            topics: Topic keywords to filter by (e.g., ["travel", "Japan"], ["AI", "agents"])
                   Extract these from the user's conversation/question.
            user_id: The user's ID
            limit: Maximum memories to return (default 10)

        Returns:
            Formatted string of matching memories
        """
        if not self.database:
            return "Memory system not available"

        if not topics:
            return "No topics provided. Extract relevant keywords from the conversation."

        try:
            # Direct database call with topic filtering
            # SQL generates: WHERE topics LIKE '%"travel"%' AND topics LIKE '%"Japan"%'
            memories = self.database.get_user_memories(
                user_id=user_id,
                topics=topics,  # SQL-level filtering - only matching memories returned
                limit=limit
            )

            if not memories:
                return f"No memories found matching topics: {', '.join(topics)}"

            result = []
            for mem in memories:
                mem_topics = ", ".join(mem.topics) if mem.topics else "general"
                result.append(f"- {mem.memory} (topics: {mem_topics})")

            logger.info(f"Memory search for topics {topics} returned {len(memories)} results")
            return "\n".join(result)

        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            return f"Memory search error: {e}"

    def get_recent_memories(self, user_id: str, limit: int = 5) -> str:
        """
        Get the most recent memories for a user (no topic filtering).

        Args:
            user_id: The user's ID
            limit: Number of recent memories (default 5)

        Returns:
            Formatted string of recent memories
        """
        if not self.database:
            return "Memory system not available"

        try:
            # Direct database call - get recent memories without topic filter
            memories = self.database.get_user_memories(
                user_id=user_id,
                limit=limit
            )

            if not memories:
                return "No memories found for this user."

            result = []
            for mem in memories:
                mem_topics = ", ".join(mem.topics) if mem.topics else "general"
                result.append(f"- {mem.memory} (topics: {mem_topics})")

            logger.info(f"Retrieved {len(memories)} recent memories for user")
            return "\n".join(result)

        except Exception as e:
            logger.error(f"Get recent memories failed: {e}")
            return f"Error: {e}"


logger.info("✅ Intelligent memory search tool loaded (v1.2.34.5 - topic filtering)")
