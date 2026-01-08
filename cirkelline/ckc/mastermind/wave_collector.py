"""
CKC MASTERMIND Wave Collector (DEL O)
======================================

Bølge-samler for MASTERMIND Tilstand.

Samler ukontrollerede strømme af informationer fra alle sider.
Hver kommandant bidrager til fællesskabet uden filtrering.

Princip: Alt samles op - intet går tabt.

Komponenter:
- WaveSource: Kilde til informationsbølger
- Wave: En enkelt bølge af information
- WaveStream: Strøm af bølger fra én kilde
- WaveCollector: Central samler af alle bølger
- WaveBuffer: Midlertidig buffer for bølger
- WaveAggregator: Aggregerer bølger til sammenhænge
"""

from __future__ import annotations

import asyncio
import logging
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class WaveType(Enum):
    """Type af informationsbølge."""
    THOUGHT = "thought"           # Tanke fra kommandant
    OBSERVATION = "observation"   # Observation af verden
    INSIGHT = "insight"           # Indsigt eller erkendelse
    QUESTION = "question"         # Spørgsmål der opstår
    MEMORY = "memory"             # Hukommelse der aktiveres
    SIGNAL = "signal"             # Signal fra system
    EMOTION = "emotion"           # Emotionel tilstand
    INTENTION = "intention"       # Intention eller mål
    REFLECTION = "reflection"     # Refleksion over proces
    DISCOVERY = "discovery"       # Ny opdagelse


class WaveOrigin(Enum):
    """Oprindelse af bølge."""
    KOMMANDANT = "kommandant"     # Fra en kommandant
    SPECIALIST = "specialist"     # Fra en specialist
    DIRIGENT = "dirigent"         # Fra Systems Dirigent
    SUPER_ADMIN = "super_admin"   # Fra Super Admin
    SYSTEM = "system"             # Fra systemet selv
    EXTERNAL = "external"         # Fra eksterne kilder
    COLLECTIVE = "collective"     # Fra fællesskabet


class WaveIntensity(Enum):
    """Intensitet af bølge."""
    WHISPER = 1      # Svag, næsten ikke mærkbar
    GENTLE = 2       # Blød, rolig
    NORMAL = 3       # Normal styrke
    STRONG = 4       # Kraftig, tydelig
    SURGE = 5        # Bølge-skvulp, markant
    TSUNAMI = 6      # Overvældende, kræver opmærksomhed


class StreamState(Enum):
    """Tilstand af en bølgestrøm."""
    DORMANT = "dormant"       # Sovende, ingen aktivitet
    FLOWING = "flowing"       # Aktiv strøm
    SURGING = "surging"       # Kraftig aktivitet
    EBBING = "ebbing"         # Aftagende
    BLOCKED = "blocked"       # Blokeret


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Wave:
    """En enkelt bølge af information."""
    wave_id: str
    wave_type: WaveType
    origin: WaveOrigin
    source_id: str  # ID på den specifikke kilde
    content: Any    # Selve indholdet - kan være hvad som helst
    intensity: WaveIntensity = WaveIntensity.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    resonates_with: Set[str] = field(default_factory=set)  # IDs af relaterede bølger

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wave_id": self.wave_id,
            "wave_type": self.wave_type.value,
            "origin": self.origin.value,
            "source_id": self.source_id,
            "content": self.content,
            "intensity": self.intensity.value,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "tags": list(self.tags),
            "resonates_with": list(self.resonates_with)
        }


