"""
Research Scanner
================
Scan academic databases and research publications.

Responsibilities:
- Monitor arXiv, CiteSeerX, Google Scholar
- Track AI/Web3 conference proceedings
- Extract keywords, abstracts, citation trends
- Identify emerging research directions
"""

import logging
import asyncio
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class ResearchSource(Enum):
    """Academic research sources."""
    ARXIV = "arxiv"
    NEURIPS = "neurips"
    ICML = "icml"
    ICLR = "iclr"
    AAAI = "aaai"
    ACL = "acl"
    IEEE = "ieee"
    CRYPTO = "crypto"
    EUROCRYPT = "eurocrypt"
    CCS = "ccs"  # ACM CCS


class PaperCategory(Enum):
    """Research paper categories."""
    AI_ML = "ai_ml"
    CRYPTOGRAPHY = "cryptography"
    BLOCKCHAIN = "blockchain"
    DISTRIBUTED_SYSTEMS = "distributed_systems"
    SECURITY = "security"
    PRIVACY = "privacy"
    ECONOMICS = "economics"
    OTHER = "other"


@dataclass
class Author:
    """Paper author information."""
    name: str
    affiliation: str = ""
    h_index: int = 0


@dataclass
class Paper:
    """Academic paper information."""
    paper_id: str
    title: str
    abstract: str
    authors: List[Author] = field(default_factory=list)
    source: ResearchSource = ResearchSource.ARXIV
    category: PaperCategory = PaperCategory.OTHER
    keywords: List[str] = field(default_factory=list)
    published_date: str = ""
    url: str = ""
    citations: int = 0
    relevance_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "abstract": self.abstract[:300] + "..." if len(self.abstract) > 300 else self.abstract,
            "authors": [a.name for a in self.authors],
            "source": self.source.value,
            "category": self.category.value,
            "keywords": self.keywords,
            "published_date": self.published_date,
            "citations": self.citations,
            "relevance_score": round(self.relevance_score, 3),
        }


@dataclass
class ResearchFeed:
    """Aggregated research feed."""
    papers: List[Paper] = field(default_factory=list)
    top_keywords: List[str] = field(default_factory=list)
    emerging_topics: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "papers_count": len(self.papers),
            "top_keywords": self.top_keywords[:10],
            "emerging_topics": self.emerging_topics[:5],
            "timestamp": self.timestamp,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SEARCH KEYWORDS
# ═══════════════════════════════════════════════════════════════════════════════

# Keywords for Web3/AI research
SEARCH_KEYWORDS = {
    "web3": [
        "blockchain consensus",
        "smart contract security",
        "decentralized finance",
        "zero knowledge proofs",
        "zkSNARK",
        "zkSTARK",
        "verifiable computation",
        "decentralized identity",
        "cross-chain",
        "layer 2 scaling",
        "MEV extraction",
        "tokenomics",
        "DAO governance",
    ],
    "ai": [
        "large language models",
        "transformer architecture",
        "reinforcement learning",
        "multi-agent systems",
        "federated learning",
        "differential privacy",
        "AI alignment",
        "neural architecture search",
        "in-context learning",
        "chain of thought",
        "AI agents",
        "autonomous agents",
    ],
    "crypto": [
        "post-quantum cryptography",
        "homomorphic encryption",
        "secure multiparty computation",
        "trusted execution environment",
        "lattice cryptography",
        "threshold signatures",
    ],
}

# arXiv categories to monitor
ARXIV_CATEGORIES = [
    "cs.CR",   # Cryptography and Security
    "cs.DC",   # Distributed Computing
    "cs.AI",   # Artificial Intelligence
    "cs.LG",   # Machine Learning
    "cs.CL",   # Computation and Language
    "cs.MA",   # Multi-Agent Systems
    "econ.TH", # Economic Theory
    "q-fin.TR", # Trading and Market Microstructure
]


# ═══════════════════════════════════════════════════════════════════════════════
# RESEARCH SCANNER
# ═══════════════════════════════════════════════════════════════════════════════

