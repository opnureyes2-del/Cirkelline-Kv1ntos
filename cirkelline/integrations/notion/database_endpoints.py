"""
Notion Database Management Endpoints
====================================
Dynamic registry-based database endpoints using notion_user_databases table.
These endpoints work with ANY database name by querying the registry by TYPE.
"""

import os
import json
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from notion_client import Client

from cirkelline.config import logger
from cirkelline.integrations.notion.notion_helpers import (
    get_user_notion_credentials,
    get_user_notion_credentials_sync,
    discover_and_store_user_databases_sync
)

# Create router
router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# NOTION DATABASE REGISTRY ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/api/notion/databases")
async def get_user_notion_databases(request: Request):
    """
    Get list of user's discovered Notion databases from registry

    Returns all databases that were discovered and stored during OAuth connection
    or manual sync. Frontend uses this to display available databases dynamically.
    """
    try:
        user_id = getattr(request.state, 'user_id', None)

        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")

        engine = create_engine(os.getenv("DATABASE_URL"))

        with Session(engine) as session:
            results = session.execute(
                text("""
                    SELECT
                        database_id,
                        database_title,
                        database_type,
                        user_label,
                        is_hidden,
                        last_synced,
                        created_at
                    FROM notion_user_databases
                    WHERE user_id = :user_id
                    ORDER BY database_type, database_title
                """),
                {"user_id": user_id}
            ).fetchall()

            databases = []
            for row in results:
                databases.append({
                    "database_id": row[0],
                    "database_title": row[1],
                    "database_type": row[2],
                    "user_label": row[3] or row[1],  # Use user_label if set, otherwise title
                    "is_hidden": row[4],
                    "last_synced": row[5].isoformat() if row[5] else None,
                    "created_at": row[6].isoformat() if row[6] else None
                })

            return {
                "success": True,
                "databases": databases,
                "total": len(databases)
            }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Error fetching user databases: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to fetch databases")

logger.info("✅ Notion databases list endpoint configured")

@router.get("/api/notion/databases/{database_type}/schema")
async def get_database_schema_by_type(request: Request, database_type: str):
    """
    Get complete schema for a database by type (tasks/projects/companies/documentation)

    Returns full property definitions from notion_user_databases registry.
    Frontend uses this to dynamically generate table columns for ALL properties.

    Response includes:
    - database_id: Notion database ID
    - database_title: User's custom database name
    - properties: Complete property schema (all 25+ properties if they exist)
      Each property includes: name, type, and type-specific config (e.g., select options)
    """
    try:
        user_id = getattr(request.state, 'user_id', None)

        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")

        engine = create_engine(os.getenv("DATABASE_URL"))

        with Session(engine) as session:
            result = session.execute(
                text("""
                    SELECT
                        database_id,
                        database_title,
                        schema,
                        property_order,
                        user_property_order
                    FROM notion_user_databases
                    WHERE user_id = :user_id
                      AND database_type = :database_type
                      AND is_hidden = FALSE
                    ORDER BY last_synced DESC
                    LIMIT 1
                """),
                {"user_id": user_id, "database_type": database_type}
            ).fetchone()

            if not result:
                raise HTTPException(
                    status_code=404,
                    detail=f"No {database_type} database found for this user"
                )

            database_id, database_title, schema_json, property_order, user_property_order = result

            # schema_json is already a dict from JSONB (don't json.loads it!)
            schema = schema_json

            # Prioritize user_property_order (custom order) over property_order (Notion order)
            final_order = user_property_order if user_property_order else (
                property_order if property_order else list(schema.get("properties", {}).keys())
            )

            return {
                "success": True,
                "database_id": database_id,
                "database_title": database_title,
                "properties": schema.get("properties", {}),
                "property_order": final_order,
                "total_properties": len(schema.get("properties", {}))
            }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Error fetching database schema: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to fetch database schema")

logger.info("✅ Notion database schema endpoint configured")

