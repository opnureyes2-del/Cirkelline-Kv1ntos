"""
Legal Domain Kommandanter
=========================

FASE 6: Multi-Bibliotek Arkitektur

Konkrete implementationer af Historiker og Bibliotekar
for Legal/Juridisk research domanen.

Implementeret: 2025-12-12
Baseret pa: web3_kommandanter.py struktur
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


class LegalHistorikerKommandant(HistorikerKommandant):
    """
    Historiker specialiseret i Legal/Juridisk viden.

    Tracker:
    - Lovgivning evolution og aendringer
    - Retsafgorelser og praecedens
    - Compliance krav (GDPR, AI Act, etc.)
    - Kontraktuel udvikling
    - Regulatoriske trends
    """

    def __init__(self, domain: str = "legal"):
        super().__init__(domain)
        self._events: List[KnowledgeEvent] = []
        self._patterns_cache: Dict[str, Pattern] = {}

    async def initialize(self) -> None:
        """Initialiser Legal Historiker."""
        await super().initialize()
        # Initialize legal-specific resources
        # Could load historical legal data from database here

    async def record_event(self, event: KnowledgeEvent) -> None:
        """Registrer et juridisk videns-event."""
        if event.domain != self.domain:
            event.domain = self.domain

        # Add legal-specific context
        if "jurisdiction" not in event.context:
            event.context["jurisdiction"] = self._infer_jurisdiction(event.topic)
        if "legal_area" not in event.context:
            event.context["legal_area"] = self._infer_legal_area(event.topic)

        self._events.append(event)

    async def get_timeline(
        self,
        topic: str,
        start: datetime,
        end: datetime
    ) -> Timeline:
        """Hent juridisk tidslinje for et emne."""
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
        """Analyser juridisk emne evolution."""
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
            confidence=0.70  # Legal predictions are inherently uncertain
        )

    async def find_patterns(
        self,
        window: timedelta
    ) -> List[Pattern]:
        """Find juridiske patterns."""
        end = datetime.utcnow()
        start = end - window

        # Filter events in window
        window_events = [
            e for e in self._events
            if start <= e.occurred_at <= end
        ]

        patterns = []

        # Look for jurisdiction activity patterns
        jurisdiction_counts = defaultdict(int)
        for event in window_events:
            jurisdiction = event.context.get("jurisdiction", "unknown")
            jurisdiction_counts[jurisdiction] += 1

        for jurisdiction, count in jurisdiction_counts.items():
            if count >= 3:
                strength = self._count_to_strength(count)
                patterns.append(Pattern(
                    name=f"{jurisdiction}_legal_activity",
                    description=f"Increased legal activity in {jurisdiction}",
                    domain=self.domain,
                    strength=strength,
                    occurrences=count,
                    first_seen=start,
                    last_seen=end,
                    related_topics=[jurisdiction]
                ))

        # Look for compliance change patterns
        compliance_events = [
            e for e in window_events
            if e.event_type == EventType.UPDATED
            or "compliance" in e.topic.lower()
            or "gdpr" in e.topic.lower()
            or "regulation" in e.topic.lower()
        ]

        if len(compliance_events) >= 2:
            patterns.append(Pattern(
                name="compliance_changes",
                description="Multiple compliance-related updates detected",
                domain=self.domain,
                strength=PatternStrength.MODERATE if len(compliance_events) < 5 else PatternStrength.STRONG,
                occurrences=len(compliance_events),
                first_seen=min(e.occurred_at for e in compliance_events),
                last_seen=max(e.occurred_at for e in compliance_events),
                related_topics=list(set(e.topic for e in compliance_events))
            ))

        # Look for contract dispute patterns
        dispute_events = [
            e for e in window_events
            if "dispute" in e.topic.lower()
            or "litigation" in e.topic.lower()
            or "breach" in e.topic.lower()
        ]

        if len(dispute_events) >= 2:
            patterns.append(Pattern(
                name="contract_disputes",
                description="Pattern of contract disputes or litigation",
                domain=self.domain,
                strength=PatternStrength.MODERATE if len(dispute_events) < 4 else PatternStrength.STRONG,
                occurrences=len(dispute_events),
                first_seen=min(e.occurred_at for e in dispute_events),
                last_seen=max(e.occurred_at for e in dispute_events),
                related_topics=list(set(e.topic for e in dispute_events))
            ))

        return patterns

    def _infer_jurisdiction(self, topic: str) -> str:
        """Udled jurisdiktion fra emne."""
        topic_lower = topic.lower()
        jurisdictions = {
            "eu": ["eu", "european", "gdpr", "ai act", "dma", "dsa"],
            "denmark": ["danish", "denmark", "dansk", "dk"],
            "usa": ["us", "usa", "american", "federal", "sec", "ftc"],
            "uk": ["uk", "british", "english law", "wales"],
            "international": ["international", "cross-border", "treaty"],
        }

        for jurisdiction, keywords in jurisdictions.items():
            if any(kw in topic_lower for kw in keywords):
                return jurisdiction

        return "general"

    def _infer_legal_area(self, topic: str) -> str:
        """Udled juridisk omrade fra emne."""
        topic_lower = topic.lower()
        areas = {
            "contract_law": ["contract", "agreement", "clause", "termination"],
            "compliance": ["compliance", "gdpr", "regulation", "audit"],
            "ip": ["patent", "trademark", "copyright", "intellectual property"],
            "corporate": ["corporate", "merger", "acquisition", "shareholder"],
            "employment": ["employment", "labor", "worker", "dismissal"],
            "litigation": ["litigation", "lawsuit", "court", "dispute"],
            "data_protection": ["data", "privacy", "personal data", "processing"],
        }

        for area, keywords in areas.items():
            if any(kw in topic_lower for kw in keywords):
                return area

        return "general"

    def _calculate_significance(self, event: KnowledgeEvent) -> float:
        """Beregn event significance."""
        base = 0.5

        # Event type matters
        if event.event_type in [EventType.CREATED, EventType.VALIDATED]:
            base += 0.15
        elif event.event_type in [EventType.INVALIDATED, EventType.DEPRECATED]:
            base += 0.25  # Legal invalidations are significant

        # Context matters
        if event.context.get("binding", False):
            base += 0.2
        if event.context.get("precedent", False):
            base += 0.15

        return min(base, 1.0)

    def _generate_event_note(self, event: KnowledgeEvent) -> str:
        """Generer note for event."""
        jurisdiction = event.context.get("jurisdiction", "")
        return f"[{jurisdiction.upper()}] {event.event_type.value}: {event.topic}"

    def _generate_timeline_summary(
        self,
        topic: str,
        entries: List[TimelineEntry]
    ) -> str:
        """Generer tidslinje opsummering."""
        if not entries:
            return f"No legal events found for {topic}"

        return (
            f"{len(entries)} legal events for {topic} "
            f"from {entries[0].timestamp.date()} to {entries[-1].timestamp.date()}"
        )

    def _identify_milestones(
        self,
        entries: List[TimelineEntry]
    ) -> List[Dict[str, Any]]:
        """Identificer vigtige juridiske milepale."""
        milestones = []
        for entry in entries:
            if entry.significance >= 0.7:
                milestones.append({
                    "date": entry.timestamp.isoformat(),
                    "event": entry.event.topic,
                    "jurisdiction": entry.event.context.get("jurisdiction", "unknown"),
                    "significance": entry.significance
                })
        return milestones

    def _identify_trends(self, entries: List[TimelineEntry]) -> List[str]:
        """Identificer juridiske trends fra entries."""
        trends = []

        # Count legal areas
        area_counts = defaultdict(int)
        for entry in entries:
            area = entry.event.context.get("legal_area", "general")
            area_counts[area] += 1

        # Identify dominant areas
        if area_counts.get("compliance", 0) > 5:
            trends.append("Increased compliance focus")
        if area_counts.get("data_protection", 0) > 3:
            trends.append("Growing data protection activity")
        if area_counts.get("litigation", 0) > 3:
            trends.append("Rising litigation trends")

        # Count event types
        type_counts = defaultdict(int)
        for entry in entries:
            type_counts[entry.event.event_type] += 1

        if type_counts[EventType.UPDATED] > type_counts.get(EventType.CREATED, 0):
            trends.append("Regulatory environment evolving rapidly")

        return trends

    def _generate_predictions(
        self,
        topic: str,
        trends: List[str]
    ) -> List[str]:
        """Generer forudsigelser baseret pa juridiske trends."""
        predictions = []

        if "Increased compliance focus" in trends:
            predictions.append(f"Expect stricter compliance requirements for {topic}")

        if "Growing data protection activity" in trends:
            predictions.append("Data protection will likely become more stringent")

        if "Regulatory environment evolving rapidly" in trends:
            predictions.append("Monitor for upcoming regulatory changes")

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


class LegalBibliotekarKommandant(BibliotekarKommandant):
    """
    Bibliotekar specialiseret i Legal/Juridisk viden.

    Organiserer:
    - Lovgivning og forordninger
    - Kontrakt skabeloner og analyser
    - Compliance dokumentation
    - Retsafgorelser
    - Juridiske analyser og notater
    """

    def __init__(self, domain: str = "legal"):
        super().__init__(domain)
        self._index: Dict[str, IndexEntry] = {}
        self._classifications: Dict[str, Classification] = {}
        self._content_store: Dict[str, Content] = {}

    async def initialize(self) -> None:
        """Initialiser Legal Bibliotekar."""
        await super().initialize()
        self._taxonomy = self._build_legal_taxonomy()

    async def classify(self, content: Content) -> Classification:
        """Klassificer juridisk indhold."""
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
            confidence=0.80  # Legal classification requires domain expertise
        )

        self._classifications[content.id] = classification
        self._content_store[content.id] = content

        return classification

    async def index(self, content: Content) -> IndexEntry:
        """Indekser juridisk indhold."""
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
        """Sog i juridisk biblioteket."""
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
        """Find relateret juridisk indhold."""
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
                        rel_type = "same_legal_area"
                    elif overlap:
                        rel_type = "shared_legal_concepts"
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
        """Hent juridisk taxonomi."""
        if not self._taxonomy:
            self._taxonomy = self._build_legal_taxonomy()
        return self._taxonomy

    def _build_legal_taxonomy(self) -> Taxonomy:
        """Byg juridisk-specifik taxonomi."""
        root_nodes = [
            TaxonomyNode(
                id="contract_law",
                name="Contract Law",
                description="Kontraktret og aftaler",
                children=[
                    TaxonomyNode(id="formation", name="Contract Formation"),
                    TaxonomyNode(id="performance", name="Performance"),
                    TaxonomyNode(id="breach", name="Breach & Remedies"),
                    TaxonomyNode(id="termination", name="Termination"),
                ]
            ),
            TaxonomyNode(
                id="compliance",
                name="Compliance",
                description="Regulatorisk overholdelse",
                children=[
                    TaxonomyNode(id="gdpr", name="GDPR"),
                    TaxonomyNode(id="ai_act", name="EU AI Act"),
                    TaxonomyNode(id="sector_specific", name="Sector-Specific"),
                    TaxonomyNode(id="internal_policies", name="Internal Policies"),
                ]
            ),
            TaxonomyNode(
                id="data_protection",
                name="Data Protection",
                description="Databeskyttelse og privacy",
                children=[
                    TaxonomyNode(id="data_processing", name="Data Processing"),
                    TaxonomyNode(id="data_subject_rights", name="Data Subject Rights"),
                    TaxonomyNode(id="data_transfers", name="International Transfers"),
                    TaxonomyNode(id="data_breaches", name="Data Breaches"),
                ]
            ),
            TaxonomyNode(
                id="ip",
                name="Intellectual Property",
                description="Immaterielle rettigheder",
                children=[
                    TaxonomyNode(id="patents", name="Patents"),
                    TaxonomyNode(id="trademarks", name="Trademarks"),
                    TaxonomyNode(id="copyrights", name="Copyrights"),
                    TaxonomyNode(id="trade_secrets", name="Trade Secrets"),
                ]
            ),
            TaxonomyNode(
                id="corporate",
                name="Corporate Law",
                description="Selskabsret",
                children=[
                    TaxonomyNode(id="governance", name="Corporate Governance"),
                    TaxonomyNode(id="ma", name="Mergers & Acquisitions"),
                    TaxonomyNode(id="shareholders", name="Shareholder Rights"),
                    TaxonomyNode(id="directors", name="Directors' Duties"),
                ]
            ),
            TaxonomyNode(
                id="employment",
                name="Employment Law",
                description="Ansaettelsesret",
                children=[
                    TaxonomyNode(id="hiring", name="Hiring & Onboarding"),
                    TaxonomyNode(id="terms", name="Terms & Conditions"),
                    TaxonomyNode(id="dismissal", name="Dismissal"),
                    TaxonomyNode(id="discrimination", name="Discrimination"),
                ]
            ),
            TaxonomyNode(
                id="litigation",
                name="Litigation",
                description="Retssager og tvistlosning",
                children=[
                    TaxonomyNode(id="civil", name="Civil Litigation"),
                    TaxonomyNode(id="arbitration", name="Arbitration"),
                    TaxonomyNode(id="mediation", name="Mediation"),
                    TaxonomyNode(id="enforcement", name="Enforcement"),
                ]
            ),
        ]

        return Taxonomy(
            domain=self.domain,
            root_nodes=root_nodes,
            total_categories=28,
            max_depth=2
        )

    def _determine_primary_category(self, content: Content) -> str:
        """Bestem primar juridisk kategori."""
        text = (content.title + " " + content.body).lower()

        categories = {
            "contract_law": ["contract", "agreement", "clause", "terms", "breach"],
            "compliance": ["compliance", "regulation", "audit", "policy", "requirements"],
            "data_protection": ["gdpr", "data protection", "privacy", "personal data", "processing"],
            "ip": ["patent", "trademark", "copyright", "intellectual property", "license"],
            "corporate": ["corporate", "governance", "shareholder", "merger", "acquisition"],
            "employment": ["employment", "employee", "labor", "dismissal", "worker"],
            "litigation": ["litigation", "court", "lawsuit", "dispute", "arbitration"],
        }

        scores = {}
        for cat, keywords in categories.items():
            scores[cat] = sum(1 for kw in keywords if kw in text)

        if max(scores.values()) == 0:
            return "uncategorized"

        return max(scores, key=scores.get)

    def _determine_secondary_categories(self, content: Content) -> List[str]:
        """Bestem sekundare juridiske kategorier."""
        primary = self._determine_primary_category(content)
        text = (content.title + " " + content.body).lower()

        secondary = []
        all_cats = ["contract_law", "compliance", "data_protection", "ip", "corporate", "employment", "litigation"]

        for cat in all_cats:
            if cat != primary:
                # Check if any keywords from this category appear
                if cat == "contract_law" and any(kw in text for kw in ["contract", "agreement"]):
                    secondary.append(cat)
                elif cat == "compliance" and any(kw in text for kw in ["compliance", "regulation"]):
                    secondary.append(cat)
                elif cat == "data_protection" and any(kw in text for kw in ["gdpr", "data", "privacy"]):
                    secondary.append(cat)

        return secondary[:2]

    def _extract_tags(self, content: Content) -> List[str]:
        """Udtrak tags fra juridisk indhold."""
        text = (content.title + " " + content.body).lower()
        tags = []

        # Jurisdiction tags
        jurisdictions = ["eu", "denmark", "usa", "uk", "international"]
        for j in jurisdictions:
            if j in text:
                tags.append(j)

        # Legal document type tags
        doc_types = ["contract", "policy", "memo", "opinion", "brief", "analysis"]
        for dt in doc_types:
            if dt in text:
                tags.append(dt)

        # Specific regulation tags
        regulations = ["gdpr", "ai-act", "nda", "dpa", "scc"]
        for r in regulations:
            if r in text:
                tags.append(r)

        return tags[:5]

    def _extract_terms(self, content: Content) -> List[str]:
        """Udtrak sogebare juridiske termer."""
        text = content.title + " " + content.body

        # Simple tokenization with legal stopwords
        legal_stopwords = {"the", "and", "for", "with", "shall", "may", "must", "herein", "thereof"}
        terms = []
        for word in text.split():
            word = word.strip(".,;:!?()[]{}\"'").lower()
            if len(word) >= 3 and word not in legal_stopwords:
                terms.append(word)

        return list(set(terms))[:50]

    def _calculate_boost(self, content: Content) -> float:
        """Beregn weight boost for juridisk indhold."""
        boost = 1.0

        # Recent legal content is more relevant
        age = datetime.utcnow() - content.created_at
        if age.days < 30:
            boost *= 1.5
        elif age.days < 90:
            boost *= 1.3
        elif age.days < 365:
            boost *= 1.1

        # Binding legal documents get boost
        if content.metadata.get("binding", False):
            boost *= 1.4

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
        """Byg facetter fra juridiske resultater."""
        category_counts = defaultdict(int)
        for r in results:
            category_counts[r.category] += 1

        return {
            "categories": [
                {"name": cat, "count": count}
                for cat, count in category_counts.items()
            ]
        }
