"""
Analysis Module
===============
Protocol backwards engineering and security analysis.

Components:
- ProtocolAnalyzer: Smart contract and protocol analysis
- SecurityAuditor: Vulnerability detection and risk assessment
- CompatibilityChecker: Integration compatibility analysis
"""

from cirkelline.web3.analysis.protocol_analyzer import (
    ProtocolAnalyzer,
    ProtocolInfo,
    ContractAnalysis,
    get_protocol_analyzer,
)

from cirkelline.web3.analysis.security_auditor import (
    SecurityAuditor,
    VulnerabilityReport,
    SecurityRisk,
    RiskSeverity,
    get_security_auditor,
)

from cirkelline.web3.analysis.compatibility_checker import (
    CompatibilityChecker,
    CompatibilityReport,
    IntegrationOption,
    get_compatibility_checker,
)

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


__all__ = [
    # Protocol Analysis
    'ProtocolAnalyzer',
    'ProtocolInfo',
    'ContractAnalysis',
    'get_protocol_analyzer',
    # Security
    'SecurityAuditor',
    'VulnerabilityReport',
    'SecurityRisk',
    'RiskSeverity',
    'get_security_auditor',
    # Compatibility
    'CompatibilityChecker',
    'CompatibilityReport',
    'IntegrationOption',
    'get_compatibility_checker',
    # Engine
    'AnalysisResult',
    'AnalysisEngine',
    'get_analysis_engine',
]


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS RESULT
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AnalysisResult:
    """Aggregated analysis result."""
    target: str
    protocol_info: Optional[ProtocolInfo] = None
    vulnerabilities: Optional[VulnerabilityReport] = None
    compatibility: Optional[CompatibilityReport] = None
    recommendations: list = field(default_factory=list)
    overall_risk: str = "unknown"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "protocol_info": self.protocol_info.to_dict() if self.protocol_info else None,
            "vulnerabilities_count": len(self.vulnerabilities.risks) if self.vulnerabilities else 0,
            "compatibility_score": self.compatibility.overall_score if self.compatibility else None,
            "overall_risk": self.overall_risk,
            "recommendations": self.recommendations[:5],
            "timestamp": self.timestamp,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class AnalysisEngine:
    """
    Unified analysis engine.

    Coordinates protocol analysis, security auditing,
    and compatibility checking.
    """

    def __init__(self):
        self._protocol = get_protocol_analyzer()
        self._security = get_security_auditor()
        self._compatibility = get_compatibility_checker()

    @property
    def protocol(self) -> ProtocolAnalyzer:
        return self._protocol

    @property
    def security(self) -> SecurityAuditor:
        return self._security

    @property
    def compatibility(self) -> CompatibilityChecker:
        return self._compatibility

    async def analyze(
        self,
        target: str,
        include_security: bool = True,
        include_compatibility: bool = True,
    ) -> AnalysisResult:
        """
        Perform full analysis of a protocol or contract.

        Args:
            target: Protocol name or contract address
            include_security: Run security audit
            include_compatibility: Run compatibility check
        """
        result = AnalysisResult(target=target)

        # Protocol analysis
        result.protocol_info = await self._protocol.analyze(target)

        # Security audit
        if include_security:
            result.vulnerabilities = await self._security.audit(target)

        # Compatibility check
        if include_compatibility:
            result.compatibility = await self._compatibility.check(target)

        # Calculate overall risk
        result.overall_risk = self._calculate_overall_risk(result)

        # Generate recommendations
        result.recommendations = self._generate_recommendations(result)

        return result

    def _calculate_overall_risk(self, result: AnalysisResult) -> str:
        """Calculate overall risk level."""
        if result.vulnerabilities:
            critical = sum(
                1 for r in result.vulnerabilities.risks
                if r.severity == RiskSeverity.CRITICAL
            )
            high = sum(
                1 for r in result.vulnerabilities.risks
                if r.severity == RiskSeverity.HIGH
            )

            if critical > 0:
                return "critical"
            elif high > 2:
                return "high"
            elif high > 0:
                return "medium"

        return "low"

    def _generate_recommendations(self, result: AnalysisResult) -> list:
        """Generate strategic recommendations."""
        recommendations = []

        # Security recommendations
        if result.vulnerabilities:
            for risk in result.vulnerabilities.risks[:3]:
                if risk.severity in [RiskSeverity.CRITICAL, RiskSeverity.HIGH]:
                    recommendations.append(
                        f"Address {risk.category}: {risk.description[:50]}"
                    )

        # Compatibility recommendations
        if result.compatibility and result.compatibility.overall_score < 0.5:
            recommendations.append(
                "Integration requires significant adaptation work"
            )

        return recommendations

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "protocol": self._protocol.get_stats(),
            "security": self._security.get_stats(),
            "compatibility": self._compatibility.get_stats(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_engine_instance: Optional[AnalysisEngine] = None


def get_analysis_engine() -> AnalysisEngine:
    """Get singleton AnalysisEngine."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = AnalysisEngine()
    return _engine_instance
