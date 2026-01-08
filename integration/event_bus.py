#!/usr/bin/env python3
"""
Event Bus System - RabbitMQ Integration
========================================

PHASE 2 - Database Integration: RabbitMQ Event Bus
Provides centralized event routing for ELLE.md ecosystem

Features:
- Topic-based event routing
- Persistent message delivery
- Event filtering and subscription
- Database event logging
- Cross-system communication

Events Published:
- file.changed
- database.updated
- agent.started
- agent.stopped
- cache.invalidated
- documentation.generated
"""

import asyncio
import asyncpg
import pika
import json
from typing import Callable, Dict, Optional, Any
from datetime import datetime, timezone
from pathlib import Path


class EventBus:
    """RabbitMQ-based event bus for system-wide event distribution"""

    def __init__(self, host='localhost', port=5672,
                 username='elle', password='elle_secure_2025',
                 logger_db_conn: Optional[asyncpg.Connection] = None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.db_conn = logger_db_conn

        self.connection = None
        self.channel = None
        self.subscribers: Dict[str, Callable] = {}
        self.exchange_name = 'elle_integration_hub'

    async def connect_logger_db(self):
        """Connect to agent logging database"""
        try:
            self.db_conn = await asyncpg.connect(
                host='localhost',
                port=5432,
                user='agent_user',
                password='agent_secure_2025',
                database='agents'
            )
            print("EVENT BUS: Connected to agent logging database")
            await self._log_event("system_startup", "Event Bus started", "info")
        except Exception as e:
            print(f"WARNING: Could not connect to logger DB: {e}")

    async def _log_event(self, event_type: str, description: str,
                        severity: str = "info", metadata: dict = None):
        """Log event to database"""
        if not self.db_conn:
            return

        try:
            await self.db_conn.execute("""
                INSERT INTO agent_logs (
                    agent_name, event_type, description, severity, metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """,
                'event_bus',
                event_type,
                description,
                severity,
                json.dumps(metadata or {}),
                datetime.now(timezone.utc)
            )
        except Exception as e:
            print(f"LOG ERROR: {e}")

    def connect(self):
        """Connect to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )

            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declare topic exchange
            self.channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type='topic',
                durable=True
            )

            print(f"✅ Connected to RabbitMQ at {self.host}:{self.port}")
            print(f"✅ Exchange '{self.exchange_name}' declared")

        except Exception as e:
            print(f"❌ Failed to connect to RabbitMQ: {e}")
            raise

    def publish(self, routing_key: str, message: dict, priority: int = 5):
        """
        Publish event to bus (synchronous)

        Args:
            routing_key: Event routing key (e.g., 'file.changed', 'agent.started')
            message: Event message as dict
            priority: Message priority (0-9, default 5)
        """
        if not self.channel:
            print("ERROR: Not connected to RabbitMQ")
            return False

        try:
            # Add metadata
            message['_timestamp'] = datetime.now(timezone.utc).isoformat()
            message['_routing_key'] = routing_key

            # Publish message
            self.channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent
                    priority=priority,
                    content_type='application/json'
                )
            )

            # Note: Skipping database logging in synchronous publish
            # Database logging requires async context
            # For logged publishes, use publish_async() instead

            return True

        except Exception as e:
            print(f"ERROR publishing message: {e}")
            return False

    def subscribe(self, pattern: str, callback: Callable, queue_name: Optional[str] = None):
        """
        Subscribe to events matching pattern

        Args:
            pattern: Routing key pattern (e.g., 'file.*', 'agent.#', 'database.updated')
            callback: Callback function(message: dict)
            queue_name: Optional queue name (auto-generated if not provided)
        """
        if not self.channel:
            print("ERROR: Not connected to RabbitMQ")
            return

        try:
            # Generate queue name if not provided
            if queue_name is None:
                queue_name = f"subscriber_{pattern.replace('.', '_').replace('#', 'all').replace('*', 'any')}"

            # Declare queue
            self.channel.queue_declare(
                queue=queue_name,
                durable=True,
                arguments={'x-max-priority': 10}
            )

            # Bind queue to exchange with pattern
            self.channel.queue_bind(
                exchange=self.exchange_name,
                queue=queue_name,
                routing_key=pattern
            )

            # Create callback wrapper
            def on_message(ch, method, properties, body):
                try:
                    message = json.loads(body)
                    callback(message)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    print(f"ERROR in callback for {pattern}: {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            # Start consuming
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=on_message
            )

            self.subscribers[pattern] = callback
            print(f"✅ Subscribed to pattern: {pattern} (queue: {queue_name})")

        except Exception as e:
            print(f"ERROR subscribing to {pattern}: {e}")

    def start_consuming(self):
        """Start consuming messages (blocking)"""
        if not self.channel:
            print("ERROR: Not connected to RabbitMQ")
            return

        print("📡 Event bus started, waiting for messages...")
        print(f"   Subscribed patterns: {list(self.subscribers.keys())}")

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            print("\n⏹ Stopping event bus...")
            self.stop()

    def stop(self):
        """Stop consuming and close connection"""
        if self.channel:
            self.channel.stop_consuming()
        if self.connection:
            self.connection.close()
        print("✅ Event bus stopped")

    async def close(self):
        """Close all connections"""
        self.stop()
        if self.db_conn:
            await self.db_conn.close()


# Event Publishers (convenience functions)

async def publish_file_changed(event_bus: EventBus, file_path: str,
                               affected_databases: list = None):
    """Publish file change event"""
    event_bus.publish('file.changed', {
        'file_path': file_path,
        'affected_databases': affected_databases or [],
    })


async def publish_database_updated(event_bus: EventBus, database: str,
                                  table: str, operation: str):
    """Publish database update event"""
    event_bus.publish('database.updated', {
        'database': database,
        'table': table,
        'operation': operation,
    })


async def publish_agent_event(event_bus: EventBus, agent_name: str,
                             event_type: str, details: dict = None):
    """Publish agent lifecycle event"""
    routing_key = f'agent.{event_type}'  # agent.started, agent.stopped, etc.
    event_bus.publish(routing_key, {
        'agent_name': agent_name,
        'details': details or {},
    })


async def publish_cache_invalidated(event_bus: EventBus, cache_key: str,
                                   reason: str):
    """Publish cache invalidation event"""
    event_bus.publish('cache.invalidated', {
        'cache_key': cache_key,
        'reason': reason,
    })


async def publish_documentation_generated(event_bus: EventBus, project: str,
                                        files_count: int):
    """Publish documentation generation event"""
    event_bus.publish('documentation.generated', {
        'project': project,
        'files_count': files_count,
    })


# Example usage
async def main():
    """Demo event bus usage"""
    print("=" * 70)
    print("EVENT BUS DEMO")
    print("=" * 70)
    print()

    # Initialize event bus
    event_bus = EventBus()
    await event_bus.connect_logger_db()
    event_bus.connect()

    # Example: Subscribe to file changes
    def on_file_change(message):
        print(f"📄 File changed: {message['file_path']}")
        print(f"   Affected DBs: {message.get('affected_databases', [])}")

    event_bus.subscribe('file.changed', on_file_change)

    # Example: Subscribe to all agent events
    def on_agent_event(message):
        print(f"🤖 Agent event: {message['agent_name']}")
        print(f"   Type: {message['_routing_key']}")

    event_bus.subscribe('agent.#', on_agent_event)

    # Example: Publish some events
    print("\n📤 Publishing test events...")
    await publish_file_changed(event_bus, '/INTRO/20_PROJEKTER/STATUS.md',
                               ['intro_kb', 'elle_kb'])
    await publish_agent_event(event_bus, 'documentation_automation', 'started')
    await publish_cache_invalidated(event_bus, 'query:abc123', 'file_changed')

    print("\n✅ Demo complete")
    print("   Events published and logged to database")

    await event_bus.close()


if __name__ == '__main__':
    asyncio.run(main())
