"""
CKC Learning Rooms System
=========================

Hvert system har sit eget læringsrum identificeret med navn og nummer.

Features:
    - Isolerede læringsmiljøer per system
    - Visual status (blå/grøn/gul/rød)
    - Input sanitering før data når læringsrum
    - Validerings flow integration
    - Historik og evolution tracking

Flow: Observeret Læringsrum -> Kommandør -> Chat -> Bruger -> tilbage til læringsrum
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import uuid
import asyncio
import hashlib
from collections import defaultdict

from cirkelline.config import logger


class RoomStatus(Enum):
    """
    Visual status for læringsrum.

    Farver:
        BLUE: Alt er godt - stabilt og valideret
        GREEN: Aktivt og funktionelt - i brug
        YELLOW: Advarsel eller mindre problem
        RED: Kritisk fejl eller sikkerhedsproblem
    """
    BLUE = "blue"      # Alt er godt
    GREEN = "green"    # Aktivt og funktionelt
    YELLOW = "yellow"  # Advarsel
    RED = "red"        # Kritisk


class ValidationState(Enum):
    """Tilstande i validerings flowet."""
    PENDING = "pending"
    IN_LEARNING_ROOM = "in_learning_room"
    AT_COMMANDER = "at_commander"
    IN_CHAT = "in_chat"
    AWAITING_USER = "awaiting_user"
    RETURNING = "returning"
    VALIDATED = "validated"
    REJECTED = "rejected"


@dataclass
class LearningEvent:
    """En hændelse i et læringsrum."""
    id: str
    event_type: str
    content: Any
    source: str
    timestamp: datetime
    validated: bool = False
    integrity_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def compute_hash(self) -> str:
        """Beregn integritetshash for hændelsen."""
        content_str = str(self.content) + str(self.timestamp) + self.event_type
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]


@dataclass
class ValidationFlowItem:
    """Et element i validerings flowet."""
    id: str
    content: Any
    source_room: str
    state: ValidationState
    created_at: datetime
    updated_at: datetime
    commander_notes: Optional[str] = None
    user_response: Optional[str] = None
    validation_result: Optional[bool] = None
    history: List[Dict[str, Any]] = field(default_factory=list)

    def advance_state(self, new_state: ValidationState, notes: str = "") -> None:
        """Avancer til næste state i flowet."""
        self.history.append({
            "from_state": self.state.value,
            "to_state": new_state.value,
            "timestamp": datetime.utcnow().isoformat(),
            "notes": notes
        })
        self.state = new_state
        self.updated_at = datetime.utcnow()


@dataclass
class LearningRoom:
    """
    Et dedikeret læringsrum for et system/agent.

    Hvert læringsrum er isoleret og har:
    - Unik identifikation (nummer + navn)
    - Visual status
    - Egen eventlog
    - Integritetskontrol
    - Forbindelse til validerings flow

    Attributes:
        room_id: Unikt nummer for rummet
        name: Navn på systemet/agenten
        owner: Bruger der ejer rummet
        status: Visual status (blå/grøn/gul/rød)
        events: Liste af hændelser
        active_validations: Aktive validerings flows
        integrity_verified: Om rummet er verificeret
    """
    room_id: int
    name: str
    owner: str
    description: str = ""
    status: RoomStatus = RoomStatus.BLUE
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    events: List[LearningEvent] = field(default_factory=list)
    active_validations: Dict[str, ValidationFlowItem] = field(default_factory=dict)
    integrity_verified: bool = True
    last_integrity_check: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Statistik
    total_events: int = 0
    validated_events: int = 0
    rejected_events: int = 0
    warnings_count: int = 0
    critical_count: int = 0

    @property
    def full_name(self) -> str:
        """Fuldt navn med nummer og ejer."""
        return f"#{self.room_id} {self.name} ({self.owner})"

    @property
    def status_color(self) -> str:
        """CSS farve for status."""
        colors = {
            RoomStatus.BLUE: "#3498db",
            RoomStatus.GREEN: "#2ecc71",
            RoomStatus.YELLOW: "#f1c40f",
            RoomStatus.RED: "#e74c3c"
        }
        return colors.get(self.status, "#95a5a6")

    def add_event(self, event: LearningEvent) -> None:
        """Tilføj en hændelse til rummet."""
        event.integrity_hash = event.compute_hash()
        self.events.append(event)
        self.total_events += 1
        self.updated_at = datetime.utcnow()

        # Opdater status baseret på event type
        if "error" in event.event_type.lower():
            self.warnings_count += 1
            if self.status != RoomStatus.RED:
                self.status = RoomStatus.YELLOW
        elif "critical" in event.event_type.lower():
            self.critical_count += 1
            self.status = RoomStatus.RED

    def start_validation(self, content: Any, source: str) -> ValidationFlowItem:
        """Start et validerings flow for indhold."""
        flow_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow()

        item = ValidationFlowItem(
            id=flow_id,
            content=content,
            source_room=self.full_name,
            state=ValidationState.IN_LEARNING_ROOM,
            created_at=now,
            updated_at=now
        )

        self.active_validations[flow_id] = item
        self.status = RoomStatus.GREEN  # Aktivt

        logger.info(f"Validation started in {self.full_name}: {flow_id}")
        return item

    def complete_validation(self, flow_id: str, approved: bool, notes: str = "") -> bool:
        """Fuldfør et validerings flow."""
        if flow_id not in self.active_validations:
            return False

        item = self.active_validations[flow_id]
        item.validation_result = approved
        item.advance_state(
            ValidationState.VALIDATED if approved else ValidationState.REJECTED,
            notes
        )

        if approved:
            self.validated_events += 1
        else:
            self.rejected_events += 1

        # Opdater status
        if self.critical_count == 0 and self.warnings_count == 0:
            self.status = RoomStatus.BLUE

        logger.info(f"Validation completed in {self.full_name}: {flow_id} -> {'approved' if approved else 'rejected'}")
        return True

    def verify_integrity(self) -> bool:
        """Verificer integriteten af alle hændelser."""
        for event in self.events:
            computed = event.compute_hash()
            if event.integrity_hash and event.integrity_hash != computed:
                self.integrity_verified = False
                self.status = RoomStatus.RED
                logger.error(f"Integrity violation in {self.full_name}: event {event.id}")
                return False

        self.integrity_verified = True
        self.last_integrity_check = datetime.utcnow()
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Konverter til dictionary."""
        return {
            "room_id": self.room_id,
            "name": self.name,
            "full_name": self.full_name,
            "owner": self.owner,
            "description": self.description,
            "status": self.status.value,
            "status_color": self.status_color,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "total_events": self.total_events,
            "validated_events": self.validated_events,
            "rejected_events": self.rejected_events,
            "active_validations": len(self.active_validations),
            "integrity_verified": self.integrity_verified,
            "warnings_count": self.warnings_count,
            "critical_count": self.critical_count
        }


