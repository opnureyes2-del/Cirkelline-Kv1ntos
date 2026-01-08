"""
Usage Examples for Unified Integration System
"""

import asyncio
from integration import (
    EventBus,
    UnifiedQueryAPI,
    MultiLayerCache,
    MasterOrchestrator
)


async def example_search():
    """Search across INTRO + ELLE knowledge bases"""
    api = UnifiedQueryAPI()
    await api.connect_databases()

    # Search both databases
    results = await api.search_all("agents", limit=10)

    for result in results:
        print(f"[{result['source']}] {result['file_path']}")
        print(f"  Relevance: {result['relevance']:.3f}")

    await api.stop()


async def example_event_bus():
    """Publish and subscribe to events"""
    bus = EventBus()
    bus.connect()

    # Subscribe to file changes
    def on_file_change(message):
        print(f"File changed: {message['file_path']}")

    bus.subscribe('file.changed', on_file_change, queue_name='my_subscriber')

    # Publish event
    await bus.publish('file.changed', {
        'file_path': '/path/to/file.md',
        'change_type': 'modified'
    })


async def example_caching():
    """Use multi-layer cache"""
    cache = MultiLayerCache()

    # Store in cache
    await cache.set('mykey', {'data': 'value'}, ttl=3600)

    # Retrieve from cache
    value = await cache.get('mykey')
    print(f"Cached value: {value}")


if __name__ == '__main__':
    # Run examples
    asyncio.run(example_search())