@router.get("/api/notion/databases/{database_type}/items")
async def get_notion_database_items(request: Request, database_type: str):
    """
    Get all items from a user's Notion database by TYPE (NOT by name search!)

    This is the CORRECT way - uses the database registry:
    1. Look up database_id from notion_user_databases table by type
    2. Query that specific database by ID
    3. Return ALL items regardless of what the user named their database

    Works with ANY database name:
    - "Domains", "Companies", "My Companies" → all work for type='companies'
    - "Tasks", "To-Do", "My Tasks" → all work for type='tasks'
    """
    try:
        user_id = getattr(request.state, 'user_id', None)
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")

        # Get user's Notion credentials
        notion_creds = await get_user_notion_credentials(user_id)
        if not notion_creds:
            raise HTTPException(
                status_code=403,
                detail="Notion workspace not connected. Please connect your Notion account first."
            )

        # Initialize Notion client
        notion = Client(auth=notion_creds['access_token'])

        # Look up database_id from registry by TYPE
        engine = create_engine(os.getenv("DATABASE_URL"))
        with Session(engine) as session:
            result = session.execute(
                text("""
                    SELECT database_id, database_title, schema
                    FROM notion_user_databases
                    WHERE user_id = :user_id
                      AND database_type = :database_type
                      AND is_hidden = FALSE
                    ORDER BY last_synced DESC
                    LIMIT 1
                """),
                {"user_id": user_id, "database_type": database_type}
            ).fetchone()

            if not result:
                # No database of this type found
                return {f"{database_type}": []}

            database_id, database_title, schema_json = result
            schema = schema_json  # Already a dict from JSONB

        logger.info(f"User {user_id[:20]}... fetching items from {database_type} database: {database_title}")

        # Query the database by ID
        db_results = notion.data_sources.query(data_source_id=database_id)

        items = []
        for page in db_results.get("results", []):
            props = page.get("properties", {})

            # Create item with basic info
            item = {
                "id": page["id"],
                "url": page.get("url", ""),
                "created_time": page.get("created_time", ""),
                "last_edited_time": page.get("last_edited_time", ""),
            }

            # Extract ALL properties from the page
            for prop_name, prop_value in props.items():
                prop_type = prop_value.get("type")
                key = prop_name.lower().replace(" ", "_")

                if prop_type == "title":
                    titles = prop_value.get("title", [])
                    item[key] = titles[0].get("text", {}).get("content", "") if titles else ""
                    # Also set common aliases
                    if not item.get("title"):
                        item["title"] = item[key]
                    if not item.get("name"):
                        item["name"] = item[key]

                elif prop_type == "rich_text":
                    texts = prop_value.get("rich_text", [])
                    item[key] = texts[0].get("text", {}).get("content", "") if texts else ""

                elif prop_type == "number":
                    item[key] = prop_value.get("number")

                elif prop_type == "select":
                    select = prop_value.get("select")
                    item[key] = select.get("name") if select else None

                elif prop_type == "multi_select":
                    multi = prop_value.get("multi_select", [])
                    item[key] = [opt.get("name") for opt in multi]

                elif prop_type == "status":
                    status = prop_value.get("status")
                    item[key] = status.get("name") if status else None

                elif prop_type == "date":
                    date_obj = prop_value.get("date")
                    if date_obj:
                        item[key] = date_obj.get("start")
                    else:
                        item[key] = None

                elif prop_type == "checkbox":
                    item[key] = prop_value.get("checkbox", False)

                elif prop_type == "url":
                    item[key] = prop_value.get("url")

                elif prop_type == "email":
                    item[key] = prop_value.get("email")

                elif prop_type == "phone_number":
                    item[key] = prop_value.get("phone_number")

                elif prop_type == "people":
                    people = prop_value.get("people", [])
                    item[key] = len(people)  # Just count for now

                elif prop_type == "files":
                    files = prop_value.get("files", [])
                    item[key] = len(files)  # Just count for now

                elif prop_type == "relation":
                    relations = prop_value.get("relation", [])
                    item[key] = len(relations)  # Just count for now

                else:
                    # Unknown type, store as-is
                    item[key] = prop_value

            items.append(item)

        return {f"{database_type}": items}

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Error fetching {database_type} items: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch {database_type} items")

logger.info("✅ Notion dynamic database items endpoint configured")

@router.put("/api/notion/databases/{database_type}/column-order")
async def save_column_order(database_type: str, request: Request):
    """
    Save user's custom column order for a Notion database table view

    Stores column order in user_property_order column, which overrides
    the default property_order from Notion.
    """
    try:
        user_id = getattr(request.state, 'user_id', None)

        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")

        # Parse request body
        body = await request.json()
        column_order = body.get('column_order')

        if not column_order or not isinstance(column_order, list):
            raise HTTPException(status_code=400, detail="column_order must be a list of property names")

        engine = create_engine(os.getenv("DATABASE_URL"))

        with Session(engine) as session:
            # Get the database record
            result = session.execute(
                text("""
                    SELECT database_id FROM notion_user_databases
                    WHERE user_id = :user_id AND database_type = :database_type
                    LIMIT 1
                """),
                {"user_id": user_id, "database_type": database_type}
            ).fetchone()

            if not result:
                raise HTTPException(
                    status_code=404,
                    detail=f"No database found for type '{database_type}'"
                )

            database_id = result[0]

            # Update user_property_order
            session.execute(
                text("""
                    UPDATE notion_user_databases
                    SET user_property_order = :column_order,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = :user_id AND database_id = :database_id
                """),
                {
                    "column_order": json.dumps(column_order),
                    "user_id": user_id,
                    "database_id": database_id
                }
            )
            session.commit()

            logger.info(f"✅ Saved column order for user {user_id[:8]}, db_type={database_type}: {column_order}")

        return {
            "success": True,
            "message": "Column order saved successfully",
            "column_order": column_order
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving column order: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to save column order")

logger.info("✅ Notion column order endpoint configured")

@router.post("/api/notion/databases/sync")
async def sync_notion_databases(request: Request):
    """
    Manually trigger database discovery and sync for user

    Re-discovers all databases in user's Notion workspace and updates registry.
    Useful when user adds new databases or renames existing ones.
    """
    try:
        user_id = getattr(request.state, 'user_id', None)

        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")

        # Get user's Notion credentials
        creds = get_user_notion_credentials_sync(user_id)
        if not creds:
            raise HTTPException(status_code=400, detail="Notion workspace not connected")

        # Run discovery
        logger.info(f"🔄 Manual database sync triggered by user {user_id[:8]}...")

        discovery_result = discover_and_store_user_databases_sync(user_id, creds['access_token'])

        if discovery_result.get("success"):
            return {
                "success": True,
                "message": "Databases synced successfully",
                "discovered": discovery_result.get("discovered", 0),
                "stored": discovery_result.get("stored", 0)
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Database sync failed: {discovery_result.get('error', 'Unknown error')}"
            )

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Error syncing databases: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to sync databases")

logger.info("✅ Notion database sync endpoint configured")


logger.info("✅ Notion database management endpoints loaded")
