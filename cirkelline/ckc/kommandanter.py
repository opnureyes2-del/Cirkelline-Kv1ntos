"""
CKC Kommandanter - Videnforvaltning
===================================

Specialiserede kommandanter til videnforvaltning:

1. Historiker-Kommandant - Temporal tracking og evolution
2. Bibliotekar-Kommandant - Videnorganisering og katalogisering

Disse kommandanter sikrer at CKC's viden er:
- Velorganiseret og let tilgængelig
- Historisk korrekt og sporbar
- Kategoriseret og søgbar
- Bevaret over tid
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import asyncio
import uuid
from collections import defaultdict

from cirkelline.config import logger
from .orchestrator import AgentCapability


class HistoricalEventType(Enum):
    """Typer af historiske hændelser."""
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    AGENT_CREATED = "agent_created"
    AGENT_UPDATED = "agent_updated"
    TASK_COMPLETED = "task_completed"
    VALIDATION_PASSED = "validation_passed"
    VALIDATION_FAILED = "validation_failed"
    USER_INTERVENTION = "user_intervention"
    ERROR_OCCURRED = "error_occurred"
    MILESTONE_REACHED = "milestone_reached"
    KNOWLEDGE_ADDED = "knowledge_added"
    KNOWLEDGE_UPDATED = "knowledge_updated"
    CONFIGURATION_CHANGED = "configuration_changed"


class KnowledgeCategory(Enum):
    """Kategorier for viden."""
    TECHNICAL = "technical"
    BUSINESS = "business"
    CREATIVE = "creative"
    EDUCATIONAL = "educational"
    PROCEDURAL = "procedural"
    REFERENCE = "reference"
    HISTORICAL = "historical"
    OPERATIONAL = "operational"


@dataclass
class HistoricalEvent:
    """En historisk hændelse i systemet."""
    id: str
    event_type: HistoricalEventType
    timestamp: datetime
    description: str
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    importance: int = 1  # 1-5, 5 = most important
    tags: Set[str] = field(default_factory=set)
    related_events: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "source": self.source,
            "data": self.data,
            "importance": self.importance,
            "tags": list(self.tags),
            "related_events": self.related_events
        }


@dataclass
class KnowledgeEntry:
    """En videnindgang i biblioteket."""
    id: str
    title: str
    content: Any
    category: KnowledgeCategory
    created_at: datetime
    updated_at: datetime
    created_by: str
    version: int = 1
    tags: Set[str] = field(default_factory=set)
    references: List[str] = field(default_factory=list)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "version": self.version,
            "tags": list(self.tags),
            "references": self.references,
            "access_count": self.access_count
        }


# ═══════════════════════════════════════════════════════════════
# HISTORIKER-KOMMANDANT
# ═══════════════════════════════════════════════════════════════

class HistorikerKommandant:
    """
    Historiker-Kommandant

    Ansvar:
        - Spore alle systemhændelser
        - Bevare historisk kontekst
        - Analysere trends og mønstre
        - Dokumentere evolution

    Principper:
        - Intet går tabt
        - Alt kan spores
        - Kontekst bevares
        - Læring fra fortiden
    """

    def __init__(self, learning_room_id: int = 7):
        self.kommandant_id = "historiker-kommandant"
        self.name = "Historiker-Kommandant"
        self.description = "Historisk videnbevaring"
        self.learning_room_id = learning_room_id
        self.capabilities = {
            AgentCapability.HISTORY_TRACKING
        }

        # Historisk data
        self._events: Dict[str, HistoricalEvent] = {}
        self._events_by_type: Dict[HistoricalEventType, List[str]] = defaultdict(list)
        self._events_by_source: Dict[str, List[str]] = defaultdict(list)
        self._timeline: List[str] = []  # Event IDs in chronological order

        # Evolution tracking
        self._milestones: List[Dict[str, Any]] = []
        self._trends: Dict[str, List[float]] = defaultdict(list)

        # Statistics
        self._stats = {
            "total_events": 0,
            "events_today": 0,
            "oldest_event": None,
            "newest_event": None
        }

        logger.info(f"Historiker-Kommandant initialized (Room {learning_room_id})")

    async def record_event(
        self,
        event_type: HistoricalEventType,
        description: str,
        source: str,
        data: Optional[Dict[str, Any]] = None,
        importance: int = 1,
        tags: Optional[Set[str]] = None
    ) -> HistoricalEvent:
        """Optag en historisk hændelse."""
        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()

        event = HistoricalEvent(
            id=event_id,
            event_type=event_type,
            timestamp=now,
            description=description,
            source=source,
            data=data or {},
            importance=importance,
            tags=tags or set()
        )

        # Store
        self._events[event_id] = event
        self._events_by_type[event_type].append(event_id)
        self._events_by_source[source].append(event_id)
        self._timeline.append(event_id)

        # Update stats
        self._stats["total_events"] += 1
        if self._stats["oldest_event"] is None:
            self._stats["oldest_event"] = now.isoformat()
        self._stats["newest_event"] = now.isoformat()

        # Check for milestone
        if importance >= 4:
            await self._check_milestone(event)

        logger.debug(f"Historical event recorded: {event_type.value} - {description[:50]}")
        return event

    async def _check_milestone(self, event: HistoricalEvent) -> None:
        """Check om hændelsen udgør en milepæl."""
        milestone = {
            "id": f"ms_{uuid.uuid4().hex[:8]}",
            "event_id": event.id,
            "type": event.event_type.value,
            "description": event.description,
            "timestamp": event.timestamp.isoformat(),
            "importance": event.importance
        }
        self._milestones.append(milestone)
        logger.info(f"Milestone reached: {event.description[:50]}")

    async def get_event(self, event_id: str) -> Optional[HistoricalEvent]:
        """Hent en specifik hændelse."""
        return self._events.get(event_id)

    async def get_timeline(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100
    ) -> List[HistoricalEvent]:
        """Hent tidslinje af hændelser."""
        events = []

        for event_id in reversed(self._timeline):
            event = self._events.get(event_id)
            if not event:
                continue

            if start and event.timestamp < start:
                continue
            if end and event.timestamp > end:
                continue

            events.append(event)
            if len(events) >= limit:
                break

        return events

    async def get_events_by_type(
        self,
        event_type: HistoricalEventType,
        limit: int = 50
    ) -> List[HistoricalEvent]:
        """Hent hændelser af en bestemt type."""
        event_ids = self._events_by_type.get(event_type, [])[-limit:]
        return [self._events[eid] for eid in event_ids if eid in self._events]

    async def get_events_by_source(
        self,
        source: str,
        limit: int = 50
    ) -> List[HistoricalEvent]:
        """Hent hændelser fra en bestemt kilde."""
        event_ids = self._events_by_source.get(source, [])[-limit:]
        return [self._events[eid] for eid in event_ids if eid in self._events]

    async def analyze_trends(
        self,
        event_type: Optional[HistoricalEventType] = None,
        period_days: int = 7
    ) -> Dict[str, Any]:
        """Analyser trends i hændelser."""
        cutoff = datetime.utcnow() - timedelta(days=period_days)

        # Tæl hændelser per dag
        daily_counts: Dict[str, int] = defaultdict(int)

        for event_id in self._timeline:
            event = self._events.get(event_id)
            if not event or event.timestamp < cutoff:
                continue
            if event_type and event.event_type != event_type:
                continue

            day_key = event.timestamp.strftime("%Y-%m-%d")
            daily_counts[day_key] += 1

        return {
            "period_days": period_days,
            "event_type": event_type.value if event_type else "all",
            "daily_counts": dict(daily_counts),
            "total": sum(daily_counts.values()),
            "average_per_day": sum(daily_counts.values()) / max(1, len(daily_counts)),
            "analyzed_at": datetime.utcnow().isoformat()
        }

    async def get_milestones(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Hent milepæle."""
        return self._milestones[-limit:]

    async def get_statistics(self) -> Dict[str, Any]:
        """Hent statistik."""
        return {
            **self._stats,
            "milestones_count": len(self._milestones),
            "unique_sources": len(self._events_by_source),
            "event_types_used": len(self._events_by_type),
            "retrieved_at": datetime.utcnow().isoformat()
        }

    async def search_events(
        self,
        query: str,
        tags: Optional[Set[str]] = None,
        limit: int = 50
    ) -> List[HistoricalEvent]:
        """Søg i historiske hændelser."""
        results = []
        query_lower = query.lower()

        for event_id in reversed(self._timeline):
            event = self._events.get(event_id)
            if not event:
                continue

            # Match query
            if query_lower not in event.description.lower():
                continue

            # Match tags if specified
            if tags and not tags.issubset(event.tags):
                continue

            results.append(event)
            if len(results) >= limit:
                break

        return results


