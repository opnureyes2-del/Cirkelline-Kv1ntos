"""
Tokenomics Modeler
==================
Token economics simulation and analysis.

Responsibilities:
- Model token supply dynamics
- Simulate vesting schedules
- Analyze token distribution
- Project inflation/deflation
"""

import logging
import asyncio
import math
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class TokenType(Enum):
    """Types of tokens."""
    GOVERNANCE = "governance"
    UTILITY = "utility"
    SECURITY = "security"
    NFT = "nft"
    STABLECOIN = "stablecoin"
    LP = "lp"  # Liquidity provider
    WRAPPED = "wrapped"


class DistributionType(Enum):
    """Token distribution categories."""
    TEAM = "team"
    INVESTORS = "investors"
    COMMUNITY = "community"
    TREASURY = "treasury"
    ECOSYSTEM = "ecosystem"
    LIQUIDITY = "liquidity"
    ADVISORS = "advisors"
    PUBLIC_SALE = "public_sale"
    AIRDROP = "airdrop"
    STAKING_REWARDS = "staking_rewards"


class VestingType(Enum):
    """Vesting schedule types."""
    LINEAR = "linear"
    CLIFF = "cliff"
    CLIFF_LINEAR = "cliff_linear"
    EXPONENTIAL = "exponential"
    CUSTOM = "custom"


@dataclass
class VestingSchedule:
    """Token vesting schedule."""
    category: DistributionType
    total_amount: float
    vesting_type: VestingType = VestingType.LINEAR
    cliff_months: int = 0
    vesting_months: int = 12
    tge_unlock: float = 0.0  # Token Generation Event unlock %
    start_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "total_amount": self.total_amount,
            "vesting_type": self.vesting_type.value,
            "cliff_months": self.cliff_months,
            "vesting_months": self.vesting_months,
            "tge_unlock": f"{self.tge_unlock * 100:.1f}%",
        }

    def get_unlocked_at_month(self, month: int) -> float:
        """Calculate tokens unlocked at a given month."""
        if month < 0:
            return 0.0

        # TGE unlock
        unlocked = self.total_amount * self.tge_unlock

        # Nothing during cliff
        if month < self.cliff_months:
            return unlocked

        # Calculate vesting progress
        vesting_elapsed = month - self.cliff_months
        remaining = self.total_amount * (1 - self.tge_unlock)

        if self.vesting_type == VestingType.LINEAR:
            if vesting_elapsed >= self.vesting_months:
                return self.total_amount
            progress = vesting_elapsed / self.vesting_months
            unlocked += remaining * progress

        elif self.vesting_type == VestingType.CLIFF:
            if vesting_elapsed >= self.vesting_months:
                unlocked = self.total_amount

        elif self.vesting_type == VestingType.EXPONENTIAL:
            # Exponential unlock (faster at end)
            if vesting_elapsed >= self.vesting_months:
                return self.total_amount
            progress = (vesting_elapsed / self.vesting_months) ** 2
            unlocked += remaining * progress

        return min(unlocked, self.total_amount)


@dataclass
class TokenDistribution:
    """Token distribution allocation."""
    category: DistributionType
    allocation: float  # 0-1 (percentage)
    amount: float = 0.0
    vesting: Optional[VestingSchedule] = None
    holders: int = 0
    top_holder_share: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "allocation": f"{self.allocation * 100:.1f}%",
            "amount": self.amount,
            "holders": self.holders,
            "vesting": self.vesting.to_dict() if self.vesting else None,
        }


@dataclass
class TokenModel:
    """Complete token economics model."""
    token_id: str
    name: str
    symbol: str
    token_type: TokenType = TokenType.GOVERNANCE
    total_supply: float = 0.0
    max_supply: Optional[float] = None
    circulating_supply: float = 0.0
    initial_price: float = 0.0
    current_price: float = 0.0
    market_cap: float = 0.0
    fdv: float = 0.0  # Fully diluted valuation
    inflation_rate: float = 0.0  # Annual %
    burn_rate: float = 0.0  # Annual %
    distributions: List[TokenDistribution] = field(default_factory=list)
    vesting_schedules: List[VestingSchedule] = field(default_factory=list)
    utility: List[str] = field(default_factory=list)
    value_accrual: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_id": self.token_id,
            "name": self.name,
            "symbol": self.symbol,
            "type": self.token_type.value,
            "total_supply": self.total_supply,
            "max_supply": self.max_supply,
            "circulating_supply": self.circulating_supply,
            "market_cap": self.market_cap,
            "fdv": self.fdv,
            "inflation_rate": f"{self.inflation_rate * 100:.2f}%",
            "utility": self.utility[:5],
        }

    def get_circulating_at_month(self, month: int) -> float:
        """Project circulating supply at given month."""
        circulating = 0.0
        for schedule in self.vesting_schedules:
            circulating += schedule.get_unlocked_at_month(month)

        # Apply inflation/deflation
        if month > 0:
            net_rate = self.inflation_rate - self.burn_rate
            circulating *= (1 + net_rate / 12) ** month

        return min(circulating, self.max_supply or self.total_supply)