class LearningRoomManager:
    """
    Manager for alle læringsrum i CKC.

    Håndterer:
    - Oprettelse og forvaltning af rum
    - Global status oversigt
    - Akut notifikation system
    - Integritetskontrol på tværs af rum
    """

    def __init__(self):
        self._rooms: Dict[int, LearningRoom] = {}
        self._rooms_by_name: Dict[str, int] = {}
        self._next_room_id: int = 1
        self._lock = asyncio.Lock()
        self._observers: List[Callable] = []
        self._acute_notifications: List[Dict[str, Any]] = []

    async def create_room(
        self,
        name: str,
        owner: str,
        description: str = ""
    ) -> LearningRoom:
        """
        Opret et nyt læringsrum.

        Args:
            name: Navn på systemet/agenten
            owner: Bruger der ejer rummet
            description: Beskrivelse

        Returns:
            Det oprettede LearningRoom
        """
        async with self._lock:
            room_id = self._next_room_id
            self._next_room_id += 1

            room = LearningRoom(
                room_id=room_id,
                name=name,
                owner=owner,
                description=description
            )

            self._rooms[room_id] = room
            self._rooms_by_name[name.lower()] = room_id

            logger.info(f"Learning room created: {room.full_name}")
            await self._notify_observers("room_created", room)

            return room

    async def get_room(self, room_id: int) -> Optional[LearningRoom]:
        """Hent et læringsrum efter ID."""
        return self._rooms.get(room_id)

    async def get_room_by_name(self, name: str) -> Optional[LearningRoom]:
        """Hent et læringsrum efter navn."""
        room_id = self._rooms_by_name.get(name.lower())
        if room_id:
            return self._rooms.get(room_id)
        return None

    async def list_rooms(self, owner: Optional[str] = None) -> List[LearningRoom]:
        """List alle læringsrum, eventuelt filtreret efter ejer."""
        rooms = list(self._rooms.values())
        if owner:
            rooms = [r for r in rooms if r.owner == owner]
        return sorted(rooms, key=lambda r: r.room_id)

    async def get_status_overview(self) -> Dict[str, Any]:
        """
        Hent samlet status oversigt for alle rum.

        Returns:
            Dict med status counts og eventuelle akutte notifikationer
        """
        status_counts = defaultdict(int)
        critical_rooms = []
        warning_rooms = []

        for room in self._rooms.values():
            status_counts[room.status.value] += 1

            if room.status == RoomStatus.RED:
                critical_rooms.append(room.to_dict())
            elif room.status == RoomStatus.YELLOW:
                warning_rooms.append(room.to_dict())

        return {
            "total_rooms": len(self._rooms),
            "status_counts": dict(status_counts),
            "critical_rooms": critical_rooms,
            "warning_rooms": warning_rooms,
            "has_acute": len(critical_rooms) > 0,
            "acute_notifications": self._acute_notifications[-10:],  # Seneste 10
            "timestamp": datetime.utcnow().isoformat()
        }

    async def get_acute_notifications_page(self) -> Dict[str, Any]:
        """
        Hent data til den akutte notifikationsside.

        Viser alle rum med rød/gul status.
        """
        acute_rooms = []

        for room in self._rooms.values():
            if room.status in [RoomStatus.RED, RoomStatus.YELLOW]:
                room_data = room.to_dict()
                room_data["recent_events"] = [
                    {
                        "id": e.id,
                        "type": e.event_type,
                        "timestamp": e.timestamp.isoformat(),
                        "validated": e.validated
                    }
                    for e in room.events[-5:]  # Seneste 5 events
                ]
                acute_rooms.append(room_data)

        return {
            "acute_rooms": sorted(acute_rooms, key=lambda r: (
                0 if r["status"] == "red" else 1,  # Rød først
                r["room_id"]
            )),
            "total_acute": len(acute_rooms),
            "notifications": self._acute_notifications,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def add_acute_notification(
        self,
        room_id: int,
        message: str,
        severity: str = "warning"
    ) -> None:
        """Tilføj en akut notifikation."""
        notification = {
            "id": str(uuid.uuid4())[:8],
            "room_id": room_id,
            "message": message,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "acknowledged": False
        }
        self._acute_notifications.append(notification)
        await self._notify_observers("acute_notification", notification)

    async def verify_all_integrity(self) -> Dict[str, Any]:
        """Verificer integriteten af alle læringsrum."""
        results = {
            "verified": [],
            "failed": [],
            "timestamp": datetime.utcnow().isoformat()
        }

        for room in self._rooms.values():
            if room.verify_integrity():
                results["verified"].append(room.room_id)
            else:
                results["failed"].append(room.room_id)
                await self.add_acute_notification(
                    room.room_id,
                    f"Integrity verification failed for {room.full_name}",
                    "critical"
                )

        return results

    def add_observer(self, callback: Callable) -> None:
        """Tilføj en observer for rum-events."""
        self._observers.append(callback)

    async def _notify_observers(self, event_type: str, data: Any) -> None:
        """Notificer alle observers."""
        for observer in self._observers:
            try:
                if asyncio.iscoroutinefunction(observer):
                    await observer(event_type, data)
                else:
                    observer(event_type, data)
            except Exception as e:
                logger.error(f"Observer notification failed: {e}")


# ═══════════════════════════════════════════════════════════════
# SINGLETON & CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

_manager: Optional[LearningRoomManager] = None


def get_room_manager() -> LearningRoomManager:
    """Hent singleton LearningRoomManager."""
    global _manager
    if _manager is None:
        _manager = LearningRoomManager()
    return _manager


async def create_learning_room(
    name: str,
    owner: str,
    description: str = ""
) -> LearningRoom:
    """Convenience function til at oprette læringsrum."""
    return await get_room_manager().create_room(name, owner, description)


async def get_learning_room(room_id: int) -> Optional[LearningRoom]:
    """Convenience function til at hente læringsrum."""
    return await get_room_manager().get_room(room_id)


async def get_learning_room_by_name(name: str) -> Optional[LearningRoom]:
    """Convenience function til at hente læringsrum efter navn."""
    return await get_room_manager().get_room_by_name(name)


# ═══════════════════════════════════════════════════════════════
# DEFAULT LEARNING ROOMS INITIALIZATION
# ═══════════════════════════════════════════════════════════════

async def initialize_default_rooms(owner: str = "system") -> Dict[str, LearningRoom]:
    """
    Initialiser standard læringsrum for CKC systemet.

    Args:
        owner: Ejeren af rummene

    Returns:
        Dict med alle oprettede rum
    """
    manager = get_room_manager()

    default_rooms = [
        ("CKC Orchestrator", "Central kommandant og orkestrator"),
        ("Tool Explorer", "Værktøjsopdagelse og integration"),
        ("Creative Synthesizer", "Kreativ indholdsproduktion"),
        ("Knowledge Architect", "Videnopbygning og læring"),
        ("Virtual World Builder", "Virtuel miljøkonstruktion"),
        ("Quality Assurance", "Kvalitetssikring og fejlsøgning"),
        ("Historiker Kommandant", "Historisk videnbevaring"),
        ("Bibliotekar Kommandant", "Videnorganisering og katalogisering"),
        ("Security Monitor", "Sikkerhedsovervågning"),
        ("Input Sanitizer", "Input validering og sanitering"),
    ]

    rooms = {}
    for name, description in default_rooms:
        room = await manager.create_room(name, owner, description)
        rooms[name.lower().replace(" ", "_")] = room

    logger.info(f"Initialized {len(rooms)} default learning rooms for CKC")
    return rooms


logger.info("CKC Learning Rooms module loaded")


# ═══════════════════════════════════════════════════════════════
# SPECIALIZED MONITORS (Memory Evolution, etc.)
# ═══════════════════════════════════════════════════════════════

# Import specialized monitors for re-export
try:
    from .monitors.memory_evolution_room import (
        MemoryEvolutionRoom,
        get_memory_evolution_room,
        start_memory_evolution_room,
        RoomStatus as MemoryRoomStatus,
        SyncFrequency,
        EvolutionSnapshot,
        TestSchedule,
    )
    _HAS_MEMORY_EVOLUTION = True
    logger.info("Memory Evolution Room loaded from monitors/")
except ImportError as e:
    _HAS_MEMORY_EVOLUTION = False
    logger.warning(f"Memory Evolution Room not available: {e}")
