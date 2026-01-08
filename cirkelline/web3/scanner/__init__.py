"""
Scanner Module
==============
Technology intelligence and trend detection for Web3 & AI.

Components:
- GitHubMonitor: Track repositories, commits, issues
- ResearchScanner: Academic papers and conference proceedings
- TrendAnalyzer: AI-driven trend detection and prediction
"""

from cirkelline.web3.scanner.github_monitor import (
    GitHubMonitor,
    RepositoryInfo,
    CommitInfo,
    IssueInfo,
    get_github_monitor,
)

from cirkelline.web3.scanner.research_scanner import (
    ResearchScanner,
    Paper,
    ResearchSource,
    get_research_scanner,
)

from cirkelline.web3.scanner.trend_analyzer import (
    TrendAnalyzer,
    Trend,
    TrendSignal,
    TrendStrength,
    TechnologyFeed,
    get_trend_analyzer,
)

__all__ = [
    # GitHub
    'GitHubMonitor',
    'RepositoryInfo',
    'CommitInfo',
    'IssueInfo',
    'get_github_monitor',
    # Research
    'ResearchScanner',
    'Paper',
    'ResearchSource',
    'get_research_scanner',
    # Trends
    'TrendAnalyzer',
    'Trend',
    'TrendSignal',
    'TrendStrength',
    'TechnologyFeed',
    'get_trend_analyzer',
]


# ═══════════════════════════════════════════════════════════════════════════════
# SCANNER MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class ScannerManager:
    """
    Unified scanner management.

    Coordinates all scanning activities and aggregates feeds.
    """

    def __init__(self):
        self._github = get_github_monitor()
        self._research = get_research_scanner()
        self._trends = get_trend_analyzer()

    @property
    def github(self) -> GitHubMonitor:
        return self._github

    @property
    def research(self) -> ResearchScanner:
        return self._research

    @property
    def trends(self) -> TrendAnalyzer:
        return self._trends

    async def scan_all(self) -> TechnologyFeed:
        """Run all scanners and aggregate results."""
        # Gather from all sources
        github_data = await self._github.scan()
        research_data = await self._research.scan()

        # Analyze trends
        feed = await self._trends.analyze(
            github_feed=github_data,
            research_feed=research_data,
        )

        return feed

    def get_stats(self):
        return {
            "github": self._github.get_stats(),
            "research": self._research.get_stats(),
            "trends": self._trends.get_stats(),
        }


_scanner_manager: ScannerManager = None


def get_scanner_manager() -> ScannerManager:
    """Get singleton ScannerManager."""
    global _scanner_manager
    if _scanner_manager is None:
        _scanner_manager = ScannerManager()
    return _scanner_manager