@dataclass
class WaveStream:
    """En strøm af bølger fra én kilde."""
    stream_id: str
    source_id: str
    origin: WaveOrigin
    state: StreamState = StreamState.DORMANT
    waves: List[Wave] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_wave_at: Optional[datetime] = None
    wave_count: int = 0

    def add_wave(self, wave: Wave) -> None:
        """Tilføj en bølge til strømmen."""
        self.waves.append(wave)
        self.wave_count += 1
        self.last_wave_at = datetime.now()
        if self.state == StreamState.DORMANT:
            self.state = StreamState.FLOWING

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stream_id": self.stream_id,
            "source_id": self.source_id,
            "origin": self.origin.value,
            "state": self.state.value,
            "wave_count": self.wave_count,
            "created_at": self.created_at.isoformat(),
            "last_wave_at": self.last_wave_at.isoformat() if self.last_wave_at else None
        }


@dataclass
class WavePattern:
    """Et mønster der opstår på tværs af bølger."""
    pattern_id: str
    wave_ids: Set[str]
    pattern_type: str
    strength: float  # 0.0 - 1.0
    description: str
    emerged_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "wave_ids": list(self.wave_ids),
            "pattern_type": self.pattern_type,
            "strength": self.strength,
            "description": self.description,
            "emerged_at": self.emerged_at.isoformat()
        }


@dataclass
class CollectedWaves:
    """Resultat af bølgesamling."""
    collection_id: str
    waves: List[Wave]
    streams_involved: Set[str]
    patterns_found: List[WavePattern]
    total_intensity: int
    dominant_type: Optional[WaveType]
    collected_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "collection_id": self.collection_id,
            "wave_count": len(self.waves),
            "streams_involved": list(self.streams_involved),
            "patterns_found": [p.to_dict() for p in self.patterns_found],
            "total_intensity": self.total_intensity,
            "dominant_type": self.dominant_type.value if self.dominant_type else None,
            "collected_at": self.collected_at.isoformat()
        }


# =============================================================================
# WAVE BUFFER
# =============================================================================

class WaveBuffer:
    """
    Buffer for midlertidig opbevaring af bølger.

    Holder bølger indtil de kan processeres eller
    samles i fællesskab.
    """

    def __init__(
        self,
        max_size: int = 1000,
        max_age_seconds: int = 300
    ):
        self.max_size = max_size
        self.max_age = timedelta(seconds=max_age_seconds)
        self._waves: List[Wave] = []
        self._lock = asyncio.Lock()

    async def add(self, wave: Wave) -> None:
        """Tilføj bølge til buffer."""
        async with self._lock:
            self._waves.append(wave)
            # Hvis buffer er fuld, fjern ældste
            if len(self._waves) > self.max_size:
                self._waves = self._waves[-self.max_size:]

    async def flush(self) -> List[Wave]:
        """Tøm og returner alle bølger."""
        async with self._lock:
            waves = self._waves.copy()
            self._waves.clear()
            return waves

    async def get_recent(self, seconds: int = 60) -> List[Wave]:
        """Hent bølger fra de seneste N sekunder."""
        cutoff = datetime.now() - timedelta(seconds=seconds)
        async with self._lock:
            return [w for w in self._waves if w.timestamp > cutoff]

    async def get_by_type(self, wave_type: WaveType) -> List[Wave]:
        """Hent alle bølger af en bestemt type."""
        async with self._lock:
            return [w for w in self._waves if w.wave_type == wave_type]

    async def get_by_origin(self, origin: WaveOrigin) -> List[Wave]:
        """Hent alle bølger fra en bestemt oprindelse."""
        async with self._lock:
            return [w for w in self._waves if w.origin == origin]

    async def cleanup_old(self) -> int:
        """Fjern gamle bølger. Returnerer antal fjernet."""
        cutoff = datetime.now() - self.max_age
        async with self._lock:
            original_count = len(self._waves)
            self._waves = [w for w in self._waves if w.timestamp > cutoff]
            return original_count - len(self._waves)

    @property
    def size(self) -> int:
        return len(self._waves)


# =============================================================================
# WAVE SOURCE (Abstract)
# =============================================================================

