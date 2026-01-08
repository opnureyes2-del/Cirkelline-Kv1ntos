#!/usr/bin/env python3
"""
Master Orchestrator - ELLE.md System Coordinator
=================================================

PHASE 2 - Database Integration: Master Orchestrator
Central coordinator for all ELLE.md system events and agents

Features:
- Subscribes to all event bus events
- Routes events to appropriate agents
- Manages agent lifecycle (start/stop/restart)
- Coordinates cross-system operations
- Load balancing across agents
- Failure detection and recovery

Events Handled:
- file.* (file.changed, file.created, file.deleted)
- database.* (database.updated, database.connected, database.migrated)
- agent.* (agent.started, agent.stopped, agent.error)
- cache.* (cache.invalidated, cache.cleared)
- documentation.* (documentation.generated, documentation.updated)
"""

import asyncio
import asyncpg
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime, timezone
from pathlib import Path
import sys

# Import event bus
from event_bus import EventBus


class AgentType(Enum):
    """Agent classification for routing"""
    INFRASTRUCTURE = "infrastructure"
    PROJECT = "project"
    GOVERNANCE = "governance"
    RESEARCH = "research"
    SPECIALIST = "specialist"


class AgentStatus(Enum):
    """Agent lifecycle states"""
    STARTING = "starting"
    RUNNING = "running"
    IDLE = "idle"
    BUSY = "busy"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class Task:
    """Orchestrator task"""
    def __init__(self, task_id: str, task_type: str, data: dict, priority: int = 5):
        self.task_id = task_id
        self.task_type = task_type
        self.data = data
        self.priority = priority
        self.assigned_to: Optional[str] = None
        self.status = "pending"
        self.result: Optional[dict] = None
        self.created_at = datetime.now(timezone.utc)


