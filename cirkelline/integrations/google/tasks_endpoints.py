"""
Google Tasks Integration Endpoints
===================================
Handles Google Tasks operations (task lists and tasks CRUD, complete, move).
"""

from fastapi import APIRouter, Request, HTTPException

from cirkelline.config import logger
from cirkelline.integrations.google.google_oauth import get_user_google_credentials

# Create router
router = APIRouter()

# ═══════════════════════════════════════════════════════════════
# TASK LIST OPERATIONS
# ═══════════════════════════════════════════════════════════════

@router.get("/api/google/tasks/lists")
async def get_task_lists(request: Request):
    """Get all Google Task lists for the authenticated user"""
    try:
        user_id = getattr(request.state, 'user_id', None)

        # v1.3.4: Require authentication - no anonymous access
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        # Get Google credentials
        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=401, detail="Google account not connected. Please connect your Google account first.")

        # Build Tasks service
        from googleapiclient.discovery import build
        service = build('tasks', 'v1', credentials=google_creds)

        # List all task lists (max 100 - Google API limit is usually enough for most users)
        results = service.tasklists().list(maxResults=100).execute()
        items = results.get('items', [])

        logger.info(f"Retrieved {len(items)} task lists for user {user_id}")

        return {
            "success": True,
            "task_lists": items,
            "count": len(items)
        }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Get task lists error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to retrieve task lists: {str(e)}")

logger.info("✅ Google get task lists endpoint configured")

@router.get("/api/google/tasks/lists/{list_id}")
async def get_task_list(list_id: str, request: Request):
    """Get a specific Google Task list by ID"""
    try:
        user_id = getattr(request.state, 'user_id', None)

        # v1.3.4: Require authentication - no anonymous access
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=401, detail="Google account not connected")

        from googleapiclient.discovery import build
        service = build('tasks', 'v1', credentials=google_creds)
        result = service.tasklists().get(tasklist=list_id).execute()

        return {"success": True, "task_list": result}

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Get task list error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve task list: {str(e)}")

logger.info("✅ Google get task list endpoint configured")

@router.post("/api/google/tasks/lists")
async def create_task_list(request: Request):
    """Create a new Google Task list"""
    try:
        user_id = getattr(request.state, 'user_id', None)

        # v1.3.4: Require authentication - no anonymous access
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        body = await request.json()
        title = body.get('title')

        if not title:
            raise HTTPException(status_code=400, detail="Task list title is required")

        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=401, detail="Google account not connected")

        from googleapiclient.discovery import build
        service = build('tasks', 'v1', credentials=google_creds)
        task_list = {'title': title}
        result = service.tasklists().insert(body=task_list).execute()

        logger.info(f"Created task list '{title}' for user {user_id}")
        return {"success": True, "task_list": result}

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Create task list error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create task list: {str(e)}")

logger.info("✅ Google create task list endpoint configured")

@router.put("/api/google/tasks/lists/{list_id}")
async def update_task_list(list_id: str, request: Request):
    """Update a Google Task list (rename)"""
    try:
        user_id = getattr(request.state, 'user_id', None)

        # v1.3.4: Require authentication - no anonymous access
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        body = await request.json()
        title = body.get('title')

        if not title:
            raise HTTPException(status_code=400, detail="Task list title is required")

        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=401, detail="Google account not connected")

        from googleapiclient.discovery import build
        service = build('tasks', 'v1', credentials=google_creds)
        task_list = {'id': list_id, 'title': title}
        result = service.tasklists().update(tasklist=list_id, body=task_list).execute()

        logger.info(f"Updated task list {list_id} for user {user_id}")
        return {"success": True, "task_list": result}

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Update task list error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update task list: {str(e)}")

logger.info("✅ Google update task list endpoint configured")

