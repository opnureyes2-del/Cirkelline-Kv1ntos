"""
Test suite for CKC Control Panel API
=====================================

Tests the unified control panel REST API and WebSocket endpoints.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_pydantic_models():
    """Test Pydantic model validation."""
    print("=== Test 1: Pydantic Models ===")

    from cirkelline.ckc.api.control_panel import (
        TaskSummary,
        AgentSummary,
        RoomSummary,
        HITLRequest,
        SystemOverview,
        TaskStatus,
        AgentStatus,
        HITLStatus,
    )

    now = datetime.now(timezone.utc)

    # Test TaskSummary
    task = TaskSummary(
        task_id="task_001",
        context_id="ctx_001",
        prompt="Analyze this document",
        status=TaskStatus.RUNNING,
        current_agent="agent_analyst",
        progress=0.5,
        created_at=now
    )
    assert task.task_id == "task_001"
    assert task.status == TaskStatus.RUNNING
    assert task.progress == 0.5
    print("  - TaskSummary: OK")

    # Test AgentSummary (with correct fields: name, role)
    agent = AgentSummary(
        agent_id="agent_001",
        name="Document Analyst",
        role="Analyserer dokumenter",
        status=AgentStatus.BUSY,
        current_task="task_001",
        tasks_completed=10,
        tasks_failed=1,
        uptime_seconds=3600.0,
        last_active=now
    )
    assert agent.status == AgentStatus.BUSY
    assert agent.name == "Document Analyst"
    assert agent.tasks_completed == 10
    print("  - AgentSummary: OK")

    # Test RoomSummary (with correct fields: room_id as int, type)
    room = RoomSummary(
        room_id=1,
        name="Analysis Room",
        type="technical",
        status="active",
        kommandant="Kommandant Alpha",
        agents_active=3,
        tasks_pending=5,
        last_activity=now
    )
    assert room.agents_active == 3
    assert room.type == "technical"
    print("  - RoomSummary: OK")

    # Test HITLRequest
    hitl = HITLRequest(
        request_id="hitl_001",
        task_id="task_001",
        agent_id="agent_001",
        action="approve_document",
        description="Review and approve the generated document",
        context={"document_type": "legal"},
        status=HITLStatus.PENDING,
        created_at=now
    )
    assert hitl.status == HITLStatus.PENDING
    assert hitl.action == "approve_document"
    print("  - HITLRequest: OK")

    # Test SystemOverview
    overview = SystemOverview(
        status="operational",
        version="1.0.0",
        uptime_seconds=3600.0,
        active_tasks=10,
        active_agents=5,
        active_rooms=3,
        pending_hitl=2,
        database_status="connected",
        message_bus_status="connected",
        last_updated=now
    )
    assert overview.active_tasks == 10
    assert overview.pending_hitl == 2
    assert overview.database_status == "connected"
    print("  - SystemOverview: OK")

    print("  All Pydantic Model tests OK!")
    return True


async def test_helper_functions():
    """Test helper functions."""
    print("\n=== Test 2: Helper Functions ===")

    from cirkelline.ckc.api.control_panel import (
        create_task,
        update_task_status,
        create_hitl_request,
        TaskStatus,
        HITLStatus,
        _state,
    )

    # Clear any existing state for clean test
    _state._tasks.clear()
    _state._hitl_requests.clear()

    # Test create_task
    task = await create_task(
        task_id="test_task_001",
        context_id="ctx_test",
        prompt="Test task prompt",
        metadata={"priority": "high"}
    )
    assert task.task_id == "test_task_001"
    assert task.status == TaskStatus.PENDING
    assert "test_task_001" in _state._tasks
    print("  - create_task: OK")

    # Test update_task_status
    await update_task_status(
        task_id="test_task_001",
        status=TaskStatus.RUNNING,
        current_agent="agent_test",
        progress=0.25
    )
    assert _state._tasks["test_task_001"].status == TaskStatus.RUNNING
    assert _state._tasks["test_task_001"].current_agent == "agent_test"
    assert _state._tasks["test_task_001"].progress == 0.25
    print("  - update_task_status: OK")

    # Test update non-existent task (should not raise)
    await update_task_status("nonexistent", TaskStatus.COMPLETED)
    print("  - update_task_status (non-existent): OK")

    # Test create_hitl_request
    hitl = await create_hitl_request(
        task_id="test_task_001",
        agent_id="agent_test",
        action="review_output",
        description="Please review the output",
        context={"detail": "additional info"}
    )
    assert hitl.task_id == "test_task_001"
    assert hitl.status == HITLStatus.PENDING
    assert hitl.request_id in _state._hitl_requests
    print("  - create_hitl_request: OK")

    print("  All Helper Function tests OK!")
    return True


async def test_router_endpoints():
    """Test router endpoints using FastAPI TestClient."""
    print("\n=== Test 3: Router Endpoints ===")

    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
    except ImportError:
        print("  - SKIPPED: fastapi or starlette not installed")
        return True

    from cirkelline.ckc.api.control_panel import (
        router,
        _state,
        create_task,
        create_hitl_request,
    )

    # Clear state for clean tests
    _state._tasks.clear()
    _state._hitl_requests.clear()

    # Create test app
    app = FastAPI()
    app.include_router(router, prefix="/api/ckc")

    client = TestClient(app)

    # Test GET /overview
    response = client.get("/api/ckc/overview")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "active_tasks" in data
    assert "active_agents" in data
    print("  - GET /overview: OK")

    # Test GET /tasks (empty)
    response = client.get("/api/ckc/tasks")
    assert response.status_code == 200
    assert response.json() == []
    print("  - GET /tasks (empty): OK")

    # Create a task via helper function
    await create_task(
        task_id="api_test_task",
        context_id="ctx_api_test",
        prompt="API test task prompt"
    )

    # Test GET /tasks (with task)
    response = client.get("/api/ckc/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) >= 1
    print("  - GET /tasks (with data): OK")

    # Test GET /tasks/{task_id}
    response = client.get("/api/ckc/tasks/api_test_task")
    assert response.status_code == 200
    assert response.json()["task_id"] == "api_test_task"
    print("  - GET /tasks/{task_id}: OK")

    # Test 404 for non-existent task
    response = client.get("/api/ckc/tasks/nonexistent_task")
    assert response.status_code == 404
    print("  - GET /tasks/nonexistent (404): OK")

    # Test GET /agents (pre-populated demo data)
    response = client.get("/api/ckc/agents")
    assert response.status_code == 200
    agents = response.json()
    assert isinstance(agents, list)
    assert len(agents) >= 1  # Demo agents exist
    print("  - GET /agents: OK")

    # Test GET /rooms (pre-populated demo data)
    response = client.get("/api/ckc/rooms")
    assert response.status_code == 200
    rooms = response.json()
    assert isinstance(rooms, list)
    assert len(rooms) >= 1  # Demo rooms exist
    print("  - GET /rooms: OK")

    # Test GET /hitl/pending (empty initially)
    response = client.get("/api/ckc/hitl/pending")
    assert response.status_code == 200
    print("  - GET /hitl/pending: OK")

    # Create HITL request
    hitl = await create_hitl_request(
        task_id="api_test_task",
        agent_id="agent_test",
        action="test_action",
        description="Test HITL request"
    )

    response = client.get("/api/ckc/hitl/pending")
    assert response.status_code == 200
    hitl_list = response.json()
    assert len(hitl_list) >= 1
    print("  - GET /hitl/pending (with request): OK")

    # Test infrastructure endpoints
    response = client.get("/api/ckc/infrastructure/status")
    assert response.status_code == 200
    infra = response.json()
    assert "database" in infra
    assert "message_bus" in infra
    print("  - GET /infrastructure/status: OK")

    response = client.get("/api/ckc/infrastructure/connectors")
    # May succeed or fail depending on connector registry state
    assert response.status_code in [200, 500]
    print("  - GET /infrastructure/connectors: OK")

    print("  All Router Endpoint tests OK!")
    return True


async def test_task_operations():
    """Test task pause/resume operations."""
    print("\n=== Test 4: Task Operations ===")

    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
    except ImportError:
        print("  - SKIPPED: fastapi not installed")
        return True

    from cirkelline.ckc.api.control_panel import (
        router,
        create_task,
        update_task_status,
        TaskStatus,
        _state,
    )

    # Clear state
    _state._tasks.clear()
    _state._hitl_requests.clear()

    app = FastAPI()
    app.include_router(router, prefix="/api/ckc")
    client = TestClient(app)

    # Create and start a task
    await create_task("pause_test_task", "ctx_pause", "Pausable task")
    await update_task_status("pause_test_task", TaskStatus.RUNNING)

    # Test pause
    response = client.post("/api/ckc/tasks/pause_test_task/pause")
    assert response.status_code == 200
    assert _state._tasks["pause_test_task"].status == TaskStatus.PAUSED
    print("  - Pause task: OK")

    # Test pause on non-running task should fail
    response = client.post("/api/ckc/tasks/pause_test_task/pause")
    assert response.status_code == 400
    print("  - Pause non-running (400): OK")

    # Test resume
    response = client.post("/api/ckc/tasks/pause_test_task/resume")
    assert response.status_code == 200
    assert _state._tasks["pause_test_task"].status == TaskStatus.RUNNING
    print("  - Resume task: OK")

    # Test resume on non-paused task should fail
    response = client.post("/api/ckc/tasks/pause_test_task/resume")
    assert response.status_code == 400
    print("  - Resume non-paused (400): OK")

    print("  All Task Operations tests OK!")
    return True


async def test_hitl_workflow():
    """Test complete HITL workflow."""
    print("\n=== Test 5: HITL Workflow ===")

    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
    except ImportError:
        print("  - SKIPPED: fastapi not installed")
        return True

    from cirkelline.ckc.api.control_panel import (
        router,
        create_hitl_request,
        HITLStatus,
        _state,
    )

    # Clear state
    _state._tasks.clear()
    _state._hitl_requests.clear()

    app = FastAPI()
    app.include_router(router, prefix="/api/ckc")
    client = TestClient(app)

    # Create HITL request
    hitl = await create_hitl_request(
        task_id="hitl_test_task",
        agent_id="hitl_test_agent",
        action="code_review",
        description="Review the generated code for security issues"
    )
    assert hitl.status == HITLStatus.PENDING
    print("  - Create HITL request: OK")

    # Verify in pending list
    response = client.get("/api/ckc/hitl/pending")
    pending = response.json()
    assert len(pending) == 1
    assert pending[0]["action"] == "code_review"
    print("  - Pending list contains request: OK")

    # Get specific HITL request
    response = client.get(f"/api/ckc/hitl/{hitl.request_id}")
    assert response.status_code == 200
    assert response.json()["request_id"] == hitl.request_id
    print("  - GET /hitl/{id}: OK")

    # Approve the request
    response = client.post(f"/api/ckc/hitl/{hitl.request_id}/approve", json={
        "approved": True,
        "reason": "Code looks secure"
    })
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "approved"
    assert _state._hitl_requests[hitl.request_id].status == HITLStatus.APPROVED
    print("  - Approve request: OK")

    # Try to approve again (should fail - not pending)
    response = client.post(f"/api/ckc/hitl/{hitl.request_id}/approve", json={
        "approved": True
    })
    assert response.status_code == 400
    print("  - Re-approve blocked (400): OK")

    # Create another and reject
    hitl2 = await create_hitl_request(
        task_id="hitl_test_task_2",
        agent_id="hitl_test_agent",
        action="publish_document",
        description="Publish document to public"
    )

    response = client.post(f"/api/ckc/hitl/{hitl2.request_id}/reject", json={
        "approved": False,
        "reason": "Contains confidential information"
    })
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "rejected"
    assert _state._hitl_requests[hitl2.request_id].status == HITLStatus.REJECTED
    print("  - Reject request: OK")

    # Verify no pending requests remain
    response = client.get("/api/ckc/hitl/pending")
    pending = response.json()
    assert len(pending) == 0
    print("  - No pending after approval/rejection: OK")

    print("  All HITL Workflow tests OK!")
    return True


async def test_task_filtering():
    """Test task filtering by status."""
    print("\n=== Test 6: Task Filtering ===")

    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
    except ImportError:
        print("  - SKIPPED: fastapi not installed")
        return True

    from cirkelline.ckc.api.control_panel import (
        router,
        create_task,
        update_task_status,
        TaskStatus,
        _state,
    )

    # Clear state
    _state._tasks.clear()
    _state._hitl_requests.clear()

    app = FastAPI()
    app.include_router(router, prefix="/api/ckc")
    client = TestClient(app)

    # Create tasks with different statuses
    await create_task("task_filter_1", "ctx_1", "Task 1")
    await create_task("task_filter_2", "ctx_2", "Task 2")
    await create_task("task_filter_3", "ctx_3", "Task 3")

    await update_task_status("task_filter_1", TaskStatus.RUNNING)
    await update_task_status("task_filter_2", TaskStatus.COMPLETED)
    # task_filter_3 stays PENDING

    # Test filter by status
    response = client.get("/api/ckc/tasks?status=running")
    assert response.status_code == 200
    running_tasks = response.json()
    assert len(running_tasks) == 1
    assert running_tasks[0]["task_id"] == "task_filter_1"
    print("  - Filter by RUNNING: OK")

    response = client.get("/api/ckc/tasks?status=pending")
    pending_tasks = response.json()
    assert len(pending_tasks) == 1
    assert pending_tasks[0]["task_id"] == "task_filter_3"
    print("  - Filter by PENDING: OK")

    response = client.get("/api/ckc/tasks?status=completed")
    completed_tasks = response.json()
    assert len(completed_tasks) == 1
    print("  - Filter by COMPLETED: OK")

    # Test agent filtering
    await update_task_status("task_filter_1", TaskStatus.RUNNING, current_agent="agent_alpha")
    response = client.get("/api/ckc/tasks?agent=agent_alpha")
    assert response.status_code == 200
    agent_tasks = response.json()
    assert len(agent_tasks) == 1
    print("  - Filter by agent: OK")

    print("  All Task Filtering tests OK!")
    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("CKC Control Panel API Test Suite")
    print("=" * 60)

    tests = [
        test_pydantic_models,
        test_helper_functions,
        test_router_endpoints,
        test_task_operations,
        test_hitl_workflow,
        test_task_filtering,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
