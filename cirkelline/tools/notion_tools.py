"""
Cirkelline Notion Integration Tools
====================================
Tools for interacting with user's Notion workspace.
Allows Cirkelline to view and manage tasks, projects, companies, and documentation.
"""

import os
from agno.tools import Toolkit
from agno.db.postgres import PostgresDb
from cirkelline.config import logger
from cirkelline.helpers.notion_helpers import (
    get_user_notion_credentials_sync,
    extract_property_value
)


class NotionTools(Toolkit):
    """
    Tools for interacting with user's Notion workspace.
    Allows Cirkelline to view and manage tasks, projects, and companies.
    """

    def __init__(self, database: PostgresDb):
        super().__init__(
            name="notion_tools",
            instructions="""
            Use these tools to interact with the user's Notion workspace.
            Use when user asks about their tasks, projects, companies, or documentation stored in Notion.
            The user must have connected their Notion workspace first.
            """,
            add_instructions=True
        )
        self.db = database
        self.register(self.get_notion_tasks)
        self.register(self.get_notion_projects)
        self.register(self.get_notion_companies)
        self.register(self.get_notion_documentation)
        self.register(self.create_notion_task)

    def get_notion_tasks(self, session_state: dict) -> str:
        """
        Get all tasks from your Notion workspace.

        🔄 UPDATED: Now uses dynamic database registry - works with any task database structure!
        Returns a formatted list of your current tasks with their status, priority, and due dates.

        Args:
            session_state: Session context containing current_user_id for authentication.

        Returns:
            Formatted string with task list or error message.
        """
        try:
            user_id = session_state.get('current_user_id')
            # v1.3.4: Require authentication - no anonymous access
            if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
                return "❌ Authentication required. Please log in to use Notion integration."
            import json

            # Get user's Notion credentials
            creds = get_user_notion_credentials_sync(user_id)
            if not creds:
                return "❌ You haven't connected your Notion workspace yet. Please connect it in your profile settings first!"

            # 🔍 Query database registry for tasks database
            from sqlalchemy import create_engine, text
            from sqlalchemy.orm import Session

            engine = create_engine(os.getenv("DATABASE_URL"))

            with Session(engine) as db_session:
                result = db_session.execute(
                    text("""
                        SELECT database_id, database_title, schema
                        FROM notion_user_databases
                        WHERE user_id = :user_id
                          AND database_type = 'tasks'
                          AND is_hidden = FALSE
                        ORDER BY last_synced DESC
                        LIMIT 1
                    """),
                    {"user_id": user_id}
                ).fetchone()

                if not result:
                    return "📋 No task-related database found in your Notion workspace. Make sure you've shared your task tracking database with Cirkelline, then say 'sync my Notion databases'!"

                tasks_db_id, db_title, schema_json = result
                schema = schema_json  # Already a dict from JSONB

            # Initialize Notion client
            from notion_client import Client
            notion = Client(auth=creds['access_token'])

            # Query tasks database
            response = notion.data_sources.query(data_source_id=tasks_db_id, page_size=100)
            tasks = []

            for page in response.get("results", []):
                task = {
                    "id": page["id"],
                    "url": page.get("url", "")
                }

                # 🎯 Extract properties dynamically using schema
                page_props = page.get("properties", {})

                for prop_name, prop_config in schema["properties"].items():
                    prop_type = prop_config["type"]
                    prop_data = page_props.get(prop_name, {})

                    # Extract value using helper function
                    value = extract_property_value(prop_data, prop_type)

                    if value:
                        # Store with normalized key (lowercase, underscores)
                        key = prop_name.lower().replace(" ", "_")
                        task[key] = value

                tasks.append(task)

            if not tasks:
                return f"📋 Your '{db_title}' database is empty. Add some items to get started!"

            # Format output - find title property dynamically
            result = f"📋 **{db_title}** ({len(tasks)} total)\n\n"

            for i, task in enumerate(tasks, 1):
                # Find title (any property with type='title' in schema)
                title = None
                for prop_name, prop_config in schema["properties"].items():
                    if prop_config["type"] == "title":
                        key = prop_name.lower().replace(" ", "_")
                        title = task.get(key, "Untitled")
                        break

                if not title:
                    title = "Untitled"

                result += f"{i}. **{title}**\n"

                # Display all other properties
                for prop_name, prop_config in schema["properties"].items():
                    prop_type = prop_config["type"]
                    key = prop_name.lower().replace(" ", "_")
                    value = task.get(key)

                    # Skip title (already shown) and empty values
                    if prop_type == "title" or not value:
                        continue

                    # Format based on type
                    if isinstance(value, list):
                        value_str = ", ".join(str(v) for v in value)
                    else:
                        value_str = str(value)

                    result += f"   • {prop_name}: {value_str}\n"

                result += f"   • Link: {task['url']}\n\n"

            return result

        except Exception as e:
            logger.error(f"❌ Error fetching Notion tasks: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"❌ Error accessing your Notion tasks: {str(e)}"

    def get_notion_projects(self, session_state: dict) -> str:
        """
        Get all projects from your Notion workspace.

        🔄 UPDATED: Now uses dynamic database registry - works with any project database structure!
        Returns a formatted list of your projects with their status and dates.

        Args:
            session_state: Session context containing current_user_id for authentication.

        Returns:
            Formatted string with project list or error message.
        """
        try:
            user_id = session_state.get('current_user_id')
            # v1.3.4: Require authentication - no anonymous access
            if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
                return "❌ Authentication required. Please log in to use Notion integration."
            import json

            # Get user's Notion credentials
            creds = get_user_notion_credentials_sync(user_id)
            if not creds:
                return "❌ You haven't connected your Notion workspace yet. Please connect it in your profile settings first!"

            # 🔍 Query database registry for projects database
            from sqlalchemy import create_engine, text
            from sqlalchemy.orm import Session

            engine = create_engine(os.getenv("DATABASE_URL"))

            with Session(engine) as db_session:
                result = db_session.execute(
                    text("""
                        SELECT database_id, database_title, schema
                        FROM notion_user_databases
                        WHERE user_id = :user_id
                          AND database_type = 'projects'
                          AND is_hidden = FALSE
                        ORDER BY last_synced DESC
                        LIMIT 1
                    """),
                    {"user_id": user_id}
                ).fetchone()

                if not result:
                    return "📁 No project-related database found in your Notion workspace. Make sure you've shared your projects database with Cirkelline, then say 'sync my Notion databases'!"

                db_id, db_title, schema_json = result
                schema = schema_json  # Already a dict from JSONB

            # Initialize Notion client
            from notion_client import Client
            notion = Client(auth=creds['access_token'])

            # Query database dynamically
            response = notion.data_sources.query(data_source_id=db_id, page_size=100)
            items = []

            for page in response.get("results", []):
                item = {"id": page["id"], "url": page.get("url", "")}
                page_props = page.get("properties", {})

                # Extract properties dynamically using schema
                for prop_name, prop_config in schema["properties"].items():
                    value = extract_property_value(page_props.get(prop_name, {}), prop_config["type"])
                    if value:
                        item[prop_name.lower().replace(" ", "_")] = value

                items.append(item)

            if not items:
                return f"📁 Your '{db_title}' database is empty!"

            # Format output dynamically
            result = f"📁 **{db_title}** ({len(items)} total)\n\n"

            for i, item in enumerate(items, 1):
                # Find title
                title = None
                for prop_name, prop_config in schema["properties"].items():
                    if prop_config["type"] == "title":
                        title = item.get(prop_name.lower().replace(" ", "_"), "Untitled")
                        break
                if not title:
                    title = "Untitled"

                result += f"{i}. **{title}**\n"

                # Display all other properties
                for prop_name, prop_config in schema["properties"].items():
                    if prop_config["type"] == "title":
                        continue
                    key = prop_name.lower().replace(" ", "_")
                    value = item.get(key)
                    if value:
                        value_str = ", ".join(str(v) for v in value) if isinstance(value, list) else str(value)
                        result += f"   • {prop_name}: {value_str}\n"

                result += f"   • Link: {item['url']}\n\n"

            return result

        except Exception as e:
            logger.error(f"❌ Error fetching Notion projects: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"❌ Error accessing your Notion projects: {str(e)}"

    def get_notion_companies(self, session_state: dict) -> str:
        """
        Get all companies from your Notion workspace.

        🔄 UPDATED: Now uses dynamic database registry - works with any companies database structure!
        Returns a formatted list of companies you're tracking.

        Args:
            session_state: Session context containing current_user_id for authentication.

        Returns:
            Formatted string with companies list or error message.
        """
        try:
            user_id = session_state.get('current_user_id')
            # v1.3.4: Require authentication - no anonymous access
            if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
                return "❌ Authentication required. Please log in to use Notion integration."
            import json

            # Get user's Notion credentials
            creds = get_user_notion_credentials_sync(user_id)
            if not creds:
                return "❌ You haven't connected your Notion workspace yet. Please connect it in your profile settings first!"

            # 🔍 Query database registry for companies database
            from sqlalchemy import create_engine, text
            from sqlalchemy.orm import Session

            engine = create_engine(os.getenv("DATABASE_URL"))

            with Session(engine) as db_session:
                result = db_session.execute(
                    text("""
                        SELECT database_id, database_title, schema
                        FROM notion_user_databases
                        WHERE user_id = :user_id
                          AND database_type = 'companies'
                          AND is_hidden = FALSE
                        ORDER BY last_synced DESC
                        LIMIT 1
                    """),
                    {"user_id": user_id}
                ).fetchone()

                if not result:
                    return "🏢 No company/client-related database found in your Notion workspace. Make sure you've shared your companies or clients database with Cirkelline, then say 'sync my Notion databases'!"

                db_id, db_title, schema_json = result
                schema = schema_json  # Already a dict from JSONB

            # Initialize Notion client
            from notion_client import Client
            notion = Client(auth=creds['access_token'])

            # Query database dynamically
            response = notion.data_sources.query(data_source_id=db_id, page_size=100)
            items = []

            for page in response.get("results", []):
                item = {"id": page["id"], "url": page.get("url", "")}
                page_props = page.get("properties", {})

                # Extract properties dynamically using schema
                for prop_name, prop_config in schema["properties"].items():
                    value = extract_property_value(page_props.get(prop_name, {}), prop_config["type"])
                    if value:
                        item[prop_name.lower().replace(" ", "_")] = value

                items.append(item)

            if not items:
                return f"🏢 Your '{db_title}' database is empty!"

            # Format output dynamically
            result = f"🏢 **{db_title}** ({len(items)} total)\n\n"

            for i, item in enumerate(items, 1):
                # Find title
                title = None
                for prop_name, prop_config in schema["properties"].items():
                    if prop_config["type"] == "title":
                        title = item.get(prop_name.lower().replace(" ", "_"), "Untitled")
                        break
                if not title:
                    title = "Untitled"

                result += f"{i}. **{title}**\n"

                # Display all other properties
                for prop_name, prop_config in schema["properties"].items():
                    if prop_config["type"] == "title":
                        continue
                    key = prop_name.lower().replace(" ", "_")
                    value = item.get(key)
                    if value:
                        value_str = ", ".join(str(v) for v in value) if isinstance(value, list) else str(value)
                        result += f"   • {prop_name}: {value_str}\n"

                result += f"   • Link: {item['url']}\n\n"

            return result

        except Exception as e:
            logger.error(f"❌ Error fetching Notion companies: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"❌ Error accessing your Notion companies: {str(e)}"

    def get_notion_documentation(self, session_state: dict) -> str:
        """
        Get all documentation from your Notion workspace.

        🔄 UPDATED: Now uses dynamic database registry - works with any documentation database structure!
        Returns a formatted list of documentation pages.

        Args:
            session_state: Session context containing current_user_id for authentication.

        Returns:
            Formatted string with documentation list or error message.
        """
        try:
            user_id = session_state.get('current_user_id')
            # v1.3.4: Require authentication - no anonymous access
            if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
                return "❌ Authentication required. Please log in to use Notion integration."
            import json

            # Get user's Notion credentials
            creds = get_user_notion_credentials_sync(user_id)
            if not creds:
                return "❌ You haven't connected your Notion workspace yet. Please connect it in your profile settings first!"

            # 🔍 Query database registry for documentation database
            from sqlalchemy import create_engine, text
            from sqlalchemy.orm import Session

            engine = create_engine(os.getenv("DATABASE_URL"))

            with Session(engine) as db_session:
                result = db_session.execute(
                    text("""
                        SELECT database_id, database_title, schema
                        FROM notion_user_databases
                        WHERE user_id = :user_id
                          AND database_type = 'documentation'
                          AND is_hidden = FALSE
                        ORDER BY last_synced DESC
                        LIMIT 1
                    """),
                    {"user_id": user_id}
                ).fetchone()

                if not result:
                    return "📚 No documentation-related database found in your Notion workspace. Make sure you've shared your documentation or knowledge base with Cirkelline, then say 'sync my Notion databases'!"

                db_id, db_title, schema_json = result
                schema = schema_json  # Already a dict from JSONB

            # Initialize Notion client
            from notion_client import Client
            notion = Client(auth=creds['access_token'])

            # Query database dynamically
            response = notion.data_sources.query(data_source_id=db_id, page_size=100)
            items = []

            for page in response.get("results", []):
                item = {"id": page["id"], "url": page.get("url", "")}
                page_props = page.get("properties", {})

                # Extract properties dynamically using schema
                for prop_name, prop_config in schema["properties"].items():
                    value = extract_property_value(page_props.get(prop_name, {}), prop_config["type"])
                    if value:
                        item[prop_name.lower().replace(" ", "_")] = value

                items.append(item)

            if not items:
                return f"📚 Your '{db_title}' database is empty!"

            # Format output dynamically
            result = f"📚 **{db_title}** ({len(items)} total)\n\n"

            for i, item in enumerate(items, 1):
                # Find title
                title = None
                for prop_name, prop_config in schema["properties"].items():
                    if prop_config["type"] == "title":
                        title = item.get(prop_name.lower().replace(" ", "_"), "Untitled")
                        break
                if not title:
                    title = "Untitled"

                result += f"**{title}**\n"

                # Display all other properties
                for prop_name, prop_config in schema["properties"].items():
                    if prop_config["type"] == "title":
                        continue
                    key = prop_name.lower().replace(" ", "_")
                    value = item.get(key)
                    if value:
                        value_str = ", ".join(str(v) for v in value) if isinstance(value, list) else str(value)
                        result += f"   • {prop_name}: {value_str}\n"

                result += f"   • Link: {item['url']}\n\n"

            return result

        except Exception as e:
            logger.error(f"❌ Error fetching Notion documentation: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"❌ Error accessing your Notion documentation: {str(e)}"

    def create_notion_task(
        self,
        session_state: dict,
        title: str,
        status: str = None,
        priority: str = None,
        due_date: str = None,
        description: str = None
    ) -> str:
        """
        Create a new task in your Notion workspace.

        🔄 UPDATED: Now uses dynamic database registry - adapts to your task database structure!

        Args:
            title: Task name (required)
            status: Task status (e.g., "Not started", "In Progress", "Done")
            priority: Task priority (e.g., "High", "Medium", "Low")
            due_date: Due date in YYYY-MM-DD format
            description: Task description/notes

        Returns:
            Confirmation message with link to the new task
        """
        try:
            user_id = session_state.get('current_user_id')
            # v1.3.4: Require authentication - no anonymous access
            if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
                return "❌ Authentication required. Please log in to use Notion integration."
            import json

            # Get user's Notion credentials
            creds = get_user_notion_credentials_sync(user_id)
            if not creds:
                return "❌ You haven't connected your Notion workspace yet. Please connect it in your profile settings first!"

            # 🔍 Query database registry for tasks database
            from sqlalchemy import create_engine, text
            from sqlalchemy.orm import Session

            engine = create_engine(os.getenv("DATABASE_URL"))

            with Session(engine) as db_session:
                result = db_session.execute(
                    text("""
                        SELECT database_id, database_title, schema
                        FROM notion_user_databases
                        WHERE user_id = :user_id
                          AND database_type = 'tasks'
                          AND is_hidden = FALSE
                        ORDER BY last_synced DESC
                        LIMIT 1
                    """),
                    {"user_id": user_id}
                ).fetchone()

                if not result:
                    return "📋 No task-related database found in your Notion workspace. Make sure you've shared your task tracking database with Cirkelline, then say 'sync my Notion databases'!"

                tasks_db_id, db_title, schema_json = result
                schema = schema_json  # Already a dict from JSONB

            # Initialize Notion client
            from notion_client import Client
            notion = Client(auth=creds['access_token'])

            # 🎯 Build properties dynamically based on schema
            properties = {}

            # Find title property (required)
            title_prop = None
            status_prop = None
            priority_prop = None
            due_date_prop = None

            for prop_name, prop_config in schema["properties"].items():
                prop_type = prop_config["type"]
                prop_lower = prop_name.lower()

                # Title property (required for all pages)
                if prop_type == "title":
                    title_prop = prop_name
                    properties[prop_name] = {
                        "title": [{"text": {"content": title}}]
                    }

                # Status property
                elif prop_type == "status" and "status" in prop_lower:
                    status_prop = prop_name
                    if status:
                        properties[prop_name] = {"status": {"name": status}}

                # Priority property
                elif prop_type == "select" and "priority" in prop_lower:
                    priority_prop = prop_name
                    if priority:
                        properties[prop_name] = {"select": {"name": priority}}

                # Due date property
                elif prop_type == "date" and ("due" in prop_lower or "deadline" in prop_lower):
                    due_date_prop = prop_name
                    if due_date:
                        properties[prop_name] = {"date": {"start": due_date}}

            if not title_prop:
                return f"❌ Your '{db_title}' database doesn't have a title property. Cannot create items without a title field."

            # Build children (description)
            children = []
            if description:
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": description}}]
                    }
                })

            # Create task
            create_params = {
                "parent": {"type": "data_source_id", "data_source_id": tasks_db_id},
                "properties": properties
            }

            # Only add children if we have content
            if children:
                create_params["children"] = children

            new_page = notion.pages.create(**create_params)

            task_url = new_page.get("url", "")

            # Format confirmation message
            result = f"✅ **Task created in '{db_title}'!**\n\n"
            result += f"📝 **{title}**\n"
            if status and status_prop:
                result += f"• {status_prop}: {status}\n"
            if priority and priority_prop:
                result += f"• {priority_prop}: {priority}\n"
            if due_date and due_date_prop:
                result += f"• {due_date_prop}: {due_date}\n"
            result += f"\n🔗 View in Notion: {task_url}"

            return result

        except Exception as e:
            logger.error(f"❌ Error creating Notion task: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"❌ Error creating task: {str(e)}"


logger.info("✅ Notion tools module loaded")
