"""
Knowledge Base & Document Endpoints
====================================
Handles document upload, listing, status checking, and deletion.
"""

import os
import json
import uuid
import shutil
from fastapi import APIRouter, Request, HTTPException, File, UploadFile, Form
from sqlalchemy import text

from cirkelline.config import logger, ADMIN_USER_IDS
from cirkelline.knowledge_base import knowledge
from cirkelline.helpers.metadata import create_document_metadata, create_private_document_metadata
from cirkelline.middleware.middleware import log_activity
from cirkelline.shared import decode_jwt_token, get_db_session

# Create router
router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# DOCUMENT UPLOAD ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.post("/api/knowledge/upload")
async def upload_to_knowledge(
    file: UploadFile = File(...),
    is_shared: str = Form("false"),
    request: Request = None
):
    """
    Upload file to user's knowledge base.
    Supports both private and admin-shared documents.
    Automatically tags with user_id from JWT.
    """
    try:
        # Decode JWT to get user info
        payload = decode_jwt_token(request)
        user_id = payload.get("user_id")
        user_type = payload.get("user_type", "Regular")
        user_name = payload.get("user_name", "User")
        is_admin = user_id in ADMIN_USER_IDS or user_type.lower() == 'admin'

        # Parse is_shared flag
        is_shared_bool = is_shared.lower() == "true"

        # Only admins can create admin-shared documents
        if is_shared_bool and not is_admin:
            raise HTTPException(status_code=403, detail="Only admins can share documents with other admins")

        # Save uploaded file temporarily
        temp_dir = "/tmp/cirkelline_uploads"
        os.makedirs(temp_dir, exist_ok=True)

        # Generate unique filename to avoid conflicts
        file_id = str(uuid.uuid4())[:8]
        temp_path = os.path.join(temp_dir, f"{file_id}_{file.filename}")

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"📤 File saved temporarily: {temp_path}")

        # Create metadata based on sharing preference
        if is_shared_bool:
            # Admin-shared document
            metadata = create_document_metadata(
                user_id=user_id,
                user_type=user_type,
                access_level="admin-shared",
                shared_by_name=user_name
            )
            logger.info(f"📤 Creating ADMIN-SHARED document for all admins")
        else:
            # Private document
            metadata = create_private_document_metadata(
                user_id=user_id,
                user_type=user_type
            )
            logger.info(f"📤 Creating PRIVATE document")

        logger.info(f"📋 Metadata: {metadata}")

        # Upload to knowledge base
        # This adds to Contents DB AND creates vector embeddings automatically
        await knowledge.add_content_async(
            name=file.filename,
            path=temp_path,
            metadata=metadata,
            description=f"Uploaded by user via chat interface"
        )

        logger.info(f"✅ Uploaded to knowledge base: {file.filename} for user {user_id}")

        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass

        # Log successful upload
        await log_activity(
            request=request,
            user_id=user_id,
            action_type="document_upload",
            success=True,
            status_code=200,
            resource_type="document",
            details={"filename": file.filename, "is_shared": is_shared_bool},
            is_admin=is_admin
        )

        return {
            "success": True,
            "message": f"✅ {file.filename} uploaded to your private knowledge base!",
            "filename": file.filename,
            "user_id": user_id
        }

    except HTTPException as he:
        # Log failed upload
        await log_activity(
            request=request,
            user_id=user_id if 'user_id' in locals() else "unknown",
            action_type="document_upload",
            success=False,
            status_code=he.status_code,
            error_message=he.detail,
            error_type="HTTPException",
            resource_type="document"
        )
        raise
    except Exception as e:
        logger.error(f"❌ Upload error: {e}")
        import traceback
        logger.error(traceback.format_exc())

        # Log error
        await log_activity(
            request=request,
            user_id=user_id if 'user_id' in locals() else "unknown",
            action_type="document_upload",
            success=False,
            status_code=500,
            error_message=str(e),
            error_type=type(e).__name__,
            resource_type="document"
        )

        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# DOCUMENT LISTING ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/api/documents")
async def list_user_documents(request: Request):
    """
    Get all documents accessible to current user.
    For admins: Returns private documents + admin-shared documents
    For regular users: Returns only private documents
    """
    user_id = getattr(request.state, 'user_id', None)

    # v1.3.4: Require authentication - no anonymous access
    if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
        raise HTTPException(status_code=401, detail="Authentication required")

    # Get user_type from dependencies (set by JWT middleware)
    dependencies = getattr(request.state, 'dependencies', {})
    user_type = dependencies.get('user_type', 'Regular')

    is_admin = user_id in ADMIN_USER_IDS or user_type.lower() == 'admin'

    logger.info(f"📚 Listing documents for user: {user_id[:20]}... (user_type={user_type}, is_admin={is_admin})")

    try:
        with get_db_session() as session:
            if is_admin:
                # Admins see: their own documents + admin-shared documents
                result = session.execute(
                    text("""
                        SELECT id, name, description, type, size, metadata, created_at
                        FROM ai.agno_knowledge
                        WHERE metadata->>'user_id' = :user_id
                           OR metadata->>'access_level' = 'admin-shared'
                        ORDER BY created_at DESC
                    """),
                    {"user_id": user_id}
                )
            else:
                # Regular users see only their own documents
                result = session.execute(
                    text("""
                        SELECT id, name, description, type, size, metadata, created_at
                        FROM ai.agno_knowledge
                        WHERE metadata->>'user_id' = :user_id
                        ORDER BY created_at DESC
                    """),
                    {"user_id": user_id}
                )

            rows = result.fetchall()

            # Format results
            user_documents = []
            for row in rows:
                metadata = row[5] if row[5] else {}
                if isinstance(metadata, str):
                    metadata = json.loads(metadata)

                user_documents.append({
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "type": row[3],
                    "size": row[4] or 0,
                    "status": "completed",
                    "uploaded_at": metadata.get("uploaded_at"),
                    "created_at": row[6],  # Unix timestamp from database
                    "metadata": metadata
                })

            logger.info(f"✅ Found {len(user_documents)} documents for user (is_admin={is_admin})")

            return {
                "success": True,
                "count": len(user_documents),
                "documents": user_documents
            }

    except Exception as e:
        logger.error(f"❌ Error listing documents: {e}")
        import traceback
        logger.error(traceback.format_exc())

        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/knowledge/documents")
