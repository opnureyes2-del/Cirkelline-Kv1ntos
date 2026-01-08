"""
Notion Integration Helper Functions
====================================
Helper functions for Notion OAuth and database management.
"""

import os
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from notion_client import Client

from cirkelline.config import logger
from cirkelline.database import db
from utils.encryption import decrypt_token


async def get_user_notion_credentials(user_id: str):
    """
    Get user's Notion credentials from database and decrypt access token

    Returns tuple: (access_token, workspace_id, workspace_name) or None if not connected
    """
    try:
        # Get database connection
        db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
        engine = create_engine(db_url)

        with Session(engine) as session:
            result = session.execute(
                text("""
                    SELECT access_token, workspace_id, workspace_name
                    FROM notion_tokens
                    WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            )

            row = result.fetchone()

            if not row:
                return None

            # Decrypt access token
            decrypted_token = decrypt_token(row[0])

            return {
                'access_token': decrypted_token,
                'workspace_id': row[1],
                'workspace_name': row[2]
            }

    except Exception as e:
        logger.error(f"Error getting Notion credentials for user {user_id[:20]}...: {e}")
        return None

def get_user_notion_credentials_sync(user_id: str):
    """
    Synchronous version for tool calls.
    Get user's Notion credentials from database and decrypt access token

    Returns dict: {'access_token', 'workspace_id', 'workspace_name'} or None if not connected
    """
    try:
        # Get database connection
        db_url = db.db_url if hasattr(db, 'db_url') else os.getenv("DATABASE_URL")
        engine = create_engine(db_url)

        with Session(engine) as session:
            result = session.execute(
                text("""
                    SELECT access_token, workspace_id, workspace_name
                    FROM notion_tokens
                    WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            )

            row = result.fetchone()

            if not row:
                return None

            # Decrypt access token
            decrypted_token = decrypt_token(row[0])

            return {
                'access_token': decrypted_token,
                'workspace_id': row[1],
                'workspace_name': row[2]
            }

    except Exception as e:
        logger.error(f"Error getting Notion credentials for user {user_id[:20]}...: {e}")
        return None

def get_database_schema(notion_client, database_id: str) -> dict:
    """
    Retrieve full schema for a Notion database

    Returns:
        {
            "id": "database-uuid",
            "title": "Database Title",
            "properties": {
                "Name": {"id": "prop-id", "type": "title", "name": "Name"},
                "Status": {"id": "prop-id", "type": "status", "name": "Status", "options": [...]},
                ...
            }
        }
    """
    try:
        db = notion_client.data_sources.retrieve(data_source_id=database_id)

        schema = {
            "id": db["id"],
            "title": "",
            "properties": {}
        }

        # Extract database title
        title_list = db.get("title", [])
        if title_list and len(title_list) > 0:
            schema["title"] = title_list[0].get("text", {}).get("content", "")

        # Extract property definitions
        for prop_name, prop_config in db.get("properties", {}).items():
            prop_type = prop_config.get("type")
            property_schema = {
                "id": prop_config.get("id"),
                "type": prop_type,
                "name": prop_name
            }

            # Include type-specific configuration
            if prop_type in ["select", "multi_select"]:
                options = prop_config.get(prop_type, {}).get("options", [])
                property_schema["options"] = [{"name": opt.get("name"), "color": opt.get("color")} for opt in options]

            elif prop_type == "status":
                status_config = prop_config.get("status", {})
                options = status_config.get("options", [])
                property_schema["options"] = [{"name": opt.get("name"), "color": opt.get("color")} for opt in options]
                property_schema["groups"] = status_config.get("groups", [])

            schema["properties"][prop_name] = property_schema

        return schema

    except Exception as e:
        logger.error(f"Error getting database schema for {database_id}: {e}")
        raise

def classify_database_type(schema: dict) -> str:
    """
    Attempt to identify database type from its properties

    Returns: 'tasks', 'projects', 'companies', 'documentation', or 'custom'
    """
    props = [p.lower() for p in schema["properties"].keys()]
    title = schema.get("title", "").lower()

    # Check database title first (most reliable)
    if "task" in title:
        return "tasks"
    elif "project" in title:
        return "projects"
    elif "compan" in title or "client" in title or "domain" in title:
        return "companies"
    elif "doc" in title or "knowledge" in title or "wiki" in title:
        return "documentation"

    # Fallback to property analysis
    # Tasks database indicators
    if any("task" in p for p in props) and any("status" in p for p in props):
        return "tasks"

    # Projects database indicators
    if any("project" in p for p in props) and any(("timeline" in p or "start" in p or "end" in p) for p in props):
        return "projects"

    # Companies database indicators
    if any(("company" in p or "domain" in p or "website" in p) for p in props) and any("industry" in p or "size" in p for p in props):
        return "companies"

    # Documentation database indicators
    if any(("doc" in p or "article" in p or "page" in p) for p in props) and any("category" in p or "tag" in p for p in props):
        return "documentation"

    return "custom"

def extract_property_value(prop_data: dict, prop_type: str):
    """
    Extract value from a Notion property based on its type

    Handles all 15+ Notion property types dynamically
    """
    if not prop_data or prop_data.get("type") != prop_type:
        return None

    try:
        # Title property
        if prop_type == "title":
            title_list = prop_data.get("title", [])
            if title_list and len(title_list) > 0:
                return title_list[0].get("text", {}).get("content", "")

        # Rich text property
        elif prop_type == "rich_text":
            text_list = prop_data.get("rich_text", [])
            if text_list and len(text_list) > 0:
                return text_list[0].get("text", {}).get("content", "")

        # Select property
        elif prop_type == "select":
            select_data = prop_data.get("select")
            if select_data:
                return select_data.get("name", "")

        # Multi-select property
        elif prop_type == "multi_select":
            return [item.get("name", "") for item in prop_data.get("multi_select", [])]

        # Status property
        elif prop_type == "status":
            status_data = prop_data.get("status")
            if status_data:
                return status_data.get("name", "")

        # Date property
        elif prop_type == "date":
            date_data = prop_data.get("date")
            if date_data:
                return date_data.get("start", "")

        # Checkbox property
        elif prop_type == "checkbox":
            return prop_data.get("checkbox", False)

        # Number property
        elif prop_type == "number":
            return prop_data.get("number")

        # URL property
        elif prop_type == "url":
            return prop_data.get("url", "")

        # Email property
        elif prop_type == "email":
            return prop_data.get("email", "")

        # Phone property
        elif prop_type == "phone_number":
            return prop_data.get("phone_number", "")

        # People property
        elif prop_type == "people":
            return [person.get("name", "") for person in prop_data.get("people", [])]

        # Files property
        elif prop_type == "files":
            return [file.get("name", "") for file in prop_data.get("files", [])]

        # Created/edited time
        elif prop_type in ["created_time", "last_edited_time"]:
            return prop_data.get(prop_type, "")

        # Created/edited by
        elif prop_type in ["created_by", "last_edited_by"]:
            user = prop_data.get(prop_type, {})
            return user.get("name", "")

    except Exception as e:
        logger.error(f"Error extracting property value for type {prop_type}: {e}")
        return None

    return None

def discover_and_store_user_databases_sync(user_id: str, access_token: str):
    """
    Discover all Notion databases for a user and store them in notion_user_databases table

    This function:
    1. Searches for all databases using Notion Search API
    2. Retrieves schema for each database
    3. Auto-classifies database type
    4. Stores in database registry

    Uses synchronous version for compatibility with existing code
    """
    try:
        notion = Client(auth=access_token)

        logger.info(f"🔍 Starting database discovery for user {user_id[:8]}...")

        # Step 1: Search for all databases (use "data_source" for API v2025-09-03)
        databases = []
        start_cursor = None
        discovered_count = 0

        while True:
            try:
                search_params = {
                    "filter": {"property": "object", "value": "data_source"},
                    "page_size": 100
                }
                if start_cursor:
                    search_params["start_cursor"] = start_cursor

                response = notion.search(**search_params)

                for result in response.get("results", []):
                    if result.get("object") == "data_source":
                        db_id = result["id"]
                        title_list = result.get("title", [])
                        db_title = title_list[0].get("text", {}).get("content", "Untitled") if title_list else "Untitled"

                        databases.append({
                            "id": db_id,
                            "title": db_title,
                            "url": result.get("url", ""),
                            "created_time": result.get("created_time", ""),
                            "last_edited_time": result.get("last_edited_time", "")
                        })
                        discovered_count += 1

                # Handle pagination
                if not response.get("has_more", False):
                    break
                start_cursor = response.get("next_cursor")

            except Exception as e:
                logger.error(f"Error during search iteration: {e}")
                break

        logger.info(f"📊 Discovered {discovered_count} databases")

        # Step 2: Get schema for each database and store
        engine = create_engine(os.getenv("DATABASE_URL"))

        with Session(engine) as session:
            stored_count = 0

            for db in databases:
                try:
                    # Get full schema
                    schema = get_database_schema(notion, db["id"])

                    # Classify database type
                    db_type = classify_database_type(schema)

                    # Extract property order with Name/title first for better UX
                    properties = schema.get("properties", {})
                    property_keys = list(properties.keys())

                    # Find the title property (usually "Name")
                    title_property = None
                    for prop_name, prop_config in properties.items():
                        if prop_config.get("type") == "title":
                            title_property = prop_name
                            break

                    # Put title first, then the rest in Notion's original order
                    if title_property and title_property in property_keys:
                        property_order = [title_property] + [k for k in property_keys if k != title_property]
                    else:
                        property_order = property_keys

                    logger.info(f"   ├─ {db['title'][:40]}: {db_type}")

                    # Store in database registry with property order
                    session.execute(
                        text("""
                            INSERT INTO notion_user_databases
                            (user_id, database_id, database_title, database_type, schema, property_order, last_synced)
                            VALUES (:user_id, :database_id, :database_title, :database_type, CAST(:schema AS jsonb), CAST(:property_order AS jsonb), NOW())
                            ON CONFLICT (user_id, database_id)
                            DO UPDATE SET
                                database_title = EXCLUDED.database_title,
                                database_type = EXCLUDED.database_type,
                                schema = EXCLUDED.schema,
                                property_order = EXCLUDED.property_order,
                                last_synced = NOW()
                        """),
                        {
                            "user_id": user_id,
                            "database_id": db["id"],
                            "database_title": db["title"],
                            "database_type": db_type,
                            "schema": json.dumps(schema),
                            "property_order": json.dumps(property_order)
                        }
                    )
                    stored_count += 1

                except Exception as e:
                    logger.error(f"Error processing database {db['title']}: {e}")
                    continue

            session.commit()
            logger.info(f"✅ Stored {stored_count} databases in registry for user {user_id[:8]}")

        return {"success": True, "discovered": discovered_count, "stored": stored_count}

    except Exception as e:
        logger.error(f"❌ Error discovering databases for user {user_id[:8]}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e)}


logger.info("✅ Notion integration helper functions loaded")
