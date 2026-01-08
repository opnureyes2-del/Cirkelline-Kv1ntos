"""
Standalone Tasks Endpoints
===========================
CRUD operations for local task lists and tasks.
Supports standalone mode without external connections.
Includes Google Tasks sync (write-through + pull sync).

Database Tables Required:
-------------------------
CREATE TABLE task_lists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(7) DEFAULT '#8E0B83',
    is_default BOOLEAN DEFAULT false,
    source VARCHAR(50) DEFAULT 'local',
    external_id VARCHAR(255),
    sync_enabled BOOLEAN DEFAULT false,
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    list_id UUID NOT NULL REFERENCES task_lists(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    notes TEXT,
    due_date TIMESTAMP WITH TIME ZONE,
    completed BOOLEAN DEFAULT false,
    completed_at TIMESTAMP WITH TIME ZONE,
    priority VARCHAR(20) DEFAULT 'medium',
    position INTEGER DEFAULT 0,
    parent_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    external_id VARCHAR(255),
    source VARCHAR(50) DEFAULT 'local',
    sync_status VARCHAR(50) DEFAULT 'local',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_task_lists_user ON task_lists(user_id);
CREATE INDEX idx_tasks_user ON tasks(user_id);
CREATE INDEX idx_tasks_list ON tasks(list_id);
CREATE INDEX idx_tasks_due ON tasks(due_date);
"""

from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import text

from cirkelline.config import logger
from cirkelline.database import engine
from cirkelline.integrations.google.google_oauth import get_user_google_credentials

router = APIRouter()


# ═══════════════════════════════════════════════════════════════
# GOOGLE TASKS HELPERS
# ═══════════════════════════════════════════════════════════════

async def get_google_tasks_service(user_id: str):
    """Get Google Tasks service if user is connected."""
    try:
        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            return None
        from googleapiclient.discovery import build
        return build('tasks', 'v1', credentials=google_creds)
    except Exception as e:
        logger.warning(f"⚠️ Could not get Google Tasks service: {e}")
        return None


async def create_google_task(service, list_id: str, task_data: dict) -> Optional[str]:
    """Create task in Google Tasks. Returns Google task ID."""
    try:
        task = {
            'title': task_data['title'],
            'notes': task_data.get('notes', ''),
        }
        if task_data.get('due_date'):
            # Google Tasks wants RFC 3339 format
            task['due'] = task_data['due_date'].isoformat()

        created = service.tasks().insert(tasklist=list_id, body=task).execute()
        logger.info(f"✅ Created Google task: {created['id']}")
        return created['id']
    except Exception as e:
        logger.error(f"❌ Failed to create Google task: {e}")
        return None


async def update_google_task(service, list_id: str, task_id: str, task_data: dict) -> bool:
    """Update task in Google Tasks."""
    try:
        # Get existing task first
        task = service.tasks().get(tasklist=list_id, task=task_id).execute()

        if 'title' in task_data:
            task['title'] = task_data['title']
        if 'notes' in task_data:
            task['notes'] = task_data['notes']
        if 'due_date' in task_data:
            task['due'] = task_data['due_date'].isoformat() if task_data['due_date'] else None
        if 'completed' in task_data:
            task['status'] = 'completed' if task_data['completed'] else 'needsAction'

        service.tasks().update(tasklist=list_id, task=task_id, body=task).execute()
        logger.info(f"✅ Updated Google task: {task_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to update Google task: {e}")
        return False


async def delete_google_task(service, list_id: str, task_id: str) -> bool:
    """Delete task from Google Tasks."""
    try:
        service.tasks().delete(tasklist=list_id, task=task_id).execute()
        logger.info(f"✅ Deleted Google task: {task_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to delete Google task: {e}")
        return False


# ═══════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════

class TaskListCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    color: str = Field(default="#8E0B83", pattern="^#[0-9A-Fa-f]{6}$")
    is_default: bool = False


class TaskListUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    is_default: Optional[bool] = None


class TaskCreate(BaseModel):
    list_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    notes: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    parent_id: Optional[UUID] = None


class TaskUpdate(BaseModel):
    list_id: Optional[UUID] = None
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    notes: Optional[str] = None
    due_date: Optional[datetime] = None
    completed: Optional[bool] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high|urgent)$")
    position: Optional[int] = None


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_user_id(request: Request) -> str:
    """Extract user_id from JWT middleware."""
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user_id