class Agent:
    """Agent representation"""
    def __init__(self, agent_id: str, agent_type: AgentType, project: Optional[str] = None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.project = project
        self.status = AgentStatus.STOPPED
        self.current_load = 0
        self.max_load = 10
        self.capabilities: List[str] = []

    async def start(self):
        """Start agent"""
        self.status = AgentStatus.STARTING
        # Implementation would start actual agent process
        self.status = AgentStatus.RUNNING
        print(f"✅ Started {self.agent_id}")

    async def stop(self):
        """Stop agent"""
        self.status = AgentStatus.STOPPING
        # Implementation would stop actual agent process
        self.status = AgentStatus.STOPPED
        print(f"⏹ Stopped {self.agent_id}")

    async def restart(self):
        """Restart agent"""
        await self.stop()
        await self.start()

    async def execute(self, task: Task) -> dict:
        """Execute task"""
        self.status = AgentStatus.BUSY
        self.current_load += 1

        try:
            # Implementation would execute actual task
            result = {
                'task_id': task.task_id,
                'status': 'completed',
                'agent': self.agent_id
            }
            return result
        finally:
            self.current_load -= 1
            if self.current_load == 0:
                self.status = AgentStatus.IDLE


class MasterOrchestrator:
    """
    Central coordinator for ELLE.md ecosystem

    Responsibilities:
    - Subscribe to all events via RabbitMQ
    - Route events to appropriate agents
    - Manage agent lifecycle
    - Handle failures and recovery
    - Load balancing
    """

    def __init__(self):
        self.event_bus: Optional[EventBus] = None
        self.db_conn: Optional[asyncpg.Connection] = None
        self.agents: Dict[str, Agent] = {}
        self.task_queue = asyncio.PriorityQueue()
        self.running_tasks: Dict[str, Task] = {}
        self.event_handlers: Dict[str, callable] = {}

        # Setup event handlers
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Map event types to handler functions"""
        self.event_handlers = {
            'file.changed': self._handle_file_changed,
            'file.created': self._handle_file_created,
            'file.deleted': self._handle_file_deleted,
            'database.updated': self._handle_database_updated,
            'database.connected': self._handle_database_connected,
            'database.migrated': self._handle_database_migrated,
            'agent.started': self._handle_agent_started,
            'agent.stopped': self._handle_agent_stopped,
            'agent.error': self._handle_agent_error,
            'cache.invalidated': self._handle_cache_invalidated,
            'cache.cleared': self._handle_cache_cleared,
            'documentation.generated': self._handle_documentation_generated,
            'documentation.updated': self._handle_documentation_updated,
        }

    async def connect_database(self):
        """Connect to agent logging database"""
        try:
            self.db_conn = await asyncpg.connect(
                host='localhost',
                port=5432,
                user='agent_user',
                password='agent_secure_2025',
                database='agents'
            )
            print("✅ Master Orchestrator: Connected to agent database")
            await self._log_event("system_startup", "Master Orchestrator started", "info")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise

    async def _log_event(self, event_type: str, description: str,
                        severity: str = "info", metadata: dict = None):
        """Log event to database"""
        if not self.db_conn:
            return

        try:
            import json
            await self.db_conn.execute("""
                INSERT INTO agent_logs (
                    agent_name, event_type, description, severity, metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """,
                'master_orchestrator',
                event_type,
                description,
                severity,
                json.dumps(metadata or {}),
                datetime.now(timezone.utc)
            )
        except Exception as e:
            print(f"LOG ERROR: {e}")

    async def connect_event_bus(self):
        """Connect to RabbitMQ event bus"""
        try:
            self.event_bus = EventBus()
            await self.event_bus.connect_logger_db()
            self.event_bus.connect()

            # Subscribe to all events
            self.event_bus.subscribe('#', self._on_event, queue_name='master_orchestrator')

            print("✅ Master Orchestrator: Subscribed to all events")
            await self._log_event("event_bus_connected",
                                 "Subscribed to all event patterns",
                                 "info")
        except Exception as e:
            print(f"❌ Event bus connection failed: {e}")
            raise

    def _on_event(self, message: dict):
        """
        Event callback - routes all events
        Called synchronously by pika, must not block
        """
        routing_key = message.get('_routing_key', 'unknown')

        # Route to appropriate handler
        handler = self.event_handlers.get(routing_key)
        if handler:
            # Schedule async handler
            asyncio.create_task(handler(message))
        else:
            # Unknown event type
            asyncio.create_task(self._handle_unknown_event(routing_key, message))

    # Event Handlers

    async def _handle_file_changed(self, message: dict):
        """Handle file change event"""
        file_path = message.get('file_path', 'unknown')
        affected_dbs = message.get('affected_databases', [])

        print(f"📄 File changed: {file_path}")
        print(f"   Affected databases: {affected_dbs}")

        await self._log_event(
            "file_change_detected",
            f"File changed: {file_path}",
            "info",
            {'file_path': file_path, 'affected_databases': affected_dbs}
        )

        # Route to knowledge sync if databases affected
        if affected_dbs:
            await self._trigger_knowledge_sync(file_path, affected_dbs)

        # Invalidate cache
        if self.event_bus:
            from event_bus import publish_cache_invalidated
            await publish_cache_invalidated(
                self.event_bus,
                cache_key=f"file:{file_path}",
                reason='file_changed'
            )

    async def _handle_file_created(self, message: dict):
        """Handle file creation event"""
        file_path = message.get('file_path', 'unknown')
        print(f"📄 File created: {file_path}")

        await self._log_event(
            "file_created",
            f"File created: {file_path}",
            "info",
            {'file_path': file_path}
        )

    async def _handle_file_deleted(self, message: dict):
        """Handle file deletion event"""
        file_path = message.get('file_path', 'unknown')
        print(f"📄 File deleted: {file_path}")

        await self._log_event(
            "file_deleted",
            f"File deleted: {file_path}",
            "info",
            {'file_path': file_path}
        )

    async def _handle_database_updated(self, message: dict):
        """Handle database update event"""
        database = message.get('database', 'unknown')
        table = message.get('table', 'unknown')
        operation = message.get('operation', 'unknown')

        print(f"🗄️ Database updated: {database}.{table} ({operation})")

        await self._log_event(
            "database_updated",
            f"Database {database}.{table} updated via {operation}",
            "info",
            {'database': database, 'table': table, 'operation': operation}
        )

    async def _handle_database_connected(self, message: dict):
        """Handle database connection event"""
        database = message.get('database', 'unknown')
        print(f"🗄️ Database connected: {database}")

        await self._log_event(
            "database_connected",
            f"Database connected: {database}",
            "info",
            {'database': database}
        )

    async def _handle_database_migrated(self, message: dict):
        """Handle database migration event"""
        database = message.get('database', 'unknown')
        version = message.get('version', 'unknown')

        print(f"🗄️ Database migrated: {database} to version {version}")

        await self._log_event(
            "database_migrated",
            f"Database {database} migrated to version {version}",
            "info",
            {'database': database, 'version': version}
        )

    async def _handle_agent_started(self, message: dict):
        """Handle agent start event"""
        agent_name = message.get('agent_name', 'unknown')
        details = message.get('details', {})

        print(f"🤖 Agent started: {agent_name}")

        await self._log_event(
            "agent_started",
            f"Agent started: {agent_name}",
            "info",
            {'agent_name': agent_name, 'details': details}
        )

    async def _handle_agent_stopped(self, message: dict):
        """Handle agent stop event"""
        agent_name = message.get('agent_name', 'unknown')
        details = message.get('details', {})

        print(f"🤖 Agent stopped: {agent_name}")

        await self._log_event(
            "agent_stopped",
            f"Agent stopped: {agent_name}",
            "info",
            {'agent_name': agent_name, 'details': details}
        )

    async def _handle_agent_error(self, message: dict):
        """Handle agent error event"""
        agent_name = message.get('agent_name', 'unknown')
        details = message.get('details', {})
        error = details.get('error', 'unknown')

        print(f"🤖 Agent error: {agent_name} - {error}")

        await self._log_event(
            "agent_error",
            f"Agent error: {agent_name}",
            "error",
            {'agent_name': agent_name, 'error': error, 'details': details}
        )

        # Attempt recovery
        await self._handle_agent_failure(agent_name)

    async def _handle_cache_invalidated(self, message: dict):
        """Handle cache invalidation event"""
        cache_key = message.get('cache_key', 'unknown')
        reason = message.get('reason', 'unknown')

        print(f"💾 Cache invalidated: {cache_key} (reason: {reason})")

        await self._log_event(
            "cache_invalidated",
            f"Cache invalidated: {cache_key}",
            "info",
            {'cache_key': cache_key, 'reason': reason}
        )

    async def _handle_cache_cleared(self, message: dict):
        """Handle cache clear event"""
        print(f"💾 Cache cleared")

        await self._log_event(
            "cache_cleared",
            "Cache completely cleared",
            "info",
            {}
        )

    async def _handle_documentation_generated(self, message: dict):
        """Handle documentation generation event"""
        project = message.get('project', 'unknown')
        files_count = message.get('files_count', 0)

        print(f"📚 Documentation generated: {project} ({files_count} files)")

        await self._log_event(
            "documentation_generated",
            f"Documentation generated for {project}",
            "info",
            {'project': project, 'files_count': files_count}
        )

    async def _handle_documentation_updated(self, message: dict):
        """Handle documentation update event"""
        project = message.get('project', 'unknown')

        print(f"📚 Documentation updated: {project}")

        await self._log_event(
            "documentation_updated",
            f"Documentation updated for {project}",
            "info",
            {'project': project}
        )

    async def _handle_unknown_event(self, routing_key: str, message: dict):
        """Handle unknown event types"""
        print(f"⚠️ Unknown event: {routing_key}")

        await self._log_event(
            "unknown_event",
            f"Unknown event type: {routing_key}",
            "warning",
            {'routing_key': routing_key, 'message': message}
        )

    # Agent Management

    async def register_agent(self, agent: Agent):
        """Register agent with orchestrator"""
        self.agents[agent.agent_id] = agent
        await agent.start()

        print(f"✅ Registered {agent.agent_id} ({agent.agent_type.value})")

        await self._log_event(
            "agent_registered",
            f"Agent registered: {agent.agent_id}",
            "info",
            {'agent_id': agent.agent_id, 'agent_type': agent.agent_type.value}
        )

    async def route_task(self, task: Task) -> dict:
        """Route task to appropriate agent"""
        suitable_agents = self._find_suitable_agents(task)

        if not suitable_agents:
            raise ValueError(f"No agents available for task: {task.task_type}")

        # Select least loaded agent
        best_agent = min(suitable_agents, key=lambda a: a.current_load)

        # Assign task
        task.assigned_to = best_agent.agent_id
        task.status = "in_progress"
        self.running_tasks[task.task_id] = task

        await self._log_event(
            "task_routed",
            f"Task {task.task_id} routed to {best_agent.agent_id}",
            "info",
            {'task_id': task.task_id, 'agent': best_agent.agent_id}
        )

        # Execute
        result = await best_agent.execute(task)

        # Update
        task.status = "completed"
        task.result = result
        del self.running_tasks[task.task_id]

        return result

    def _find_suitable_agents(self, task: Task) -> List[Agent]:
        """Find agents capable of handling task"""
        if task.task_type == "project_query":
            project = task.data.get('project')
            return [a for a in self.agents.values()
                    if a.agent_type == AgentType.PROJECT and a.project == project]

        elif task.task_type == "cross_project_query":
            return [a for a in self.agents.values()
                    if a.agent_type == AgentType.PROJECT]

        elif task.task_type == "web_research":
            return [a for a in self.agents.values()
                    if a.agent_type == AgentType.RESEARCH]

        else:
            return [a for a in self.agents.values()
                    if a.agent_type == AgentType.GOVERNANCE]

    async def _handle_agent_failure(self, agent_id: str):
        """Handle agent failure gracefully"""
        failed_agent = self.agents.get(agent_id)
        if not failed_agent:
            return

        # Find affected tasks
        affected_tasks = [t for t in self.running_tasks.values()
                         if t.assigned_to == agent_id]

        print(f"⚠️ Agent {agent_id} failed with {len(affected_tasks)} running tasks")

        # Reassign tasks
        for task in affected_tasks:
            print(f"⚠️ Reassigning {task.task_id} from failed agent")
            task.assigned_to = None
            task.status = "pending"
            await self.task_queue.put((task.priority, task))

        # Try to restart agent
        try:
            await failed_agent.restart()
            print(f"✅ Restarted {agent_id}")

            await self._log_event(
                "agent_restarted",
                f"Agent restarted after failure: {agent_id}",
                "info",
                {'agent_id': agent_id}
            )
        except Exception as e:
            print(f"❌ Failed to restart {agent_id}: {e}")
            failed_agent.status = AgentStatus.ERROR

            await self._log_event(
                "agent_restart_failed",
                f"Failed to restart agent: {agent_id}",
                "error",
                {'agent_id': agent_id, 'error': str(e)}
            )

    async def _trigger_knowledge_sync(self, file_path: str, affected_databases: List[str]):
        """Trigger knowledge base synchronization"""
        print(f"🔄 Triggering knowledge sync for {file_path}")

        # This would coordinate knowledge_sync_system.py
        # For now, just log the intent
        await self._log_event(
            "knowledge_sync_triggered",
            f"Knowledge sync triggered for {file_path}",
            "info",
            {'file_path': file_path, 'databases': affected_databases}
        )

    async def start(self):
        """Start orchestrator"""
        print("=" * 70)
        print("MASTER ORCHESTRATOR STARTING")
        print("=" * 70)
        print()

        # Connect to database
        await self.connect_database()

        # Connect to event bus
        await self.connect_event_bus()

        print()
        print("✅ Master Orchestrator ready")
        print("   Listening for events on RabbitMQ...")
        print()

        # Start consuming events (blocking)
        self.event_bus.start_consuming()

    async def stop(self):
        """Stop orchestrator"""
        print()
        print("⏹ Stopping Master Orchestrator...")

        # Stop all agents
        for agent in self.agents.values():
            await agent.stop()

        # Close event bus
        if self.event_bus:
            await self.event_bus.close()

        # Close database
        if self.db_conn:
            await self.db_conn.close()

        await self._log_event(
            "system_shutdown",
            "Master Orchestrator stopped",
            "info"
        )

        print("✅ Master Orchestrator stopped")


async def main():
    """Run Master Orchestrator"""
    orchestrator = MasterOrchestrator()

    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        print("\n⏹ Shutdown signal received")
        await orchestrator.stop()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        await orchestrator.stop()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
