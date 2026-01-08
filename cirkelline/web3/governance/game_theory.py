"""
Game Theory Engine
==================
Nash equilibria and incentive mechanism analysis.

Responsibilities:
- Model strategic interactions in governance
- Identify Nash equilibria in voting games
- Analyze incentive alignment
- Detect potential attack vectors
"""

import logging
import asyncio
import math
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class PlayerType(Enum):
    """Types of game players."""
    WHALE = "whale"              # Large token holder
    RETAIL = "retail"            # Small token holder
    PROTOCOL = "protocol"        # Protocol team
    VALIDATOR = "validator"      # Network validator
    ATTACKER = "attacker"        # Malicious actor
    ARBITRAGEUR = "arbitrageur"  # Economic optimizer


class StrategyType(Enum):
    """Types of player strategies."""
    COOPERATIVE = "cooperative"
    DEFECT = "defect"
    TIT_FOR_TAT = "tit_for_tat"
    ALWAYS_VOTE = "always_vote"
    NEVER_VOTE = "never_vote"
    RATIONAL = "rational"
    HONEST = "honest"
    MALICIOUS = "malicious"


class GameType(Enum):
    """Types of strategic games."""
    PRISONERS_DILEMMA = "prisoners_dilemma"
    COORDINATION = "coordination"
    CHICKEN = "chicken"
    STAG_HUNT = "stag_hunt"
    VOTING = "voting"
    AUCTION = "auction"
    SIGNALING = "signaling"


@dataclass
class Player:
    """A game theory player."""
    player_id: str
    player_type: PlayerType
    strategy: StrategyType = StrategyType.RATIONAL
    stake: float = 0.0  # Economic stake
    utility: float = 0.0  # Current utility

    def to_dict(self) -> Dict[str, Any]:
        return {
            "player_id": self.player_id,
            "type": self.player_type.value,
            "strategy": self.strategy.value,
            "stake": round(self.stake, 2),
            "utility": round(self.utility, 2),
        }


@dataclass
class Strategy:
    """A game strategy."""
    name: str
    strategy_type: StrategyType
    actions: List[str] = field(default_factory=list)
    expected_payoff: float = 0.0
    risk_level: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.strategy_type.value,
            "expected_payoff": round(self.expected_payoff, 3),
            "risk_level": round(self.risk_level, 3),
        }


@dataclass
class NashEquilibrium:
    """A Nash equilibrium state."""
    equilibrium_id: str
    strategies: Dict[str, StrategyType] = field(default_factory=dict)
    payoffs: Dict[str, float] = field(default_factory=dict)
    is_pareto_optimal: bool = False
    is_stable: bool = True
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "equilibrium_id": self.equilibrium_id,
            "strategies": {k: v.value for k, v in self.strategies.items()},
            "payoffs": {k: round(v, 3) for k, v in self.payoffs.items()},
            "pareto_optimal": self.is_pareto_optimal,
            "stable": self.is_stable,
            "description": self.description[:100],
        }


@dataclass
class GameModel:
    """A complete game theory model."""
    game_id: str
    game_type: GameType
    players: List[Player] = field(default_factory=list)
    strategies: Dict[str, List[Strategy]] = field(default_factory=dict)
    payoff_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)
    equilibria: List[NashEquilibrium] = field(default_factory=list)
    dominant_strategies: Dict[str, StrategyType] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "game_id": self.game_id,
            "type": self.game_type.value,
            "player_count": len(self.players),
            "equilibria_count": len(self.equilibria),
            "dominant_strategies": {k: v.value for k, v in self.dominant_strategies.items()},
        }


@dataclass
class IncentiveAnalysis:
    """Analysis of incentive mechanisms."""
    system_name: str
    incentive_compatible: bool = True
    budget_balanced: bool = True
    individually_rational: bool = True
    collusion_resistant: bool = True
    sybil_resistant: bool = True
    centralization_risk: float = 0.0  # 0-1
    attack_vectors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system_name": self.system_name,
            "incentive_compatible": self.incentive_compatible,
            "budget_balanced": self.budget_balanced,
            "individually_rational": self.individually_rational,
            "collusion_resistant": self.collusion_resistant,
            "sybil_resistant": self.sybil_resistant,
            "centralization_risk": round(self.centralization_risk, 3),
            "attack_vectors": self.attack_vectors[:5],
            "recommendations": self.recommendations[:3],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# PAYOFF MATRICES
