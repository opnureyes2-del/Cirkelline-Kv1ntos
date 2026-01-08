"""
Trend Analyzer
==============
AI-driven technology trend detection and prediction.

Responsibilities:
- Analyze signals from GitHub, research, social media
- Detect weak signals and early trends
- Predict emerging technologies and paradigm shifts
- Score technology relevance for Cirkelline ecosystem
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import Counter

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class TrendStrength(Enum):
    """Trend signal strength classification."""
    WEAK = "weak"           # Early signal, low confidence
    MODERATE = "moderate"   # Growing interest, medium confidence
    STRONG = "strong"       # Established trend, high confidence
    DOMINANT = "dominant"   # Industry-wide adoption


class TrendCategory(Enum):
    """Technology trend categories."""
    PROTOCOL = "protocol"
    CONSENSUS = "consensus"
    SCALING = "scaling"
    PRIVACY = "privacy"
    IDENTITY = "identity"
    AI_INTEGRATION = "ai_integration"
    TOKENOMICS = "tokenomics"
    GOVERNANCE = "governance"
    SECURITY = "security"
    INTEROPERABILITY = "interoperability"


class SignalSource(Enum):
    """Sources for trend signals."""
    GITHUB = "github"
    ARXIV = "arxiv"
    CONFERENCE = "conference"
    TWITTER = "twitter"
    REDDIT = "reddit"
    HACKERNEWS = "hackernews"
    BLOG = "blog"
    INTERNAL = "internal"


@dataclass
class TrendSignal:
    """A single trend signal from a source."""
    signal_id: str
    topic: str
    source: SignalSource
    strength: float  # 0.0-1.0
    timestamp: str
    context: str = ""
    keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "topic": self.topic,
            "source": self.source.value,
            "strength": round(self.strength, 3),
            "timestamp": self.timestamp,
            "keywords": self.keywords[:5],
        }


@dataclass
class Trend:
    """An identified technology trend."""
    trend_id: str
    name: str
    category: TrendCategory
    strength: TrendStrength
    description: str
    signals: List[TrendSignal] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    relevance_score: float = 0.0  # Relevance to Cirkelline
    momentum: float = 0.0  # Rate of growth (-1.0 to 1.0)
    first_detected: str = ""
    last_updated: str = ""
    prediction: str = ""  # Future outlook
    risk_level: str = "low"
    opportunities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trend_id": self.trend_id,
            "name": self.name,
            "category": self.category.value,
            "strength": self.strength.value,
            "description": self.description[:200],
            "signal_count": len(self.signals),
            "keywords": self.keywords[:10],
            "relevance_score": round(self.relevance_score, 3),
            "momentum": round(self.momentum, 3),
            "first_detected": self.first_detected,
            "prediction": self.prediction,
            "risk_level": self.risk_level,
            "opportunities": self.opportunities[:3],
        }


@dataclass
class TechnologyFeed:
    """Aggregated technology intelligence feed."""
    trends: List[Trend] = field(default_factory=list)
    signals: List[TrendSignal] = field(default_factory=list)
    top_technologies: List[str] = field(default_factory=list)
    weak_signals: List[str] = field(default_factory=list)  # Early/emerging
    recommendations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trends_count": len(self.trends),
            "signals_count": len(self.signals),
            "top_technologies": self.top_technologies[:10],
            "weak_signals": self.weak_signals[:5],
            "recommendations": self.recommendations[:5],
            "timestamp": self.timestamp,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# TREND DETECTION CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Technology keywords and their relevance to Cirkelline
TECHNOLOGY_RELEVANCE = {
    # High relevance (core to Cirkelline)
    "zero-knowledge": 1.0,
    "zkp": 1.0,
    "zk-snark": 1.0,
    "zk-stark": 1.0,
    "did": 0.95,
    "decentralized identity": 0.95,
    "verifiable credentials": 0.95,
    "multi-agent": 0.95,
    "ai agents": 0.95,
    "autonomous agents": 0.90,
    "federated learning": 0.90,
    "privacy-preserving": 0.90,
    "homomorphic encryption": 0.85,
    "secure multiparty": 0.85,
    "mpc": 0.85,

    # Medium-high relevance
    "layer 2": 0.80,
    "rollup": 0.80,
    "cross-chain": 0.75,
    "interoperability": 0.75,
    "dao governance": 0.75,
    "tokenomics": 0.70,
    "smart contract": 0.70,
    "llm": 0.70,
    "transformer": 0.65,
    "ipfs": 0.65,
    "arweave": 0.65,

    # Medium relevance
    "consensus": 0.60,
    "byzantine": 0.60,
    "defi": 0.55,
    "nft": 0.40,
    "metaverse": 0.30,

    # Post-quantum (future-critical)
    "post-quantum": 0.95,
    "lattice cryptography": 0.90,
    "quantum-resistant": 0.90,
}

# Trend detection thresholds
TREND_THRESHOLDS = {
    TrendStrength.WEAK: 0.2,
    TrendStrength.MODERATE: 0.4,
    TrendStrength.STRONG: 0.7,
    TrendStrength.DOMINANT: 0.9,
}


# ═══════════════════════════════════════════════════════════════════════════════
# TREND ANALYZER
# ═══════════════════════════════════════════════════════════════════════════════

class TrendAnalyzer:
    """
    AI-driven technology trend detection and prediction.

    Analyzes signals from multiple sources to identify
    emerging technologies, paradigm shifts, and opportunities.
    """

    def __init__(self):
        self._trends: Dict[str, Trend] = {}
        self._signals: List[TrendSignal] = []
        self._relevance_weights = TECHNOLOGY_RELEVANCE
        self._last_analysis: Optional[datetime] = None

        # Statistics
        self._stats = {
            "total_analyses": 0,
            "trends_identified": 0,
            "signals_processed": 0,
            "weak_signals_detected": 0,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════════

    def set_relevance_weight(self, keyword: str, weight: float) -> None:
        """Set relevance weight for a keyword (0.0-1.0)."""
        self._relevance_weights[keyword.lower()] = max(0.0, min(1.0, weight))

    def add_custom_keywords(self, keywords: Dict[str, float]) -> None:
        """Add custom keywords with weights."""
        for kw, weight in keywords.items():
            self.set_relevance_weight(kw, weight)

    # ═══════════════════════════════════════════════════════════════════════════
    # ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════

    async def analyze(
        self,
        github_feed: Any = None,
        research_feed: Any = None,
        social_data: Optional[Dict[str, Any]] = None,
    ) -> TechnologyFeed:
        """
        Analyze data from all sources to identify trends.

        Integrates GitHub activity, research papers, and social signals
        to detect and predict technology trends.
        """
        self._stats["total_analyses"] += 1
        self._last_analysis = datetime.utcnow()

        feed = TechnologyFeed()

        # Extract signals from sources
        if github_feed:
            signals = self._extract_github_signals(github_feed)
            self._signals.extend(signals)
            feed.signals.extend(signals)

        if research_feed:
            signals = self._extract_research_signals(research_feed)
            self._signals.extend(signals)
            feed.signals.extend(signals)

        if social_data:
            signals = self._extract_social_signals(social_data)
            self._signals.extend(signals)
            feed.signals.extend(signals)

        self._stats["signals_processed"] = len(self._signals)

        # Cluster signals into trends
        trends = self._cluster_into_trends(feed.signals)

        # Score and rank trends
        for trend in trends:
            self._score_trend(trend)
            self._calculate_momentum(trend)
            self._generate_prediction(trend)
            self._identify_opportunities(trend)
            self._trends[trend.trend_id] = trend

        feed.trends = sorted(trends, key=lambda t: t.relevance_score, reverse=True)
        self._stats["trends_identified"] = len(feed.trends)

        # Extract insights
        feed.top_technologies = self._get_top_technologies(feed.trends)
        feed.weak_signals = self._detect_weak_signals(feed.signals)
        feed.recommendations = self._generate_recommendations(feed.trends)

        self._stats["weak_signals_detected"] = len(feed.weak_signals)

        return feed

    def _extract_github_signals(self, github_feed: Any) -> List[TrendSignal]:
        """Extract trend signals from GitHub data."""
        signals = []

        # Process repositories
        if hasattr(github_feed, 'repositories'):
            for repo in github_feed.repositories:
                keywords = self._extract_keywords_from_text(
                    f"{repo.name} {repo.description}"
                )
                if keywords:
                    signal = TrendSignal(
                        signal_id=f"gh-{repo.full_name}",
                        topic=repo.name,
                        source=SignalSource.GITHUB,
                        strength=self._calculate_github_strength(repo),
                        timestamp=repo.updated_at or datetime.utcnow().isoformat(),
                        context=repo.description,
                        keywords=keywords,
                        metadata={
                            "stars": repo.stars,
                            "forks": repo.forks,
                            "language": repo.language,
                        },
                    )
                    signals.append(signal)

        # Process trending repos
        if hasattr(github_feed, 'trending_repos'):
            for repo in github_feed.trending_repos:
                keywords = self._extract_keywords_from_text(
                    f"{repo.name} {repo.description}"
                )
                if keywords:
                    signal = TrendSignal(
                        signal_id=f"gh-trending-{repo.full_name}",
                        topic=repo.name,
                        source=SignalSource.GITHUB,
                        strength=min(1.0, 0.5 + repo.stars / 10000),
                        timestamp=datetime.utcnow().isoformat(),
                        context=f"Trending: {repo.description}",
                        keywords=keywords,
                    )
                    signals.append(signal)

        return signals

    def _extract_research_signals(self, research_feed: Any) -> List[TrendSignal]:
        """Extract trend signals from research papers."""
        signals = []

        if hasattr(research_feed, 'papers'):
            for paper in research_feed.papers:
                keywords = self._extract_keywords_from_text(
                    f"{paper.title} {paper.abstract}"
                )
                keywords.extend(paper.keywords)

                if keywords:
                    signal = TrendSignal(
                        signal_id=f"arxiv-{paper.paper_id}",
                        topic=paper.title[:100],
                        source=SignalSource.ARXIV,
                        strength=paper.relevance_score,
                        timestamp=paper.published_date or datetime.utcnow().isoformat(),
                        context=paper.abstract[:200],
                        keywords=list(set(keywords)),
                        metadata={
                            "citations": paper.citations,
                            "category": paper.category.value if hasattr(paper.category, 'value') else str(paper.category),
                        },
                    )
                    signals.append(signal)

        # Process emerging topics
        if hasattr(research_feed, 'emerging_topics'):
            for topic in research_feed.emerging_topics:
                signal = TrendSignal(
                    signal_id=f"research-emerging-{topic.replace(' ', '-')}",
                    topic=topic,
                    source=SignalSource.CONFERENCE,
                    strength=0.6,
                    timestamp=datetime.utcnow().isoformat(),
                    context=f"Emerging research topic: {topic}",
                    keywords=[topic],
                )
                signals.append(signal)

        return signals

    def _extract_social_signals(self, social_data: Dict[str, Any]) -> List[TrendSignal]:
        """Extract trend signals from social media data."""
        signals = []

        # Twitter/X signals
        if "twitter" in social_data:
            for item in social_data["twitter"]:
                keywords = self._extract_keywords_from_text(item.get("text", ""))
                if keywords:
                    signal = TrendSignal(
                        signal_id=f"twitter-{item.get('id', 'unknown')}",
                        topic=keywords[0] if keywords else "unknown",
                        source=SignalSource.TWITTER,
                        strength=item.get("engagement", 0) / 1000,
                        timestamp=item.get("timestamp", datetime.utcnow().isoformat()),
                        context=item.get("text", "")[:200],
                        keywords=keywords,
                    )
                    signals.append(signal)

        # Reddit signals
        if "reddit" in social_data:
            for item in social_data["reddit"]:
                keywords = self._extract_keywords_from_text(
                    f"{item.get('title', '')} {item.get('text', '')}"
                )
                if keywords:
                    signal = TrendSignal(
                        signal_id=f"reddit-{item.get('id', 'unknown')}",
                        topic=item.get("title", "")[:100],
                        source=SignalSource.REDDIT,
                        strength=min(1.0, item.get("score", 0) / 5000),
                        timestamp=item.get("timestamp", datetime.utcnow().isoformat()),
                        context=item.get("text", "")[:200],
                        keywords=keywords,
                    )
                    signals.append(signal)

        return signals

    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """Extract relevant keywords from text."""
        text_lower = text.lower()
        found_keywords = []

        for keyword in self._relevance_weights.keys():
            if keyword in text_lower:
                found_keywords.append(keyword)

        return found_keywords

    def _calculate_github_strength(self, repo: Any) -> float:
        """Calculate signal strength from GitHub repo metrics."""
        strength = 0.0

        # Stars contribution
        if hasattr(repo, 'stars'):
            strength += min(0.4, repo.stars / 5000)

        # Forks contribution
        if hasattr(repo, 'forks'):
            strength += min(0.2, repo.forks / 1000)

        # Activity contribution (not archived)
        if hasattr(repo, 'is_archived') and not repo.is_archived:
            strength += 0.2

        # Topic relevance
        if hasattr(repo, 'topics'):
            relevant_topics = sum(
                1 for t in repo.topics
                if t.lower() in self._relevance_weights
            )
            strength += min(0.2, relevant_topics * 0.05)

        return min(1.0, strength)

    # ═══════════════════════════════════════════════════════════════════════════
    # TREND CLUSTERING
    # ═══════════════════════════════════════════════════════════════════════════

    def _cluster_into_trends(self, signals: List[TrendSignal]) -> List[Trend]:
        """Cluster signals into coherent trends."""
        # Group signals by keywords
        keyword_signals: Dict[str, List[TrendSignal]] = {}

        for signal in signals:
            for keyword in signal.keywords:
                kw_lower = keyword.lower()
                if kw_lower not in keyword_signals:
                    keyword_signals[kw_lower] = []
                keyword_signals[kw_lower].append(signal)

        # Create trends from clusters
        trends = []
        processed_keywords = set()

        for keyword, kw_signals in sorted(
            keyword_signals.items(),
            key=lambda x: len(x[1]),
            reverse=True
        ):
            if keyword in processed_keywords:
                continue

            if len(kw_signals) < 2:
                continue  # Need multiple signals

            # Find related keywords
            related = self._find_related_keywords(keyword, keyword_signals)
            for r in related:
                processed_keywords.add(r)

            # Create trend
            trend = Trend(
                trend_id=f"trend-{keyword.replace(' ', '-')}",
                name=keyword.title(),
                category=self._categorize_trend(keyword, kw_signals),
                strength=self._determine_trend_strength(kw_signals),
                description=self._generate_trend_description(keyword, kw_signals),
                signals=kw_signals,
                keywords=[keyword] + list(related)[:5],
                first_detected=min(s.timestamp for s in kw_signals),
                last_updated=max(s.timestamp for s in kw_signals),
            )
            trends.append(trend)

            processed_keywords.add(keyword)

        return trends

    def _find_related_keywords(
        self,
        keyword: str,
        keyword_signals: Dict[str, List[TrendSignal]],
    ) -> set:
        """Find keywords that co-occur with the given keyword."""
        related = set()
        signals = keyword_signals.get(keyword, [])

        for signal in signals:
            for kw in signal.keywords:
                if kw.lower() != keyword.lower():
                    related.add(kw.lower())

        return related

    def _categorize_trend(
        self,
        keyword: str,
        signals: List[TrendSignal],
    ) -> TrendCategory:
        """Categorize a trend based on keyword and signals."""
        keyword_lower = keyword.lower()

        # Category mapping
        category_keywords = {
            TrendCategory.PRIVACY: ["privacy", "zkp", "zero-knowledge", "zk-snark", "zk-stark", "homomorphic"],
            TrendCategory.IDENTITY: ["did", "identity", "verifiable", "credentials", "ssi"],
            TrendCategory.AI_INTEGRATION: ["ai", "llm", "transformer", "agent", "ml", "learning"],
            TrendCategory.SCALING: ["layer 2", "rollup", "scaling", "sharding"],
            TrendCategory.INTEROPERABILITY: ["cross-chain", "interop", "bridge"],
            TrendCategory.GOVERNANCE: ["dao", "governance", "voting"],
            TrendCategory.TOKENOMICS: ["token", "economics", "incentive"],
            TrendCategory.SECURITY: ["security", "audit", "vulnerability"],
            TrendCategory.CONSENSUS: ["consensus", "byzantine", "pbft", "raft"],
            TrendCategory.PROTOCOL: ["protocol", "smart contract", "evm"],
        }

        for category, keywords in category_keywords.items():
            if any(kw in keyword_lower for kw in keywords):
                return category

        return TrendCategory.PROTOCOL

    def _determine_trend_strength(self, signals: List[TrendSignal]) -> TrendStrength:
        """Determine trend strength from signals."""
        if not signals:
            return TrendStrength.WEAK

        avg_strength = sum(s.strength for s in signals) / len(signals)
        signal_count_bonus = min(0.3, len(signals) * 0.03)
        total_strength = avg_strength + signal_count_bonus

        for strength, threshold in sorted(
            TREND_THRESHOLDS.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if total_strength >= threshold:
                return strength

        return TrendStrength.WEAK

    def _generate_trend_description(
        self,
        keyword: str,
        signals: List[TrendSignal],
    ) -> str:
        """Generate description for a trend."""
        sources = Counter(s.source.value for s in signals)
        top_sources = sources.most_common(2)

        source_str = " and ".join(s[0] for s in top_sources)
        return (
            f"Emerging activity around {keyword} detected across {source_str}. "
            f"Based on {len(signals)} signals with varying strength levels."
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # SCORING & PREDICTION
    # ═══════════════════════════════════════════════════════════════════════════

    def _score_trend(self, trend: Trend) -> None:
        """Score trend relevance to Cirkelline ecosystem."""
        score = 0.0

        # Keyword relevance
        for keyword in trend.keywords:
            kw_lower = keyword.lower()
            if kw_lower in self._relevance_weights:
                score += self._relevance_weights[kw_lower]

        # Normalize by keyword count
        if trend.keywords:
            score /= len(trend.keywords)

        # Boost for signal count
        score += min(0.2, len(trend.signals) * 0.02)

        # Boost for strength
        strength_boost = {
            TrendStrength.WEAK: 0.0,
            TrendStrength.MODERATE: 0.05,
            TrendStrength.STRONG: 0.1,
            TrendStrength.DOMINANT: 0.15,
        }
        score += strength_boost.get(trend.strength, 0)

        trend.relevance_score = min(1.0, score)

    def _calculate_momentum(self, trend: Trend) -> None:
        """Calculate trend momentum (growth rate)."""
        if len(trend.signals) < 2:
            trend.momentum = 0.0
            return

        # Sort by timestamp
        sorted_signals = sorted(trend.signals, key=lambda s: s.timestamp)

        # Compare recent vs older signals
        midpoint = len(sorted_signals) // 2
        older_avg = sum(s.strength for s in sorted_signals[:midpoint]) / midpoint
        recent_avg = sum(s.strength for s in sorted_signals[midpoint:]) / (len(sorted_signals) - midpoint)

        # Momentum is the relative change
        if older_avg > 0:
            trend.momentum = (recent_avg - older_avg) / older_avg
        else:
            trend.momentum = recent_avg

        trend.momentum = max(-1.0, min(1.0, trend.momentum))

    def _generate_prediction(self, trend: Trend) -> None:
        """Generate future outlook for trend."""
        if trend.momentum > 0.3:
            trend.prediction = "Strong growth expected. Consider early adoption and integration planning."
        elif trend.momentum > 0.1:
            trend.prediction = "Steady growth. Monitor for maturity signals before major investment."
        elif trend.momentum > -0.1:
            trend.prediction = "Stable. Established technology with predictable trajectory."
        elif trend.momentum > -0.3:
            trend.prediction = "Declining interest. Evaluate alternatives unless core dependency."
        else:
            trend.prediction = "Significant decline. Consider migration strategy if currently in use."

        # Risk assessment
        if trend.strength == TrendStrength.WEAK:
            trend.risk_level = "high"
        elif trend.strength == TrendStrength.MODERATE:
            trend.risk_level = "medium"
        else:
            trend.risk_level = "low"

    def _identify_opportunities(self, trend: Trend) -> None:
        """Identify strategic opportunities from trend."""
        opportunities = []

        # High relevance + strong momentum
        if trend.relevance_score > 0.7 and trend.momentum > 0.2:
            opportunities.append(f"Early mover advantage in {trend.name} integration")

        # Privacy/security trends
        if trend.category in [TrendCategory.PRIVACY, TrendCategory.SECURITY]:
            opportunities.append(f"Enhance Cirkelline security posture with {trend.name}")

        # Identity trends
        if trend.category == TrendCategory.IDENTITY:
            opportunities.append(f"Strengthen DID infrastructure using {trend.name}")

        # AI trends
        if trend.category == TrendCategory.AI_INTEGRATION:
            opportunities.append(f"Agent capability enhancement via {trend.name}")

        # Default opportunity
        if not opportunities and trend.relevance_score > 0.5:
            opportunities.append(f"Research {trend.name} for potential integration")

        trend.opportunities = opportunities

    # ═══════════════════════════════════════════════════════════════════════════
    # INSIGHTS
    # ═══════════════════════════════════════════════════════════════════════════

    def _get_top_technologies(self, trends: List[Trend]) -> List[str]:
        """Get top technologies by relevance and strength."""
        # Combine relevance and momentum
        scored = [
            (t.name, t.relevance_score + (t.momentum * 0.2))
            for t in trends
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in scored[:10]]

    def _detect_weak_signals(self, signals: List[TrendSignal]) -> List[str]:
        """Detect weak signals (early/emerging trends)."""
        weak = []

        # Find signals with low strength but high relevance keywords
        for signal in signals:
            if signal.strength < 0.3:
                for keyword in signal.keywords:
                    kw_lower = keyword.lower()
                    if kw_lower in self._relevance_weights:
                        if self._relevance_weights[kw_lower] > 0.7:
                            weak.append(f"Early signal: {keyword} ({signal.source.value})")

        return list(set(weak))[:10]

    def _generate_recommendations(self, trends: List[Trend]) -> List[str]:
        """Generate strategic recommendations."""
        recommendations = []

        # High relevance trends
        high_relevance = [t for t in trends if t.relevance_score > 0.7]
        if high_relevance:
            recommendations.append(
                f"Priority: Investigate {high_relevance[0].name} for integration"
            )

        # Growing trends
        growing = [t for t in trends if t.momentum > 0.3]
        if growing:
            recommendations.append(
                f"Watch: {growing[0].name} showing strong growth momentum"
            )

        # Privacy/security trends
        security_trends = [
            t for t in trends
            if t.category in [TrendCategory.PRIVACY, TrendCategory.SECURITY]
            and t.strength in [TrendStrength.STRONG, TrendStrength.DOMINANT]
        ]
        if security_trends:
            recommendations.append(
                f"Security: Adopt {security_trends[0].name} to strengthen defenses"
            )

        # Post-quantum awareness
        pq_trends = [
            t for t in trends
            if any("quantum" in kw.lower() for kw in t.keywords)
        ]
        if pq_trends:
            recommendations.append(
                "Strategic: Begin post-quantum cryptography migration planning"
            )

        return recommendations[:5]

    # ═══════════════════════════════════════════════════════════════════════════
    # QUERIES
    # ═══════════════════════════════════════════════════════════════════════════

    def get_trend(self, trend_id: str) -> Optional[Trend]:
        """Get trend by ID."""
        return self._trends.get(trend_id)

    def get_trends_by_category(self, category: TrendCategory) -> List[Trend]:
        """Get all trends in a category."""
        return [t for t in self._trends.values() if t.category == category]

    def get_high_relevance_trends(self, threshold: float = 0.7) -> List[Trend]:
        """Get trends with high relevance to Cirkelline."""
        return [
            t for t in self._trends.values()
            if t.relevance_score >= threshold
        ]

    def get_emerging_trends(self) -> List[Trend]:
        """Get weak/early-stage trends with potential."""
        return [
            t for t in self._trends.values()
            if t.strength == TrendStrength.WEAK and t.momentum > 0.1
        ]

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get analyzer statistics."""
        return {
            **self._stats,
            "active_trends": len(self._trends),
            "total_signals": len(self._signals),
            "keyword_count": len(self._relevance_weights),
            "last_analysis": self._last_analysis.isoformat() if self._last_analysis else None,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_analyzer_instance: Optional[TrendAnalyzer] = None


def get_trend_analyzer() -> TrendAnalyzer:
    """Get singleton TrendAnalyzer instance."""
    global _analyzer_instance

    if _analyzer_instance is None:
        _analyzer_instance = TrendAnalyzer()

    return _analyzer_instance