# ═══════════════════════════════════════════════════════════════
# TASK LIST ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/api/tasks/lists")
async def list_task_lists(
    request: Request,
    source: Optional[str] = None  # Filter by source: 'local' or 'google'
):
    """List all task lists for the current user, optionally filtered by source."""
    user_id = get_user_id(request)

    try:
        with engine.connect() as conn:
            query = """
                SELECT id, name, color, is_default, source,
                       external_id, sync_enabled, last_synced_at, created_at, updated_at
                FROM task_lists
                WHERE user_id = :user_id
            """
            params = {"user_id": user_id}

            # Filter by source (local or google)
            if source:
                query += " AND source = :source"
                params["source"] = source

            query += " ORDER BY is_default DESC, name ASC"

            result = conn.execute(text(query), params)

            lists = []
            for row in result:
                lists.append({
                    "id": str(row.id),
                    "name": row.name,
                    "color": row.color,
                    "is_default": row.is_default,
                    "source": row.source,
                    "external_id": row.external_id,
                    "sync_enabled": row.sync_enabled,
                    "last_synced_at": row.last_synced_at.isoformat() if row.last_synced_at else None,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                })

            return JSONResponse(content={"lists": lists, "total": len(lists)})

    except Exception as e:
        logger.error(f"❌ Error listing task lists: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/tasks/lists")
