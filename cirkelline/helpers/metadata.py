"""
Cirkelline Document Metadata Helpers
=====================================
Functions for creating and filtering document metadata.
"""

from datetime import datetime
from typing import Optional, Dict
from cirkelline.config import logger

def create_document_metadata(
    user_id: str,
    user_type: str,
    access_level: str = "private",
    shared_by_name: Optional[str] = None,
    additional_meta: Optional[Dict] = None
) -> Dict:
    """
    Create metadata for documents uploaded via frontend chat.

    Supports both private documents (Phase 1) and admin-shared documents (Phase 2).

    Args:
        user_id: ID of user uploading document
        user_type: "Admin" or "Regular"
        access_level: "private" or "admin-shared" (default: "private")
        shared_by_name: Name of admin sharing the document (required for admin-shared)
        additional_meta: Optional additional metadata

    Returns:
        Metadata dict with proper access_level and sharing information
    """
    metadata = {
        "user_id": user_id,
        "user_type": user_type,
        "access_level": access_level,
        "uploaded_by": user_id,
        "uploaded_at": datetime.now().isoformat(),
        "uploaded_via": "frontend_chat",
    }

    # Add shared_by_name for admin-shared documents
    if access_level == "admin-shared" and shared_by_name:
        metadata["shared_by_name"] = shared_by_name

    if additional_meta:
        metadata.update(additional_meta)

    return metadata

# Backward compatibility alias for Phase 1 code
def create_private_document_metadata(
    user_id: str,
    user_type: str,
    additional_meta: Optional[Dict] = None
) -> Dict:
    """
    Legacy function for backward compatibility.
    Creates private documents only.
    """
    return create_document_metadata(
        user_id=user_id,
        user_type=user_type,
        access_level="private",
        additional_meta=additional_meta
    )

def get_private_knowledge_filters(user_id: str) -> Dict:
    """
    Build knowledge filters for private documents only.
    For Phase 1, users only see their own private documents.

    Args:
        user_id: Current user's ID

    Returns:
        Filter dict that returns only user's private documents
    """
    return {"user_id": user_id}

logger.info("✅ Document metadata helpers loaded")
