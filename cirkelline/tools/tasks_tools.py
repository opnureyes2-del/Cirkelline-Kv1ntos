"""
Cirkelline Standalone Tasks Tools
=================================
Tools for managing user's tasks stored in PostgreSQL.
Allows Cirkelline to view and manage tasks from the standalone tasks system.

v1.3.5: Created to match calendar_tools pattern
v1.3.6: Added automatic Google Tasks sync (like calendar_tools)
"""

from agno.tools import Toolkit
from sqlalchemy import text
from datetime import datetime, timezone
from typing import Optional

from cirkelline.config import logger
from cirkelline.database import engine


class CirkellineTasksTools(Toolkit):
    """
    Tools for managing user's standalone tasks.
    Uses the same database as the Tasks UI panel.
    """

    def __init__(self):
        super().__init__(
            name="tasks_tools",
            tools=[
                self.get_task_lists,
                self.get_tasks,
                self.create_task,
                self.update_task,
                self.delete_task,
                self.create_task_list,
            ],
            instructions="""
            Use these tools to manage the user's tasks.
            - get_task_lists: See all task lists
            - get_tasks: See tasks (optionally filtered by list, completion, priority)
            - create_task: Create a new task
            - update_task: Update or complete a task
            - delete_task: Delete a task
            - create_task_list: Create a new task list
            """,
            add_instructions=True
        )
        logger.info("✅ CirkellineTasksTools loaded (v1.3.6 - with Google Tasks sync)")

    def _get_or_create_default_list(self, user_id: str) -> str:
        """Get or create the user's default task list. Returns list_id."""
        with engine.connect() as conn:
            # Check for existing default list
            result = conn.execute(
                text("SELECT id FROM task_lists WHERE user_id = :user_id AND is_default = true"),
                {"user_id": user_id}
            )
            row = result.fetchone()

            if row:
                return str(row.id)

            # Create default list
            result = conn.execute(
                text("""
                    INSERT INTO task_lists (user_id, name, color, is_default, source)
                    VALUES (:user_id, 'My Tasks', '#8E0B83', true, 'local')
                    RETURNING id
                """),
                {"user_id": user_id}
            )
            row = result.fetchone()
            conn.commit()
            logger.info(f"Created default task list for user {user_id}")
            return str(row.id)

    def _get_list_external_id(self, list_id: str, user_id: str) -> Optional[str]:
        """Get the external_id for a task list (for Google sync)."""
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT external_id FROM task_lists WHERE id = :id AND user_id = :user_id"),
                {"id": list_id, "user_id": user_id}
            )
            row = result.fetchone()
            if row and row.external_id:
                return row.external_id
        return None

    def _try_google_sync(self, user_id: str, task_id: str, list_id: str, action: str, data: dict) -> str:
        """
        Try to sync with Google Tasks if connected. Returns status message.

        v1.3.6: Automatic sync like calendar_tools - syncs if user has Google connected,
        regardless of sync_enabled flag. Creates task in user's primary task list if no external_id.
        """
        try:
            from cirkelline.integrations.google.google_oauth import get_user_google_credentials
            import asyncio

            # Get Google credentials
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                google_creds = loop.run_until_complete(get_user_google_credentials(user_id))
            finally:
                loop.close()

            if not google_creds:
                return ""  # Not connected, no message needed

            from googleapiclient.discovery import build
            service = build('tasks', 'v1', credentials=google_creds)

            # Get or find the Google task list to use
            google_list_id = self._get_list_external_id(list_id, user_id)

            if not google_list_id:
                # Use the user's primary Google task list (@default)
                google_list_id = "@default"

            if action == "create":
                task = {
                    'title': data['title'],
                    'notes': data.get('notes', '') or '',
                }
                if data.get('due_date'):
                    # Google Tasks wants RFC 3339 format
                    task['due'] = data['due_date'].isoformat()

                created = service.tasks().insert(tasklist=google_list_id, body=task).execute()

                # Update local task with Google ID
                with engine.connect() as conn:
                    conn.execute(
                        text("UPDATE tasks SET external_id = :ext_id, sync_status = 'synced' WHERE id = :id"),
                        {"ext_id": created['id'], "id": task_id}
                    )
                    # Also update the list to have external_id if it didn't have one
                    if google_list_id == "@default":
                        conn.execute(
                            text("UPDATE task_lists SET external_id = :ext_id, sync_enabled = true WHERE id = :id"),
                            {"ext_id": "@default", "id": list_id}
                        )
                    conn.commit()
                return "📤 Synced to Google Tasks"

            elif action == "update":
                external_id = data.get("external_id")
                if not external_id:
                    # Get external_id from database
                    with engine.connect() as conn:
                        result = conn.execute(
                            text("SELECT external_id FROM tasks WHERE id = :id"),
                            {"id": task_id}
                        )
                        row = result.fetchone()
                        if row:
                            external_id = row.external_id

                if external_id:
                    # Get current task, update it
                    task = service.tasks().get(tasklist=google_list_id, task=external_id).execute()
                    if 'title' in data and data['title']:
                        task['title'] = data['title']
                    if 'notes' in data:
                        task['notes'] = data['notes'] or ''
                    if 'due_date' in data:
                        task['due'] = data['due_date'].isoformat() if data['due_date'] else None
                    if 'completed' in data:
                        task['status'] = 'completed' if data['completed'] else 'needsAction'

                    service.tasks().update(tasklist=google_list_id, task=external_id, body=task).execute()
                    return "📤 Synced to Google Tasks"

            elif action == "delete":
                external_id = data.get("external_id")
                if external_id:
                    try:
                        service.tasks().delete(tasklist=google_list_id, task=external_id).execute()
                        return "📤 Deleted from Google Tasks"
                    except Exception as e:
                        logger.warning(f"Could not delete from Google Tasks: {e}")

            return ""

        except Exception as e:
            logger.warning(f"Google Tasks sync failed (non-critical): {e}")
            return ""  # Don't report sync failures to user

    def get_task_lists(self, session_state: dict) -> str:
        """
        Get all task lists for the user.

        Args:
            session_state: Session context containing current_user_id.

        Returns:
            Formatted list of task lists with names and colors.
        """
        try:
            user_id = session_state.get('current_user_id')
            if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
                return "Please log in to access your tasks."

            with engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT id, name, color, is_default,
                               (SELECT COUNT(*) FROM tasks WHERE list_id = task_lists.id AND completed = false) as active_count,
                               (SELECT COUNT(*) FROM tasks WHERE list_id = task_lists.id AND completed = true) as completed_count
                        FROM task_lists
                        WHERE user_id = :user_id
                        ORDER BY is_default DESC, name ASC
                    """),
                    {"user_id": user_id}
                )

                lists = []
                for row in result:
                    lists.append({
                        "id": str(row.id),
                        "name": row.name,
                        "color": row.color,
                        "is_default": row.is_default,
                        "active": row.active_count,
                        "completed": row.completed_count
                    })

                if not lists:
                    return "No task lists found. Create one by saying 'create a task list called Work'."

                result_lines = [f"You have {len(lists)} task list(s):"]
                for lst in lists:
                    default = " (default)" if lst["is_default"] else ""
                    result_lines.append(f"- {lst['name']}{default}: {lst['active']} active, {lst['completed']} completed (ID: {lst['id']})")

                return "\n".join(result_lines)

        except Exception as e:
            logger.error(f"Error getting task lists: {e}")
            return f"Error getting task lists: {e}"

    def get_tasks(
        self,
        session_state: dict,
        list_id: str = None,
        completed: bool = None,
        priority: str = None
    ) -> str:
        """
        Get tasks for the user, optionally filtered.

        Args:
            session_state: Session context containing current_user_id.
            list_id: Optional - filter by specific list ID.
            completed: Optional - filter by completion status (true/false).
            priority: Optional - filter by priority (low/medium/high/urgent).

        Returns:
            Formatted list of tasks with titles, due dates, and priorities.
        """
        try:
            user_id = session_state.get('current_user_id')
            if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
                return "Please log in to access your tasks."

            with engine.connect() as conn:
                query = """
                    SELECT t.id, t.title, t.notes, t.due_date, t.completed, t.priority,
                           tl.name as list_name
                    FROM tasks t
                    JOIN task_lists tl ON t.list_id = tl.id
                    WHERE t.user_id = :user_id
                """
                params = {"user_id": user_id}

                if list_id:
                    query += " AND t.list_id = :list_id"
                    params["list_id"] = list_id

                if completed is not None:
                    query += " AND t.completed = :completed"
                    params["completed"] = completed

                if priority:
                    query += " AND t.priority = :priority"
                    params["priority"] = priority

                query += " ORDER BY t.completed ASC, t.priority DESC, t.due_date ASC NULLS LAST, t.created_at DESC LIMIT 50"

                result = conn.execute(text(query), params)

                tasks = []
                for row in result:
                    tasks.append({
                        "id": str(row.id),
                        "title": row.title,
                        "notes": row.notes,
                        "due_date": row.due_date,
                        "completed": row.completed,
                        "priority": row.priority,
                        "list_name": row.list_name
                    })

                if not tasks:
                    return "No tasks found matching your criteria."

                active = [t for t in tasks if not t["completed"]]
                done = [t for t in tasks if t["completed"]]

                result_lines = [f"Found {len(tasks)} task(s) ({len(active)} active, {len(done)} completed):"]

                for task in tasks:
                    status = "✓" if task["completed"] else "○"
                    priority_icon = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(task["priority"], "")
                    due = f" (due: {task['due_date'].strftime('%Y-%m-%d')})" if task["due_date"] else ""
                    result_lines.append(f"{status} {priority_icon} {task['title']}{due} [{task['list_name']}] (ID: {task['id']})")

                return "\n".join(result_lines)

        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return f"Error getting tasks: {e}"

    def create_task(
        self,
        session_state: dict,
        title: str,
        list_id: str = None,
        notes: str = None,
        due_date: str = None,
        priority: str = "medium"
    ) -> str:
        """
        Create a new task.

        Args:
            session_state: Session context containing current_user_id.
            title: The task title (required).
            list_id: Optional - the list to add the task to. Uses default list if not provided.
            notes: Optional - additional notes for the task.
            due_date: Optional - due date in YYYY-MM-DD format.
            priority: Priority level - low, medium, high, or urgent (default: medium).

        Returns:
            Confirmation message with task details.
        """
        try:
            user_id = session_state.get('current_user_id')
            if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
                return "Please log in to create tasks."

            # Get or create default list if not provided
            if not list_id:
                list_id = self._get_or_create_default_list(user_id)

            # Parse due_date
            parsed_due = None
            if due_date:
                try:
                    parsed_due = datetime.strptime(due_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except ValueError:
                    return f"Invalid date format. Use YYYY-MM-DD (e.g., 2025-12-25)."

            with engine.connect() as conn:
                # Verify list ownership
                check = conn.execute(
                    text("SELECT id, name FROM task_lists WHERE id = :id AND user_id = :user_id"),
                    {"id": list_id, "user_id": user_id}
                )
                list_row = check.fetchone()
                if not list_row:
                    return "Task list not found or doesn't belong to you."

                # Get next position
                pos_result = conn.execute(
                    text("SELECT COALESCE(MAX(position), 0) + 1 FROM tasks WHERE list_id = :list_id"),
                    {"list_id": list_id}
                )
                position = pos_result.fetchone()[0]

                # Create task
                result = conn.execute(
                    text("""
                        INSERT INTO tasks (user_id, list_id, title, notes, due_date, priority, position, source, sync_status)
                        VALUES (:user_id, :list_id, :title, :notes, :due_date, :priority, :position, 'local', 'local')
                        RETURNING id
                    """),
                    {
                        "user_id": user_id,
                        "list_id": list_id,
                        "title": title,
                        "notes": notes,
                        "due_date": parsed_due,
                        "priority": priority,
                        "position": position
                    }
                )
                task_id = result.fetchone().id
                conn.commit()

                logger.info(f"✅ Created task '{title}' for user {user_id}")

                # Try to sync to Google (if connected)
                sync_msg = self._try_google_sync(user_id, str(task_id), list_id, "create", {
                    "title": title,
                    "notes": notes,
                    "due_date": parsed_due,
                    "priority": priority
                })

                response = f"✅ Created task: {title}\n📋 List: {list_row.name}\n⚡ Priority: {priority}"
                if parsed_due:
                    response += f"\n📅 Due: {due_date}"
                response += f"\nID: {task_id}"
                if sync_msg:
                    response += f"\n{sync_msg}"

                return response

        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return f"Error creating task: {e}"

    def update_task(
        self,
        session_state: dict,
        task_id: str,
        title: str = None,
        notes: str = None,
        due_date: str = None,
        priority: str = None,
        completed: bool = None
    ) -> str:
        """
        Update an existing task.

        Args:
            session_state: Session context containing current_user_id.
            task_id: The task ID to update (required).
            title: Optional - new title.
            notes: Optional - new notes.
            due_date: Optional - new due date in YYYY-MM-DD format.
            priority: Optional - new priority (low/medium/high/urgent).
            completed: Optional - mark as completed (true) or incomplete (false).

        Returns:
            Confirmation of the update.
        """
        try:
            user_id = session_state.get('current_user_id')
            if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
                return "Please log in to update tasks."

            with engine.connect() as conn:
                # Get task info for Google sync
                check = conn.execute(
                    text("SELECT list_id, external_id FROM tasks WHERE id = :task_id AND user_id = :user_id"),
                    {"task_id": task_id, "user_id": user_id}
                )
                task_info = check.fetchone()
                if not task_info:
                    return "Task not found or doesn't belong to you."

                list_id = str(task_info.list_id)
                external_id = task_info.external_id

                # Build dynamic update
                updates = []
                params = {"task_id": task_id, "user_id": user_id}
                parsed_due = None

                if title is not None:
                    updates.append("title = :title")
                    params["title"] = title

                if notes is not None:
                    updates.append("notes = :notes")
                    params["notes"] = notes

                if due_date is not None:
                    try:
                        parsed_due = datetime.strptime(due_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                        params["due_date"] = parsed_due
                        updates.append("due_date = :due_date")
                    except ValueError:
                        return "Invalid date format. Use YYYY-MM-DD."

                if priority is not None:
                    updates.append("priority = :priority")
                    params["priority"] = priority

                if completed is not None:
                    updates.append("completed = :completed")
                    params["completed"] = completed
                    if completed:
                        updates.append("completed_at = NOW()")
                    else:
                        updates.append("completed_at = NULL")

                if not updates:
                    return "No updates provided."

                updates.append("updated_at = NOW()")

                query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = :task_id AND user_id = :user_id RETURNING title, completed"
                result = conn.execute(text(query), params)
                row = result.fetchone()

                if not row:
                    return "Task not found or doesn't belong to you."

                conn.commit()

                logger.info(f"✅ Updated task {task_id} for user {user_id}")

                # Try to sync to Google (if connected and task has external_id)
                sync_msg = ""
                if external_id:
                    sync_msg = self._try_google_sync(user_id, task_id, list_id, "update", {
                        "external_id": external_id,
                        "title": title,
                        "notes": notes,
                        "due_date": parsed_due,
                        "completed": completed
                    })

                if completed:
                    response = f"✅ Completed task: {row.title}"
                else:
                    response = f"✅ Updated task: {row.title}"

                if sync_msg:
                    response += f"\n{sync_msg}"
                return response

        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return f"Error updating task: {e}"

    def delete_task(self, session_state: dict, task_id: str) -> str:
        """
        Delete a task.

        Args:
            session_state: Session context containing current_user_id.
            task_id: The task ID to delete (required).

        Returns:
            Confirmation of deletion.
        """
        try:
            user_id = session_state.get('current_user_id')
            if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
                return "Please log in to delete tasks."

            with engine.connect() as conn:
                # Get task info for Google sync
                check = conn.execute(
                    text("SELECT title, list_id, external_id FROM tasks WHERE id = :id AND user_id = :user_id"),
                    {"id": task_id, "user_id": user_id}
                )
                row = check.fetchone()

                if not row:
                    return "Task not found or doesn't belong to you."

                title = row.title
                list_id = str(row.list_id)
                external_id = row.external_id

                conn.execute(
                    text("DELETE FROM tasks WHERE id = :id AND user_id = :user_id"),
                    {"id": task_id, "user_id": user_id}
                )
                conn.commit()

                logger.info(f"✅ Deleted task '{title}' for user {user_id}")

                # Try to sync delete to Google
                sync_msg = ""
                if external_id:
                    sync_msg = self._try_google_sync(user_id, task_id, list_id, "delete", {
                        "external_id": external_id
                    })

                response = f"✅ Deleted task: {title}"
                if sync_msg:
                    response += f"\n{sync_msg}"
                return response

        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            return f"Error deleting task: {e}"

    def create_task_list(
        self,
        session_state: dict,
        name: str,
        color: str = "#8E0B83"
    ) -> str:
        """
        Create a new task list.

        Args:
            session_state: Session context containing current_user_id.
            name: The list name (required).
            color: Optional hex color for the list (default: #8E0B83).

        Returns:
            Confirmation with the new list details.
        """
        try:
            user_id = session_state.get('current_user_id')
            if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
                return "Please log in to create task lists."

            with engine.connect() as conn:
                # Check if first list (make it default)
                count_result = conn.execute(
                    text("SELECT COUNT(*) FROM task_lists WHERE user_id = :user_id"),
                    {"user_id": user_id}
                )
                is_default = count_result.fetchone()[0] == 0

                result = conn.execute(
                    text("""
                        INSERT INTO task_lists (user_id, name, color, is_default, source)
                        VALUES (:user_id, :name, :color, :is_default, 'local')
                        RETURNING id
                    """),
                    {"user_id": user_id, "name": name, "color": color, "is_default": is_default}
                )
                list_id = result.fetchone().id
                conn.commit()

                logger.info(f"✅ Created task list '{name}' for user {user_id}")

                default_msg = " (set as default)" if is_default else ""
                return f"✅ Created task list: {name}{default_msg}\nID: {list_id}"

        except Exception as e:
            logger.error(f"Error creating task list: {e}")
            return f"Error creating task list: {e}"


# Create singleton instance
tasks_tools = CirkellineTasksTools()

logger.info("✅ Tasks tools module loaded (v1.3.6 - with Google Tasks sync)")
