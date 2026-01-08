"""
Cirkelline Knowledge Base Tools
================================
Tools for saving and searching user's private knowledge base.
"""

import os
from typing import Optional
from agno.tools import Toolkit
from agno.knowledge.knowledge import Knowledge
from agno.db.postgres import PostgresDb
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from cirkelline.config import logger, ADMIN_USER_IDS
from cirkelline.helpers.metadata import create_private_document_metadata


class PrivateKnowledgeTools(Toolkit):
    """Tools for saving files to private knowledge base (Phase 1)"""

    def __init__(self, knowledge_base: Knowledge):
        super().__init__(
            name="private_knowledge_tools",
            instructions="""
            Use this tool to save files to the user's private knowledge base.
            When a user uploads a document and asks to save it, use save_to_my_knowledge.
            The saved documents become searchable for that user only.
            """,
            add_instructions=True
        )
        self.knowledge = knowledge_base
        self.register(self.save_to_my_knowledge)

    def save_to_my_knowledge(
        self,
        file_path: str,
        user_id: str,
        user_type: str,
        description: Optional[str] = None
    ) -> str:
        """
        Save a file to user's private knowledge base.

        Args:
            file_path: Path to the file
            user_id: User's ID (from session)
            user_type: "Admin" or "Regular"
            description: Optional file description

        Returns:
            Confirmation message
        """
        try:
            filename = os.path.basename(file_path)

            # Create private metadata
            metadata = create_private_document_metadata(
                user_id=user_id,
                user_type=user_type
            )

            # Save to knowledge base synchronously
            self.knowledge.add_content(
                name=filename,
                path=file_path,
                metadata=metadata,
                description=description
            )

            logger.info(f"✅ Saved {filename} to private knowledge for user {user_id}")

            return f"✅ Saved '{filename}' to your private knowledge base! You can search for it anytime."

        except Exception as e:
            logger.error(f"❌ Error saving to knowledge: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"❌ Error saving file: {str(e)}"


class FilteredKnowledgeSearchTool(Toolkit):
    """
    Custom tool that searches knowledge base with user permission filtering.
    Receives session_state automatically from Agno, which contains user context.

    This is the ONLY way to pass user context to knowledge search in Agno:
    - Custom retrievers don't work (no agent/kwargs passed)
    - knowledge_filters don't work (no $or operator support)
    - This tool receives session_state automatically!
    """

    def __init__(self, knowledge_base: Knowledge, database: PostgresDb, admin_ids: set):
        super().__init__(
            name="filtered_knowledge_search",
            instructions="""
            Use this tool to search the user's private document library.
            This is the primary way to find information in documents the user has uploaded.
            Use search_my_documents when the user asks about their files or needs information from saved documents.
            Results are automatically filtered by user permissions.
            """,
            add_instructions=True
        )
        self.knowledge = knowledge_base
        self.db = database
        self.admin_ids = admin_ids
        self.register(self.search_my_documents)

    def search_my_documents(self, session_state: dict, query: str, num_documents: int = 5) -> str:
        """
        Search the knowledge base for documents you have access to.

        This tool searches through documents and only returns ones you're allowed to see
        based on your permissions.

        Args:
            query: What to search for in the documents
            num_documents: Maximum number of documents to return (default: 5)

        Returns:
            Formatted string with accessible document contents
        """

        # Step 1: Get user context from session_state (passed by endpoint)
        user_id = session_state.get('current_user_id')
        user_type = session_state.get('current_user_type', 'Regular')

        if not user_id:
            logger.error("❌ No user_id in session_state!")
            return "Error: User context not available. Please sign in to search documents."

        is_admin = user_id in self.admin_ids or user_type.lower() == 'admin'

        logger.info(f"🔍 Searching knowledge for user_id={user_id[:20]}..., user_type={user_type}, is_admin={is_admin}, query={query[:50]}...")

        # Step 2: Detect if user wants to LIST ALL documents (not search)
        list_keywords = ['list', 'all', 'show', 'my documents', 'what documents', 'files i have', 'available']
        # ALSO treat generic "documents" query as LIST ALL (not content search)
        query_lower = query.lower().strip()
        is_listing = any(keyword in query_lower for keyword in list_keywords) or query_lower in ['documents', 'files', 'my files', 'uploads']

        # Step 3: Get document names
        if is_listing:
            # LIST ALL mode: Query database directly for ALL user's documents
            logger.info("📋 LIST ALL mode detected - querying database for all documents")

            db_url = self.db.db_url if hasattr(self.db, 'db_url') else os.getenv("DATABASE_URL")
            engine = create_engine(db_url)

            try:
                with Session(engine) as session:
                    if is_admin:
                        # Admins see: their own documents + admin-shared documents
                        result = session.execute(
                            text("""
                                SELECT name
                                FROM ai.agno_knowledge
                                WHERE metadata->>'user_id' = :user_id
                                   OR metadata->>'access_level' = 'admin-shared'
                                ORDER BY created_at DESC
                                LIMIT 20
                            """),
                            {"user_id": user_id}
                        )
                    else:
                        # Regular users see only their own documents
                        result = session.execute(
                            text("""
                                SELECT name
                                FROM ai.agno_knowledge
                                WHERE metadata->>'user_id' = :user_id
                                ORDER BY created_at DESC
                                LIMIT 20
                            """),
                            {"user_id": user_id}
                        )

                    rows = result.fetchall()
                    doc_names = [row[0] for row in rows]
                    logger.info(f"📋 Found {len(doc_names)} documents in database")
            except Exception as e:
                logger.error(f"❌ Database query error: {e}")
                return f"Error accessing documents: {str(e)}"

            if not doc_names:
                logger.info("No documents found in database")
                return "You don't have any documents yet. Upload some files to get started!"

        else:
            # SEARCH mode: Use vector search
            logger.info("🔎 SEARCH mode - using vector similarity search")
            try:
                search_results = self.knowledge.search(query, max_results=20)
            except Exception as e:
                logger.error(f"❌ Vector search error: {e}")
                return f"Error searching documents: {str(e)}"

            if not search_results:
                logger.info("No documents found matching query")
                return "No documents found matching your query."

            # Get document names from search results
            doc_names = list(set([result.name for result in search_results if hasattr(result, 'name')]))

            if not doc_names:
                logger.info("No document names in search results")
                return "No documents found."

        # Step 4: Query database for REAL metadata (vector search doesn't return it properly)
        db_url = self.db.db_url if hasattr(self.db, 'db_url') else os.getenv("DATABASE_URL")
        engine = create_engine(db_url)

        metadata_map = {}
        # Map doc names to their search results for content (only in SEARCH mode)
        content_map = {}
        if not is_listing and 'search_results' in locals():
            content_map = {result.name: result.content for result in search_results if hasattr(result, 'content')}

        try:
            with Session(engine) as session:
                result = session.execute(
                    text("""
                        SELECT name, metadata
                        FROM ai.agno_knowledge
                        WHERE name = ANY(:doc_names)
                    """),
                    {"doc_names": doc_names}
                )

                rows = result.fetchall()

                for row in rows:
                    doc_name = row[0]
                    doc_metadata = row[1] if row[1] else {}

                    # Parse JSON if it's a string
                    if isinstance(doc_metadata, str):
                        import json as json_lib
                        doc_metadata = json_lib.loads(doc_metadata)

                    metadata_map[doc_name] = doc_metadata
        except Exception as e:
            logger.error(f"❌ Database query error: {e}")
            return f"Error accessing document metadata: {str(e)}"

        logger.info(f"✅ Loaded metadata for {len(metadata_map)} documents from database")

        # Step 5: Filter by permissions using real metadata
        accessible_docs = []

        for doc_name in doc_names:
            doc_metadata = metadata_map.get(doc_name, {})
            doc_owner = doc_metadata.get('user_id')
            doc_access = doc_metadata.get('access_level', 'private')
            doc_content = content_map.get(doc_name, '')

            # Permission logic
            is_accessible = False
            access_reason = ""

            # User can see their own documents
            if doc_owner == user_id:
                is_accessible = True
                access_reason = "own"
                logger.info(f"  ✅ {doc_name} - User owns this document")

            # Admins can see admin-shared documents
            elif doc_access == 'admin-shared' and is_admin:
                is_accessible = True
                access_reason = "admin-shared"
                logger.info(f"  ✅ {doc_name} - Admin access to shared document")

            # Everyone can see public documents
            elif doc_access == 'public':
                is_accessible = True
                access_reason = "public"
                logger.info(f"  ✅ {doc_name} - Public document")

            else:
                logger.info(f"  ❌ {doc_name} - Access denied")

            if is_accessible:
                # Truncate content to 500 chars per doc
                truncated_content = doc_content[:500]
                if len(doc_content) > 500:
                    truncated_content += "... [truncated]"

                accessible_docs.append({
                    'name': doc_name,
                    'content': truncated_content,
                    'reason': access_reason
                })

            # Stop after we have enough documents
            if len(accessible_docs) >= num_documents:
                break

        # Step 6: Format results
        if not accessible_docs:
            logger.info("No accessible documents after filtering")
            return "No documents found that you have access to."

        formatted_docs = [
            f"--- Document: {doc['name']} ---\n{doc['content']}"
            for doc in accessible_docs
        ]

        result = "\n\n".join(formatted_docs)
        logger.info(f"📊 Returned {len(accessible_docs)} documents, {len(result)} chars total")

        return result


logger.info("✅ Knowledge tools module loaded")
