"""
Reporting Module
================
Strategic reporting and risk analysis.

Components:
- ReportGenerator: Strategic report generation
- RiskAnalyzer: Risk analysis and recommendations
- ReportingEngine: Unified reporting interface
"""

from cirkelline.web3.reporting.report_generator import (
    ReportGenerator,
    Report,
    ReportType,
    ReportSection,
    get_report_generator,
)

from cirkelline.web3.reporting.risk_analyzer import (
    RiskAnalyzer,
    RiskAssessment,
    RiskLevel,
    RiskCategory,
    RiskMitigation,
    get_risk_analyzer,
)

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


__all__ = [
    # Report Generator
    'ReportGenerator',
    'Report',
    'ReportType',
    'ReportSection',
    'get_report_generator',
    # Risk Analyzer
    'RiskAnalyzer',
    'RiskAssessment',
    'RiskLevel',
    'RiskCategory',
    'RiskMitigation',
    'get_risk_analyzer',
    # Engine
    'ReportingEngine',
    'get_reporting_engine',
]


@dataclass
class AnalysisContext:
    """Context for comprehensive analysis."""
    protocols: List[str]
    governance: Dict[str, Any]
    security: Dict[str, Any]
    market_data: Dict[str, Any]
    timestamp: str


class ReportingEngine:
    """
    Unified reporting engine.

    Coordinates report generation and risk analysis
    for comprehensive Web3 intelligence.
    """

    def __init__(
        self,
        report_generator: Optional[ReportGenerator] = None,
        risk_analyzer: Optional[RiskAnalyzer] = None,
    ):
        self._reporter = report_generator or get_report_generator()
        self._risk = risk_analyzer or get_risk_analyzer()

    async def generate_comprehensive_report(
        self,
        subject: str,
        context: Optional[AnalysisContext] = None,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive analysis report.

        Args:
            subject: Subject of analysis (protocol, project, etc.)
            context: Optional analysis context
        """
        # Generate base report
        report = await self._reporter.generate(
            subject=subject,
            report_type=ReportType.COMPREHENSIVE,
        )

        # Generate risk assessment
        risk = await self._risk.assess(
            subject=subject,
            context=context.__dict__ if context else None,
        )

        return {
            "subject": subject,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "report": report.to_dict(),
            "risk_assessment": risk.to_dict(),
            "executive_summary": self._create_executive_summary(report, risk),
        }

    async def generate_security_brief(
        self,
        subject: str,
        audit_findings: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate a security-focused brief."""
        report = await self._reporter.generate(
            subject=subject,
            report_type=ReportType.SECURITY_AUDIT,
        )

        risk = await self._risk.assess(
            subject=subject,
            categories=[RiskCategory.TECHNICAL, RiskCategory.SMART_CONTRACT],
        )

        return {
            "subject": subject,
            "type": "security_brief",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "report": report.to_dict(),
            "risk_assessment": risk.to_dict(),
            "audit_findings": audit_findings or [],
        }

    async def generate_investment_analysis(
        self,
        subject: str,
        market_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate investment-focused analysis."""
        report = await self._reporter.generate(
            subject=subject,
            report_type=ReportType.INVESTMENT_THESIS,
        )

        risk = await self._risk.assess(
            subject=subject,
            categories=[
                RiskCategory.MARKET,
                RiskCategory.REGULATORY,
                RiskCategory.OPERATIONAL,
            ],
        )

        return {
            "subject": subject,
            "type": "investment_analysis",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "report": report.to_dict(),
            "risk_assessment": risk.to_dict(),
            "market_data": market_data or {},
        }

    def _create_executive_summary(
        self,
        report: Report,
        risk: RiskAssessment,
    ) -> Dict[str, Any]:
        """Create executive summary from report and risk."""
        key_findings = []

        for section in report.sections:
            if section.key_findings:
                key_findings.extend(section.key_findings[:2])

        return {
            "overall_risk": risk.overall_level.value,
            "risk_score": risk.overall_score,
            "key_findings": key_findings[:5],
            "critical_risks": len([
                r for r in risk.risks
                if r.level in [RiskLevel.CRITICAL, RiskLevel.HIGH]
            ]),
            "recommendations_count": len(risk.mitigations),
            "confidence": report.metadata.get("confidence", "medium"),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return {
            "reporter_stats": self._reporter.get_stats(),
            "risk_stats": self._risk.get_stats(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_engine_instance: Optional[ReportingEngine] = None


def get_reporting_engine() -> ReportingEngine:
    """Get singleton ReportingEngine instance."""
    global _engine_instance

    if _engine_instance is None:
        _engine_instance = ReportingEngine()

    return _engine_instance
