"""
Compatibility Checker
=====================
Integration compatibility analysis for protocols and contracts.

Responsibilities:
- Assess Cirkelline ecosystem compatibility
- Identify integration requirements
- Evaluate technical dependencies
- Generate integration recommendations
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

class CompatibilityLevel(Enum):
    """Integration compatibility levels."""
    NATIVE = "native"        # Direct integration available
    ADAPTER = "adapter"      # Requires adapter implementation
    BRIDGE = "bridge"        # Requires bridge/wrapper
    INCOMPATIBLE = "incompatible"  # Cannot be integrated
    UNKNOWN = "unknown"


class IntegrationRequirement(Enum):
    """Types of integration requirements."""
    SDK = "sdk"              # SDK/library needed
    API = "api"              # API access required
    CONTRACT = "contract"    # Smart contract interaction
    ORACLE = "oracle"        # Oracle integration
    WALLET = "wallet"        # Wallet connection
    RPC = "rpc"              # RPC node access
    INDEXER = "indexer"      # Blockchain indexer
    GRAPH = "graph"          # The Graph subgraph
    IPFS = "ipfs"            # IPFS access
    SIGNING = "signing"      # Transaction signing


class IntegrationDomain(Enum):
    """Integration domains within Cirkelline."""
    IDENTITY = "identity"    # DID/credential integration
    STORAGE = "storage"      # Decentralized storage
    AGENTS = "agents"        # Agent capabilities
    GOVERNANCE = "governance"  # DAO participation
    ANALYTICS = "analytics"  # Data analytics
    SECURITY = "security"    # Security services
    PAYMENTS = "payments"    # Token/payment handling


@dataclass
class IntegrationOption:
    """A possible integration approach."""
    name: str
    level: CompatibilityLevel
    requirements: List[IntegrationRequirement] = field(default_factory=list)
    complexity: str = "low"  # low, medium, high
    effort_score: float = 0.0  # 0-10
    description: str = ""
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level.value,
            "requirements": [r.value for r in self.requirements],
            "complexity": self.complexity,
            "effort_score": round(self.effort_score, 1),
            "description": self.description[:150],
            "pros": self.pros[:3],
            "cons": self.cons[:3],
        }


@dataclass
class DomainCompatibility:
    """Compatibility assessment for a specific domain."""
    domain: IntegrationDomain
    score: float = 0.0  # 0-1
    level: CompatibilityLevel = CompatibilityLevel.UNKNOWN
    notes: str = ""
    blockers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain.value,
            "score": round(self.score, 2),
            "level": self.level.value,
            "notes": self.notes[:100],
            "has_blockers": len(self.blockers) > 0,
        }


@dataclass
class CompatibilityReport:
    """Complete compatibility assessment report."""
    target: str
    overall_score: float = 0.0  # 0-1
    overall_level: CompatibilityLevel = CompatibilityLevel.UNKNOWN
    domain_scores: List[DomainCompatibility] = field(default_factory=list)
    integration_options: List[IntegrationOption] = field(default_factory=list)
    requirements: List[IntegrationRequirement] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "overall_score": round(self.overall_score, 2),
            "overall_level": self.overall_level.value,
            "domain_count": len(self.domain_scores),
            "options_count": len(self.integration_options),
            "requirements": [r.value for r in self.requirements],
            "blockers_count": len(self.blockers),
            "recommendations": self.recommendations[:3],
            "timestamp": self.timestamp,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# PROTOCOL COMPATIBILITY DATA
# ═══════════════════════════════════════════════════════════════════════════════

PROTOCOL_COMPATIBILITY = {
    "ethereum": {
        "level": CompatibilityLevel.NATIVE,
        "score": 0.95,
        "requirements": [
            IntegrationRequirement.RPC,
            IntegrationRequirement.WALLET,
        ],
        "domains": {
            IntegrationDomain.IDENTITY: 0.9,
            IntegrationDomain.STORAGE: 0.7,
            IntegrationDomain.AGENTS: 0.85,
            IntegrationDomain.GOVERNANCE: 0.95,
            IntegrationDomain.ANALYTICS: 0.9,
            IntegrationDomain.PAYMENTS: 0.95,
        },
    },
    "ipfs": {
        "level": CompatibilityLevel.NATIVE,
        "score": 0.90,
        "requirements": [
            IntegrationRequirement.IPFS,
            IntegrationRequirement.API,
        ],
        "domains": {
            IntegrationDomain.STORAGE: 0.95,
            IntegrationDomain.AGENTS: 0.8,
            IntegrationDomain.ANALYTICS: 0.6,
        },
    },
    "arweave": {
        "level": CompatibilityLevel.ADAPTER,
        "score": 0.80,
        "requirements": [
            IntegrationRequirement.API,
            IntegrationRequirement.WALLET,
        ],
        "domains": {
            IntegrationDomain.STORAGE: 0.95,
            IntegrationDomain.ANALYTICS: 0.7,
        },
    },
    "chainlink": {
        "level": CompatibilityLevel.NATIVE,
        "score": 0.85,
        "requirements": [
            IntegrationRequirement.ORACLE,
            IntegrationRequirement.CONTRACT,
        ],
        "domains": {
            IntegrationDomain.ANALYTICS: 0.9,
            IntegrationDomain.AGENTS: 0.7,
        },
    },
    "ens": {
        "level": CompatibilityLevel.NATIVE,
        "score": 0.90,
        "requirements": [
            IntegrationRequirement.CONTRACT,
            IntegrationRequirement.RPC,
        ],
        "domains": {
            IntegrationDomain.IDENTITY: 0.95,
            IntegrationDomain.AGENTS: 0.8,
        },
    },
    "polygon": {
        "level": CompatibilityLevel.NATIVE,
        "score": 0.90,
        "requirements": [
            IntegrationRequirement.RPC,
            IntegrationRequirement.WALLET,
        ],
        "domains": {
            IntegrationDomain.IDENTITY: 0.85,
            IntegrationDomain.GOVERNANCE: 0.9,
            IntegrationDomain.PAYMENTS: 0.9,
            IntegrationDomain.ANALYTICS: 0.85,
        },
    },
    "the-graph": {
        "level": CompatibilityLevel.NATIVE,
        "score": 0.88,
        "requirements": [
            IntegrationRequirement.GRAPH,
            IntegrationRequirement.API,
        ],
        "domains": {
            IntegrationDomain.ANALYTICS: 0.95,
            IntegrationDomain.AGENTS: 0.8,
        },
    },
    "solana": {
        "level": CompatibilityLevel.ADAPTER,
        "score": 0.70,
        "requirements": [
            IntegrationRequirement.SDK,
            IntegrationRequirement.RPC,
            IntegrationRequirement.WALLET,
        ],
        "domains": {
            IntegrationDomain.PAYMENTS: 0.8,
            IntegrationDomain.ANALYTICS: 0.75,
        },
    },
    "cosmos": {
        "level": CompatibilityLevel.BRIDGE,
        "score": 0.60,
        "requirements": [
            IntegrationRequirement.SDK,
            IntegrationRequirement.RPC,
            IntegrationRequirement.SIGNING,
        ],
        "domains": {
            IntegrationDomain.GOVERNANCE: 0.8,
            IntegrationDomain.PAYMENTS: 0.7,
        },
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# COMPATIBILITY CHECKER
# ═══════════════════════════════════════════════════════════════════════════════

class CompatibilityChecker:
    """
    Integration compatibility analyzer.

    Assesses how well external protocols and technologies
    can integrate with the Cirkelline ecosystem.
    """

    def __init__(self):
        self._compatibility_data = PROTOCOL_COMPATIBILITY
        self._check_cache: Dict[str, CompatibilityReport] = {}

        # Cirkelline ecosystem requirements
        self._ecosystem_requirements = [
            IntegrationRequirement.API,
            IntegrationRequirement.SIGNING,
        ]

        # Statistics
        self._stats = {
            "total_checks": 0,
            "native_compatible": 0,
            "requires_adapter": 0,
            "incompatible": 0,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # CHECKING
    # ═══════════════════════════════════════════════════════════════════════════

    async def check(self, target: str) -> CompatibilityReport:
        """
        Check compatibility of a target with Cirkelline.

        Args:
            target: Protocol or technology name

        Returns:
            Compatibility report
        """
        self._stats["total_checks"] += 1

        # Check cache
        target_lower = target.lower()
        if target_lower in self._check_cache:
            return self._check_cache[target_lower]

        report = CompatibilityReport(target=target)

        # Check known protocols
        if target_lower in self._compatibility_data:
            data = self._compatibility_data[target_lower]
            report = self._build_report_from_data(target, data)
        else:
            # Unknown protocol - perform generic analysis
            report = await self._analyze_unknown(target)

        # Generate integration options
        report.integration_options = self._generate_integration_options(report)

        # Generate recommendations
        report.recommendations = self._generate_recommendations(report)

        # Update stats
        self._update_stats(report)

        self._check_cache[target_lower] = report
        return report

    async def check_domain(
        self,
        target: str,
        domain: IntegrationDomain,
    ) -> DomainCompatibility:
        """
        Check compatibility for a specific integration domain.

        Args:
            target: Protocol or technology name
            domain: Integration domain to check
        """
        report = await self.check(target)

        for dc in report.domain_scores:
            if dc.domain == domain:
                return dc

        # Domain not assessed
        return DomainCompatibility(
            domain=domain,
            score=0.0,
            level=CompatibilityLevel.UNKNOWN,
            notes="Domain not assessed for this target",
        )

    async def compare(
        self,
        targets: List[str],
    ) -> Dict[str, CompatibilityReport]:
        """
        Compare compatibility of multiple targets.

        Returns sorted by overall score.
        """
        reports = {}
        for target in targets:
            reports[target] = await self.check(target)

        # Sort by score
        sorted_reports = dict(
            sorted(
                reports.items(),
                key=lambda x: x[1].overall_score,
                reverse=True
            )
        )

        return sorted_reports

    def _build_report_from_data(
        self,
        target: str,
        data: Dict[str, Any],
    ) -> CompatibilityReport:
        """Build report from known compatibility data."""
        report = CompatibilityReport(
            target=target,
            overall_score=data["score"],
            overall_level=data["level"],
            requirements=data.get("requirements", []),
        )

        # Build domain scores
        for domain, score in data.get("domains", {}).items():
            level = self._score_to_level(score)
            report.domain_scores.append(DomainCompatibility(
                domain=domain,
                score=score,
                level=level,
            ))

        return report

    async def _analyze_unknown(self, target: str) -> CompatibilityReport:
        """Analyze unknown protocol."""
        # Default conservative assessment
        return CompatibilityReport(
            target=target,
            overall_score=0.3,
            overall_level=CompatibilityLevel.UNKNOWN,
            requirements=[
                IntegrationRequirement.SDK,
                IntegrationRequirement.API,
            ],
            blockers=["Unknown protocol - requires detailed analysis"],
            domain_scores=[
                DomainCompatibility(
                    domain=IntegrationDomain.AGENTS,
                    score=0.5,
                    level=CompatibilityLevel.ADAPTER,
                    notes="Generic agent integration possible",
                ),
            ],
        )

    def _score_to_level(self, score: float) -> CompatibilityLevel:
        """Convert score to compatibility level."""
        if score >= 0.85:
            return CompatibilityLevel.NATIVE
        elif score >= 0.65:
            return CompatibilityLevel.ADAPTER
        elif score >= 0.40:
            return CompatibilityLevel.BRIDGE
        else:
            return CompatibilityLevel.INCOMPATIBLE

    # ═══════════════════════════════════════════════════════════════════════════
    # INTEGRATION OPTIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def _generate_integration_options(
        self,
        report: CompatibilityReport,
    ) -> List[IntegrationOption]:
        """Generate possible integration approaches."""
        options = []

        if report.overall_level == CompatibilityLevel.NATIVE:
            options.append(IntegrationOption(
                name="Direct Integration",
                level=CompatibilityLevel.NATIVE,
                requirements=report.requirements,
                complexity="low",
                effort_score=2.0,
                description="Direct integration using native SDK/API",
                pros=["Fast implementation", "Full feature access", "Minimal overhead"],
                cons=["Tight coupling"],
            ))

        if report.overall_level in [CompatibilityLevel.NATIVE, CompatibilityLevel.ADAPTER]:
            options.append(IntegrationOption(
                name="Adapter Pattern",
                level=CompatibilityLevel.ADAPTER,
                requirements=[IntegrationRequirement.SDK] + report.requirements,
                complexity="medium",
                effort_score=5.0,
                description="Build adapter layer for abstraction",
                pros=["Loose coupling", "Easy to swap", "Testable"],
                cons=["Additional code", "Maintenance overhead"],
            ))

        if report.overall_level in [CompatibilityLevel.ADAPTER, CompatibilityLevel.BRIDGE]:
            options.append(IntegrationOption(
                name="Bridge Integration",
                level=CompatibilityLevel.BRIDGE,
                requirements=[
                    IntegrationRequirement.CONTRACT,
                    IntegrationRequirement.API,
                ],
                complexity="high",
                effort_score=8.0,
                description="Build bridge contract for cross-protocol interaction",
                pros=["Full isolation", "Security boundary"],
                cons=["Complex", "Gas overhead", "Bridge risks"],
            ))

        return options

    def _generate_recommendations(
        self,
        report: CompatibilityReport,
    ) -> List[str]:
        """Generate integration recommendations."""
        recommendations = []

        if report.overall_score >= 0.85:
            recommendations.append(
                "High compatibility - recommend direct integration"
            )
        elif report.overall_score >= 0.65:
            recommendations.append(
                "Good compatibility - consider adapter pattern for flexibility"
            )
        elif report.overall_score >= 0.40:
            recommendations.append(
                "Limited compatibility - bridge pattern required"
            )
        else:
            recommendations.append(
                "Low compatibility - evaluate alternatives before proceeding"
            )

        # Domain-specific recommendations
        for dc in report.domain_scores:
            if dc.score < 0.5:
                recommendations.append(
                    f"Warning: {dc.domain.value} integration requires significant work"
                )

        # Requirement recommendations
        if IntegrationRequirement.ORACLE in report.requirements:
            recommendations.append(
                "Oracle dependency detected - ensure reliable price feeds"
            )

        if IntegrationRequirement.SIGNING in report.requirements:
            recommendations.append(
                "Transaction signing required - integrate with wallet infrastructure"
            )

        return recommendations[:5]

    def _update_stats(self, report: CompatibilityReport) -> None:
        """Update statistics based on report."""
        if report.overall_level == CompatibilityLevel.NATIVE:
            self._stats["native_compatible"] += 1
        elif report.overall_level in [CompatibilityLevel.ADAPTER, CompatibilityLevel.BRIDGE]:
            self._stats["requires_adapter"] += 1
        else:
            self._stats["incompatible"] += 1

    # ═══════════════════════════════════════════════════════════════════════════
    # QUERIES
    # ═══════════════════════════════════════════════════════════════════════════

    def get_known_protocols(self) -> List[str]:
        """Get list of known protocols."""
        return list(self._compatibility_data.keys())

    def get_compatible_protocols(
        self,
        min_score: float = 0.7,
    ) -> List[str]:
        """Get protocols meeting minimum compatibility score."""
        return [
            name for name, data in self._compatibility_data.items()
            if data["score"] >= min_score
        ]

    def get_protocols_for_domain(
        self,
        domain: IntegrationDomain,
        min_score: float = 0.7,
    ) -> List[str]:
        """Get protocols compatible with a specific domain."""
        compatible = []
        for name, data in self._compatibility_data.items():
            domain_scores = data.get("domains", {})
            if domain in domain_scores and domain_scores[domain] >= min_score:
                compatible.append(name)
        return compatible

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get checker statistics."""
        return {
            **self._stats,
            "known_protocols": len(self._compatibility_data),
            "cache_size": len(self._check_cache),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_checker_instance: Optional[CompatibilityChecker] = None


def get_compatibility_checker() -> CompatibilityChecker:
    """Get singleton CompatibilityChecker instance."""
    global _checker_instance

    if _checker_instance is None:
        _checker_instance = CompatibilityChecker()

    return _checker_instance
