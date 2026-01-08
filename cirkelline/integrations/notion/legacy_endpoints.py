"""
Notion Legacy Database Endpoints
=================================
LEGACY endpoints that search for databases by NAME (hardcoded searches).

These endpoints remain for backward compatibility but are deprecated.
NEW code should use database_endpoints.py which queries by TYPE instead.

Why these are legacy:
- Hardcoded database name searches ("compan", "project", "task")
- Don't work if user renames their database
- Less flexible than registry-based approach
- Single-user assumptions

Maintained for backward compatibility with existing clients.
"""

from fastapi import APIRouter, Request, HTTPException
from notion_client import Client

from cirkelline.config import logger
from cirkelline.integrations.notion.notion_helpers import (
    get_user_notion_credentials,
    extract_property_value
)

# Create router
router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# LEGACY COMPANIES DATABASE ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/notion/companies")
async def get_notion_companies(request: Request):
    """
    LEGACY: Get companies from Notion by searching for database name containing 'compan'

    DEPRECATED: Use /api/notion/databases/companies/items instead

    This endpoint searches for a database with name containing "compan" (case-insensitive).
    If user renames their database to "Domains" or "Clients", this breaks!
    """
    try:
        user_id = getattr(request.state, 'user_id', None)
        # v1.3.4: Require authentication - no anonymous access
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
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

        # Search for database by name (LEGACY HARDCODED SEARCH)
        search_response = notion.search(
            filter={"property": "object", "value": "data_source"}
        )

        companies_db = None
        for result in search_response.get("results", []):
            if result.get("object") == "data_source":
                title_list = result.get("title", [])
                if title_list and len(title_list) > 0:
                    db_title = title_list[0].get("text", {}).get("content", "").lower()
                    if "compan" in db_title:  # HARDCODED SEARCH
                        companies_db = result
                        break

        if not companies_db:
            return {"companies": []}

        database_id = companies_db["id"]
        logger.info(f"User {user_id[:20]}... fetching companies from LEGACY endpoint (database: {database_id})")

        # Query the database
        db_results = notion.data_sources.query(data_source_id=database_id)

        companies = []
        for page in db_results.get("results", []):
            props = page.get("properties", {})

            company = {
                "id": page["id"],
                "url": page.get("url", ""),
                "created_time": page.get("created_time", ""),
                "last_edited_time": page.get("last_edited_time", ""),
            }

            # Extract properties
            for prop_name, prop_value in props.items():
                prop_type = prop_value.get("type")
                key = prop_name.lower().replace(" ", "_")

                if prop_type == "title":
                    titles = prop_value.get("title", [])
                    company[key] = titles[0].get("text", {}).get("content", "") if titles else ""
                    if not company.get("name"):
                        company["name"] = company[key]

                elif prop_type == "rich_text":
                    texts = prop_value.get("rich_text", [])
                    company[key] = texts[0].get("text", {}).get("content", "") if texts else ""

                elif prop_type == "select":
                    select = prop_value.get("select")
                    company[key] = select.get("name") if select else None

                elif prop_type == "multi_select":
                    multi = prop_value.get("multi_select", [])
                    company[key] = [opt.get("name") for opt in multi]

                elif prop_type == "url":
                    company[key] = prop_value.get("url")

                elif prop_type == "email":
                    company[key] = prop_value.get("email")

                elif prop_type == "number":
                    company[key] = prop_value.get("number")

            companies.append(company)

        return {"companies": companies}

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Get Notion companies error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch companies: {str(e)}")

logger.info("✅ Notion companies endpoint (LEGACY) configured")