class ResearchScanner:
    """
    Academic research monitoring system.

    Scans research databases for relevant papers
    in Web3, AI, and cryptography domains.
    """

    def __init__(self):
        self._sources: List[ResearchSource] = [
            ResearchSource.ARXIV,
            ResearchSource.NEURIPS,
            ResearchSource.ICML,
        ]
        self._keywords = SEARCH_KEYWORDS
        self._categories = ARXIV_CATEGORIES

        # Cache
        self._paper_cache: Dict[str, Paper] = {}
        self._last_scan: Optional[datetime] = None

        # Statistics
        self._stats = {
            "total_scans": 0,
            "papers_found": 0,
            "sources_active": len(self._sources),
            "api_calls": 0,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════════

    def add_keywords(self, category: str, keywords: List[str]) -> None:
        """Add search keywords to a category."""
        if category not in self._keywords:
            self._keywords[category] = []
        self._keywords[category].extend(keywords)

    def add_source(self, source: ResearchSource) -> None:
        """Add research source to scan."""
        if source not in self._sources:
            self._sources.append(source)
            self._stats["sources_active"] = len(self._sources)

    # ═══════════════════════════════════════════════════════════════════════════
    # SCANNING
    # ═══════════════════════════════════════════════════════════════════════════

    async def scan(self) -> ResearchFeed:
        """
        Perform full scan of research sources.

        Returns aggregated feed of papers and trends.
        """
        self._stats["total_scans"] += 1
        self._last_scan = datetime.utcnow()

        feed = ResearchFeed()

        # Scan each source
        for source in self._sources:
            try:
                papers = await self._scan_source(source)
                feed.papers.extend(papers)
            except Exception as e:
                logger.error(f"Error scanning {source.value}: {e}")

        # Calculate relevance scores
        self._calculate_relevance(feed.papers)

        # Sort by relevance
        feed.papers.sort(key=lambda p: p.relevance_score, reverse=True)

        # Extract top keywords and trends
        feed.top_keywords = self._extract_keywords(feed.papers)
        feed.emerging_topics = self._identify_emerging_topics(feed.papers)

        self._stats["papers_found"] = len(feed.papers)
        return feed

    async def scan_arxiv(
        self,
        query: str,
        max_results: int = 20,
    ) -> List[Paper]:
        """Scan arXiv for papers matching query."""
        self._stats["api_calls"] += 1

        # Mock arXiv response (in production, use arxiv API)
        papers = []

        # Generate mock papers for testing
        mock_titles = [
            "Advances in Zero-Knowledge Proofs for Blockchain Scalability",
            "Federated Learning with Differential Privacy Guarantees",
            "Multi-Agent Reinforcement Learning in Decentralized Systems",
            "Post-Quantum Cryptographic Primitives for Secure Communication",
            "On the Security of Smart Contract Languages",
        ]

        for i, title in enumerate(mock_titles[:max_results]):
            if query.lower() in title.lower() or not query:
                paper = Paper(
                    paper_id=f"arxiv:{2312 + i}.{10000 + i}",
                    title=title,
                    abstract=f"This paper presents novel approaches to {title.lower()}...",
                    authors=[Author(name=f"Researcher {i}")],
                    source=ResearchSource.ARXIV,
                    published_date=datetime.utcnow().isoformat(),
                )
                papers.append(paper)
                self._paper_cache[paper.paper_id] = paper

        return papers

    async def _scan_source(self, source: ResearchSource) -> List[Paper]:
        """Scan a specific research source."""
        self._stats["api_calls"] += 1

        if source == ResearchSource.ARXIV:
            # Scan arXiv with Web3/AI keywords
            all_papers = []
            for category, keywords in self._keywords.items():
                for keyword in keywords[:3]:  # Limit per keyword
                    papers = await self.scan_arxiv(keyword, max_results=5)
                    all_papers.extend(papers)
            return all_papers

        # Other sources would have similar implementations
        return []

    # ═══════════════════════════════════════════════════════════════════════════
    # ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════

    def _calculate_relevance(self, papers: List[Paper]) -> None:
        """Calculate relevance score for each paper."""
        all_keywords = []
        for keywords in self._keywords.values():
            all_keywords.extend(keywords)

        for paper in papers:
            score = 0.0

            # Keyword matching in title
            title_lower = paper.title.lower()
            for keyword in all_keywords:
                if keyword.lower() in title_lower:
                    score += 0.2

            # Keyword matching in abstract
            abstract_lower = paper.abstract.lower()
            for keyword in all_keywords:
                if keyword.lower() in abstract_lower:
                    score += 0.1

            # Citation bonus
            if paper.citations > 0:
                score += min(0.3, paper.citations / 100)

            # Recency bonus (papers from last 30 days)
            score += 0.1

            paper.relevance_score = min(1.0, score)

    def _extract_keywords(self, papers: List[Paper]) -> List[str]:
        """Extract most common keywords from papers."""
        keyword_counts: Dict[str, int] = {}

        for paper in papers:
            # Extract keywords from title
            words = re.findall(r'\b[A-Za-z]{4,}\b', paper.title.lower())
            for word in words:
                keyword_counts[word] = keyword_counts.get(word, 0) + 1

            # Count paper keywords
            for keyword in paper.keywords:
                keyword_counts[keyword.lower()] = keyword_counts.get(keyword.lower(), 0) + 2

        # Sort by count
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        return [k for k, _ in sorted_keywords[:20]]

    def _identify_emerging_topics(self, papers: List[Paper]) -> List[str]:
        """Identify emerging research topics."""
        # Simple heuristic: topics that appear in recent high-relevance papers
        emerging = set()

        for paper in papers[:10]:  # Top 10 by relevance
            for keyword in paper.keywords:
                emerging.add(keyword)

            # Extract key phrases from title
            if "zero knowledge" in paper.title.lower():
                emerging.add("zero-knowledge proofs")
            if "federated" in paper.title.lower():
                emerging.add("federated learning")
            if "multi-agent" in paper.title.lower():
                emerging.add("multi-agent systems")

        return list(emerging)[:10]

    def categorize_paper(self, paper: Paper) -> PaperCategory:
        """Categorize a paper based on content."""
        title_abstract = (paper.title + " " + paper.abstract).lower()

        if any(k in title_abstract for k in ["blockchain", "smart contract", "defi", "dao"]):
            return PaperCategory.BLOCKCHAIN
        elif any(k in title_abstract for k in ["cryptograph", "encryption", "zero knowledge"]):
            return PaperCategory.CRYPTOGRAPHY
        elif any(k in title_abstract for k in ["machine learning", "neural", "transformer", "llm"]):
            return PaperCategory.AI_ML
        elif any(k in title_abstract for k in ["privacy", "differential privacy"]):
            return PaperCategory.PRIVACY
        elif any(k in title_abstract for k in ["security", "vulnerability", "attack"]):
            return PaperCategory.SECURITY
        elif any(k in title_abstract for k in ["distributed", "consensus", "byzantine"]):
            return PaperCategory.DISTRIBUTED_SYSTEMS
        elif any(k in title_abstract for k in ["economic", "incentive", "game theory"]):
            return PaperCategory.ECONOMICS

        return PaperCategory.OTHER

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get scanner statistics."""
        return {
            **self._stats,
            "cache_size": len(self._paper_cache),
            "keyword_categories": len(self._keywords),
            "total_keywords": sum(len(kw) for kw in self._keywords.values()),
            "last_scan": self._last_scan.isoformat() if self._last_scan else None,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_scanner_instance: Optional[ResearchScanner] = None


def get_research_scanner() -> ResearchScanner:
    """Get singleton ResearchScanner instance."""
    global _scanner_instance

    if _scanner_instance is None:
        _scanner_instance = ResearchScanner()

    return _scanner_instance