# ═══════════════════════════════════════════════════════════════════════════════
# KNOWN TOKEN MODELS
# ═══════════════════════════════════════════════════════════════════════════════

KNOWN_TOKENS = {
    "uni": TokenModel(
        token_id="uni",
        name="Uniswap",
        symbol="UNI",
        token_type=TokenType.GOVERNANCE,
        total_supply=1_000_000_000,
        max_supply=1_000_000_000,
        utility=["Governance voting", "Protocol fee voting", "Delegation"],
        distributions=[
            TokenDistribution(DistributionType.COMMUNITY, 0.60),
            TokenDistribution(DistributionType.TEAM, 0.2125),
            TokenDistribution(DistributionType.INVESTORS, 0.175),
            TokenDistribution(DistributionType.ADVISORS, 0.0125),
        ],
    ),
    "aave": TokenModel(
        token_id="aave",
        name="Aave",
        symbol="AAVE",
        token_type=TokenType.GOVERNANCE,
        total_supply=16_000_000,
        max_supply=16_000_000,
        utility=["Governance", "Staking", "Safety module", "Fee discounts"],
        value_accrual=["Protocol fees", "Safety module rewards"],
    ),
    "mkr": TokenModel(
        token_id="mkr",
        name="Maker",
        symbol="MKR",
        token_type=TokenType.GOVERNANCE,
        total_supply=1_000_000,
        utility=["Governance", "Backstop for DAI", "Protocol profits"],
        value_accrual=["Stability fees", "Liquidation fees"],
    ),
    "crv": TokenModel(
        token_id="crv",
        name="Curve DAO",
        symbol="CRV",
        token_type=TokenType.GOVERNANCE,
        total_supply=3_030_303_031,
        max_supply=3_030_303_031,
        inflation_rate=0.10,  # 10% initial, decreasing
        utility=["Governance", "Boosted rewards", "Vote locking (veCRV)"],
        value_accrual=["Trading fees", "veTokenomics bribes"],
    ),
    "op": TokenModel(
        token_id="op",
        name="Optimism",
        symbol="OP",
        token_type=TokenType.GOVERNANCE,
        total_supply=4_294_967_296,
        inflation_rate=0.02,  # 2% annual
        utility=["Governance", "RetroPGF voting"],
        distributions=[
            TokenDistribution(DistributionType.ECOSYSTEM, 0.25),
            TokenDistribution(DistributionType.AIRDROP, 0.19),
            TokenDistribution(DistributionType.INVESTORS, 0.17),
            TokenDistribution(DistributionType.TEAM, 0.19),
            TokenDistribution(DistributionType.TREASURY, 0.20),
        ],
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# TOKENOMICS MODELER
# ═══════════════════════════════════════════════════════════════════════════════

class TokenomicsModeler:
    """
    Token economics modeling engine.

    Simulates token supply dynamics, vesting,
    and economic projections.
    """

    def __init__(self):
        self._known_tokens = KNOWN_TOKENS
        self._model_cache: Dict[str, TokenModel] = {}

        # Statistics
        self._stats = {
            "total_models": 0,
            "simulations_run": 0,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # MODELING
    # ═══════════════════════════════════════════════════════════════════════════

    async def model_token(self, token_id: str) -> Optional[TokenModel]:
        """
        Get or create token model.

        Args:
            token_id: Token identifier or address
        """
        token_key = token_id.lower()

        # Check known tokens
        if token_key in self._known_tokens:
            return self._known_tokens[token_key]

        # Check cache
        if token_key in self._model_cache:
            return self._model_cache[token_key]

        # Unknown token - create basic model
        model = await self._create_unknown_token_model(token_id)
        self._model_cache[token_key] = model
        self._stats["total_models"] += 1

        return model

    def create_token_model(
        self,
        name: str,
        symbol: str,
        total_supply: float,
        distributions: Dict[str, float],
        vesting_config: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> TokenModel:
        """
        Create a new token model.

        Args:
            name: Token name
            symbol: Token symbol
            total_supply: Total token supply
            distributions: Category -> allocation percentage
            vesting_config: Optional vesting schedules per category
        """
        self._stats["total_models"] += 1

        model = TokenModel(
            token_id=symbol.lower(),
            name=name,
            symbol=symbol,
            total_supply=total_supply,
        )

        # Build distributions
        for category_name, allocation in distributions.items():
            try:
                category = DistributionType(category_name.lower())
            except ValueError:
                category = DistributionType.COMMUNITY

            dist = TokenDistribution(
                category=category,
                allocation=allocation,
                amount=total_supply * allocation,
            )

            # Add vesting if configured
            if vesting_config and category_name in vesting_config:
                vc = vesting_config[category_name]
                schedule = VestingSchedule(
                    category=category,
                    total_amount=dist.amount,
                    vesting_type=VestingType(vc.get("type", "linear")),
                    cliff_months=vc.get("cliff", 0),
                    vesting_months=vc.get("vesting", 12),
                    tge_unlock=vc.get("tge", 0.0),
                )
                dist.vesting = schedule
                model.vesting_schedules.append(schedule)

            model.distributions.append(dist)

        return model

    async def _create_unknown_token_model(self, token_id: str) -> TokenModel:
        """Create model for unknown token."""
        # In production, fetch from CoinGecko, DeFiLlama, etc.
        return TokenModel(
            token_id=token_id,
            name=token_id.upper(),
            symbol=token_id.upper(),
            total_supply=0,
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # SIMULATION
    # ═══════════════════════════════════════════════════════════════════════════

    def simulate_supply(
        self,
        model: TokenModel,
        months: int = 48,
    ) -> List[Dict[str, Any]]:
        """
        Simulate token supply over time.

        Args:
            model: Token model
            months: Simulation period in months
        """
        self._stats["simulations_run"] += 1

        projections = []
        for month in range(months + 1):
            circulating = model.get_circulating_at_month(month)
            projections.append({
                "month": month,
                "circulating": round(circulating, 2),
                "locked": round(model.total_supply - circulating, 2),
                "percent_unlocked": round(circulating / model.total_supply * 100, 1),
            })

        return projections

    def simulate_vesting(
        self,
        schedules: List[VestingSchedule],
        months: int = 48,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Simulate vesting for multiple schedules.

        Returns per-category unlock projections.
        """
        self._stats["simulations_run"] += 1

        result = {}
        for schedule in schedules:
            category_key = schedule.category.value
            result[category_key] = []

            for month in range(months + 1):
                unlocked = schedule.get_unlocked_at_month(month)
                result[category_key].append({
                    "month": month,
                    "unlocked": round(unlocked, 2),
                    "locked": round(schedule.total_amount - unlocked, 2),
                    "percent_unlocked": round(unlocked / schedule.total_amount * 100, 1),
                })

        return result

    def project_market_cap(
        self,
        model: TokenModel,
        price_projections: List[float],
    ) -> List[Dict[str, Any]]:
        """
        Project market cap based on price and supply.

        Args:
            model: Token model
            price_projections: Monthly price projections
        """
        projections = []
        for month, price in enumerate(price_projections):
            circulating = model.get_circulating_at_month(month)
            projections.append({
                "month": month,
                "price": round(price, 4),
                "circulating": round(circulating, 2),
                "market_cap": round(circulating * price, 2),
                "fdv": round(model.total_supply * price, 2),
            })

        return projections

    # ═══════════════════════════════════════════════════════════════════════════
    # ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════

    def analyze_distribution(
        self,
        model: TokenModel,
    ) -> Dict[str, Any]:
        """Analyze token distribution health."""
        if not model.distributions:
            return {"status": "unknown", "issues": ["No distribution data"]}

        issues = []
        warnings = []

        # Calculate category shares
        team_share = sum(
            d.allocation for d in model.distributions
            if d.category in [DistributionType.TEAM, DistributionType.ADVISORS]
        )
        investor_share = sum(
            d.allocation for d in model.distributions
            if d.category == DistributionType.INVESTORS
        )
        community_share = sum(
            d.allocation for d in model.distributions
            if d.category in [
                DistributionType.COMMUNITY,
                DistributionType.ECOSYSTEM,
                DistributionType.AIRDROP,
            ]
        )

        # Analysis
        if team_share > 0.30:
            issues.append(f"High team allocation ({team_share*100:.0f}%) - centralization risk")
        elif team_share > 0.20:
            warnings.append(f"Moderate team allocation ({team_share*100:.0f}%)")

        if investor_share > 0.25:
            warnings.append(f"High investor allocation ({investor_share*100:.0f}%)")

        if community_share < 0.40:
            issues.append(f"Low community allocation ({community_share*100:.0f}%) - may limit adoption")

        # Vesting analysis
        vested_share = sum(
            d.allocation for d in model.distributions
            if d.vesting and d.vesting.vesting_months > 0
        )
        if vested_share < 0.50:
            warnings.append("Less than 50% of tokens have vesting - high unlock risk")

        return {
            "team_share": round(team_share * 100, 1),
            "investor_share": round(investor_share * 100, 1),
            "community_share": round(community_share * 100, 1),
            "vested_share": round(vested_share * 100, 1),
            "issues": issues,
            "warnings": warnings,
            "health_score": max(0, 100 - len(issues) * 20 - len(warnings) * 10),
        }

    def analyze_inflation(
        self,
        model: TokenModel,
        years: int = 5,
    ) -> Dict[str, Any]:
        """Analyze token inflation impact."""
        projections = []
        supply = model.total_supply

        for year in range(years + 1):
            dilution = 1 - (model.total_supply / supply)
            projections.append({
                "year": year,
                "supply": round(supply, 0),
                "dilution": f"{dilution * 100:.2f}%",
            })
            supply *= (1 + model.inflation_rate)
            supply *= (1 - model.burn_rate)

        net_inflation = model.inflation_rate - model.burn_rate

        return {
            "annual_inflation": f"{model.inflation_rate * 100:.2f}%",
            "annual_burn": f"{model.burn_rate * 100:.2f}%",
            "net_inflation": f"{net_inflation * 100:.2f}%",
            "is_deflationary": net_inflation < 0,
            "projections": projections,
            "final_supply": round(projections[-1]["supply"], 0),
            "total_dilution": projections[-1]["dilution"],
        }

    def calculate_fair_launch_score(
        self,
        model: TokenModel,
    ) -> Dict[str, Any]:
        """
        Calculate fair launch score based on distribution.

        Higher score = more fair distribution.
        """
        score = 100.0
        factors = []

        # Check for insider allocation
        insider_share = sum(
            d.allocation for d in model.distributions
            if d.category in [
                DistributionType.TEAM,
                DistributionType.INVESTORS,
                DistributionType.ADVISORS,
            ]
        )
        if insider_share > 0.40:
            deduction = (insider_share - 0.40) * 100
            score -= deduction
            factors.append(f"High insider allocation: -{deduction:.0f}")

        # Check for vesting
        has_team_vesting = any(
            d.vesting and d.vesting.vesting_months >= 24
            for d in model.distributions
            if d.category == DistributionType.TEAM
        )
        if not has_team_vesting:
            score -= 20
            factors.append("No team vesting: -20")

        # Check for community allocation
        community = sum(
            d.allocation for d in model.distributions
            if d.category == DistributionType.COMMUNITY
        )
        if community >= 0.50:
            score += 10
            factors.append("High community allocation: +10")

        # Check for airdrop
        has_airdrop = any(
            d.category == DistributionType.AIRDROP
            for d in model.distributions
        )
        if has_airdrop:
            score += 5
            factors.append("Community airdrop: +5")

        return {
            "score": max(0, min(100, round(score))),
            "rating": self._score_to_rating(score),
            "factors": factors,
        }

    def _score_to_rating(self, score: float) -> str:
        """Convert score to rating."""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        elif score >= 20:
            return "Poor"
        return "Very Poor"

    # ═══════════════════════════════════════════════════════════════════════════
    # QUERIES
    # ═══════════════════════════════════════════════════════════════════════════

    def get_known_tokens(self) -> List[str]:
        """Get list of known token symbols."""
        return list(self._known_tokens.keys())

    def get_tokens_by_type(self, token_type: TokenType) -> List[TokenModel]:
        """Get tokens by type."""
        return [
            t for t in self._known_tokens.values()
            if t.token_type == token_type
        ]

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get modeler statistics."""
        return {
            **self._stats,
            "known_tokens": len(self._known_tokens),
            "cache_size": len(self._model_cache),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_modeler_instance: Optional[TokenomicsModeler] = None


def get_tokenomics_modeler() -> TokenomicsModeler:
    """Get singleton TokenomicsModeler instance."""
    global _modeler_instance

    if _modeler_instance is None:
        _modeler_instance = TokenomicsModeler()

    return _modeler_instance