# ═══════════════════════════════════════════════════════════════
# LEGACY PROJECTS DATABASE ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/notion/projects")
async def get_notion_projects(request: Request):
    """
    LEGACY: Get projects from Notion by searching for database name containing 'project'

    DEPRECATED: Use /api/notion/databases/projects/items instead
    """
    try:
        user_id = getattr(request.state, 'user_id', None)
        # v1.3.4: Require authentication - no anonymous access
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        notion_creds = await get_user_notion_credentials(user_id)
        if not notion_creds:
            raise HTTPException(
                status_code=403,
                detail="Notion workspace not connected. Please connect your Notion account first."
            )

        notion = Client(auth=notion_creds['access_token'])

        # Search for database by name (LEGACY HARDCODED SEARCH)
        search_response = notion.search(
            filter={"property": "object", "value": "data_source"}
        )

        projects_db = None
        for result in search_response.get("results", []):
            if result.get("object") == "data_source":
                title_list = result.get("title", [])
                if title_list and len(title_list) > 0:
                    db_title = title_list[0].get("text", {}).get("content", "").lower()
                    if "project" in db_title:  # HARDCODED SEARCH
                        projects_db = result
                        break

        if not projects_db:
            return {"projects": []}

        database_id = projects_db["id"]
        logger.info(f"User {user_id[:20]}... fetching projects from LEGACY endpoint (database: {database_id})")

        db_results = notion.data_sources.query(data_source_id=database_id)

        projects = []
        for page in db_results.get("results", []):
            props = page.get("properties", {})

            project = {
                "id": page["id"],
                "url": page.get("url", ""),
                "created_time": page.get("created_time", ""),
                "last_edited_time": page.get("last_edited_time", ""),
            }

            for prop_name, prop_value in props.items():
                prop_type = prop_value.get("type")
                key = prop_name.lower().replace(" ", "_")

                if prop_type == "title":
                    titles = prop_value.get("title", [])
                    project[key] = titles[0].get("text", {}).get("content", "") if titles else ""
                    if not project.get("name"):
                        project["name"] = project[key]

                elif prop_type == "rich_text":
                    texts = prop_value.get("rich_text", [])
                    project[key] = texts[0].get("text", {}).get("content", "") if texts else ""

                elif prop_type == "select":
                    select = prop_value.get("select")
                    project[key] = select.get("name") if select else None

                elif prop_type == "status":
                    status = prop_value.get("status")
                    project[key] = status.get("name") if status else None

                elif prop_type == "date":
                    date_obj = prop_value.get("date")
                    if date_obj:
                        project[key] = date_obj.get("start")
                    else:
                        project[key] = None

            projects.append(project)

        return {"projects": projects}

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Get Notion projects error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")

logger.info("✅ Notion projects endpoint (LEGACY) configured")

# ═══════════════════════════════════════════════════════════════
# LEGACY TASKS DATABASE ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/api/notion/tasks")
async def get_notion_tasks(request: Request):
    """
    LEGACY: Get tasks from Notion by searching for database name containing 'task'

    DEPRECATED: Use /api/notion/databases/tasks/items instead
    """
    try:
        user_id = getattr(request.state, 'user_id', None)
        # v1.3.4: Require authentication - no anonymous access
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        notion_creds = await get_user_notion_credentials(user_id)
        if not notion_creds:
            raise HTTPException(
                status_code=403,
                detail="Notion workspace not connected. Please connect your Notion account first."
            )

        notion = Client(auth=notion_creds['access_token'])

        # Search for database by name (LEGACY HARDCODED SEARCH)
        search_response = notion.search(
            filter={"property": "object", "value": "data_source"}
        )

        tasks_db = None
        for result in search_response.get("results", []):
            if result.get("object") == "data_source":
                title_list = result.get("title", [])
                if title_list and len(title_list) > 0:
                    db_title = title_list[0].get("text", {}).get("content", "").lower()
                    if "task" in db_title:  # HARDCODED SEARCH
                        tasks_db = result
                        break

        if not tasks_db:
            return {"tasks": []}

        database_id = tasks_db["id"]
        logger.info(f"User {user_id[:20]}... fetching tasks from LEGACY endpoint (database: {database_id})")

        db_results = notion.data_sources.query(data_source_id=database_id)

        tasks = []
        for page in db_results.get("results", []):
            props = page.get("properties", {})

            task = {
                "id": page["id"],
                "url": page.get("url", ""),
                "created_time": page.get("created_time", ""),
                "last_edited_time": page.get("last_edited_time", ""),
            }

            for prop_name, prop_value in props.items():
                prop_type = prop_value.get("type")
                key = prop_name.lower().replace(" ", "_")

                if prop_type == "title":
                    titles = prop_value.get("title", [])
                    task[key] = titles[0].get("text", {}).get("content", "") if titles else ""
                    if not task.get("name"):
                        task["name"] = task[key]

                elif prop_type == "rich_text":
                    texts = prop_value.get("rich_text", [])
                    task[key] = texts[0].get("text", {}).get("content", "") if texts else ""

                elif prop_type == "status":
                    status = prop_value.get("status")
                    task[key] = status.get("name") if status else None

                elif prop_type == "date":
                    date_obj = prop_value.get("date")
                    if date_obj:
                        task[key] = date_obj.get("start")
                    else:
                        task[key] = None

                elif prop_type == "checkbox":
                    task[key] = prop_value.get("checkbox", False)

            tasks.append(task)

        return {"tasks": tasks}

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Get Notion tasks error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {str(e)}")