@router.delete("/api/google/tasks/lists/{list_id}")
async def delete_task_list(list_id: str, request: Request):
    """Delete a Google Task list"""
    try:
        user_id = getattr(request.state, 'user_id', None)

        # v1.3.4: Require authentication - no anonymous access
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=401, detail="Google account not connected")

        from googleapiclient.discovery import build
        service = build('tasks', 'v1', credentials=google_creds)
        service.tasklists().delete(tasklist=list_id).execute()

        logger.info(f"Deleted task list {list_id} for user {user_id}")
        return {"success": True, "message": "Task list deleted successfully"}

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Delete task list error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete task list: {str(e)}")

logger.info("✅ Google delete task list endpoint configured")

# ═══════════════════════════════════════════════════════════════
# TASK OPERATIONS
# ═══════════════════════════════════════════════════════════════

@router.get("/api/google/tasks/lists/{list_id}/tasks")
async def get_tasks(list_id: str, request: Request, show_completed: bool = False, show_deleted: bool = False):
    """Get all tasks in a specific task list"""
    try:
        user_id = getattr(request.state, 'user_id', None)

        # v1.3.4: Require authentication - no anonymous access
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=401, detail="Google account not connected")

        from googleapiclient.discovery import build
        service = build('tasks', 'v1', credentials=google_creds)
        results = service.tasks().list(
            tasklist=list_id,
            showCompleted=show_completed,
            showDeleted=show_deleted,
            maxResults=100
        ).execute()

        items = results.get('items', [])
        logger.info(f"Retrieved {len(items)} tasks from list {list_id} for user {user_id}")

        return {
            "success": True,
            "tasks": items,
            "count": len(items)
        }

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Get tasks error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tasks: {str(e)}")

logger.info("✅ Google get tasks endpoint configured")

@router.get("/api/google/tasks/lists/{list_id}/tasks/{task_id}")
async def get_task(list_id: str, task_id: str, request: Request):
    """Get a specific task by ID"""
    try:
        user_id = getattr(request.state, 'user_id', None)

        # v1.3.4: Require authentication - no anonymous access
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=401, detail="Google account not connected")

        from googleapiclient.discovery import build
        service = build('tasks', 'v1', credentials=google_creds)
        result = service.tasks().get(tasklist=list_id, task=task_id).execute()

        return {"success": True, "task": result}

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Get task error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve task: {str(e)}")

logger.info("✅ Google get task endpoint configured")

@router.post("/api/google/tasks/lists/{list_id}/tasks")
async def create_task(list_id: str, request: Request):
    """Create a new task in a task list"""
    try:
        user_id = getattr(request.state, 'user_id', None)

        # v1.3.4: Require authentication - no anonymous access
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        body = await request.json()
        title = body.get('title')

        if not title:
            raise HTTPException(status_code=400, detail="Task title is required")

        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=401, detail="Google account not connected")

        # Build task object
        task = {'title': title}

        # Optional fields
        if body.get('notes'):
            task['notes'] = body.get('notes')
        if body.get('due'):
            task['due'] = body.get('due')
        if body.get('parent'):
            task['parent'] = body.get('parent')

        from googleapiclient.discovery import build
        service = build('tasks', 'v1', credentials=google_creds)
        result = service.tasks().insert(tasklist=list_id, body=task).execute()

        logger.info(f"Created task '{title}' in list {list_id} for user {user_id}")
        return {"success": True, "task": result}

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Create task error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

logger.info("✅ Google create task endpoint configured")

