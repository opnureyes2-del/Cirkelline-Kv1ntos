"""
DAO Analyzer
============
Decentralized Autonomous Organization analysis.

Responsibilities:
- Analyze DAO governance structures
- Track proposals and voting patterns
- Identify governance risks and optimizations
- Compare governance models
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class VotingSystem(Enum):
    """Types of voting systems."""
    TOKEN_WEIGHTED = "token_weighted"      # 1 token = 1 vote
    QUADRATIC = "quadratic"                # Quadratic voting
    CONVICTION = "conviction"              # Time-weighted conviction
    HOLOGRAPHIC = "holographic"            # Holographic consensus
    OPTIMISTIC = "optimistic"              # Optimistic governance
    MULTISIG = "multisig"                  # Multi-signature
    HYBRID = "hybrid"                      # Combination of methods


class ProposalState(Enum):
    """Proposal lifecycle states."""
    DRAFT = "draft"
    PENDING = "pending"
    ACTIVE = "active"
    PASSED = "passed"
    DEFEATED = "defeated"
    QUEUED = "queued"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class GovernanceRisk(Enum):
    """Governance risk categories."""
    CENTRALIZATION = "centralization"
    LOW_PARTICIPATION = "low_participation"
    FLASH_LOAN_ATTACK = "flash_loan_attack"
    BRIBERY = "bribery"
    COLLUSION = "collusion"
    GOVERNANCE_CAPTURE = "governance_capture"
    PROPOSAL_SPAM = "proposal_spam"


@dataclass
class Vote:
    """A single vote record."""
    voter: str
    proposal_id: str
    support: bool
    weight: float = 0.0
    reason: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "voter": self.voter[:10] + "...",
            "support": "for" if self.support else "against",
            "weight": round(self.weight, 2),
        }


@dataclass
class GovernanceProposal:
    """A governance proposal."""
    proposal_id: str
    title: str
    description: str
    proposer: str
    state: ProposalState = ProposalState.DRAFT
    votes_for: float = 0.0
    votes_against: float = 0.0
    quorum: float = 0.0
    created_at: str = ""
    voting_starts: str = ""
    voting_ends: str = ""
    executed_at: Optional[str] = None
    actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        total_votes = self.votes_for + self.votes_against
        return {
            "proposal_id": self.proposal_id,
            "title": self.title[:80],
            "state": self.state.value,
            "votes_for": round(self.votes_for, 2),
            "votes_against": round(self.votes_against, 2),
            "participation": round(total_votes, 2),
            "passed": self.votes_for > self.votes_against,
            "quorum_reached": total_votes >= self.quorum,
        }


@dataclass
class DAOInfo:
    """Complete DAO information."""
    name: str
    dao_id: str
    voting_system: VotingSystem = VotingSystem.TOKEN_WEIGHTED
    token_address: Optional[str] = None
    token_symbol: str = ""
    total_voting_power: float = 0.0
    active_voters: int = 0
    total_proposals: int = 0
    passed_proposals: int = 0
    quorum_threshold: float = 0.0  # 0-1
    proposal_threshold: float = 0.0  # Min tokens to propose
    voting_period: int = 0  # In blocks or seconds
    timelock_delay: int = 0
    governor_contract: Optional[str] = None
    treasury_value: float = 0.0
    description: str = ""
    website: str = ""
    risks: List[GovernanceRisk] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "dao_id": self.dao_id,
            "voting_system": self.voting_system.value,
            "token_symbol": self.token_symbol,
            "active_voters": self.active_voters,
            "total_proposals": self.total_proposals,
            "pass_rate": self.passed_proposals / self.total_proposals if self.total_proposals else 0,
            "quorum": f"{self.quorum_threshold * 100:.1f}%",
            "voting_period": self.voting_period,
            "has_timelock": self.timelock_delay > 0,
            "treasury_value": self.treasury_value,
            "risks": [r.value for r in self.risks],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# KNOWN DAOS DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

KNOWN_DAOS = {
    "makerdao": DAOInfo(
        name="MakerDAO",
        dao_id="maker",
        voting_system=VotingSystem.TOKEN_WEIGHTED,
        token_symbol="MKR",
        quorum_threshold=0.0,  # No quorum, just needs majority
        voting_period=259200,  # ~3 days
        timelock_delay=172800,  # 48 hours
        description="Decentralized credit protocol governing DAI stablecoin",
    ),
    "uniswap": DAOInfo(
        name="Uniswap Governance",
        dao_id="uniswap",
        voting_system=VotingSystem.TOKEN_WEIGHTED,
        token_symbol="UNI",
        quorum_threshold=0.04,  # 4% of total supply
        proposal_threshold=2500000,  # 2.5M UNI
        voting_period=40320,  # ~7 days in blocks
        timelock_delay=172800,  # 48 hours
        description="Governance for Uniswap DEX protocol",
    ),
    "aave": DAOInfo(
        name="Aave Governance",
        dao_id="aave",
        voting_system=VotingSystem.TOKEN_WEIGHTED,
        token_symbol="AAVE",
        quorum_threshold=0.02,  # 2%
        voting_period=259200,  # 3 days
        timelock_delay=86400,  # 24 hours
        description="Governance for Aave lending protocol",
    ),
    "compound": DAOInfo(
        name="Compound Governance",
        dao_id="compound",
        voting_system=VotingSystem.TOKEN_WEIGHTED,
        token_symbol="COMP",
        quorum_threshold=0.04,  # 4%
        proposal_threshold=25000,  # 25k COMP
        voting_period=19710,  # ~3 days in blocks
        timelock_delay=172800,  # 48 hours
        description="Governance for Compound lending protocol",
    ),
    "optimism": DAOInfo(
        name="Optimism Collective",
        dao_id="optimism",
        voting_system=VotingSystem.HYBRID,
        token_symbol="OP",
        description="Bicameral governance with Token House and Citizens House",
    ),
    "gitcoin": DAOInfo(
        name="Gitcoin DAO",
        dao_id="gitcoin",
        voting_system=VotingSystem.QUADRATIC,
        token_symbol="GTC",
        description="Governance using quadratic voting for public goods funding",
    ),
    "aragon": DAOInfo(
        name="Aragon DAO",
        dao_id="aragon",
        voting_system=VotingSystem.TOKEN_WEIGHTED,
        token_symbol="ANT",
        description="DAO infrastructure and governance toolkit",
    ),
    "ens": DAOInfo(
        name="ENS DAO",
        dao_id="ens",
        voting_system=VotingSystem.TOKEN_WEIGHTED,
        token_symbol="ENS",
        quorum_threshold=0.01,  # 1%
        voting_period=604800,  # 7 days
        description="Governance for Ethereum Name Service",
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# DAO ANALYZER
# ═══════════════════════════════════════════════════════════════════════════════

class DAOAnalyzer:
    """
    DAO governance analyzer.

    Analyzes decentralized governance structures,
    voting patterns, and governance risks.
    """

    def __init__(self):
        self._known_daos = KNOWN_DAOS
        self._analysis_cache: Dict[str, DAOInfo] = {}
        self._proposal_cache: Dict[str, List[GovernanceProposal]] = {}

        # Statistics
        self._stats = {
            "total_analyses": 0,
            "daos_analyzed": 0,
            "proposals_analyzed": 0,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════

    async def analyze(self, dao_name: str) -> Optional[DAOInfo]:
        """
        Analyze a DAO's governance structure.

        Args:
            dao_name: Name or address of DAO

        Returns:
            DAO information
        """
        self._stats["total_analyses"] += 1

        dao_key = dao_name.lower().replace(" ", "")

        # Check known DAOs
        if dao_key in self._known_daos:
            dao = self._known_daos[dao_key]
            # Enrich with risk analysis
            dao.risks = self._analyze_risks(dao)
            return dao

        # Check cache
        if dao_key in self._analysis_cache:
            return self._analysis_cache[dao_key]

        # Unknown DAO - try to analyze
        dao = await self._analyze_unknown_dao(dao_name)
        if dao:
            self._analysis_cache[dao_key] = dao
            self._stats["daos_analyzed"] += 1

        return dao

    async def get_proposals(
        self,
        dao_name: str,
        state: Optional[ProposalState] = None,
        limit: int = 10,
    ) -> List[GovernanceProposal]:
        """
        Get proposals for a DAO.

        Args:
            dao_name: Name of DAO
            state: Filter by proposal state
            limit: Maximum proposals to return
        """
        dao_key = dao_name.lower()

        if dao_key in self._proposal_cache:
            proposals = self._proposal_cache[dao_key]
        else:
            proposals = await self._fetch_proposals(dao_name)
            self._proposal_cache[dao_key] = proposals

        # Filter by state
        if state:
            proposals = [p for p in proposals if p.state == state]

        return proposals[:limit]

    async def analyze_proposal(
        self,
        dao_name: str,
        proposal_id: str,
    ) -> Optional[GovernanceProposal]:
        """Analyze a specific proposal."""
        proposals = await self.get_proposals(dao_name)
        for p in proposals:
            if p.proposal_id == proposal_id:
                self._stats["proposals_analyzed"] += 1
                return p
        return None

    async def _analyze_unknown_dao(self, name: str) -> Optional[DAOInfo]:
        """Analyze unknown DAO."""
        # In production, this would fetch from Snapshot, Tally, etc.
        return DAOInfo(
            name=name.title(),
            dao_id=name.lower().replace(" ", "-"),
            voting_system=VotingSystem.TOKEN_WEIGHTED,
            description=f"DAO: {name}",
        )

    async def _fetch_proposals(
        self,
        dao_name: str,
    ) -> List[GovernanceProposal]:
        """Fetch proposals from governance system."""
        # Mock proposals (in production, fetch from Snapshot/Tally/Compound)
        return [
            GovernanceProposal(
                proposal_id=f"{dao_name.lower()}-001",
                title="Treasury Diversification",
                description="Proposal to diversify treasury holdings",
                proposer="0x1234...5678",
                state=ProposalState.PASSED,
                votes_for=1500000,
                votes_against=200000,
                quorum=100000,
                voting_starts=datetime.utcnow().isoformat(),
            ),
            GovernanceProposal(
                proposal_id=f"{dao_name.lower()}-002",
                title="Protocol Fee Update",
                description="Adjust protocol fees for sustainability",
                proposer="0xabcd...efgh",
                state=ProposalState.ACTIVE,
                votes_for=800000,
                votes_against=600000,
                quorum=100000,
                voting_starts=datetime.utcnow().isoformat(),
            ),
        ]

    # ═══════════════════════════════════════════════════════════════════════════
    # RISK ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════

    def _analyze_risks(self, dao: DAOInfo) -> List[GovernanceRisk]:
        """Identify governance risks."""
        risks = []

        # Low quorum risk
        if dao.quorum_threshold < 0.02:
            risks.append(GovernanceRisk.LOW_PARTICIPATION)

        # Flash loan risk (token-weighted without timelock)
        if dao.voting_system == VotingSystem.TOKEN_WEIGHTED:
            if dao.timelock_delay == 0:
                risks.append(GovernanceRisk.FLASH_LOAN_ATTACK)

        # High proposal threshold (centralization)
        if dao.proposal_threshold > 0 and dao.total_voting_power > 0:
            threshold_ratio = dao.proposal_threshold / dao.total_voting_power
            if threshold_ratio > 0.01:  # > 1% needed to propose
                risks.append(GovernanceRisk.CENTRALIZATION)

        return risks

    def analyze_voting_power_distribution(
        self,
        voters: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Analyze distribution of voting power.

        Returns Gini coefficient and top holder metrics.
        """
        if not voters:
            return {"gini": 0, "top10_share": 0, "decentralized": True}

        # Sort by voting power
        sorted_voters = sorted(
            voters,
            key=lambda v: v.get("power", 0),
            reverse=True
        )

        total_power = sum(v.get("power", 0) for v in voters)
        if total_power == 0:
            return {"gini": 0, "top10_share": 0, "decentralized": True}

        # Top 10 share
        top10 = sorted_voters[:10]
        top10_power = sum(v.get("power", 0) for v in top10)
        top10_share = top10_power / total_power

        # Simple Gini approximation
        n = len(voters)
        powers = [v.get("power", 0) / total_power for v in voters]
        gini = 1 - 2 * sum((n - i) * p for i, p in enumerate(sorted(powers))) / n

        return {
            "gini": round(gini, 3),
            "top10_share": round(top10_share, 3),
            "decentralized": top10_share < 0.5 and gini < 0.7,
        }

    def compare_voting_systems(
        self,
        systems: List[VotingSystem],
    ) -> Dict[str, Dict[str, Any]]:
        """Compare different voting systems."""
        comparisons = {}

        system_traits = {
            VotingSystem.TOKEN_WEIGHTED: {
                "plutocracy_resistance": 0.2,
                "sybil_resistance": 0.9,
                "simplicity": 0.9,
                "speed": 0.8,
                "capital_efficiency": 0.4,
            },
            VotingSystem.QUADRATIC: {
                "plutocracy_resistance": 0.7,
                "sybil_resistance": 0.5,
                "simplicity": 0.6,
                "speed": 0.7,
                "capital_efficiency": 0.7,
            },
            VotingSystem.CONVICTION: {
                "plutocracy_resistance": 0.6,
                "sybil_resistance": 0.8,
                "simplicity": 0.4,
                "speed": 0.3,
                "capital_efficiency": 0.8,
            },
            VotingSystem.HOLOGRAPHIC: {
                "plutocracy_resistance": 0.7,
                "sybil_resistance": 0.7,
                "simplicity": 0.3,
                "speed": 0.6,
                "capital_efficiency": 0.9,
            },
            VotingSystem.OPTIMISTIC: {
                "plutocracy_resistance": 0.5,
                "sybil_resistance": 0.8,
                "simplicity": 0.7,
                "speed": 0.9,
                "capital_efficiency": 0.6,
            },
            VotingSystem.MULTISIG: {
                "plutocracy_resistance": 0.3,
                "sybil_resistance": 1.0,
                "simplicity": 0.9,
                "speed": 0.95,
                "capital_efficiency": 0.2,
            },
        }

        for system in systems:
            if system in system_traits:
                comparisons[system.value] = system_traits[system]

        return comparisons

    # ═══════════════════════════════════════════════════════════════════════════
    # QUERIES
    # ═══════════════════════════════════════════════════════════════════════════

    def get_known_daos(self) -> List[str]:
        """Get list of known DAO names."""
        return list(self._known_daos.keys())

    def get_daos_by_voting_system(
        self,
        voting_system: VotingSystem,
    ) -> List[DAOInfo]:
        """Get DAOs using a specific voting system."""
        return [
            dao for dao in self._known_daos.values()
            if dao.voting_system == voting_system
        ]

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get analyzer statistics."""
        return {
            **self._stats,
            "known_daos": len(self._known_daos),
            "cache_size": len(self._analysis_cache),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_analyzer_instance: Optional[DAOAnalyzer] = None


def get_dao_analyzer() -> DAOAnalyzer:
    """Get singleton DAOAnalyzer instance."""
    global _analyzer_instance

    if _analyzer_instance is None:
        _analyzer_instance = DAOAnalyzer()

    return _analyzer_instance