logger.info("✅ Notion tasks GET endpoint (LEGACY) configured")

@router.post("/api/notion/tasks")
async def create_notion_task(request: Request):
    """
    LEGACY: Create a task in Notion by searching for database name containing 'task'

    DEPRECATED: Use registry-based approach with database_type='tasks'

    Request body:
    {
        "title": "Task title",
        "description": "Task description",
        "status": "Not Started",
        "due_date": "2025-11-15"
    }
    """
    try:
        user_id = getattr(request.state, 'user_id', None)
        # v1.3.4: Require authentication - no anonymous access
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        body = await request.json()
        title = body.get('title')

        if not title:
            raise HTTPException(status_code=400, detail="Task title is required")

        notion_creds = await get_user_notion_credentials(user_id)
        if not notion_creds:
            raise HTTPException(
                status_code=403,
                detail="Notion workspace not connected. Please connect your Notion account first."
            )

        notion = Client(auth=notion_creds['access_token'])

        # Search for database by name (LEGACY HARDCODED SEARCH)
        search_response = notion.search(
            filter={"property": "object", "value": "data_source"}
        )

        tasks_db = None
        for result in search_response.get("results", []):
            if result.get("object") == "data_source":
                title_list = result.get("title", [])
                if title_list and len(title_list) > 0:
                    db_title = title_list[0].get("text", {}).get("content", "").lower()
                    if "task" in db_title:  # HARDCODED SEARCH
                        tasks_db = result
                        break

        if not tasks_db:
            raise HTTPException(status_code=404, detail="Tasks database not found in your Notion workspace")

        database_id = tasks_db["id"]

        # Get database schema to find property names
        db_schema = notion.data_sources.retrieve(data_source_id=database_id)
        properties_schema = db_schema.get("properties", {})

        # Find the title property name
        title_property = None
        for prop_name, prop_config in properties_schema.items():
            if prop_config.get("type") == "title":
                title_property = prop_name
                break

        if not title_property:
            raise HTTPException(status_code=500, detail="Could not find title property in Tasks database")

        # Build page properties
        page_properties = {
            title_property: {
                "title": [{"text": {"content": title}}]
            }
        }

        # Add optional properties if they exist in schema
        description = body.get('description')
        if description:
            for prop_name, prop_config in properties_schema.items():
                if prop_config.get("type") == "rich_text" and "description" in prop_name.lower():
                    page_properties[prop_name] = {
                        "rich_text": [{"text": {"content": description}}]
                    }
                    break

        status = body.get('status')
        if status:
            for prop_name, prop_config in properties_schema.items():
                if prop_config.get("type") == "status" and "status" in prop_name.lower():
                    page_properties[prop_name] = {
                        "status": {"name": status}
                    }
                    break

        due_date = body.get('due_date')
        if due_date:
            for prop_name, prop_config in properties_schema.items():
                if prop_config.get("type") == "date" and "due" in prop_name.lower():
                    page_properties[prop_name] = {
                        "date": {"start": due_date}
                    }
                    break

        # Create page
        new_page = notion.pages.create(
            parent={"database_id": database_id},
            properties=page_properties
        )

        logger.info(f"User {user_id[:20]}... created task in LEGACY endpoint: {title}")

        return {
            "success": True,
            "message": "Task created successfully",
            "task_id": new_page["id"],
            "url": new_page.get("url", "")
        }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Create Notion task error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