@router.put("/api/google/tasks/lists/{list_id}/tasks/{task_id}")
async def update_task(list_id: str, task_id: str, request: Request):
    """Update a task"""
    try:
        user_id = getattr(request.state, 'user_id', None)

        # v1.3.4: Require authentication - no anonymous access
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        body = await request.json()

        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=401, detail="Google account not connected")

        # Get current task
        from googleapiclient.discovery import build
        service = build('tasks', 'v1', credentials=google_creds)
        current_task = service.tasks().get(tasklist=list_id, task=task_id).execute()

        # Update fields
        if 'title' in body:
            current_task['title'] = body['title']
        if 'notes' in body:
            current_task['notes'] = body['notes']
        if 'due' in body:
            current_task['due'] = body['due']
        if 'status' in body:
            current_task['status'] = body['status']

        # Update task
        result = service.tasks().update(tasklist=list_id, task=task_id, body=current_task).execute()

        logger.info(f"Updated task {task_id} in list {list_id} for user {user_id}")
        return {"success": True, "task": result}

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Update task error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")

logger.info("✅ Google update task endpoint configured")

@router.delete("/api/google/tasks/lists/{list_id}/tasks/{task_id}")
async def delete_task(list_id: str, task_id: str, request: Request):
    """Delete a task"""
    try:
        user_id = getattr(request.state, 'user_id', None)

        # v1.3.4: Require authentication - no anonymous access
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=401, detail="Google account not connected")

        from googleapiclient.discovery import build
        service = build('tasks', 'v1', credentials=google_creds)
        service.tasks().delete(tasklist=list_id, task=task_id).execute()

        logger.info(f"Deleted task {task_id} from list {list_id} for user {user_id}")
        return {"success": True, "message": "Task deleted successfully"}

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Delete task error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")

logger.info("✅ Google delete task endpoint configured")

@router.post("/api/google/tasks/lists/{list_id}/tasks/{task_id}/complete")
async def toggle_task_complete(list_id: str, task_id: str, request: Request):
    """Toggle task completion status"""
    try:
        user_id = getattr(request.state, 'user_id', None)

        # v1.3.4: Require authentication - no anonymous access
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        body = await request.json()
        completed = body.get('completed', True)

        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=401, detail="Google account not connected")

        from googleapiclient.discovery import build
        service = build('tasks', 'v1', credentials=google_creds)

        # Get current task
        task = service.tasks().get(tasklist=list_id, task=task_id).execute()

        # Update status
        from datetime import datetime, timezone
        if completed:
            task['status'] = 'completed'
            task['completed'] = datetime.now(timezone.utc).isoformat()
        else:
            task['status'] = 'needsAction'
            if 'completed' in task:
                del task['completed']

        # Update task
        result = service.tasks().update(tasklist=list_id, task=task_id, body=task).execute()

        status_text = "completed" if completed else "uncompleted"
        logger.info(f"Marked task {task_id} as {status_text} for user {user_id}")
        return {"success": True, "task": result}

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Toggle task complete error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update task status: {str(e)}")

logger.info("✅ Google toggle task complete endpoint configured")

@router.post("/api/google/tasks/lists/{list_id}/tasks/{task_id}/move")
async def move_task(list_id: str, task_id: str, request: Request):
    """Move task to different position or parent"""
    try:
        user_id = getattr(request.state, 'user_id', None)

        # v1.3.4: Require authentication - no anonymous access
        if not user_id or user_id == 'anonymous' or user_id.startswith('anon-'):
            raise HTTPException(status_code=401, detail="Authentication required")

        body = await request.json()
        parent = body.get('parent')
        previous = body.get('previous')

        google_creds = await get_user_google_credentials(user_id)
        if not google_creds:
            raise HTTPException(status_code=401, detail="Google account not connected")

        from googleapiclient.discovery import build
        service = build('tasks', 'v1', credentials=google_creds)

        # Build move parameters
        move_params = {'tasklist': list_id, 'task': task_id}
        if parent:
            move_params['parent'] = parent
        if previous:
            move_params['previous'] = previous

        result = service.tasks().move(**move_params).execute()

        logger.info(f"Moved task {task_id} in list {list_id} for user {user_id}")
        return {"success": True, "task": result}

    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"Move task error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to move task: {str(e)}")

logger.info("✅ Google move task endpoint configured")


logger.info("✅ Google Tasks integration endpoints loaded")