# ═══════════════════════════════════════════════════════════════════════════════

CLASSIC_GAMES = {
    GameType.PRISONERS_DILEMMA: {
        "description": "Two players choose to cooperate or defect",
        "matrix": {
            ("cooperate", "cooperate"): (3, 3),
            ("cooperate", "defect"): (0, 5),
            ("defect", "cooperate"): (5, 0),
            ("defect", "defect"): (1, 1),
        },
        "nash": [("defect", "defect")],
        "pareto_optimal": [("cooperate", "cooperate")],
    },
    GameType.COORDINATION: {
        "description": "Players benefit from choosing same action",
        "matrix": {
            ("A", "A"): (2, 2),
            ("A", "B"): (0, 0),
            ("B", "A"): (0, 0),
            ("B", "B"): (2, 2),
        },
        "nash": [("A", "A"), ("B", "B")],
        "pareto_optimal": [("A", "A"), ("B", "B")],
    },
    GameType.CHICKEN: {
        "description": "Each player prefers other to yield",
        "matrix": {
            ("swerve", "swerve"): (0, 0),
            ("swerve", "straight"): (-1, 1),
            ("straight", "swerve"): (1, -1),
            ("straight", "straight"): (-10, -10),
        },
        "nash": [("swerve", "straight"), ("straight", "swerve")],
        "pareto_optimal": [("swerve", "straight"), ("straight", "swerve"), ("swerve", "swerve")],
    },
    GameType.STAG_HUNT: {
        "description": "Cooperation yields best outcome but requires trust",
        "matrix": {
            ("stag", "stag"): (4, 4),
            ("stag", "hare"): (0, 3),
            ("hare", "stag"): (3, 0),
            ("hare", "hare"): (3, 3),
        },
        "nash": [("stag", "stag"), ("hare", "hare")],
        "pareto_optimal": [("stag", "stag")],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# GAME THEORY ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class GameTheoryEngine:
    """
    Game theory analysis engine.

    Models strategic interactions in governance,
    identifies equilibria, and analyzes incentives.
    """

    def __init__(self):
        self._classic_games = CLASSIC_GAMES
        self._model_cache: Dict[str, GameModel] = {}

        # Statistics
        self._stats = {
            "total_analyses": 0,
            "models_created": 0,
            "equilibria_found": 0,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # MODEL CREATION
    # ═══════════════════════════════════════════════════════════════════════════

    def create_voting_game(
        self,
        voters: List[Dict[str, Any]],
        quorum: float = 0.5,
        threshold: float = 0.5,
    ) -> GameModel:
        """
        Create a voting game model.

        Args:
            voters: List of voter info with stake
            quorum: Required participation
            threshold: Required majority
        """
        self._stats["models_created"] += 1

        players = [
            Player(
                player_id=v.get("id", f"voter_{i}"),
                player_type=self._classify_voter(v.get("stake", 0)),
                stake=v.get("stake", 0),
            )
            for i, v in enumerate(voters)
        ]

        game = GameModel(
            game_id=f"voting-{len(voters)}-players",
            game_type=GameType.VOTING,
            players=players,
            description=f"Voting game with {len(voters)} voters",
        )

        # Find equilibria
        game.equilibria = self._find_voting_equilibria(players, quorum, threshold)
        self._stats["equilibria_found"] += len(game.equilibria)

        return game

    def create_classic_game(
        self,
        game_type: GameType,
        player_stakes: Tuple[float, float] = (1.0, 1.0),
    ) -> Optional[GameModel]:
        """Create a classic 2-player game model."""
        if game_type not in self._classic_games:
            return None

        config = self._classic_games[game_type]

        players = [
            Player(
                player_id="player_1",
                player_type=PlayerType.RETAIL,
                stake=player_stakes[0],
            ),
            Player(
                player_id="player_2",
                player_type=PlayerType.RETAIL,
                stake=player_stakes[1],
            ),
        ]

        # Build payoff matrix
        payoff_matrix = {}
        for (a1, a2), (p1, p2) in config["matrix"].items():
            if a1 not in payoff_matrix:
                payoff_matrix[a1] = {}
            payoff_matrix[a1][a2] = (p1, p2)

        # Build equilibria
        equilibria = []
        for i, (a1, a2) in enumerate(config["nash"]):
            p1, p2 = config["matrix"][(a1, a2)]
            eq = NashEquilibrium(
                equilibrium_id=f"nash-{i+1}",
                strategies={"player_1": StrategyType.RATIONAL, "player_2": StrategyType.RATIONAL},
                payoffs={"player_1": p1, "player_2": p2},
                is_pareto_optimal=(a1, a2) in config.get("pareto_optimal", []),
                description=f"Nash equilibrium: ({a1}, {a2})",
            )
            equilibria.append(eq)

        return GameModel(
            game_id=f"{game_type.value}-game",
            game_type=game_type,
            players=players,
            payoff_matrix=payoff_matrix,
            equilibria=equilibria,
            description=config["description"],
        )

    def _classify_voter(self, stake: float) -> PlayerType:
        """Classify voter by stake size."""
        if stake > 1000000:
            return PlayerType.WHALE
        elif stake > 10000:
            return PlayerType.VALIDATOR
        else:
            return PlayerType.RETAIL

    def _find_voting_equilibria(
        self,
        players: List[Player],
        quorum: float,
        threshold: float,
    ) -> List[NashEquilibrium]:
        """Find Nash equilibria in voting game."""
        equilibria = []

        total_stake = sum(p.stake for p in players)
        if total_stake == 0:
            return equilibria

        # Equilibrium 1: All vote
        all_vote_payoff = self._calculate_voting_payoff(
            players, 1.0, quorum, threshold
        )
        equilibria.append(NashEquilibrium(
            equilibrium_id="all-participate",
            strategies={p.player_id: StrategyType.ALWAYS_VOTE for p in players},
            payoffs={p.player_id: all_vote_payoff * p.stake / total_stake for p in players},
            is_pareto_optimal=True,
            description="All players participate in voting",
        ))

        # Equilibrium 2: Whales only
        whale_stake = sum(p.stake for p in players if p.player_type == PlayerType.WHALE)
        if whale_stake / total_stake >= quorum:
            equilibria.append(NashEquilibrium(
                equilibrium_id="whale-dominated",
                strategies={
                    p.player_id: (
                        StrategyType.ALWAYS_VOTE if p.player_type == PlayerType.WHALE
                        else StrategyType.NEVER_VOTE
                    ) for p in players
                },
                payoffs={p.player_id: 0.5 * p.stake / total_stake for p in players},
                is_pareto_optimal=False,
                is_stable=True,
                description="Only whales vote - retail free-rides",
            ))

        # Equilibrium 3: No one votes (if quorum allows)
        if quorum == 0:
            equilibria.append(NashEquilibrium(
                equilibrium_id="no-participation",
                strategies={p.player_id: StrategyType.NEVER_VOTE for p in players},
                payoffs={p.player_id: 0.0 for p in players},
                is_pareto_optimal=False,
                is_stable=False,
                description="No participation - governance failure",
            ))

        return equilibria

    def _calculate_voting_payoff(
        self,
        players: List[Player],
        participation: float,
        quorum: float,
        threshold: float,
    ) -> float:
        """Calculate expected payoff for voting participation."""
        if participation < quorum:
            return 0.0  # Proposal fails

        # Higher participation = better legitimacy
        return 1.0 + 0.5 * (participation - quorum)

    # ═══════════════════════════════════════════════════════════════════════════
    # INCENTIVE ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════

    async def analyze_incentives(
        self,
        voting_system: Any,  # VotingSystem enum from dao_analyzer
    ) -> IncentiveAnalysis:
        """
        Analyze incentive properties of a governance system.

        Args:
            voting_system: Type of voting system
        """
        self._stats["total_analyses"] += 1

        analysis = IncentiveAnalysis(
            system_name=str(voting_system.value) if hasattr(voting_system, 'value') else str(voting_system)
        )

        # Analyze based on voting system type
        system_name = analysis.system_name.lower()

        if "token_weighted" in system_name:
            analysis.centralization_risk = 0.7
            analysis.collusion_resistant = False
            analysis.attack_vectors = [
                "Flash loan voting attack",
                "Vote buying through OTC",
                "Governance token accumulation",
            ]
            analysis.recommendations = [
                "Add timelock for proposal execution",
                "Implement delegation with vesting",
                "Consider quadratic voting for plutocracy resistance",
            ]

        elif "quadratic" in system_name:
            analysis.centralization_risk = 0.3
            analysis.sybil_resistant = False
            analysis.attack_vectors = [
                "Sybil attack through identity splitting",
                "Collusion through identity verification bypass",
            ]
            analysis.recommendations = [
                "Implement proof-of-personhood",
                "Use identity verification layer",
                "Add collusion detection mechanisms",
            ]

        elif "conviction" in system_name:
            analysis.centralization_risk = 0.4
            analysis.attack_vectors = [
                "Long-term token lockup by whales",
                "Proposal spamming to dilute conviction",
            ]
            analysis.recommendations = [
                "Cap maximum conviction per proposal",
                "Implement proposal bond requirements",
            ]

        elif "multisig" in system_name:
            analysis.centralization_risk = 0.9
            analysis.collusion_resistant = False
            analysis.attack_vectors = [
                "Key compromise of multiple signers",
                "Signer collusion",
                "Social engineering attacks",
            ]
            analysis.recommendations = [
                "Increase signer threshold",
                "Implement geographic/organizational diversity",
                "Add timelock for critical operations",
            ]

        else:
            analysis.attack_vectors = ["Unknown system - requires detailed analysis"]
            analysis.recommendations = ["Conduct comprehensive security audit"]

        return analysis

    def analyze_mechanism_design(
        self,
        participants: int,
        total_value: float,
        distribution: str = "uniform",
    ) -> Dict[str, Any]:
        """
        Analyze mechanism design properties.

        Args:
            participants: Number of participants
            total_value: Total value at stake
            distribution: Value distribution type
        """
        result = {
            "participants": participants,
            "total_value": total_value,
            "properties": {},
            "recommendations": [],
        }

        # Check individual rationality
        avg_value = total_value / participants if participants > 0 else 0
        result["properties"]["individually_rational"] = avg_value > 0

        # Check budget balance
        result["properties"]["budget_balanced"] = True  # Assuming closed system

        # Check incentive compatibility (simplified)
        result["properties"]["incentive_compatible"] = distribution == "quadratic"

        # Recommendations
        if participants < 10:
            result["recommendations"].append(
                "Low participation - consider reducing barriers to entry"
            )
        if not result["properties"]["incentive_compatible"]:
            result["recommendations"].append(
                "Consider quadratic distribution for better incentive alignment"
            )

        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # ATTACK ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════

    def analyze_attack_profitability(
        self,
        attack_cost: float,
        success_probability: float,
        potential_gain: float,
        detection_penalty: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Analyze profitability of a governance attack.

        Returns expected value and risk assessment.
        """
        expected_gain = success_probability * potential_gain
        expected_penalty = (1 - success_probability) * detection_penalty
        expected_value = expected_gain - attack_cost - expected_penalty

        risk_ratio = attack_cost / (potential_gain + 0.001)  # Avoid div by zero

        return {
            "attack_cost": attack_cost,
            "success_probability": success_probability,
            "potential_gain": potential_gain,
            "expected_value": round(expected_value, 2),
            "profitable": expected_value > 0,
            "risk_ratio": round(risk_ratio, 3),
            "risk_level": "high" if risk_ratio > 0.5 else "medium" if risk_ratio > 0.2 else "low",
            "recommendation": (
                "Increase attack cost or detection penalty"
                if expected_value > 0
                else "Current mechanism provides adequate deterrence"
            ),
        }

    def calculate_bribe_cost(
        self,
        total_voting_power: float,
        threshold: float,
        avg_voter_valuation: float,
    ) -> Dict[str, Any]:
        """
        Calculate theoretical cost to bribe governance attack.

        Args:
            total_voting_power: Total voting power in system
            threshold: Required majority (0-1)
            avg_voter_valuation: Average voter's valuation of vote
        """
        required_votes = total_voting_power * threshold
        min_bribe_cost = required_votes * avg_voter_valuation

        return {
            "total_voting_power": total_voting_power,
            "threshold": threshold,
            "required_votes": round(required_votes, 2),
            "min_bribe_cost": round(min_bribe_cost, 2),
            "recommendation": (
                "Bribe cost is low - consider increasing vote value"
                if min_bribe_cost < 1000000
                else "Bribe attack is expensive - good defense"
            ),
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            **self._stats,
            "classic_games": len(self._classic_games),
            "cache_size": len(self._model_cache),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_engine_instance: Optional[GameTheoryEngine] = None


def get_game_theory_engine() -> GameTheoryEngine:
    """Get singleton GameTheoryEngine instance."""
    global _engine_instance

    if _engine_instance is None:
        _engine_instance = GameTheoryEngine()

    return _engine_instance