logger.info("✅ Notion tasks POST endpoint (LEGACY) configured")

# ═══════════════════════════════════════════════════════════════
# LEGACY DOCUMENTATION DATABASE ENDPOINT
# ═══════════════════════════════════════════════════════════════

@router.get("/api/notion/documentation")
async def get_notion_documentation(request: Request):
    """
    LEGACY: Get documentation pages from Notion by searching for database name
    containing 'doc', 'knowledge', or 'wiki'

    DEPRECATED: Use /api/notion/databases/documentation/items instead
    """
    try:
        user_id = getattr(request.state, 'user_id', None)
        # v1.3.4: Require authentication - no anonymous access
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        notion_creds = await get_user_notion_credentials(user_id)
        if not notion_creds:
            raise HTTPException(
                status_code=403,
                detail="Notion workspace not connected. Please connect your Notion account first."
            )

        notion = Client(auth=notion_creds['access_token'])

        # Search for database by name (LEGACY HARDCODED SEARCH)
        search_response = notion.search(
            filter={"property": "object", "value": "data_source"}
        )

        docs_db = None
        for result in search_response.get("results", []):
            if result.get("object") == "data_source":
                title_list = result.get("title", [])
                if title_list and len(title_list) > 0:
                    db_title = title_list[0].get("text", {}).get("content", "").lower()
                    if any(keyword in db_title for keyword in ["doc", "knowledge", "wiki"]):  # HARDCODED SEARCH
                        docs_db = result
                        break

        if not docs_db:
            return {"documentation": []}

        database_id = docs_db["id"]
        logger.info(f"User {user_id[:20]}... fetching documentation from LEGACY endpoint (database: {database_id})")

        db_results = notion.data_sources.query(data_source_id=database_id)

        docs = []
        for page in db_results.get("results", []):
            props = page.get("properties", {})

            doc = {
                "id": page["id"],
                "url": page.get("url", ""),
                "created_time": page.get("created_time", ""),
                "last_edited_time": page.get("last_edited_time", ""),
            }

            for prop_name, prop_value in props.items():
                prop_type = prop_value.get("type")
                key = prop_name.lower().replace(" ", "_")

                if prop_type == "title":
                    titles = prop_value.get("title", [])
                    doc[key] = titles[0].get("text", {}).get("content", "") if titles else ""
                    if not doc.get("name"):
                        doc["name"] = doc[key]

                elif prop_type == "rich_text":
                    texts = prop_value.get("rich_text", [])
                    doc[key] = texts[0].get("text", {}).get("content", "") if texts else ""

                elif prop_type == "select":
                    select = prop_value.get("select")
                    doc[key] = select.get("name") if select else None

                elif prop_type == "multi_select":
                    multi = prop_value.get("multi_select", [])
                    doc[key] = [opt.get("name") for opt in multi]

            docs.append(doc)

        return {"documentation": docs}

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Get Notion documentation error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch documentation: {str(e)}")

logger.info("✅ Notion documentation endpoint (LEGACY) configured")


logger.info("✅ Notion legacy database endpoints loaded")