# ═══════════════════════════════════════════════════════════════
# BIBLIOTEKAR-KOMMANDANT
# ═══════════════════════════════════════════════════════════════

class BibliotekarKommandant:
    """
    Bibliotekar-Kommandant

    Ansvar:
        - Organisere al viden
        - Katalogisere indhold
        - Sikre tilgængelighed
        - Vedligeholde referencer

    Principper:
        - Alt skal kunne findes
        - Struktur og orden
        - Versionering
        - Krydsreferencer
    """

    def __init__(self, learning_room_id: int = 8):
        self.kommandant_id = "bibliotekar-kommandant"
        self.name = "Bibliotekar-Kommandant"
        self.description = "Videnorganisering og katalogisering"
        self.learning_room_id = learning_room_id
        self.capabilities = {
            AgentCapability.LIBRARY_MANAGEMENT
        }

        # Bibliotek
        self._entries: Dict[str, KnowledgeEntry] = {}
        self._entries_by_category: Dict[KnowledgeCategory, List[str]] = defaultdict(list)
        self._entries_by_tag: Dict[str, List[str]] = defaultdict(list)
        self._title_index: Dict[str, str] = {}  # title -> entry_id

        # Version history
        self._version_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # Statistics
        self._stats = {
            "total_entries": 0,
            "total_accesses": 0,
            "most_accessed": None
        }

        logger.info(f"Bibliotekar-Kommandant initialized (Room {learning_room_id})")

    async def add_entry(
        self,
        title: str,
        content: Any,
        category: KnowledgeCategory,
        created_by: str,
        tags: Optional[Set[str]] = None,
        references: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeEntry:
        """Tilføj en ny videnindgang."""
        entry_id = f"kb_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()

        entry = KnowledgeEntry(
            id=entry_id,
            title=title,
            content=content,
            category=category,
            created_at=now,
            updated_at=now,
            created_by=created_by,
            tags=tags or set(),
            references=references or [],
            metadata=metadata or {}
        )

        # Store
        self._entries[entry_id] = entry
        self._entries_by_category[category].append(entry_id)
        self._title_index[title.lower()] = entry_id

        for tag in entry.tags:
            self._entries_by_tag[tag.lower()].append(entry_id)

        # Store initial version
        self._version_history[entry_id].append({
            "version": 1,
            "timestamp": now.isoformat(),
            "changed_by": created_by,
            "action": "created"
        })

        self._stats["total_entries"] += 1

        logger.debug(f"Knowledge entry added: {title}")
        return entry

    async def update_entry(
        self,
        entry_id: str,
        content: Optional[Any] = None,
        title: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        updated_by: str = "system"
    ) -> Optional[KnowledgeEntry]:
        """Opdater en videnindgang."""
        entry = self._entries.get(entry_id)
        if not entry:
            return None

        now = datetime.utcnow()
        entry.version += 1
        entry.updated_at = now

        if content is not None:
            entry.content = content
        if title is not None:
            # Update title index
            del self._title_index[entry.title.lower()]
            entry.title = title
            self._title_index[title.lower()] = entry_id
        if tags is not None:
            # Update tag index
            for old_tag in entry.tags:
                if entry_id in self._entries_by_tag[old_tag.lower()]:
                    self._entries_by_tag[old_tag.lower()].remove(entry_id)
            entry.tags = tags
            for new_tag in tags:
                self._entries_by_tag[new_tag.lower()].append(entry_id)

        # Store version
        self._version_history[entry_id].append({
            "version": entry.version,
            "timestamp": now.isoformat(),
            "changed_by": updated_by,
            "action": "updated"
        })

        logger.debug(f"Knowledge entry updated: {entry.title} (v{entry.version})")
        return entry

    async def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Hent en videnindgang."""
        entry = self._entries.get(entry_id)
        if entry:
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()
            self._stats["total_accesses"] += 1

            # Update most accessed
            if (self._stats["most_accessed"] is None or
                entry.access_count > self._entries.get(
                    self._stats["most_accessed"], KnowledgeEntry(
                        id="", title="", content="",
                        category=KnowledgeCategory.REFERENCE,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        created_by=""
                    )
                ).access_count):
                self._stats["most_accessed"] = entry_id

        return entry

    async def get_entry_by_title(self, title: str) -> Optional[KnowledgeEntry]:
        """Hent en videnindgang efter titel."""
        entry_id = self._title_index.get(title.lower())
        if entry_id:
            return await self.get_entry(entry_id)
        return None

    async def search(
        self,
        query: str,
        category: Optional[KnowledgeCategory] = None,
        tags: Optional[Set[str]] = None,
        limit: int = 50
    ) -> List[KnowledgeEntry]:
        """Søg i biblioteket."""
        results = []
        query_lower = query.lower()

        entries_to_search = list(self._entries.values())

        # Filter by category if specified
        if category:
            entry_ids = set(self._entries_by_category.get(category, []))
            entries_to_search = [e for e in entries_to_search if e.id in entry_ids]

        for entry in entries_to_search:
            # Match query
            if query_lower not in entry.title.lower():
                content_str = str(entry.content).lower()
                if query_lower not in content_str:
                    continue

            # Match tags if specified
            if tags and not tags.issubset(entry.tags):
                continue

            results.append(entry)
            if len(results) >= limit:
                break

        # Sort by relevance (title match > content match) and access count
        results.sort(key=lambda e: (
            0 if query_lower in e.title.lower() else 1,
            -e.access_count
        ))

        return results

    async def list_by_category(
        self,
        category: KnowledgeCategory,
        limit: int = 50
    ) -> List[KnowledgeEntry]:
        """List indgange i en kategori."""
        entry_ids = self._entries_by_category.get(category, [])[-limit:]
        return [self._entries[eid] for eid in entry_ids if eid in self._entries]

    async def list_by_tag(
        self,
        tag: str,
        limit: int = 50
    ) -> List[KnowledgeEntry]:
        """List indgange med et bestemt tag."""
        entry_ids = self._entries_by_tag.get(tag.lower(), [])[-limit:]
        return [self._entries[eid] for eid in entry_ids if eid in self._entries]

    async def get_version_history(
        self,
        entry_id: str
    ) -> List[Dict[str, Any]]:
        """Hent versionshistorik for en indgang."""
        return self._version_history.get(entry_id, [])

    async def get_related_entries(
        self,
        entry_id: str,
        limit: int = 10
    ) -> List[KnowledgeEntry]:
        """Find relaterede indgange baseret på tags og referencer."""
        entry = self._entries.get(entry_id)
        if not entry:
            return []

        related_ids: Set[str] = set()

        # Add referenced entries
        for ref_id in entry.references:
            if ref_id in self._entries:
                related_ids.add(ref_id)

        # Add entries with same tags
        for tag in entry.tags:
            for related_id in self._entries_by_tag.get(tag.lower(), []):
                if related_id != entry_id:
                    related_ids.add(related_id)

        # Sort by access count
        related = [self._entries[rid] for rid in related_ids if rid in self._entries]
        related.sort(key=lambda e: -e.access_count)

        return related[:limit]

    async def get_statistics(self) -> Dict[str, Any]:
        """Hent biblioteksstatistik."""
        category_counts = {
            cat.value: len(ids)
            for cat, ids in self._entries_by_category.items()
        }

        return {
            **self._stats,
            "category_counts": category_counts,
            "unique_tags": len(self._entries_by_tag),
            "retrieved_at": datetime.utcnow().isoformat()
        }

    async def get_catalog(self) -> Dict[str, Any]:
        """Hent komplet katalog oversigt."""
        return {
            "total_entries": self._stats["total_entries"],
            "categories": {
                cat.value: {
                    "count": len(ids),
                    "entries": [
                        self._entries[eid].title
                        for eid in ids[-5:]
                        if eid in self._entries
                    ]
                }
                for cat, ids in self._entries_by_category.items()
            },
            "recent_entries": [
                entry.to_dict()
                for entry in sorted(
                    self._entries.values(),
                    key=lambda e: e.created_at,
                    reverse=True
                )[:10]
            ],
            "most_accessed": [
                entry.to_dict()
                for entry in sorted(
                    self._entries.values(),
                    key=lambda e: e.access_count,
                    reverse=True
                )[:10]
            ],
            "generated_at": datetime.utcnow().isoformat()
        }


# ═══════════════════════════════════════════════════════════════
# SINGLETON & CONVENIENCE
# ═══════════════════════════════════════════════════════════════

_historiker: Optional[HistorikerKommandant] = None
_bibliotekar: Optional[BibliotekarKommandant] = None


def get_historiker() -> HistorikerKommandant:
    """Hent singleton Historiker-Kommandant."""
    global _historiker
    if _historiker is None:
        _historiker = HistorikerKommandant()
    return _historiker


def get_bibliotekar() -> BibliotekarKommandant:
    """Hent singleton Bibliotekar-Kommandant."""
    global _bibliotekar
    if _bibliotekar is None:
        _bibliotekar = BibliotekarKommandant()
    return _bibliotekar


async def record_historical_event(
    event_type: HistoricalEventType,
    description: str,
    source: str,
    **kwargs
) -> HistoricalEvent:
    """Convenience function til at optage hændelser."""
    return await get_historiker().record_event(event_type, description, source, **kwargs)


async def add_knowledge(
    title: str,
    content: Any,
    category: KnowledgeCategory,
    created_by: str,
    **kwargs
) -> KnowledgeEntry:
    """Convenience function til at tilføje viden."""
    return await get_bibliotekar().add_entry(title, content, category, created_by, **kwargs)


logger.info("CKC Kommandanter module loaded - Historiker & Bibliotekar ready")
