"""
Web3 Domain Kommandanter
========================

FASE 6: Multi-Bibliotek Arkitektur

Konkrete implementationer af Historiker og Bibliotekar
for Web3/Blockchain research domanen.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict

from ..historiker import (
    HistorikerKommandant,
    KnowledgeEvent,
    Timeline,
    TimelineEntry,
    EvolutionReport,
    Pattern,
    EventType,
    PatternStrength,
)
from ..bibliotekar import (
    BibliotekarKommandant,
    Content,
    Classification,
    IndexEntry,
    SearchResults,
    SearchResult,
    SearchFilters,
    RelatedContent,
    Taxonomy,
    TaxonomyNode,
    ContentType,
    RelevanceLevel,
)


class Web3HistorikerKommandant(HistorikerKommandant):
    """
    Historiker specialiseret i Web3/Blockchain viden.

    Tracker:
    - Protocol evolution (Ethereum, Solana, etc.)
    - DeFi trends og innovation
    - Security incidents og vulnerabilities
    - Governance changes
    - Market cycles
    """

    def __init__(self, domain: str = "web3"):
        super().__init__(domain)
        self._events: List[KnowledgeEvent] = []
        self._patterns_cache: Dict[str, Pattern] = {}

    async def initialize(self) -> None:
        """Initialiser Web3 Historiker."""
        await super().initialize()
        # Initialize Web3-specific resources
        # Could load historical data from database here

    async def record_event(self, event: KnowledgeEvent) -> None:
        """Registrer et Web3 videns-event."""
        if event.domain != self.domain:
            event.domain = self.domain

        # Add Web3-specific context
        if "protocol" not in event.context:
            event.context["protocol"] = self._infer_protocol(event.topic)

        self._events.append(event)

    async def get_timeline(
        self,
        topic: str,
        start: datetime,
        end: datetime
    ) -> Timeline:
        """Hent Web3 tidslinje for et emne."""
        matching_events = []

        for event in self._events:
            if event.occurred_at < start or event.occurred_at > end:
                continue

            if topic == "*" or topic.lower() in event.topic.lower():
                significance = self._calculate_significance(event)
                matching_events.append(TimelineEntry(
                    timestamp=event.occurred_at,
                    event=event,
                    significance=significance,
                    notes=self._generate_event_note(event)
                ))

        # Sort by timestamp
        matching_events.sort(key=lambda e: e.timestamp)

        return Timeline(
            topic=topic,
            domain=self.domain,
            entries=matching_events,
            start_date=start,
            end_date=end,
            summary=self._generate_timeline_summary(topic, matching_events)
        )

    async def analyze_evolution(self, topic: str) -> EvolutionReport:
        """Analyser Web3 emne evolution."""
        # Get all events for topic
        timeline = await self.get_timeline(
            topic,
            datetime.min,
            datetime.utcnow()
        )

        # Analyze milestones
        milestones = self._identify_milestones(timeline.entries)

        # Identify trends
        trends = self._identify_trends(timeline.entries)

        # Generate predictions
        predictions = self._generate_predictions(topic, trends)

        return EvolutionReport(
            topic=topic,
            domain=self.domain,
            period=timeline.duration,
            key_milestones=milestones,
            trends=trends,
            predictions=predictions,
            confidence=0.75
        )

    async def find_patterns(
        self,
        window: timedelta
    ) -> List[Pattern]:
        """Find Web3-specifikke patterns."""
        end = datetime.utcnow()
        start = end - window

        # Filter events in window
        window_events = [
            e for e in self._events
            if start <= e.occurred_at <= end
        ]

        patterns = []

        # Look for protocol adoption patterns
        protocol_counts = defaultdict(int)
        for event in window_events:
            protocol = event.context.get("protocol", "unknown")
            protocol_counts[protocol] += 1

        for protocol, count in protocol_counts.items():
            if count >= 3:
                strength = self._count_to_strength(count)
                patterns.append(Pattern(
                    name=f"{protocol}_adoption",
                    description=f"Increased activity in {protocol} ecosystem",
                    domain=self.domain,
                    strength=strength,
                    occurrences=count,
                    first_seen=start,
                    last_seen=end,
                    related_topics=[protocol]
                ))

        # Look for security incident patterns
        security_events = [
            e for e in window_events
            if e.event_type == EventType.INVALIDATED
            or "security" in e.topic.lower()
            or "vulnerability" in e.topic.lower()
        ]

        if len(security_events) >= 2:
            patterns.append(Pattern(
                name="security_concerns",
                description="Multiple security-related events detected",
                domain=self.domain,
                strength=PatternStrength.MODERATE if len(security_events) < 5 else PatternStrength.STRONG,
                occurrences=len(security_events),
                first_seen=min(e.occurred_at for e in security_events),
                last_seen=max(e.occurred_at for e in security_events),
                related_topics=list(set(e.topic for e in security_events))
            ))

        return patterns

    def _infer_protocol(self, topic: str) -> str:
        """Udled protocol fra emne."""
        topic_lower = topic.lower()
        protocols = {
            "ethereum": ["eth", "ethereum", "erc", "solidity"],
            "solana": ["solana", "sol", "rust"],
            "polygon": ["polygon", "matic"],
            "arbitrum": ["arbitrum", "arb"],
            "optimism": ["optimism", "op"],
            "avalanche": ["avalanche", "avax"],
            "bitcoin": ["bitcoin", "btc"],
        }

        for protocol, keywords in protocols.items():
            if any(kw in topic_lower for kw in keywords):
                return protocol

        return "multi-chain"

    def _calculate_significance(self, event: KnowledgeEvent) -> float:
        """Beregn event significance."""
        base = 0.5

        # Event type matters
        if event.event_type in [EventType.CREATED, EventType.TREND_DETECTED]:
            base += 0.2
        elif event.event_type in [EventType.INVALIDATED]:
            base += 0.3

        # Context matters
        if event.context.get("impact", "low") == "high":
            base += 0.2

        return min(base, 1.0)

    def _generate_event_note(self, event: KnowledgeEvent) -> str:
        """Generer note for event."""
        return f"{event.event_type.value}: {event.topic}"

    def _generate_timeline_summary(
        self,
        topic: str,
        entries: List[TimelineEntry]
    ) -> str:
        """Generer tidslinje opsummering."""
        if not entries:
            return f"No events found for {topic}"

        return (
            f"{len(entries)} events for {topic} "
            f"from {entries[0].timestamp.date()} to {entries[-1].timestamp.date()}"
        )

    def _identify_milestones(
        self,
        entries: List[TimelineEntry]
    ) -> List[Dict[str, Any]]:
        """Identificer vigtige milepale."""
        milestones = []
        for entry in entries:
            if entry.significance >= 0.7:
                milestones.append({
                    "date": entry.timestamp.isoformat(),
                    "event": entry.event.topic,
                    "significance": entry.significance
                })
        return milestones

    def _identify_trends(self, entries: List[TimelineEntry]) -> List[str]:
        """Identificer trends fra entries."""
        trends = []

        # Count event types
        type_counts = defaultdict(int)
        for entry in entries:
            type_counts[entry.event.event_type] += 1

        if type_counts[EventType.CREATED] > type_counts.get(EventType.DEPRECATED, 0):
            trends.append("Growing ecosystem activity")

        if type_counts.get(EventType.VALIDATED, 0) > 5:
            trends.append("Increased protocol validation")

        return trends

    def _generate_predictions(
        self,
        topic: str,
        trends: List[str]
    ) -> List[str]:
        """Generer forudsigelser baseret pa trends."""
        predictions = []

        if "Growing ecosystem activity" in trends:
            predictions.append(f"Continued growth expected for {topic}")

        return predictions

    def _count_to_strength(self, count: int) -> PatternStrength:
        """Konverter count til pattern strength."""
        if count >= 10:
            return PatternStrength.DOMINANT
        elif count >= 7:
            return PatternStrength.STRONG
        elif count >= 4:
            return PatternStrength.MODERATE
        else:
            return PatternStrength.WEAK


class Web3BibliotekarKommandant(BibliotekarKommandant):
    """
    Bibliotekar specialiseret i Web3/Blockchain viden.

    Organiserer:
    - Protocol documentation
    - Smart contract analysis
    - DeFi mechanisms
    - Governance proposals
    - Security audits
    """

    def __init__(self, domain: str = "web3"):
        super().__init__(domain)
        self._index: Dict[str, IndexEntry] = {}
        self._classifications: Dict[str, Classification] = {}
        self._content_store: Dict[str, Content] = {}

    async def initialize(self) -> None:
        """Initialiser Web3 Bibliotekar."""
        await super().initialize()
        self._taxonomy = self._build_web3_taxonomy()

    async def classify(self, content: Content) -> Classification:
        """Klassificer Web3 indhold."""
        # Analyze content
        primary = self._determine_primary_category(content)
        secondary = self._determine_secondary_categories(content)
        tags = self._extract_tags(content)

        classification = Classification(
            content_id=content.id,
            domain=self.domain,
            primary_category=primary,
            secondary_categories=secondary,
            tags=tags,
            confidence=0.85
        )

        self._classifications[content.id] = classification
        self._content_store[content.id] = content

        return classification

    async def index(self, content: Content) -> IndexEntry:
        """Indekser Web3 indhold."""
        # Extract searchable terms
        terms = self._extract_terms(content)

        entry = IndexEntry(
            content_id=content.id,
            domain=self.domain,
            terms=terms,
            weight_boost=self._calculate_boost(content)
        )

        self._index[content.id] = entry
        return entry

    async def search(
        self,
        query: str,
        filters: Optional[SearchFilters] = None
    ) -> SearchResults:
        """Sog i Web3 biblioteket."""
        start_time = datetime.utcnow()
        results = []

        # Search through index
        query_terms = set(query.lower().split())

        for content_id, entry in self._index.items():
            # Calculate match score
            matched = query_terms.intersection(set(t.lower() for t in entry.terms))
            if not matched and query != "*":
                continue

            # Apply filters
            if filters:
                classification = self._classifications.get(content_id)
                if classification:
                    if filters.categories:
                        if classification.primary_category not in filters.categories:
                            continue
                    if filters.tags:
                        if not set(classification.tags).intersection(set(filters.tags)):
                            continue

            # Get content
            content = self._content_store.get(content_id)
            if not content:
                continue

            # Calculate relevance
            score = len(matched) / max(len(query_terms), 1) if query != "*" else 0.5
            relevance = self._score_to_relevance(score)

            results.append(SearchResult(
                content_id=content_id,
                title=content.title,
                snippet=content.body[:200] + "..." if len(content.body) > 200 else content.body,
                relevance=relevance,
                score=score * entry.weight_boost,
                category=self._classifications.get(content_id, Classification(
                    content_id=content_id,
                    domain=self.domain,
                    primary_category="uncategorized"
                )).primary_category,
                matched_terms=list(matched)
            ))

        # Sort by score
        results.sort(key=lambda r: r.score, reverse=True)

        elapsed = (datetime.utcnow() - start_time).total_seconds() * 1000

        return SearchResults(
            query=query,
            total_count=len(results),
            results=results[:20],  # Limit to 20
            execution_time_ms=elapsed,
            facets=self._build_facets(results)
        )

    async def find_related(
        self,
        content_id: str,
        depth: int = 1
    ) -> List[RelatedContent]:
        """Find relateret Web3 indhold."""
        related = []

        source_class = self._classifications.get(content_id)
        source_index = self._index.get(content_id)

        if not source_class or not source_index:
            return related

        source_terms = set(source_index.terms)

        for other_id, other_index in self._index.items():
            if other_id == content_id:
                continue

            other_terms = set(other_index.terms)
            overlap = source_terms.intersection(other_terms)

            if len(overlap) >= 2:
                other_class = self._classifications.get(other_id)
                other_content = self._content_store.get(other_id)

                if other_content:
                    # Determine relationship type
                    if source_class.primary_category == other_class.primary_category:
                        rel_type = "same_category"
                    elif overlap:
                        rel_type = "shared_concepts"
                    else:
                        rel_type = "tangential"

                    related.append(RelatedContent(
                        content_id=other_id,
                        title=other_content.title,
                        relationship_type=rel_type,
                        strength=len(overlap) / max(len(source_terms), 1)
                    ))

        # Sort by strength and limit
        related.sort(key=lambda r: r.strength, reverse=True)
        return related[:10]

    async def get_taxonomy(self) -> Taxonomy:
        """Hent Web3 taxonomi."""
        if not self._taxonomy:
            self._taxonomy = self._build_web3_taxonomy()
        return self._taxonomy

    def _build_web3_taxonomy(self) -> Taxonomy:
        """Byg Web3-specifik taxonomi."""
        root_nodes = [
            TaxonomyNode(
                id="protocols",
                name="Protocols",
                description="Blockchain protocols and networks",
                children=[
                    TaxonomyNode(id="ethereum", name="Ethereum"),
                    TaxonomyNode(id="solana", name="Solana"),
                    TaxonomyNode(id="polygon", name="Polygon"),
                    TaxonomyNode(id="arbitrum", name="Arbitrum"),
                ]
            ),
            TaxonomyNode(
                id="defi",
                name="DeFi",
                description="Decentralized Finance",
                children=[
                    TaxonomyNode(id="lending", name="Lending"),
                    TaxonomyNode(id="dex", name="DEX"),
                    TaxonomyNode(id="yield", name="Yield"),
                    TaxonomyNode(id="derivatives", name="Derivatives"),
                ]
            ),
            TaxonomyNode(
                id="security",
                name="Security",
                description="Security and audits",
                children=[
                    TaxonomyNode(id="audits", name="Audits"),
                    TaxonomyNode(id="vulnerabilities", name="Vulnerabilities"),
                    TaxonomyNode(id="incidents", name="Incidents"),
                ]
            ),
            TaxonomyNode(
                id="governance",
                name="Governance",
                description="DAO and governance",
                children=[
                    TaxonomyNode(id="proposals", name="Proposals"),
                    TaxonomyNode(id="voting", name="Voting"),
                    TaxonomyNode(id="treasury", name="Treasury"),
                ]
            ),
        ]

        return Taxonomy(
            domain=self.domain,
            root_nodes=root_nodes,
            total_categories=16,
            max_depth=2
        )

    def _determine_primary_category(self, content: Content) -> str:
        """Bestem primar kategori."""
        text = (content.title + " " + content.body).lower()

        categories = {
            "defi": ["defi", "lending", "swap", "yield", "liquidity"],
            "security": ["security", "audit", "vulnerability", "hack", "exploit"],
            "governance": ["governance", "dao", "proposal", "vote", "treasury"],
            "protocols": ["protocol", "ethereum", "solana", "polygon", "layer"],
        }

        scores = {}
        for cat, keywords in categories.items():
            scores[cat] = sum(1 for kw in keywords if kw in text)

        if max(scores.values()) == 0:
            return "uncategorized"

        return max(scores, key=scores.get)

    def _determine_secondary_categories(self, content: Content) -> List[str]:
        """Bestem sekundare kategorier."""
        primary = self._determine_primary_category(content)
        text = (content.title + " " + content.body).lower()

        secondary = []
        all_cats = ["defi", "security", "governance", "protocols"]

        for cat in all_cats:
            if cat != primary and cat in text:
                secondary.append(cat)

        return secondary[:2]

    def _extract_tags(self, content: Content) -> List[str]:
        """Udtrak tags fra indhold."""
        text = (content.title + " " + content.body).lower()
        tags = []

        # Protocol tags
        protocols = ["ethereum", "solana", "polygon", "arbitrum", "optimism"]
        for p in protocols:
            if p in text:
                tags.append(p)

        # Topic tags
        topics = ["nft", "token", "smart-contract", "bridge", "oracle"]
        for t in topics:
            if t in text:
                tags.append(t)

        return tags[:5]

    def _extract_terms(self, content: Content) -> List[str]:
        """Udtrak sogebare termer."""
        text = content.title + " " + content.body

        # Simple tokenization
        terms = []
        for word in text.split():
            word = word.strip(".,;:!?()[]{}\"'").lower()
            if len(word) >= 3 and word not in ["the", "and", "for", "with"]:
                terms.append(word)

        return list(set(terms))[:50]

    def _calculate_boost(self, content: Content) -> float:
        """Beregn weight boost for indhold."""
        boost = 1.0

        # Recent content gets boost
        age = datetime.utcnow() - content.created_at
        if age.days < 7:
            boost *= 1.5
        elif age.days < 30:
            boost *= 1.2

        return boost

    def _score_to_relevance(self, score: float) -> RelevanceLevel:
        """Konverter score til relevance level."""
        if score >= 0.9:
            return RelevanceLevel.EXACT_MATCH
        elif score >= 0.7:
            return RelevanceLevel.HIGH
        elif score >= 0.4:
            return RelevanceLevel.MEDIUM
        elif score >= 0.2:
            return RelevanceLevel.LOW
        else:
            return RelevanceLevel.TANGENTIAL

    def _build_facets(self, results: List[SearchResult]) -> Dict[str, List[Dict[str, Any]]]:
        """Byg facetter fra resultater."""
        category_counts = defaultdict(int)
        for r in results:
            category_counts[r.category] += 1

        return {
            "categories": [
                {"name": cat, "count": count}
                for cat, count in category_counts.items()
            ]
        }
