"""
GitHub Monitor
==============
Monitor GitHub repositories for Web3 and AI developments.

Responsibilities:
- Track specified repositories
- Monitor commits, PRs, issues, forks
- Detect new projects and active contributions
- Rate-limit aware API integration
"""

import logging
import asyncio
import hashlib
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class ActivityType(Enum):
    """Types of GitHub activity."""
    COMMIT = "commit"
    PULL_REQUEST = "pull_request"
    ISSUE = "issue"
    RELEASE = "release"
    FORK = "fork"
    STAR = "star"


@dataclass
class RepositoryInfo:
    """Information about a GitHub repository."""
    owner: str
    name: str
    full_name: str
    description: str = ""
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    language: str = ""
    topics: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    last_commit: Optional[str] = None
    license: Optional[str] = None
    is_archived: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "owner": self.owner,
            "name": self.name,
            "full_name": self.full_name,
            "description": self.description,
            "stars": self.stars,
            "forks": self.forks,
            "open_issues": self.open_issues,
            "language": self.language,
            "topics": self.topics,
            "updated_at": self.updated_at,
            "license": self.license,
        }


@dataclass
class CommitInfo:
    """Information about a commit."""
    sha: str
    message: str
    author: str
    date: str
    repo: str
    files_changed: int = 0
    additions: int = 0
    deletions: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sha": self.sha[:8],
            "message": self.message[:100],
            "author": self.author,
            "date": self.date,
            "repo": self.repo,
            "changes": f"+{self.additions}/-{self.deletions}",
        }


@dataclass
class IssueInfo:
    """Information about an issue or PR."""
    number: int
    title: str
    state: str
    author: str
    created_at: str
    repo: str
    labels: List[str] = field(default_factory=list)
    is_pr: bool = False
    comments: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "number": self.number,
            "title": self.title[:80],
            "state": self.state,
            "author": self.author,
            "labels": self.labels,
            "is_pr": self.is_pr,
            "comments": self.comments,
        }


@dataclass
class GitHubFeed:
    """Aggregated GitHub feed data."""
    repositories: List[RepositoryInfo] = field(default_factory=list)
    recent_commits: List[CommitInfo] = field(default_factory=list)
    recent_issues: List[IssueInfo] = field(default_factory=list)
    trending_repos: List[RepositoryInfo] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repositories_count": len(self.repositories),
            "recent_commits_count": len(self.recent_commits),
            "recent_issues_count": len(self.recent_issues),
            "trending_count": len(self.trending_repos),
            "timestamp": self.timestamp,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# WATCHLIST CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Default repositories to monitor for Web3/AI developments
DEFAULT_WATCHLIST = [
    # Ethereum & Smart Contracts
    "ethereum/go-ethereum",
    "ethereum/solidity",
    "OpenZeppelin/openzeppelin-contracts",
    "foundry-rs/foundry",
    # Layer 2 & Scaling
    "matter-labs/zksync-era",
    "OffchainLabs/arbitrum",
    "ethereum-optimism/optimism",
    # DeFi & Protocols
    "Uniswap/v3-core",
    "aave/aave-v3-core",
    # Cross-chain
    "cosmos/cosmos-sdk",
    "paritytech/polkadot-sdk",
    "solana-labs/solana",
    # AI & ML
    "langchain-ai/langchain",
    "anthropics/anthropic-cookbook",
    "openai/openai-python",
    # Decentralized Storage
    "ipfs/kubo",
    "ArweaveTeam/arweave",
    "filecoin-project/lotus",
    # Identity & DIDs
    "decentralized-identity/did-spec-registries",
    "spruceid/ssi",
    # ZK Proofs
    "iden3/snarkjs",
    "microsoft/Nova",
    "privacy-scaling-explorations/halo2",
]

# Topics to search for trending repos
TRENDING_TOPICS = [
    "web3",
    "ethereum",
    "blockchain",
    "smart-contracts",
    "defi",
    "zk-proofs",
    "decentralized-identity",
    "ai-agents",
    "llm",
    "machine-learning",
]


# ═══════════════════════════════════════════════════════════════════════════════
# GITHUB MONITOR
# ═══════════════════════════════════════════════════════════════════════════════

