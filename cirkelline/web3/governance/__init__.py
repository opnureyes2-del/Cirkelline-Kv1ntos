"""
Governance Module
=================
DAO analysis, game theory, and tokenomics modeling.

Components:
- DAOAnalyzer: Analyze DAO structures and governance mechanisms
- GameTheoryEngine: Nash equilibria and incentive analysis
- TokenomicsModeler: Token economics simulation
"""

from cirkelline.web3.governance.dao_analyzer import (
    DAOAnalyzer,
    DAOInfo,
    GovernanceProposal,
    VotingSystem,
    get_dao_analyzer,
)

from cirkelline.web3.governance.game_theory import (
    GameTheoryEngine,
    GameModel,
    NashEquilibrium,
    IncentiveAnalysis,
    get_game_theory_engine,
)

from cirkelline.web3.governance.tokenomics import (
    TokenomicsModeler,
    TokenModel,
    TokenDistribution,
    VestingSchedule,
    get_tokenomics_modeler,
)

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


__all__ = [
    # DAO
    'DAOAnalyzer',
    'DAOInfo',
    'GovernanceProposal',
    'VotingSystem',
    'get_dao_analyzer',
    # Game Theory
    'GameTheoryEngine',
    'GameModel',
    'NashEquilibrium',
    'IncentiveAnalysis',
    'get_game_theory_engine',
    # Tokenomics
    'TokenomicsModeler',
    'TokenModel',
    'TokenDistribution',
    'VestingSchedule',
    'get_tokenomics_modeler',
    # Engine
    'GovernanceEngine',
    'get_governance_engine',
]


# ═══════════════════════════════════════════════════════════════════════════════
# GOVERNANCE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class GovernanceEngine:
    """
    Unified governance analysis engine.

    Coordinates DAO analysis, game theory modeling,
    and tokenomics simulation.
    """

    def __init__(self):
        self._dao = get_dao_analyzer()
        self._game_theory = get_game_theory_engine()
        self._tokenomics = get_tokenomics_modeler()

    @property
    def dao(self) -> DAOAnalyzer:
        return self._dao

    @property
    def game_theory(self) -> GameTheoryEngine:
        return self._game_theory

    @property
    def tokenomics(self) -> TokenomicsModeler:
        return self._tokenomics

    async def analyze_governance(
        self,
        dao_name: str,
        include_game_theory: bool = True,
        include_tokenomics: bool = True,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive governance analysis.

        Args:
            dao_name: Name or address of DAO
            include_game_theory: Include game theory analysis
            include_tokenomics: Include tokenomics modeling
        """
        result = {
            "dao": None,
            "game_theory": None,
            "tokenomics": None,
            "recommendations": [],
        }

        # DAO analysis
        dao_info = await self._dao.analyze(dao_name)
        result["dao"] = dao_info.to_dict() if dao_info else None

        # Game theory analysis
        if include_game_theory and dao_info:
            incentive_analysis = await self._game_theory.analyze_incentives(
                dao_info.voting_system
            )
            result["game_theory"] = incentive_analysis.to_dict() if incentive_analysis else None

        # Tokenomics analysis
        if include_tokenomics and dao_info and dao_info.token_address:
            token_model = await self._tokenomics.model_token(
                dao_info.token_address
            )
            result["tokenomics"] = token_model.to_dict() if token_model else None

        # Generate recommendations
        result["recommendations"] = self._generate_recommendations(result)

        return result

    def _generate_recommendations(self, result: Dict[str, Any]) -> list:
        """Generate governance recommendations."""
        recommendations = []

        if result.get("dao"):
            dao = result["dao"]
            if dao.get("quorum", 0) < 0.1:
                recommendations.append(
                    "Low quorum threshold may lead to governance attacks"
                )
            if not dao.get("has_timelock"):
                recommendations.append(
                    "Consider implementing timelock for critical decisions"
                )

        if result.get("game_theory"):
            gt = result["game_theory"]
            if gt.get("centralization_risk", 0) > 0.7:
                recommendations.append(
                    "High centralization risk detected in voting power"
                )

        return recommendations[:5]

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "dao": self._dao.get_stats(),
            "game_theory": self._game_theory.get_stats(),
            "tokenomics": self._tokenomics.get_stats(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_engine_instance: Optional[GovernanceEngine] = None


def get_governance_engine() -> GovernanceEngine:
    """Get singleton GovernanceEngine."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = GovernanceEngine()
    return _engine_instance