class WaveSource(ABC):
    """
    Abstrakt base-klasse for bølgekilder.

    Enhver kilde der kan producere informationsbølger
    skal implementere dette interface.
    """

    @property
    @abstractmethod
    def source_id(self) -> str:
        """Unik ID for kilden."""
        pass

    @property
    @abstractmethod
    def origin(self) -> WaveOrigin:
        """Oprindelse-type for kilden."""
        pass

    @abstractmethod
    async def emit_wave(self, content: Any, wave_type: WaveType, **kwargs) -> Wave:
        """Udsend en bølge fra denne kilde."""
        pass

    @abstractmethod
    async def listen(self) -> AsyncIterator[Wave]:
        """Lyt efter bølger fra denne kilde."""
        pass


# =============================================================================
# KONKRET WAVE SOURCE: KOMMANDANT
# =============================================================================

class KommandantWaveSource(WaveSource):
    """
    Bølgekilde for en Kommandant.

    Hver kommandant kan udsende tanker, observationer,
    indsigter og meget mere til fællesskabet.
    """

    def __init__(self, kommandant_id: str, kommandant_name: str):
        self._id = kommandant_id
        self._name = kommandant_name
        self._wave_queue: asyncio.Queue[Wave] = asyncio.Queue()
        self._active = True

    @property
    def source_id(self) -> str:
        return self._id

    @property
    def origin(self) -> WaveOrigin:
        return WaveOrigin.KOMMANDANT

    async def emit_wave(
        self,
        content: Any,
        wave_type: WaveType,
        intensity: WaveIntensity = WaveIntensity.NORMAL,
        tags: Optional[Set[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Wave:
        """Udsend en bølge fra kommandanten."""
        wave = Wave(
            wave_id=f"wave_{secrets.token_hex(8)}",
            wave_type=wave_type,
            origin=self.origin,
            source_id=self._id,
            content=content,
            intensity=intensity,
            tags=tags or set(),
            context=context or {"kommandant_name": self._name}
        )
        await self._wave_queue.put(wave)
        logger.debug(f"[{self._name}] Udsendte bølge: {wave_type.value}")
        return wave

    async def listen(self) -> AsyncIterator[Wave]:
        """Lyt efter bølger fra denne kommandant."""
        while self._active:
            try:
                wave = await asyncio.wait_for(
                    self._wave_queue.get(),
                    timeout=1.0
                )
                yield wave
            except asyncio.TimeoutError:
                continue

    async def think(self, thought: str) -> Wave:
        """Udtryk en tanke."""
        return await self.emit_wave(thought, WaveType.THOUGHT)

    async def observe(self, observation: str) -> Wave:
        """Del en observation."""
        return await self.emit_wave(observation, WaveType.OBSERVATION)

    async def share_insight(self, insight: str) -> Wave:
        """Del en indsigt."""
        return await self.emit_wave(insight, WaveType.INSIGHT, intensity=WaveIntensity.STRONG)

    async def ask(self, question: str) -> Wave:
        """Stil et spørgsmål til fællesskabet."""
        return await self.emit_wave(question, WaveType.QUESTION)

    async def remember(self, memory: Any) -> Wave:
        """Del en hukommelse."""
        return await self.emit_wave(memory, WaveType.MEMORY)

    async def reflect(self, reflection: str) -> Wave:
        """Del en refleksion."""
        return await self.emit_wave(reflection, WaveType.REFLECTION)

    def deactivate(self) -> None:
        """Deaktiver kilden."""
        self._active = False


# =============================================================================
# WAVE AGGREGATOR
# =============================================================================

class WaveAggregator:
    """
    Aggregerer bølger til sammenhængende mønstre.

    Finder forbindelser mellem bølger på tværs af
    kilder og typer.
    """

    def __init__(self):
        self._patterns: List[WavePattern] = []

    async def find_patterns(self, waves: List[Wave]) -> List[WavePattern]:
        """Find mønstre i en samling bølger."""
        patterns: List[WavePattern] = []

        # Gruppér efter type
        type_groups: Dict[WaveType, List[Wave]] = {}
        for wave in waves:
            if wave.wave_type not in type_groups:
                type_groups[wave.wave_type] = []
            type_groups[wave.wave_type].append(wave)

        # Find type-klynger
        for wave_type, type_waves in type_groups.items():
            if len(type_waves) >= 3:
                pattern = WavePattern(
                    pattern_id=f"pattern_{secrets.token_hex(6)}",
                    wave_ids={w.wave_id for w in type_waves},
                    pattern_type=f"type_cluster_{wave_type.value}",
                    strength=min(1.0, len(type_waves) / 10.0),
                    description=f"Klynge af {len(type_waves)} {wave_type.value}-bølger"
                )
                patterns.append(pattern)

        # Find tag-mønstre
        tag_groups: Dict[str, List[Wave]] = {}
        for wave in waves:
            for tag in wave.tags:
                if tag not in tag_groups:
                    tag_groups[tag] = []
                tag_groups[tag].append(wave)

        for tag, tagged_waves in tag_groups.items():
            if len(tagged_waves) >= 2:
                pattern = WavePattern(
                    pattern_id=f"pattern_{secrets.token_hex(6)}",
                    wave_ids={w.wave_id for w in tagged_waves},
                    pattern_type=f"tag_resonance_{tag}",
                    strength=min(1.0, len(tagged_waves) / 5.0),
                    description=f"Resonans omkring tag '{tag}'"
                )
                patterns.append(pattern)

        # Find tidsmæssige klynger (bølger inden for kort tid)
        time_clusters = self._find_time_clusters(waves, seconds=5)
        for cluster in time_clusters:
            if len(cluster) >= 3:
                pattern = WavePattern(
                    pattern_id=f"pattern_{secrets.token_hex(6)}",
                    wave_ids={w.wave_id for w in cluster},
                    pattern_type="temporal_surge",
                    strength=min(1.0, len(cluster) / 8.0),
                    description=f"Tidsmæssig bølge-surge med {len(cluster)} bølger"
                )
                patterns.append(pattern)

        self._patterns.extend(patterns)
        return patterns

    def _find_time_clusters(
        self,
        waves: List[Wave],
        seconds: int
    ) -> List[List[Wave]]:
        """Find klynger af bølger der kom tæt på hinanden."""
        if not waves:
            return []

        sorted_waves = sorted(waves, key=lambda w: w.timestamp)
        clusters: List[List[Wave]] = []
        current_cluster: List[Wave] = [sorted_waves[0]]

        for wave in sorted_waves[1:]:
            time_diff = (wave.timestamp - current_cluster[-1].timestamp).total_seconds()
            if time_diff <= seconds:
                current_cluster.append(wave)
            else:
                if len(current_cluster) >= 2:
                    clusters.append(current_cluster)
                current_cluster = [wave]

        if len(current_cluster) >= 2:
            clusters.append(current_cluster)

        return clusters


# =============================================================================
# MAIN CLASS: WAVE COLLECTOR
# =============================================================================

class WaveCollector:
    """
    Central samler af alle informationsbølger.

    Samler ukontrollerede strømme af informationer fra alle kilder.
    Intet filtreres - alt samles op i fællesskab.

    Princip: "Vi samler alt op i fællesskab"
    """

    def __init__(self, buffer_size: int = 5000):
        self._streams: Dict[str, WaveStream] = {}
        self._sources: Dict[str, WaveSource] = {}
        self._buffer = WaveBuffer(max_size=buffer_size)
        self._aggregator = WaveAggregator()
        self._listeners: List[Callable[[Wave], None]] = []
        self._active = False
        self._collection_tasks: List[asyncio.Task] = []
        self._all_waves: List[Wave] = []  # Permanent lager
        self._lock = asyncio.Lock()

    # =========================================================================
    # SOURCE MANAGEMENT
    # =========================================================================

    async def register_source(self, source: WaveSource) -> WaveStream:
        """
        Registrer en ny bølgekilde.

        Enhver kilde kan bidrage til fællesskabet.
        """
        stream = WaveStream(
            stream_id=f"stream_{secrets.token_hex(8)}",
            source_id=source.source_id,
            origin=source.origin
        )

        async with self._lock:
            self._sources[source.source_id] = source
            self._streams[stream.stream_id] = stream

        logger.info(f"Registreret bølgekilde: {source.source_id} ({source.origin.value})")

        # Start at lytte til kilden
        if self._active:
            task = asyncio.create_task(
                self._collect_from_source(source, stream)
            )
            self._collection_tasks.append(task)

        return stream

    async def unregister_source(self, source_id: str) -> bool:
        """Afregistrer en bølgekilde."""
        async with self._lock:
            if source_id in self._sources:
                del self._sources[source_id]
                # Find og fjern tilhørende stream
                stream_id = None
                for sid, stream in self._streams.items():
                    if stream.source_id == source_id:
                        stream_id = sid
                        break
                if stream_id:
                    del self._streams[stream_id]
                logger.info(f"Afregistreret bølgekilde: {source_id}")
                return True
        return False

    # =========================================================================
    # WAVE COLLECTION
    # =========================================================================

    async def start(self) -> None:
        """Start bølgesamling fra alle kilder."""
        self._active = True
        logger.info("Wave Collector startet - samler alle bølger")

        # Start samling fra alle eksisterende kilder
        for source_id, source in self._sources.items():
            stream = next(
                (s for s in self._streams.values() if s.source_id == source_id),
                None
            )
            if stream:
                task = asyncio.create_task(
                    self._collect_from_source(source, stream)
                )
                self._collection_tasks.append(task)

        # Start baggrunds-cleanup
        asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Stop bølgesamling."""
        self._active = False
        for task in self._collection_tasks:
            task.cancel()
        self._collection_tasks.clear()
        logger.info("Wave Collector stoppet")

    async def _collect_from_source(
        self,
        source: WaveSource,
        stream: WaveStream
    ) -> None:
        """Saml bølger fra en specifik kilde."""
        try:
            async for wave in source.listen():
                if not self._active:
                    break

                # Tilføj til stream
                stream.add_wave(wave)

                # Tilføj til buffer
                await self._buffer.add(wave)

                # Tilføj til permanent lager
                async with self._lock:
                    self._all_waves.append(wave)

                # Notificer listeners
                for listener in self._listeners:
                    try:
                        listener(wave)
                    except Exception as e:
                        logger.error(f"Listener fejl: {e}")

                logger.debug(
                    f"Samlet bølge: {wave.wave_type.value} fra {source.source_id}"
                )
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Fejl ved samling fra {source.source_id}: {e}")

    async def _cleanup_loop(self) -> None:
        """Periodisk oprydning af gamle bølger i buffer."""
        while self._active:
            await asyncio.sleep(60)
            removed = await self._buffer.cleanup_old()
            if removed > 0:
                logger.debug(f"Fjernet {removed} gamle bølger fra buffer")

    # =========================================================================
    # DIRECT WAVE INJECTION
    # =========================================================================

    async def inject_wave(self, wave: Wave) -> None:
        """
        Injicer en bølge direkte i samleren.

        Bruges når bølger kommer fra kilder der ikke er
        registreret som WaveSource.
        """
        await self._buffer.add(wave)
        async with self._lock:
            self._all_waves.append(wave)

        # Opret/opdater stream for kilden
        stream_id = f"injected_{wave.source_id}"
        if stream_id not in self._streams:
            self._streams[stream_id] = WaveStream(
                stream_id=stream_id,
                source_id=wave.source_id,
                origin=wave.origin
            )
        self._streams[stream_id].add_wave(wave)

        # Notificer listeners
        for listener in self._listeners:
            try:
                listener(wave)
            except Exception as e:
                logger.error(f"Listener fejl: {e}")

    # =========================================================================
    # WAVE RETRIEVAL
    # =========================================================================

    async def collect_all(self) -> CollectedWaves:
        """
        Saml alle aktuelle bølger og find mønstre.

        Dette er hovedmetoden for at få et samlet billede
        af alt hvad der foregår i fællesskabet.
        """
        waves = await self._buffer.flush()

        if not waves:
            return CollectedWaves(
                collection_id=f"col_{secrets.token_hex(8)}",
                waves=[],
                streams_involved=set(),
                patterns_found=[],
                total_intensity=0,
                dominant_type=None
            )

        # Find mønstre
        patterns = await self._aggregator.find_patterns(waves)

        # Beregn total intensitet
        total_intensity = sum(w.intensity.value for w in waves)

        # Find dominant type
        type_counts: Dict[WaveType, int] = {}
        for wave in waves:
            type_counts[wave.wave_type] = type_counts.get(wave.wave_type, 0) + 1
        dominant_type = max(type_counts.keys(), key=lambda t: type_counts[t]) if type_counts else None

        # Identificer involverede streams
        streams_involved = {
            stream_id for stream_id, stream in self._streams.items()
            if any(w.source_id == stream.source_id for w in waves)
        }

        return CollectedWaves(
            collection_id=f"col_{secrets.token_hex(8)}",
            waves=waves,
            streams_involved=streams_involved,
            patterns_found=patterns,
            total_intensity=total_intensity,
            dominant_type=dominant_type
        )

    async def get_recent_waves(self, seconds: int = 60) -> List[Wave]:
        """Hent bølger fra de seneste N sekunder."""
        return await self._buffer.get_recent(seconds)

    async def get_waves_by_type(self, wave_type: WaveType) -> List[Wave]:
        """Hent alle bølger af en bestemt type."""
        return await self._buffer.get_by_type(wave_type)

    async def get_waves_by_origin(self, origin: WaveOrigin) -> List[Wave]:
        """Hent alle bølger fra en bestemt oprindelse."""
        return await self._buffer.get_by_origin(origin)

    async def get_all_waves(self) -> List[Wave]:
        """Hent ALLE samlede bølger (permanent lager)."""
        async with self._lock:
            return self._all_waves.copy()

    # =========================================================================
    # LISTENERS
    # =========================================================================

    def add_listener(self, callback: Callable[[Wave], None]) -> None:
        """Tilføj en listener der kaldes ved hver ny bølge."""
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[Wave], None]) -> None:
        """Fjern en listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    # =========================================================================
    # STATUS
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """Hent samlerens status."""
        return {
            "active": self._active,
            "source_count": len(self._sources),
            "stream_count": len(self._streams),
            "buffer_size": self._buffer.size,
            "total_waves_collected": len(self._all_waves),
            "listener_count": len(self._listeners),
            "streams": [s.to_dict() for s in self._streams.values()]
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_wave_collector_instance: Optional[WaveCollector] = None


def create_wave_collector(buffer_size: int = 5000) -> WaveCollector:
    """Opret en ny Wave Collector."""
    global _wave_collector_instance
    _wave_collector_instance = WaveCollector(buffer_size=buffer_size)
    return _wave_collector_instance


def get_wave_collector() -> Optional[WaveCollector]:
    """Hent den aktive Wave Collector."""
    return _wave_collector_instance


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "WaveType",
    "WaveOrigin",
    "WaveIntensity",
    "StreamState",

    # Data classes
    "Wave",
    "WaveStream",
    "WavePattern",
    "CollectedWaves",

    # Classes
    "WaveBuffer",
    "WaveSource",
    "KommandantWaveSource",
    "WaveAggregator",
    "WaveCollector",

    # Factory functions
    "create_wave_collector",
    "get_wave_collector",
]