async def create_task_list(request: Request, data: TaskListCreate):
    """Create a new task list."""
    user_id = get_user_id(request)

    try:
        with engine.connect() as conn:
            # If this is set as default, unset other defaults first
            if data.is_default:
                conn.execute(
                    text("UPDATE task_lists SET is_default = false WHERE user_id = :user_id"),
                    {"user_id": user_id}
                )

            # Check if user has any lists - if not, make this one default
            count_result = conn.execute(
                text("SELECT COUNT(*) FROM task_lists WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            is_first_list = count_result.scalar() == 0

            result = conn.execute(
                text("""
                    INSERT INTO task_lists (user_id, name, color, is_default, source)
                    VALUES (:user_id, :name, :color, :is_default, 'local')
                    RETURNING id, name, color, is_default, source, created_at
                """),
                {
                    "user_id": user_id,
                    "name": data.name,
                    "color": data.color,
                    "is_default": data.is_default or is_first_list
                }
            )

            row = result.fetchone()
            conn.commit()

            logger.info(f"✅ Created task list '{data.name}' for user {user_id}")

            return JSONResponse(
                status_code=201,
                content={
                    "id": str(row.id),
                    "name": row.name,
                    "color": row.color,
                    "is_default": row.is_default,
                    "source": row.source,
                    "created_at": row.created_at.isoformat() if row.created_at else None
                }
            )

    except Exception as e:
        logger.error(f"❌ Error creating task list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/tasks/lists/{list_id}")
async def update_task_list(request: Request, list_id: UUID, data: TaskListUpdate):
    """Update a task list."""
    user_id = get_user_id(request)

    try:
        with engine.connect() as conn:
            # Verify ownership
            check = conn.execute(
                text("SELECT id FROM task_lists WHERE id = :id AND user_id = :user_id"),
                {"id": str(list_id), "user_id": user_id}
            )
            if not check.fetchone():
                raise HTTPException(status_code=404, detail="Task list not found")

            # If setting as default, unset other defaults first
            if data.is_default:
                conn.execute(
                    text("UPDATE task_lists SET is_default = false WHERE user_id = :user_id"),
                    {"user_id": user_id}
                )

            # Build update query dynamically
            updates = []
            params = {"id": str(list_id), "user_id": user_id}

            if data.name is not None:
                updates.append("name = :name")
                params["name"] = data.name
            if data.color is not None:
                updates.append("color = :color")
                params["color"] = data.color
            if data.is_default is not None:
                updates.append("is_default = :is_default")
                params["is_default"] = data.is_default

            if updates:
                updates.append("updated_at = NOW()")
                query = f"UPDATE task_lists SET {', '.join(updates)} WHERE id = :id AND user_id = :user_id RETURNING *"
                result = conn.execute(text(query), params)
                row = result.fetchone()
                conn.commit()

                return JSONResponse(content={
                    "id": str(row.id),
                    "name": row.name,
                    "color": row.color,
                    "is_default": row.is_default,
                    "source": row.source,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                })

            return JSONResponse(content={"message": "No updates provided"})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating task list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/tasks/lists/{list_id}")
async def delete_task_list(request: Request, list_id: UUID):
    """Delete a task list and all its tasks."""
    user_id = get_user_id(request)

    try:
        with engine.connect() as conn:
            # Verify ownership and delete
            result = conn.execute(
                text("DELETE FROM task_lists WHERE id = :id AND user_id = :user_id RETURNING id"),
                {"id": str(list_id), "user_id": user_id}
            )

            if not result.fetchone():
                raise HTTPException(status_code=404, detail="Task list not found")

            conn.commit()
            logger.info(f"✅ Deleted task list {list_id} for user {user_id}")

            return JSONResponse(content={"message": "Task list deleted", "id": str(list_id)})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting task list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# TASK ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/api/tasks/tasks")
async def list_tasks(
    request: Request,
    list_id: Optional[UUID] = None,
    completed: Optional[bool] = None,
    source: Optional[str] = None  # Filter by source: 'local' or 'google'
):
    """List tasks, optionally filtered by list, completion status, and source."""
    user_id = get_user_id(request)

    try:
        with engine.connect() as conn:
            query = """
                SELECT t.id, t.list_id, t.title, t.notes, t.due_date,
                       t.completed, t.completed_at, t.priority, t.position,
                       t.parent_id, t.external_id, t.source, t.sync_status,
                       t.created_at, t.updated_at,
                       tl.name as list_name, tl.color as list_color
                FROM tasks t
                JOIN task_lists tl ON t.list_id = tl.id
                WHERE t.user_id = :user_id
            """
            params = {"user_id": user_id}

            if list_id:
                query += " AND t.list_id = :list_id"
                params["list_id"] = str(list_id)

            if completed is not None:
                query += " AND t.completed = :completed"
                params["completed"] = completed

            # Filter by source (local or google)
            if source:
                query += " AND t.source = :source"
                params["source"] = source

            query += " ORDER BY t.completed ASC, t.position ASC, t.due_date ASC NULLS LAST, t.created_at DESC"

            result = conn.execute(text(query), params)

            tasks = []
            for row in result:
                tasks.append({
                    "id": str(row.id),
                    "list_id": str(row.list_id),
                    "list_name": row.list_name,
                    "list_color": row.list_color,
                    "title": row.title,
                    "notes": row.notes,
                    "due_date": row.due_date.isoformat() if row.due_date else None,
                    "completed": row.completed,
                    "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                    "priority": row.priority,
                    "position": row.position,
                    "parent_id": str(row.parent_id) if row.parent_id else None,
                    "external_id": row.external_id,
                    "source": row.source,
                    "sync_status": row.sync_status,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                })

            return JSONResponse(content={"tasks": tasks, "total": len(tasks)})

    except Exception as e:
        logger.error(f"❌ Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/tasks/tasks/{task_id}")
async def get_task(request: Request, task_id: UUID):
    """Get a single task by ID."""
    user_id = get_user_id(request)

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT t.id, t.list_id, t.title, t.notes, t.due_date,
                           t.completed, t.completed_at, t.priority, t.position,
                           t.parent_id, t.external_id, t.source, t.sync_status,
                           t.created_at, t.updated_at,
                           tl.name as list_name, tl.color as list_color
                    FROM tasks t
                    JOIN task_lists tl ON t.list_id = tl.id
                    WHERE t.id = :id AND t.user_id = :user_id
                """),
                {"id": str(task_id), "user_id": user_id}
            )

            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Task not found")

            return JSONResponse(content={
                "id": str(row.id),
                "list_id": str(row.list_id),
                "list_name": row.list_name,
                "list_color": row.list_color,
                "title": row.title,
                "notes": row.notes,
                "due_date": row.due_date.isoformat() if row.due_date else None,
                "completed": row.completed,
                "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                "priority": row.priority,
                "position": row.position,
                "parent_id": str(row.parent_id) if row.parent_id else None,
                "external_id": row.external_id,
                "source": row.source,
                "sync_status": row.sync_status,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None
            })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/tasks/tasks")
async def create_task(request: Request, data: TaskCreate):
    """Create a new task."""
    user_id = get_user_id(request)

    try:
        with engine.connect() as conn:
            # Verify list ownership
            check = conn.execute(
                text("SELECT id, sync_enabled, external_id FROM task_lists WHERE id = :id AND user_id = :user_id"),
                {"id": str(data.list_id), "user_id": user_id}
            )
            list_row = check.fetchone()
            if not list_row:
                raise HTTPException(status_code=404, detail="Task list not found")

            # Get max position for this list
            pos_result = conn.execute(
                text("SELECT COALESCE(MAX(position), 0) + 1 FROM tasks WHERE list_id = :list_id"),
                {"list_id": str(data.list_id)}
            )
            next_position = pos_result.scalar()

            result = conn.execute(
                text("""
                    INSERT INTO tasks (list_id, user_id, title, notes, due_date, priority, position, parent_id, source)
                    VALUES (:list_id, :user_id, :title, :notes, :due_date, :priority, :position, :parent_id, 'local')
                    RETURNING id, list_id, title, notes, due_date, completed, completed_at,
                              priority, position, parent_id, source, sync_status, created_at
                """),
                {
                    "list_id": str(data.list_id),
                    "user_id": user_id,
                    "title": data.title,
                    "notes": data.notes,
                    "due_date": data.due_date,
                    "priority": data.priority,
                    "position": next_position,
                    "parent_id": str(data.parent_id) if data.parent_id else None
                }
            )

            row = result.fetchone()
            conn.commit()

            logger.info(f"✅ Created task '{data.title}' for user {user_id}")

            # Sync to Google if enabled
            if list_row.sync_enabled and list_row.external_id:
                service = await get_google_tasks_service(user_id)
                if service:
                    google_id = await create_google_task(service, list_row.external_id, {
                        "title": data.title,
                        "notes": data.notes,
                        "due_date": data.due_date
                    })
                    if google_id:
                        conn.execute(
                            text("UPDATE tasks SET external_id = :external_id, sync_status = 'synced' WHERE id = :id"),
                            {"external_id": google_id, "id": str(row.id)}
                        )
                        conn.commit()

            return JSONResponse(
                status_code=201,
                content={
                    "id": str(row.id),
                    "list_id": str(row.list_id),
                    "title": row.title,
                    "notes": row.notes,
                    "due_date": row.due_date.isoformat() if row.due_date else None,
                    "completed": row.completed,
                    "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                    "priority": row.priority,
                    "position": row.position,
                    "parent_id": str(row.parent_id) if row.parent_id else None,
                    "source": row.source,
                    "sync_status": row.sync_status,
                    "created_at": row.created_at.isoformat() if row.created_at else None
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/tasks/tasks/{task_id}")
async def update_task(request: Request, task_id: UUID, data: TaskUpdate):
    """Update a task."""
    user_id = get_user_id(request)

    try:
        with engine.connect() as conn:
            # Verify ownership and get current task
            check = conn.execute(
                text("""
                    SELECT t.id, t.list_id, t.external_id, tl.sync_enabled, tl.external_id as list_external_id
                    FROM tasks t
                    JOIN task_lists tl ON t.list_id = tl.id
                    WHERE t.id = :id AND t.user_id = :user_id
                """),
                {"id": str(task_id), "user_id": user_id}
            )
            task_row = check.fetchone()
            if not task_row:
                raise HTTPException(status_code=404, detail="Task not found")

            # Build update query dynamically
            updates = []
            params = {"id": str(task_id), "user_id": user_id}

            if data.list_id is not None:
                updates.append("list_id = :list_id")
                params["list_id"] = str(data.list_id)
            if data.title is not None:
                updates.append("title = :title")
                params["title"] = data.title
            if data.notes is not None:
                updates.append("notes = :notes")
                params["notes"] = data.notes
            if data.due_date is not None:
                updates.append("due_date = :due_date")
                params["due_date"] = data.due_date
            if data.completed is not None:
                updates.append("completed = :completed")
                params["completed"] = data.completed
                if data.completed:
                    updates.append("completed_at = NOW()")
                else:
                    updates.append("completed_at = NULL")
            if data.priority is not None:
                updates.append("priority = :priority")
                params["priority"] = data.priority
            if data.position is not None:
                updates.append("position = :position")
                params["position"] = data.position

            if updates:
                updates.append("updated_at = NOW()")
                query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = :id AND user_id = :user_id RETURNING *"
                result = conn.execute(text(query), params)
                row = result.fetchone()
                conn.commit()

                # Sync to Google if enabled
                if task_row.sync_enabled and task_row.external_id and task_row.list_external_id:
                    service = await get_google_tasks_service(user_id)
                    if service:
                        await update_google_task(service, task_row.list_external_id, task_row.external_id, {
                            "title": data.title,
                            "notes": data.notes,
                            "due_date": data.due_date,
                            "completed": data.completed
                        })

                return JSONResponse(content={
                    "id": str(row.id),
                    "list_id": str(row.list_id),
                    "title": row.title,
                    "notes": row.notes,
                    "due_date": row.due_date.isoformat() if row.due_date else None,
                    "completed": row.completed,
                    "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                    "priority": row.priority,
                    "position": row.position,
                    "parent_id": str(row.parent_id) if row.parent_id else None,
                    "source": row.source,
                    "sync_status": row.sync_status,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                })

            return JSONResponse(content={"message": "No updates provided"})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/tasks/tasks/{task_id}")
async def delete_task(request: Request, task_id: UUID):
    """Delete a task."""
    user_id = get_user_id(request)

    try:
        with engine.connect() as conn:
            # Get task info for Google sync
            check = conn.execute(
                text("""
                    SELECT t.id, t.external_id, tl.sync_enabled, tl.external_id as list_external_id
                    FROM tasks t
                    JOIN task_lists tl ON t.list_id = tl.id
                    WHERE t.id = :id AND t.user_id = :user_id
                """),
                {"id": str(task_id), "user_id": user_id}
            )
            task_row = check.fetchone()
            if not task_row:
                raise HTTPException(status_code=404, detail="Task not found")

            # Delete from local DB
            conn.execute(
                text("DELETE FROM tasks WHERE id = :id AND user_id = :user_id"),
                {"id": str(task_id), "user_id": user_id}
            )
            conn.commit()

            # Sync deletion to Google if enabled
            if task_row.sync_enabled and task_row.external_id and task_row.list_external_id:
                service = await get_google_tasks_service(user_id)
                if service:
                    await delete_google_task(service, task_row.list_external_id, task_row.external_id)

            logger.info(f"✅ Deleted task {task_id} for user {user_id}")

            return JSONResponse(content={"message": "Task deleted", "id": str(task_id)})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# SYNC ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.post("/api/tasks/sync/google")
async def sync_from_google(request: Request):
    """Pull tasks from Google Tasks and merge with local database."""
    user_id = get_user_id(request)

    try:
        service = await get_google_tasks_service(user_id)
        if not service:
            raise HTTPException(status_code=400, detail="Google Tasks not connected")

        synced_lists = 0
        synced_tasks = 0

        with engine.connect() as conn:
            # Get all task lists from Google
            google_lists = service.tasklists().list().execute()

            for google_list in google_lists.get('items', []):
                google_list_id = google_list['id']
                list_title = google_list['title']

                # Check if list exists locally (by external_id)
                existing = conn.execute(
                    text("SELECT id FROM task_lists WHERE external_id = :external_id AND user_id = :user_id"),
                    {"external_id": google_list_id, "user_id": user_id}
                ).fetchone()

                if existing:
                    local_list_id = existing.id
                    # Update existing list
                    conn.execute(
                        text("""
                            UPDATE task_lists
                            SET name = :name, sync_enabled = true, last_synced_at = NOW(), updated_at = NOW()
                            WHERE id = :id
                        """),
                        {"name": list_title, "id": str(local_list_id)}
                    )
                else:
                    # Create new list
                    result = conn.execute(
                        text("""
                            INSERT INTO task_lists (user_id, name, external_id, source, sync_enabled, last_synced_at)
                            VALUES (:user_id, :name, :external_id, 'google', true, NOW())
                            RETURNING id
                        """),
                        {"user_id": user_id, "name": list_title, "external_id": google_list_id}
                    )
                    local_list_id = result.fetchone().id
                    synced_lists += 1

                # Get tasks for this list from Google
                google_tasks = service.tasks().list(tasklist=google_list_id, showCompleted=True).execute()

                for google_task in google_tasks.get('items', []):
                    google_task_id = google_task['id']

                    # Check if task exists locally
                    existing_task = conn.execute(
                        text("SELECT id FROM tasks WHERE external_id = :external_id AND user_id = :user_id"),
                        {"external_id": google_task_id, "user_id": user_id}
                    ).fetchone()

                    task_data = {
                        "title": google_task.get('title', 'Untitled'),
                        "notes": google_task.get('notes'),
                        "due_date": google_task.get('due'),
                        "completed": google_task.get('status') == 'completed'
                    }

                    if existing_task:
                        # Update existing task
                        conn.execute(
                            text("""
                                UPDATE tasks
                                SET title = :title, notes = :notes, due_date = :due_date,
                                    completed = :completed, sync_status = 'synced', updated_at = NOW()
                                WHERE id = :id
                            """),
                            {
                                "title": task_data["title"],
                                "notes": task_data["notes"],
                                "due_date": task_data["due_date"],
                                "completed": task_data["completed"],
                                "id": str(existing_task.id)
                            }
                        )
                    else:
                        # Create new task
                        conn.execute(
                            text("""
                                INSERT INTO tasks (list_id, user_id, title, notes, due_date, completed,
                                                   external_id, source, sync_status)
                                VALUES (:list_id, :user_id, :title, :notes, :due_date, :completed,
                                        :external_id, 'google', 'synced')
                            """),
                            {
                                "list_id": str(local_list_id),
                                "user_id": user_id,
                                "title": task_data["title"],
                                "notes": task_data["notes"],
                                "due_date": task_data["due_date"],
                                "completed": task_data["completed"],
                                "external_id": google_task_id
                            }
                        )
                        synced_tasks += 1

            conn.commit()

        logger.info(f"✅ Synced {synced_lists} lists and {synced_tasks} tasks from Google for user {user_id}")

        return JSONResponse(content={
            "success": True,
            "synced_lists": synced_lists,
            "synced_tasks": synced_tasks,
            "message": f"Synced {synced_lists} lists and {synced_tasks} new tasks from Google"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error syncing from Google Tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/tasks/sync/status")
async def get_sync_status(request: Request):
    """Get Google Tasks sync status."""
    user_id = get_user_id(request)

    try:
        service = await get_google_tasks_service(user_id)
        google_connected = service is not None

        with engine.connect() as conn:
            # Get sync-enabled lists count
            result = conn.execute(
                text("""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN sync_enabled THEN 1 ELSE 0 END) as synced
                    FROM task_lists WHERE user_id = :user_id
                """),
                {"user_id": user_id}
            )
            row = result.fetchone()

            return JSONResponse(content={
                "google_connected": google_connected,
                "total_lists": row.total or 0,
                "synced_lists": row.synced or 0
            })

    except Exception as e:
        logger.error(f"❌ Error getting sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/tasks/sync/google")
async def disconnect_google_tasks(request: Request):
    """
    Remove all Google-synced tasks and lists from local database.
    Called when user toggles OFF Google Tasks sync.
    Note: This does NOT delete tasks from Google - only removes local copies.
    """
    user_id = get_user_id(request)

    try:
        with engine.connect() as conn:
            # Delete Google tasks first (FK constraint - tasks reference task_lists)
            tasks_result = conn.execute(
                text("DELETE FROM tasks WHERE source = 'google' AND user_id = :user_id"),
                {"user_id": user_id}
            )
            deleted_tasks = tasks_result.rowcount

            # Then delete Google task lists
            lists_result = conn.execute(
                text("DELETE FROM task_lists WHERE source = 'google' AND user_id = :user_id"),
                {"user_id": user_id}
            )
            deleted_lists = lists_result.rowcount

            conn.commit()

            logger.info(f"✅ Disconnected Google Tasks for user {user_id}: removed {deleted_lists} lists and {deleted_tasks} tasks")

            return JSONResponse(content={
                "success": True,
                "deleted_lists": deleted_lists,
                "deleted_tasks": deleted_tasks,
                "message": f"Removed {deleted_lists} Google lists and {deleted_tasks} Google tasks from local database"
            })

    except Exception as e:
        logger.error(f"❌ Error disconnecting Google Tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
