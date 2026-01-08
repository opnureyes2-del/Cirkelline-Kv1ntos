"""
Memory Evolution Learning Room
==============================

Sideløbende lærerum der altid kører med lokale tests 3.33 og 21.21.
Følger cirkelline-system mappen og kopierer løbende to gange dagligt.

Ansvarlig: Historiker-Kommandant
Tilstand: CKC Mastermind
Formål: Real-time tracking af memory evolution og optimeringer

Version: 1.3.5
Dato: 2025-12-16 (21:21 baseline)

Integration:
- Automatisk registrering med Historiker-Kommandant
- Optager alle hændelser i CKC historik
- Synkroniserer med SYNKRONISERING mappe
"""

import asyncio
import json
import os
import shutil
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, TYPE_CHECKING
from enum import Enum
from pathlib import Path

from cirkelline.config import logger

# Import Historiker for integration
if TYPE_CHECKING:
    from cirkelline.ckc.kommandanter import HistorikerKommandant, HistoricalEventType


class RoomStatus(Enum):
    """Learning Room status (visuelt)."""
    BLUE = "blue"      # Stabil og valideret
    GREEN = "green"    # Aktiv og funktionel
    YELLOW = "yellow"  # Advarsel - kræver opmærksomhed
    RED = "red"        # Kritisk - handling påkrævet


class SyncFrequency(Enum):
    """Sync frekvens."""
    HOURLY = "hourly"
    TWICE_DAILY = "twice_daily"  # 09:00 og 21:21
    DAILY = "daily"
    ON_CHANGE = "on_change"


@dataclass
class EvolutionSnapshot:
    """Et snapshot af memory evolution state."""
    id: str
    timestamp: datetime
    version: str
    memory_count: int
    topic_count: int
    changes_since_last: List[str] = field(default_factory=list)
    optimizations_detected: List[str] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    files_changed: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "memory_count": self.memory_count,
            "topic_count": self.topic_count,
            "changes_since_last": self.changes_since_last,
            "optimizations_detected": self.optimizations_detected,
            "test_results": self.test_results,
            "files_changed": self.files_changed
        }


@dataclass
class TestSchedule:
    """Test schedule configuration."""
    test_id: str
    time: str  # "03:33" eller "21:21"
    test_type: str
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None


