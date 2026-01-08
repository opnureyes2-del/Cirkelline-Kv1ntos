"""
Risk Analyzer
=============
Web3 risk analysis and mitigation recommendations.

Responsibilities:
- Identify and categorize risks
- Quantify risk severity
- Generate mitigation strategies
- Track risk evolution
"""

import logging
import secrets
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class RiskLevel(Enum):
    """Risk severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class RiskCategory(Enum):
    """Categories of risk."""
    SMART_CONTRACT = "smart_contract"
    TECHNICAL = "technical"
    GOVERNANCE = "governance"
    MARKET = "market"
    REGULATORY = "regulatory"
    OPERATIONAL = "operational"
    COUNTERPARTY = "counterparty"
    LIQUIDITY = "liquidity"
    CUSTODY = "custody"
    ORACLE = "oracle"
    MEV = "mev"
    BRIDGE = "bridge"


class MitigationType(Enum):
    """Types of risk mitigation."""
    TECHNICAL = "technical"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    GOVERNANCE = "governance"
    MONITORING = "monitoring"
    INSURANCE = "insurance"
    DIVERSIFICATION = "diversification"


class RiskTrend(Enum):
    """Risk trend direction."""
    INCREASING = "increasing"
    STABLE = "stable"
    DECREASING = "decreasing"
    UNKNOWN = "unknown"


@dataclass
class Risk:
    """A specific risk."""
    risk_id: str
    category: RiskCategory
    level: RiskLevel
    title: str
    description: str
    impact: str = ""
    probability: float = 0.5  # 0-1
    affected_areas: List[str] = field(default_factory=list)
    indicators: List[str] = field(default_factory=list)
    trend: RiskTrend = RiskTrend.STABLE
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.risk_id,
            "category": self.category.value,
            "level": self.level.value,
            "title": self.title,
            "description": self.description[:200] + "..." if len(self.description) > 200 else self.description,
            "probability": round(self.probability, 2),
            "trend": self.trend.value,
        }

    @property
    def score(self) -> float:
        """Calculate risk score (0-100)."""
        level_weights = {
            RiskLevel.CRITICAL: 1.0,
            RiskLevel.HIGH: 0.75,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.LOW: 0.25,
            RiskLevel.INFORMATIONAL: 0.1,
        }
        return round(level_weights.get(self.level, 0.5) * self.probability * 100, 1)


@dataclass
class RiskMitigation:
    """A risk mitigation strategy."""
    mitigation_id: str
    risk_id: str
    mitigation_type: MitigationType
    title: str
    description: str
    effectiveness: float = 0.5  # 0-1
    implementation_complexity: str = "medium"
    estimated_cost: str = ""
    timeframe: str = ""
    priority: int = 2  # 1-5, 1 is highest
    prerequisites: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.mitigation_id,
            "risk_id": self.risk_id,
            "type": self.mitigation_type.value,
            "title": self.title,
            "effectiveness": round(self.effectiveness, 2),
            "complexity": self.implementation_complexity,
            "priority": self.priority,
        }


@dataclass
class RiskAssessment:
    """Complete risk assessment."""
    assessment_id: str
    subject: str
    risks: List[Risk] = field(default_factory=list)
    mitigations: List[RiskMitigation] = field(default_factory=list)
    overall_level: RiskLevel = RiskLevel.MEDIUM
    overall_score: float = 50.0
    created_at: str = ""
    methodology: str = "cirkelline-risk-framework"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "subject": self.subject,
            "overall_level": self.overall_level.value,
            "overall_score": round(self.overall_score, 1),
            "risks_count": len(self.risks),
            "mitigations_count": len(self.mitigations),
            "risks_by_level": self._count_by_level(),
            "created_at": self.created_at,
        }

    def _count_by_level(self) -> Dict[str, int]:
        """Count risks by severity level."""
        counts = {}
        for risk in self.risks:
            level = risk.level.value
            counts[level] = counts.get(level, 0) + 1
        return counts

    def get_risks_by_category(
        self,
        category: RiskCategory,
    ) -> List[Risk]:
        """Get risks filtered by category."""
        return [r for r in self.risks if r.category == category]

    def get_critical_risks(self) -> List[Risk]:
        """Get critical and high severity risks."""
        return [
            r for r in self.risks
            if r.level in [RiskLevel.CRITICAL, RiskLevel.HIGH]
        ]


# ═══════════════════════════════════════════════════════════════════════════════
# RISK PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════

RISK_PATTERNS = {
    RiskCategory.SMART_CONTRACT: [
        {
            "title": "Reentrancy Vulnerability",
            "description": "Contract may be vulnerable to reentrancy attacks where external calls can re-enter the contract before state updates complete.",
            "level": RiskLevel.CRITICAL,
            "indicators": ["external calls before state updates", "callback patterns"],
            "mitigation": "Implement checks-effects-interactions pattern and reentrancy guards",
        },
        {
            "title": "Access Control Weakness",
            "description": "Insufficient access control on critical functions may allow unauthorized operations.",
            "level": RiskLevel.HIGH,
            "indicators": ["missing role checks", "public critical functions"],
            "mitigation": "Implement role-based access control with principle of least privilege",
        },
        {
            "title": "Integer Overflow/Underflow",
            "description": "Arithmetic operations may overflow or underflow without proper checks.",
            "level": RiskLevel.HIGH,
            "indicators": ["unchecked arithmetic", "pre-0.8.0 Solidity"],
            "mitigation": "Use SafeMath or Solidity 0.8+ with built-in overflow checks",
        },
    ],
    RiskCategory.GOVERNANCE: [
        {
            "title": "Voter Apathy",
            "description": "Low governance participation may lead to centralization of decision-making power.",
            "level": RiskLevel.MEDIUM,
            "indicators": ["low quorum achievement", "declining participation"],
            "mitigation": "Implement incentives for participation and delegation mechanisms",
        },
        {
            "title": "Whale Domination",
            "description": "Large token holders may disproportionately influence governance outcomes.",
            "level": RiskLevel.HIGH,
            "indicators": ["high Nakamoto coefficient", "concentrated voting power"],
            "mitigation": "Consider quadratic voting or conviction voting mechanisms",
        },
        {
            "title": "Governance Attack",
            "description": "Flash loan or temporary stake accumulation may enable hostile governance takeover.",
            "level": RiskLevel.HIGH,
            "indicators": ["no snapshot mechanism", "short voting period"],
            "mitigation": "Implement vote escrow with lock periods and block-based snapshots",
        },
    ],
    RiskCategory.MARKET: [
        {
            "title": "Token Volatility",
            "description": "High price volatility may impact protocol stability and user experience.",
            "level": RiskLevel.MEDIUM,
            "indicators": ["high daily volatility", "thin order books"],
            "mitigation": "Implement stability mechanisms and diversified treasury",
        },
        {
            "title": "Liquidity Concentration",
            "description": "Liquidity concentrated in few venues may create single points of failure.",
            "level": RiskLevel.MEDIUM,
            "indicators": ["single DEX dependency", "concentrated LP positions"],
            "mitigation": "Incentivize multi-venue liquidity provision",
        },
    ],
    RiskCategory.ORACLE: [
        {
            "title": "Oracle Manipulation",
            "description": "Price feeds may be manipulated through flash loans or market manipulation.",
            "level": RiskLevel.CRITICAL,
            "indicators": ["single oracle source", "no TWAP", "low liquidity pairs"],
            "mitigation": "Use multiple oracle sources with TWAP and circuit breakers",
        },
        {
            "title": "Oracle Latency",
            "description": "Delayed price updates may create arbitrage opportunities at protocol expense.",
            "level": RiskLevel.MEDIUM,
            "indicators": ["infrequent updates", "volatile market conditions"],
            "mitigation": "Implement pull-based oracles with freshness checks",
        },
    ],
    RiskCategory.REGULATORY: [
        {
            "title": "Securities Classification",
            "description": "Token may be classified as a security in certain jurisdictions.",
            "level": RiskLevel.HIGH,
            "indicators": ["profit expectations", "centralized team control"],
            "mitigation": "Progressive decentralization and legal counsel engagement",
        },
        {
            "title": "Sanctions Compliance",
            "description": "Protocol may inadvertently facilitate sanctioned transactions.",
            "level": RiskLevel.HIGH,
            "indicators": ["no screening", "mixing protocols integration"],
            "mitigation": "Implement compliance screening for sanctioned addresses",
        },
    ],
    RiskCategory.OPERATIONAL: [
        {
            "title": "Key Person Risk",
            "description": "Critical operations depend on limited team members.",
            "level": RiskLevel.MEDIUM,
            "indicators": ["single maintainers", "centralized deployment keys"],
            "mitigation": "Implement multi-sig and document operational procedures",
        },
        {
            "title": "Dependency Risk",
            "description": "Protocol relies on external dependencies that may fail or change.",
            "level": RiskLevel.MEDIUM,
            "indicators": ["external protocol calls", "third-party infrastructure"],
            "mitigation": "Monitor dependencies and implement fallback mechanisms",
        },
    ],
}


MITIGATION_TEMPLATES = {
    MitigationType.TECHNICAL: {
        "complexity": "high",
        "timeframe": "weeks to months",
        "effectiveness": 0.8,
    },
    MitigationType.OPERATIONAL: {
        "complexity": "medium",
        "timeframe": "days to weeks",
        "effectiveness": 0.7,
    },
    MitigationType.MONITORING: {
        "complexity": "low",
        "timeframe": "hours to days",
        "effectiveness": 0.5,
    },
    MitigationType.INSURANCE: {
        "complexity": "medium",
        "timeframe": "weeks",
        "effectiveness": 0.6,
    },
    MitigationType.GOVERNANCE: {
        "complexity": "medium",
        "timeframe": "weeks to months",
        "effectiveness": 0.7,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# RISK ANALYZER
# ═══════════════════════════════════════════════════════════════════════════════

class RiskAnalyzer:
    """
    Web3 risk analyzer.

    Identifies, quantifies, and provides mitigation
    strategies for various categories of Web3 risks.
    """

    def __init__(self):
        self._risk_patterns = RISK_PATTERNS
        self._mitigation_templates = MITIGATION_TEMPLATES
        self._assessment_cache: Dict[str, RiskAssessment] = {}

        # Statistics
        self._stats = {
            "assessments_performed": 0,
            "risks_identified": 0,
            "mitigations_generated": 0,
            "by_category": {},
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # ASSESSMENT
    # ═══════════════════════════════════════════════════════════════════════════

    async def assess(
        self,
        subject: str,
        context: Optional[Dict[str, Any]] = None,
        categories: Optional[List[RiskCategory]] = None,
    ) -> RiskAssessment:
        """
        Perform risk assessment.

        Args:
            subject: Subject of assessment
            context: Optional context data
            categories: Optional categories to focus on
        """
        self._stats["assessments_performed"] += 1

        assessment_id = f"assess-{secrets.token_hex(8)}"
        target_categories = categories or list(RiskCategory)

        # Identify risks
        risks = []
        for category in target_categories:
            category_risks = await self._assess_category(
                subject, category, context
            )
            risks.extend(category_risks)
            self._stats["risks_identified"] += len(category_risks)
            self._stats["by_category"][category.value] = (
                self._stats["by_category"].get(category.value, 0) +
                len(category_risks)
            )

        # Generate mitigations
        mitigations = []
        for risk in risks:
            if risk.level in [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM]:
                mitigation = await self._generate_mitigation(risk)
                mitigations.append(mitigation)
                self._stats["mitigations_generated"] += 1

        # Calculate overall risk
        overall_score = self._calculate_overall_score(risks)
        overall_level = self._score_to_level(overall_score)

        assessment = RiskAssessment(
            assessment_id=assessment_id,
            subject=subject,
            risks=risks,
            mitigations=mitigations,
            overall_level=overall_level,
            overall_score=overall_score,
            created_at=datetime.utcnow().isoformat() + "Z",
            metadata={
                "categories_assessed": [c.value for c in target_categories],
                "context_provided": context is not None,
            },
        )

        self._assessment_cache[assessment_id] = assessment
        return assessment

    async def _assess_category(
        self,
        subject: str,
        category: RiskCategory,
        context: Optional[Dict[str, Any]],
    ) -> List[Risk]:
        """Assess risks in a specific category."""
        risks = []
        patterns = self._risk_patterns.get(category, [])

        for pattern in patterns:
            # Apply pattern matching (simplified)
            risk = Risk(
                risk_id=f"risk-{secrets.token_hex(6)}",
                category=category,
                level=pattern["level"],
                title=pattern["title"],
                description=pattern["description"],
                indicators=pattern.get("indicators", []),
                probability=self._estimate_probability(pattern, context),
                trend=RiskTrend.STABLE,
            )
            risks.append(risk)

        return risks

    def _estimate_probability(
        self,
        pattern: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> float:
        """Estimate probability based on pattern and context."""
        # Base probability by severity
        base_probs = {
            RiskLevel.CRITICAL: 0.3,
            RiskLevel.HIGH: 0.4,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.LOW: 0.6,
            RiskLevel.INFORMATIONAL: 0.7,
        }
        return base_probs.get(pattern["level"], 0.5)

    async def _generate_mitigation(self, risk: Risk) -> RiskMitigation:
        """Generate mitigation for a risk."""
        # Determine mitigation type based on category
        type_mapping = {
            RiskCategory.SMART_CONTRACT: MitigationType.TECHNICAL,
            RiskCategory.TECHNICAL: MitigationType.TECHNICAL,
            RiskCategory.GOVERNANCE: MitigationType.GOVERNANCE,
            RiskCategory.MARKET: MitigationType.FINANCIAL,
            RiskCategory.REGULATORY: MitigationType.OPERATIONAL,
            RiskCategory.OPERATIONAL: MitigationType.OPERATIONAL,
            RiskCategory.ORACLE: MitigationType.TECHNICAL,
            RiskCategory.LIQUIDITY: MitigationType.FINANCIAL,
        }

        mit_type = type_mapping.get(risk.category, MitigationType.OPERATIONAL)
        template = self._mitigation_templates.get(mit_type, {})

        # Find pattern mitigation description
        mitigation_desc = "Implement appropriate controls and monitoring"
        for pattern in self._risk_patterns.get(risk.category, []):
            if pattern["title"] == risk.title:
                mitigation_desc = pattern.get("mitigation", mitigation_desc)
                break

        return RiskMitigation(
            mitigation_id=f"mit-{secrets.token_hex(6)}",
            risk_id=risk.risk_id,
            mitigation_type=mit_type,
            title=f"Mitigate: {risk.title}",
            description=mitigation_desc,
            effectiveness=template.get("effectiveness", 0.5),
            implementation_complexity=template.get("complexity", "medium"),
            timeframe=template.get("timeframe", "weeks"),
            priority=self._calculate_priority(risk),
        )

    def _calculate_priority(self, risk: Risk) -> int:
        """Calculate mitigation priority (1-5, 1 is highest)."""
        priority_map = {
            RiskLevel.CRITICAL: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.MEDIUM: 3,
            RiskLevel.LOW: 4,
            RiskLevel.INFORMATIONAL: 5,
        }
        return priority_map.get(risk.level, 3)

    def _calculate_overall_score(self, risks: List[Risk]) -> float:
        """Calculate overall risk score."""
        if not risks:
            return 0.0

        total_score = sum(r.score for r in risks)
        max_possible = len(risks) * 100

        # Weighted by critical risks
        critical_count = len([
            r for r in risks
            if r.level in [RiskLevel.CRITICAL, RiskLevel.HIGH]
        ])
        critical_weight = 1 + (critical_count * 0.1)

        return min(100, (total_score / max_possible) * 100 * critical_weight)

    def _score_to_level(self, score: float) -> RiskLevel:
        """Convert score to risk level."""
        if score >= 80:
            return RiskLevel.CRITICAL
        elif score >= 60:
            return RiskLevel.HIGH
        elif score >= 40:
            return RiskLevel.MEDIUM
        elif score >= 20:
            return RiskLevel.LOW
        else:
            return RiskLevel.INFORMATIONAL

    # ═══════════════════════════════════════════════════════════════════════════
    # QUICK CHECKS
    # ═══════════════════════════════════════════════════════════════════════════

    async def quick_check(
        self,
        subject: str,
        categories: Optional[List[RiskCategory]] = None,
    ) -> Dict[str, Any]:
        """
        Perform quick risk check.

        Args:
            subject: Subject to check
            categories: Categories to focus on
        """
        assessment = await self.assess(
            subject=subject,
            categories=categories,
        )

        return {
            "subject": subject,
            "overall_level": assessment.overall_level.value,
            "overall_score": assessment.overall_score,
            "critical_risks": len([
                r for r in assessment.risks
                if r.level == RiskLevel.CRITICAL
            ]),
            "high_risks": len([
                r for r in assessment.risks
                if r.level == RiskLevel.HIGH
            ]),
            "summary": self._generate_summary(assessment),
        }

    def _generate_summary(self, assessment: RiskAssessment) -> str:
        """Generate risk summary."""
        critical = len(assessment.get_critical_risks())
        total = len(assessment.risks)

        if critical == 0:
            return f"Assessment complete. {total} risks identified, none critical."
        else:
            return f"Assessment complete. {critical} critical/high risks of {total} total require attention."

    # ═══════════════════════════════════════════════════════════════════════════
    # COMPARISONS
    # ═══════════════════════════════════════════════════════════════════════════

    async def compare(
        self,
        subjects: List[str],
        categories: Optional[List[RiskCategory]] = None,
    ) -> Dict[str, Any]:
        """
        Compare risks across multiple subjects.

        Args:
            subjects: List of subjects to compare
            categories: Categories to focus on
        """
        assessments = {}
        for subject in subjects:
            assessment = await self.assess(subject, categories=categories)
            assessments[subject] = assessment

        comparison = {
            "subjects": subjects,
            "scores": {
                s: a.overall_score for s, a in assessments.items()
            },
            "levels": {
                s: a.overall_level.value for s, a in assessments.items()
            },
            "risk_counts": {
                s: len(a.risks) for s, a in assessments.items()
            },
            "ranking": sorted(
                subjects,
                key=lambda s: assessments[s].overall_score
            ),
        }

        return comparison

    # ═══════════════════════════════════════════════════════════════════════════
    # QUERIES
    # ═══════════════════════════════════════════════════════════════════════════

    def get_assessment(self, assessment_id: str) -> Optional[RiskAssessment]:
        """Get assessment by ID."""
        return self._assessment_cache.get(assessment_id)

    def get_risk_patterns(
        self,
        category: Optional[RiskCategory] = None,
    ) -> Dict[str, Any]:
        """Get risk patterns for reference."""
        if category:
            return {category.value: self._risk_patterns.get(category, [])}
        return {c.value: patterns for c, patterns in self._risk_patterns.items()}

    def list_categories(self) -> List[str]:
        """List available risk categories."""
        return [c.value for c in RiskCategory]

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get analyzer statistics."""
        return {
            **self._stats,
            "cached_assessments": len(self._assessment_cache),
            "risk_patterns": sum(
                len(p) for p in self._risk_patterns.values()
            ),
            "categories_covered": len(self._risk_patterns),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_analyzer_instance: Optional[RiskAnalyzer] = None


def get_risk_analyzer() -> RiskAnalyzer:
    """Get singleton RiskAnalyzer instance."""
    global _analyzer_instance

    if _analyzer_instance is None:
        _analyzer_instance = RiskAnalyzer()

    return _analyzer_instance
