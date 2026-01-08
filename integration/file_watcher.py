#!/usr/bin/env python3
"""
File Watcher Agent
==================

PHASE 2 - Database Integration: Automatic File Change Detection
Watches INTRO and ELLE directories for changes and publishes events

Features:
- inotify-based file watching
- Recursive directory monitoring
- Debouncing (avoid duplicate events)
- File filter (only .md files)
- Event publishing to RabbitMQ
"""

import asyncio
import asyncpg
from pathlib import Path
from datetime import datetime, timezone
import json
import time
from typing import Set, Dict

try:
    import inotify.adapters
    import inotify.constants
    INOTIFY_AVAILABLE = True
except ImportError:
    INOTIFY_AVAILABLE = False
    print("⚠️ inotify not available - using polling fallback")

from event_bus import EventBus, publish_file_changed


class FileWatcher:
    """
    Watches file system for changes and publishes events

    Monitors:
    - /INTRO/*.md (all markdown files)
    - /ELLE.md/*.md (all markdown files)

    Publishes:
    - file.changed
    - file.created
    - file.deleted
    """

    def __init__(self):
        self.event_bus: Optional[EventBus] = None
        self.agent_db: Optional[asyncpg.Connection] = None

        # Paths to watch
        self.intro_path = Path("/home/rasmus/Desktop/projekts/status opdaterings rapport/INTRO")
        self.elle_path = Path("/home/rasmus/Desktop/ELLE.md")

        # Debouncing (avoid duplicate events within 1 second)
        self.last_events: Dict[str, float] = {}
        self.debounce_seconds = 1.0

        # Processing tracking
        self.files_watched = 0
        self.events_published = 0

    async def connect_database(self):
        """Connect to agent logging database"""
        try:
            self.agent_db = await asyncpg.connect(
                host='localhost',
                port=5432,
                user='agent_user',
                password='agent_secure_2025',
                database='agents'
            )
            print("✅ File Watcher: Connected to agent database")
            await self._log_event("system_startup", "File Watcher started", "info")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            raise

    async def _log_event(self, event_type: str, description: str,
                        severity: str = "info", metadata: dict = None):
        """Log event to database"""
        if not self.agent_db:
            return

        try:
            await self.agent_db.execute("""
                INSERT INTO agent_logs (
                    agent_name, event_type, description, severity, metadata, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """,
                'file_watcher',
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

            print("✅ File Watcher: Connected to event bus")
            await self._log_event(
                "event_bus_connected",
                "Connected to RabbitMQ",
                "info"
            )
        except Exception as e:
            print(f"❌ Event bus connection failed: {e}")
            raise

    def _should_watch_file(self, file_path: str) -> bool:
        """Determine if file should be watched"""
        # Only watch .md files
        if not file_path.endswith('.md'):
            return False

        # Skip hidden files
        if '/.git/' in file_path or '/.' in file_path.split('/')[-1]:
            return False

        # Skip node_modules, .venv, etc.
        skip_dirs = ['node_modules', '.venv', 'venv', '__pycache__', 'dist', 'build']
        for skip_dir in skip_dirs:
            if f'/{skip_dir}/' in file_path:
                return False

        return True

    def _should_publish_event(self, file_path: str) -> bool:
        """Check if event should be published (debouncing)"""
        now = time.time()
        last_event_time = self.last_events.get(file_path, 0)

        if now - last_event_time < self.debounce_seconds:
            # Too soon, skip
            return False

        # Update last event time
        self.last_events[file_path] = now
        return True

    def _determine_affected_databases(self, file_path: str) -> list:
        """Determine which databases are affected by file change"""
        affected = []

        # Files in INTRO affect intro_kb
        if '/INTRO/' in file_path:
            affected.append('intro_kb')

        # Files in ELLE affect elle_kb
        if '/ELLE.md/' in file_path:
            affected.append('elle_kb')

        # Shared files affect both
        if any(keyword in file_path for keyword in ['AGENTS.md', 'TEMPLATE', 'ELLERULES']):
            if 'intro_kb' not in affected:
                affected.append('intro_kb')
            if 'elle_kb' not in affected:
                affected.append('elle_kb')

        return affected

    async def _publish_file_event(self, event_type: str, file_path: str):
        """Publish file event to event bus"""
        if not self._should_publish_event(file_path):
            return

        affected_dbs = self._determine_affected_databases(file_path)

        if self.event_bus:
            await publish_file_changed(
                self.event_bus,
                file_path=file_path,
                affected_databases=affected_dbs
            )

            self.events_published += 1

            print(f"📄 {event_type}: {file_path}")
            print(f"   Affected DBs: {affected_dbs}")

            await self._log_event(
                f"file_{event_type}",
                f"File {event_type}: {file_path}",
                "info",
                {'file_path': file_path, 'affected_databases': affected_dbs}
            )

    async def watch_with_inotify(self):
        """Watch files using inotify (Linux only)"""
        print(f"👁️ Watching directories with inotify:")
        print(f"   - {self.intro_path}")
        print(f"   - {self.elle_path}")
        print()

        # Create inotify watchers
        intro_watcher = inotify.adapters.InotifyTree(str(self.intro_path))
        elle_watcher = inotify.adapters.InotifyTree(str(self.elle_path))

        while True:
            # Watch INTRO
            for event in intro_watcher.event_gen(yield_nones=False, timeout_s=0.1):
                (_, type_names, path, filename) = event
                file_path = Path(path) / filename
                file_str = str(file_path)

                if not self._should_watch_file(file_str):
                    continue

                if 'IN_MODIFY' in type_names or 'IN_CLOSE_WRITE' in type_names:
                    await self._publish_file_event('changed', file_str)
                elif 'IN_CREATE' in type_names:
                    await self._publish_file_event('created', file_str)
                elif 'IN_DELETE' in type_names:
                    await self._publish_file_event('deleted', file_str)

            # Watch ELLE
            for event in elle_watcher.event_gen(yield_nones=False, timeout_s=0.1):
                (_, type_names, path, filename) = event
                file_path = Path(path) / filename
                file_str = str(file_path)

                if not self._should_watch_file(file_str):
                    continue

                if 'IN_MODIFY' in type_names or 'IN_CLOSE_WRITE' in type_names:
                    await self._publish_file_event('changed', file_str)
                elif 'IN_CREATE' in type_names:
                    await self._publish_file_event('created', file_str)
                elif 'IN_DELETE' in type_names:
                    await self._publish_file_event('deleted', file_str)

            # Small sleep to avoid busy loop
            await asyncio.sleep(0.1)

    async def watch_with_polling(self):
        """Fallback: Watch files using polling (slower but portable)"""
        print(f"👁️ Watching directories with polling (fallback):")
        print(f"   - {self.intro_path}")
        print(f"   - {self.elle_path}")
        print()

        # Track file modification times
        file_mtimes: Dict[str, float] = {}

        while True:
            # Scan INTRO
            for file_path in self.intro_path.rglob("*.md"):
                file_str = str(file_path)

                if not self._should_watch_file(file_str):
                    continue

                try:
                    mtime = file_path.stat().st_mtime

                    if file_str not in file_mtimes:
                        # New file
                        file_mtimes[file_str] = mtime
                        await self._publish_file_event('created', file_str)
                    elif file_mtimes[file_str] < mtime:
                        # File modified
                        file_mtimes[file_str] = mtime
                        await self._publish_file_event('changed', file_str)
                except FileNotFoundError:
                    # File deleted
                    if file_str in file_mtimes:
                        del file_mtimes[file_str]
                        await self._publish_file_event('deleted', file_str)

            # Scan ELLE
            for file_path in self.elle_path.rglob("*.md"):
                file_str = str(file_path)

                if not self._should_watch_file(file_str):
                    continue

                try:
                    mtime = file_path.stat().st_mtime

                    if file_str not in file_mtimes:
                        file_mtimes[file_str] = mtime
                        await self._publish_file_event('created', file_str)
                    elif file_mtimes[file_str] < mtime:
                        file_mtimes[file_str] = mtime
                        await self._publish_file_event('changed', file_str)
                except FileNotFoundError:
                    if file_str in file_mtimes:
                        del file_mtimes[file_str]
                        await self._publish_file_event('deleted', file_str)

            # Poll every 2 seconds
            await asyncio.sleep(2)

    async def start(self):
        """Start file watcher"""
        print("=" * 70)
        print("FILE WATCHER STARTING")
        print("=" * 70)
        print()

        # Connect to database
        await self.connect_database()

        # Connect to event bus
        await self.connect_event_bus()

        print()
        print("✅ File Watcher ready")
        print()

        # Start watching (use inotify if available, otherwise polling)
        if INOTIFY_AVAILABLE:
            await self.watch_with_inotify()
        else:
            await self.watch_with_polling()

    async def stop(self):
        """Stop file watcher"""
        print()
        print(f"⏹ Stopping File Watcher...")
        print(f"   Events published: {self.events_published}")

        # Close event bus
        if self.event_bus:
            await self.event_bus.close()

        # Close database
        if self.agent_db:
            await self.agent_db.close()

        print("✅ File Watcher stopped")


async def main():
    """Run file watcher"""
    watcher = FileWatcher()

    try:
        await watcher.start()
    except KeyboardInterrupt:
        print("\n⏹ Shutdown signal received")
        await watcher.stop()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        await watcher.stop()


if __name__ == '__main__':
    asyncio.run(main())