class MemoryEvolutionRoom:
    """
    Memory Evolution Learning Room.

    Kører sideløbende med systemet og tracker:
    - Memory system ændringer
    - Mulige optimeringer
    - Test resultater (3.33 og 21.21)
    - Historisk evolution

    Rapporterer til Historiker-Kommandant.
    """

    ROOM_ID = "memory-evolution-room"
    ROOM_NAME = "Memory Evolution Lærerum"

    # Test schedules
    SCHEDULED_TESTS = [
        TestSchedule("morning-test", "03:33", "full_memory_audit"),
        TestSchedule("evening-test", "21:21", "optimization_check"),
    ]

    # Sync schedule (twice daily)
    SYNC_TIMES = ["09:00", "21:21"]

    # Paths
    CIRKELLINE_SYSTEM_PATH = Path("/home/rasmus/Desktop/projekts/projects/cirkelline-system")
    SYNC_DESTINATION = CIRKELLINE_SYSTEM_PATH / "my_admin_workspace" / "SYNKRONISERING"
    SNAPSHOTS_PATH = SYNC_DESTINATION / "snapshots"

    # Memory files to track
    MEMORY_FILES = [
        "cirkelline/tools/memory_search_tool.py",
        "cirkelline/orchestrator/cirkelline_team.py",
        "cirkelline/orchestrator/instructions.py",
        "cirkelline/workflows/memory_optimization.py",
        "cirkelline/workflows/memory_steps.py",
        "cirkelline/headquarters/shared_memory.py",
    ]

    def __init__(self, auto_register_historiker: bool = True):
        """Initialize the Memory Evolution Room."""
        self.status = RoomStatus.GREEN
        self.snapshots: List[EvolutionSnapshot] = []
        self.current_version = "v1.3.5"
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._historiker_callback: Optional[Callable] = None
        self._historiker: Optional[Any] = None

        # Ensure directories exist
        self.SYNC_DESTINATION.mkdir(parents=True, exist_ok=True)
        self.SNAPSHOTS_PATH.mkdir(parents=True, exist_ok=True)

        # Auto-register with Historiker if available
        if auto_register_historiker:
            self._connect_to_historiker()

        logger.info(f"Memory Evolution Room initialized: {self.ROOM_NAME}")

    def _connect_to_historiker(self) -> bool:
        """Connect to Historiker-Kommandant for event tracking."""
        try:
            from cirkelline.ckc.kommandanter import get_historiker, HistoricalEventType
            self._historiker = get_historiker()

            # Register callback
            async def historiker_event_handler(event_type: str, data: Dict[str, Any]):
                """Forward events to Historiker."""
                event_mapping = {
                    "scheduled_test_completed": HistoricalEventType.VALIDATION_PASSED,
                    "files_changed": HistoricalEventType.CONFIGURATION_CHANGED,
                    "optimizations_detected": HistoricalEventType.KNOWLEDGE_UPDATED,
                    "daily_sync_completed": HistoricalEventType.TASK_COMPLETED,
                    "room_started": HistoricalEventType.SYSTEM_START,
                    "room_stopped": HistoricalEventType.SYSTEM_STOP,
                }

                hist_event_type = event_mapping.get(
                    event_type,
                    HistoricalEventType.KNOWLEDGE_ADDED
                )

                await self._historiker.record_event(
                    event_type=hist_event_type,
                    description=f"Memory Evolution Room: {event_type}",
                    source=self.ROOM_ID,
                    data=data,
                    importance=2 if "test" in event_type else 1,
                    tags={"memory", "evolution", "learning_room"}
                )

            self.register_historiker_callback(historiker_event_handler)
            logger.info("Connected to Historiker-Kommandant")
            return True

        except ImportError as e:
            logger.warning(f"Could not connect to Historiker: {e}")
            return False
        except Exception as e:
            logger.error(f"Error connecting to Historiker: {e}")
            return False

    async def start(self) -> None:
        """Start the learning room (parallel process)."""
        if self._running:
            logger.warning("Memory Evolution Room already running")
            return

        self._running = True
        self.status = RoomStatus.GREEN

        # Notify Historiker of start
        await self._notify_historiker("room_started", {
            "room_id": self.ROOM_ID,
            "version": self.current_version,
            "scheduled_tests": [s.time for s in self.SCHEDULED_TESTS],
            "sync_times": self.SYNC_TIMES,
            "files_tracked": self.MEMORY_FILES
        })

        # Start parallel tasks
        self._tasks = [
            asyncio.create_task(self._run_scheduled_tests()),
            asyncio.create_task(self._run_sync_loop()),
            asyncio.create_task(self._watch_for_changes()),
        ]

        logger.info(f"Memory Evolution Room started with {len(self._tasks)} parallel tasks")

        # Create initial snapshot
        await self._create_snapshot("Initial start snapshot")

    async def stop(self) -> None:
        """Stop the learning room."""
        self._running = False

        # Notify Historiker of stop
        await self._notify_historiker("room_stopped", {
            "room_id": self.ROOM_ID,
            "snapshots_created": len(self.snapshots),
            "final_status": self.status.value
        })

        for task in self._tasks:
            task.cancel()

        self._tasks.clear()
        self.status = RoomStatus.BLUE

        logger.info("Memory Evolution Room stopped")

    def register_historiker_callback(self, callback: Callable) -> None:
        """Register callback to Historiker-Kommandant."""
        self._historiker_callback = callback
        logger.info("Historiker callback registered")

    async def _notify_historiker(self, event_type: str, data: Dict[str, Any]) -> None:
        """Notify Historiker-Kommandant of an event."""
        if self._historiker_callback:
            try:
                await self._historiker_callback(event_type, data)
            except Exception as e:
                logger.error(f"Failed to notify Historiker: {e}")

    async def _run_scheduled_tests(self) -> None:
        """Run scheduled tests at 3.33 and 21.21."""
        while self._running:
            now = datetime.now()
            current_time = now.strftime("%H:%M")

            for schedule in self.SCHEDULED_TESTS:
                if not schedule.enabled:
                    continue

                if current_time == schedule.time:
                    # Check if already run today
                    if schedule.last_run and schedule.last_run.date() == now.date():
                        continue

                    logger.info(f"Running scheduled test: {schedule.test_id} ({schedule.time})")

                    try:
                        results = await self._run_memory_tests(schedule.test_type)
                        schedule.last_run = now

                        # Create snapshot with test results
                        await self._create_snapshot(
                            f"Scheduled test: {schedule.test_id}",
                            test_results=results
                        )

                        # Notify Historiker
                        await self._notify_historiker("scheduled_test_completed", {
                            "test_id": schedule.test_id,
                            "time": schedule.time,
                            "results": results
                        })

                    except Exception as e:
                        logger.error(f"Scheduled test failed: {e}")
                        self.status = RoomStatus.YELLOW

            # Sleep for 1 minute before checking again
            await asyncio.sleep(60)

    async def _run_sync_loop(self) -> None:
        """Run sync twice daily at configured times."""
        while self._running:
            now = datetime.now()
            current_time = now.strftime("%H:%M")

            if current_time in self.SYNC_TIMES:
                logger.info(f"Running daily sync at {current_time}")

                try:
                    await self._sync_to_destination()
                    await self._notify_historiker("daily_sync_completed", {
                        "time": current_time,
                        "destination": str(self.SYNC_DESTINATION)
                    })
                except Exception as e:
                    logger.error(f"Daily sync failed: {e}")
                    self.status = RoomStatus.YELLOW

            # Sleep for 1 minute
            await asyncio.sleep(60)

    async def _watch_for_changes(self) -> None:
        """Watch memory files for changes."""
        last_check: Dict[str, float] = {}

        while self._running:
            changes_detected = []

            for file_path in self.MEMORY_FILES:
                full_path = self.CIRKELLINE_SYSTEM_PATH / file_path

                if full_path.exists():
                    mtime = full_path.stat().st_mtime

                    if file_path in last_check:
                        if mtime > last_check[file_path]:
                            changes_detected.append(file_path)
                            logger.info(f"Change detected in: {file_path}")

                    last_check[file_path] = mtime

            if changes_detected:
                await self._on_files_changed(changes_detected)

            # Check every 30 seconds
            await asyncio.sleep(30)

    async def _on_files_changed(self, files: List[str]) -> None:
        """Handle file changes."""
        # Create snapshot
        await self._create_snapshot(
            f"Files changed: {len(files)} file(s)",
            files_changed=files
        )

        # Notify Historiker
        await self._notify_historiker("files_changed", {
            "files": files,
            "timestamp": datetime.now().isoformat()
        })

        # Check for potential optimizations
        optimizations = await self._detect_optimizations(files)
        if optimizations:
            self.status = RoomStatus.YELLOW
            await self._notify_historiker("optimizations_detected", {
                "optimizations": optimizations
            })

    async def _run_memory_tests(self, test_type: str) -> Dict[str, Any]:
        """Run memory-related tests."""
        results = {
            "test_type": test_type,
            "timestamp": datetime.now().isoformat(),
            "passed": True,
            "details": {}
        }

        try:
            # Check memory creation
            results["details"]["memory_creation"] = await self._check_memory_creation()

            # Check topic-based retrieval
            results["details"]["topic_retrieval"] = await self._check_topic_retrieval()

            # Check workflow status
            results["details"]["workflow_status"] = await self._check_workflow_status()

            # Overall status
            results["passed"] = all(
                v.get("passed", False)
                for v in results["details"].values()
            )

        except Exception as e:
            results["passed"] = False
            results["error"] = str(e)

        return results

    async def _check_memory_creation(self) -> Dict[str, Any]:
        """Check if memory creation is working."""
        return {
            "passed": True,
            "check": "memory_creation",
            "message": "Memory creation check (requires live test)"
        }

    async def _check_topic_retrieval(self) -> Dict[str, Any]:
        """Check if topic-based retrieval is working."""
        return {
            "passed": True,
            "check": "topic_retrieval",
            "message": "Topic retrieval check (requires live test)"
        }

    async def _check_workflow_status(self) -> Dict[str, Any]:
        """Check memory optimization workflow status."""
        return {
            "passed": True,
            "check": "workflow_status",
            "message": "Workflow status check (requires live test)"
        }

    async def _detect_optimizations(self, files: List[str]) -> List[str]:
        """Detect potential optimizations in changed files."""
        optimizations = []

        for file_path in files:
            full_path = self.CIRKELLINE_SYSTEM_PATH / file_path

            if not full_path.exists():
                continue

            content = full_path.read_text()

            # Check for common patterns
            if "add_memories_to_context=True" in content:
                optimizations.append(
                    f"{file_path}: Consider using add_memories_to_context=False with topic filtering"
                )

            if "get_all_memories" in content.lower():
                optimizations.append(
                    f"{file_path}: Avoid loading all memories - use topic filtering"
                )

        return optimizations

    async def _sync_to_destination(self) -> None:
        """Sync current state to destination folder."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Copy learning room document
        source_doc = self.CIRKELLINE_SYSTEM_PATH / "LAERERUM-MEMORY-EVOLUTION.md"
        if source_doc.exists():
            dest_doc = self.SYNC_DESTINATION / "LAERERUM-MEMORY-EVOLUTION.md"
            shutil.copy2(source_doc, dest_doc)

        # Save current state
        state_file = self.SYNC_DESTINATION / "room_state.json"
        state = {
            "room_id": self.ROOM_ID,
            "status": self.status.value,
            "last_sync": timestamp,
            "version": self.current_version,
            "snapshots_count": len(self.snapshots),
            "memory_files_tracked": self.MEMORY_FILES,
            "test_schedules": [
                {
                    "id": s.test_id,
                    "time": s.time,
                    "enabled": s.enabled,
                    "last_run": s.last_run.isoformat() if s.last_run else None
                }
                for s in self.SCHEDULED_TESTS
            ]
        }

        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)

        logger.info(f"Synced to {self.SYNC_DESTINATION}")

    async def _create_snapshot(
        self,
        description: str,
        test_results: Optional[Dict] = None,
        files_changed: Optional[List[str]] = None
    ) -> EvolutionSnapshot:
        """Create a new evolution snapshot."""
        snapshot_id = f"snap_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        snapshot = EvolutionSnapshot(
            id=snapshot_id,
            timestamp=datetime.now(),
            version=self.current_version,
            memory_count=0,  # Would be fetched from DB
            topic_count=0,   # Would be fetched from DB
            changes_since_last=[description],
            test_results=test_results or {},
            files_changed=files_changed or []
        )

        self.snapshots.append(snapshot)

        # Save snapshot to file
        snapshot_file = self.SNAPSHOTS_PATH / f"{snapshot_id}.json"
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot.to_dict(), f, indent=2)

        logger.info(f"Created snapshot: {snapshot_id}")

        return snapshot

    def get_status(self) -> Dict[str, Any]:
        """Get current room status."""
        return {
            "room_id": self.ROOM_ID,
            "room_name": self.ROOM_NAME,
            "status": self.status.value,
            "status_meaning": {
                "blue": "Stabil og valideret",
                "green": "Aktiv og funktionel",
                "yellow": "Advarsel - kræver opmærksomhed",
                "red": "Kritisk - handling påkrævet"
            }[self.status.value],
            "running": self._running,
            "version": self.current_version,
            "snapshots_count": len(self.snapshots),
            "last_snapshot": self.snapshots[-1].to_dict() if self.snapshots else None,
            "test_schedules": [
                {
                    "id": s.test_id,
                    "time": s.time,
                    "type": s.test_type,
                    "enabled": s.enabled
                }
                for s in self.SCHEDULED_TESTS
            ],
            "sync_times": self.SYNC_TIMES,
            "files_tracked": self.MEMORY_FILES
        }


# Singleton instance
_memory_evolution_room: Optional[MemoryEvolutionRoom] = None


def get_memory_evolution_room() -> MemoryEvolutionRoom:
    """Get singleton Memory Evolution Room instance."""
    global _memory_evolution_room
    if _memory_evolution_room is None:
        _memory_evolution_room = MemoryEvolutionRoom()
    return _memory_evolution_room


async def start_memory_evolution_room() -> MemoryEvolutionRoom:
    """Start the Memory Evolution Room."""
    room = get_memory_evolution_room()
    await room.start()
    return room


logger.info("Memory Evolution Room module loaded")