async def list_knowledge_documents(request: Request):
    """
    Alias for /api/documents endpoint.
    Frontend calls this for consistency with /api/knowledge/upload.
    """
    return await list_user_documents(request)


# ═══════════════════════════════════════════════════════════════
# DOCUMENT STATUS ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/documents/{document_id}/status")
async def get_document_status(
    document_id: str,
    request: Request
):
    """
    Get processing status of a specific document.
    Used for polling during upload.
    """
    user_id = getattr(request.state, 'user_id', None)

    # v1.3.4: Require authentication - no anonymous access
    if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
        raise HTTPException(status_code=401, detail="Authentication required")

    logger.info(f"🔍 Checking status for document: {document_id}")

    try:
        with get_db_session() as session:
            result = session.execute(
                text("""
                    SELECT id, name, metadata
                    FROM ai.agno_knowledge
                    WHERE id = :document_id AND metadata->>'user_id' = :user_id
                """),
                {"document_id": document_id, "user_id": user_id}
            )

            row = result.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Document not found")

            # Parse metadata
            metadata = row[2] if row[2] else {}
            if isinstance(metadata, str):
                metadata = json.loads(metadata)

            # Log successful status check
            await log_activity(
                request=request,
                user_id=user_id,
                action_type="document_status",
                success=True,
                status_code=200,
                target_resource_id=document_id,
                resource_type="document"
            )

            return {
                "id": row[0],
                "name": row[1],
                "status": "completed",  # Agno doesn't track status, assume completed if exists
                "metadata": metadata
            }

    except HTTPException as he:
        # Log failed status check
        await log_activity(
            request=request,
            user_id=user_id if 'user_id' in locals() else "unknown",
            action_type="document_status",
            success=False,
            status_code=he.status_code,
            error_message=he.detail,
            error_type="HTTPException",
            target_resource_id=document_id,
            resource_type="document"
        )
        raise
    except Exception as e:
        logger.error(f"❌ Error checking status: {e}")
        import traceback
        logger.error(traceback.format_exc())

        # Log error
        await log_activity(
            request=request,
            user_id=user_id if 'user_id' in locals() else "unknown",
            action_type="document_status",
            success=False,
            status_code=500,
            error_message=str(e),
            error_type=type(e).__name__,
            target_resource_id=document_id,
            resource_type="document"
        )

        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# DOCUMENT DELETE ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.delete("/api/documents/{document_id}")
async def delete_document(
    document_id: str,
    request: Request
):
    """
    Delete a document from knowledge base.
    Only owner can delete their documents.
    """
    user_id = getattr(request.state, 'user_id', None)

    # v1.3.4: Require authentication - no anonymous access
    if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
        raise HTTPException(status_code=401, detail="Authentication required")

    logger.info(f"🗑️  Delete request for document: {document_id}")
    logger.info(f"👤 User: {user_id[:20]}...")

    try:
        # Query database directly to verify document exists and user owns it
        with get_db_session() as session:
            result = session.execute(
                text("""
                    SELECT id, name, metadata
                    FROM ai.agno_knowledge
                    WHERE id = :document_id AND metadata->>'user_id' = :user_id
                """),
                {"document_id": document_id, "user_id": user_id}
            )

            row = result.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Document not found")

            doc_name = row[1]

        # Delete from knowledge base (synchronous method, not async)
        knowledge.remove_content_by_id(document_id)

        logger.info(f"✅ Document deleted: {doc_name}")

        # Log successful delete
        await log_activity(
            request=request,
            user_id=user_id,
            action_type="document_delete",
            success=True,
            status_code=200,
            target_resource_id=document_id,
            resource_type="document",
            details={"document_name": doc_name}
        )

        return {
            "success": True,
            "message": f"Document '{doc_name}' deleted successfully"
        }

    except HTTPException as he:
        # Log failed delete
        await log_activity(
            request=request,
            user_id=user_id if 'user_id' in locals() else "unknown",
            action_type="document_delete",
            success=False,
            status_code=he.status_code,
            error_message=he.detail,
            error_type="HTTPException",
            target_resource_id=document_id,
            resource_type="document"
        )
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting document: {e}")
        import traceback
        logger.error(traceback.format_exc())

        # Log error
        await log_activity(
            request=request,
            user_id=user_id if 'user_id' in locals() else "unknown",
            action_type="document_delete",
            success=False,
            status_code=500,
            error_message=str(e),
            error_type=type(e).__name__,
            target_resource_id=document_id,
            resource_type="document"
        )

        raise HTTPException(status_code=500, detail=str(e))


logger.info("✅ Knowledge base endpoints loaded")