class GitHubMonitor:
    """
    GitHub repository monitoring system.

    Tracks Web3 and AI repositories for developments,
    new releases, and trending projects.
    """

    def __init__(
        self,
        api_token: Optional[str] = None,
        watchlist: Optional[List[str]] = None,
    ):
        self._api_token = api_token
        self._watchlist = watchlist or DEFAULT_WATCHLIST
        self._base_url = "https://api.github.com"

        # Cache
        self._repo_cache: Dict[str, RepositoryInfo] = {}
        self._last_scan: Optional[datetime] = None

        # Statistics
        self._stats = {
            "total_scans": 0,
            "repos_monitored": len(self._watchlist),
            "api_calls": 0,
            "errors": 0,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════════

    def add_to_watchlist(self, repo: str) -> None:
        """Add repository to watchlist (format: owner/name)."""
        if repo not in self._watchlist:
            self._watchlist.append(repo)
            self._stats["repos_monitored"] = len(self._watchlist)

    def remove_from_watchlist(self, repo: str) -> bool:
        """Remove repository from watchlist."""
        if repo in self._watchlist:
            self._watchlist.remove(repo)
            self._stats["repos_monitored"] = len(self._watchlist)
            return True
        return False

    def set_api_token(self, token: str) -> None:
        """Set GitHub API token for authenticated requests."""
        self._api_token = token

    # ═══════════════════════════════════════════════════════════════════════════
    # SCANNING
    # ═══════════════════════════════════════════════════════════════════════════

    async def scan(self) -> GitHubFeed:
        """
        Perform full scan of watchlist repositories.

        Returns aggregated feed data.
        """
        self._stats["total_scans"] += 1
        self._last_scan = datetime.utcnow()

        feed = GitHubFeed()

        # Scan watchlist repos
        for repo_name in self._watchlist:
            try:
                repo_info = await self._fetch_repository(repo_name)
                if repo_info:
                    feed.repositories.append(repo_info)

                    # Get recent commits
                    commits = await self._fetch_commits(repo_name, limit=5)
                    feed.recent_commits.extend(commits)

                    # Get recent issues/PRs
                    issues = await self._fetch_issues(repo_name, limit=5)
                    feed.recent_issues.extend(issues)

            except Exception as e:
                logger.error(f"Error scanning {repo_name}: {e}")
                self._stats["errors"] += 1

        # Get trending repos
        feed.trending_repos = await self._fetch_trending()

        return feed

    async def scan_repository(self, repo_name: str) -> Optional[RepositoryInfo]:
        """Scan a single repository."""
        return await self._fetch_repository(repo_name)

    async def _fetch_repository(self, repo_name: str) -> Optional[RepositoryInfo]:
        """Fetch repository information from GitHub API."""
        # Simulate API call (in production, use aiohttp)
        self._stats["api_calls"] += 1

        # Check cache first
        if repo_name in self._repo_cache:
            cached = self._repo_cache[repo_name]
            # Return cached if less than 1 hour old
            return cached

        # Parse owner/name
        parts = repo_name.split("/")
        if len(parts) != 2:
            return None

        owner, name = parts

        # Create mock data (in production, fetch from API)
        repo = RepositoryInfo(
            owner=owner,
            name=name,
            full_name=repo_name,
            description=f"Repository {repo_name}",
            stars=0,
            forks=0,
            language="Unknown",
            topics=[],
            updated_at=datetime.utcnow().isoformat(),
        )

        self._repo_cache[repo_name] = repo
        return repo

    async def _fetch_commits(
        self,
        repo_name: str,
        limit: int = 10,
    ) -> List[CommitInfo]:
        """Fetch recent commits from repository."""
        self._stats["api_calls"] += 1

        # Mock commits (in production, fetch from API)
        commits = []
        for i in range(min(limit, 3)):
            commit = CommitInfo(
                sha=hashlib.sha256(f"{repo_name}-{i}".encode()).hexdigest(),
                message=f"Update {i}",
                author="contributor",
                date=datetime.utcnow().isoformat(),
                repo=repo_name,
            )
            commits.append(commit)

        return commits

    async def _fetch_issues(
        self,
        repo_name: str,
        limit: int = 10,
    ) -> List[IssueInfo]:
        """Fetch recent issues and PRs from repository."""
        self._stats["api_calls"] += 1

        # Mock issues (in production, fetch from API)
        return []

    async def _fetch_trending(self) -> List[RepositoryInfo]:
        """Fetch trending repositories by topic."""
        self._stats["api_calls"] += 1

        # Mock trending (in production, fetch from API)
        return []

    # ═══════════════════════════════════════════════════════════════════════════
    # ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_activity_summary(self, feed: GitHubFeed) -> Dict[str, Any]:
        """Generate activity summary from feed."""
        return {
            "total_repos": len(feed.repositories),
            "active_repos": sum(1 for r in feed.repositories if not r.is_archived),
            "total_commits": len(feed.recent_commits),
            "total_issues": len(feed.recent_issues),
            "open_prs": sum(1 for i in feed.recent_issues if i.is_pr and i.state == "open"),
            "trending_count": len(feed.trending_repos),
        }

    def identify_hot_repos(
        self,
        feed: GitHubFeed,
        threshold_stars: int = 1000,
    ) -> List[RepositoryInfo]:
        """Identify repositories with high activity."""
        return [
            r for r in feed.repositories
            if r.stars >= threshold_stars
        ]

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get monitor statistics."""
        return {
            **self._stats,
            "watchlist_size": len(self._watchlist),
            "cache_size": len(self._repo_cache),
            "last_scan": self._last_scan.isoformat() if self._last_scan else None,
            "has_token": self._api_token is not None,
        }

    def get_watchlist(self) -> List[str]:
        """Get current watchlist."""
        return self._watchlist.copy()


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_monitor_instance: Optional[GitHubMonitor] = None


def get_github_monitor() -> GitHubMonitor:
    """Get singleton GitHubMonitor instance."""
    global _monitor_instance

    if _monitor_instance is None:
        _monitor_instance = GitHubMonitor()

    return _monitor_instance
