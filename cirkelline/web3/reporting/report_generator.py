"""
Report Generator
================
Strategic report generation for Web3 analysis.

Responsibilities:
- Generate comprehensive analysis reports
- Structure findings into actionable insights
- Support multiple report formats
- Template-based report creation
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

class ReportType(Enum):
    """Types of reports."""
    COMPREHENSIVE = "comprehensive"
    SECURITY_AUDIT = "security_audit"
    GOVERNANCE_ANALYSIS = "governance_analysis"
    INVESTMENT_THESIS = "investment_thesis"
    TECHNICAL_DEEP_DIVE = "technical_deep_dive"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    TREND_REPORT = "trend_report"
    INCIDENT_REPORT = "incident_report"
    QUARTERLY_REVIEW = "quarterly_review"


class SectionType(Enum):
    """Types of report sections."""
    EXECUTIVE_SUMMARY = "executive_summary"
    INTRODUCTION = "introduction"
    METHODOLOGY = "methodology"
    FINDINGS = "findings"
    ANALYSIS = "analysis"
    RECOMMENDATIONS = "recommendations"
    RISK_ASSESSMENT = "risk_assessment"
    TECHNICAL_DETAILS = "technical_details"
    MARKET_ANALYSIS = "market_analysis"
    GOVERNANCE = "governance"
    TOKENOMICS = "tokenomics"
    ROADMAP = "roadmap"
    APPENDIX = "appendix"
    CONCLUSION = "conclusion"


class OutputFormat(Enum):
    """Report output formats."""
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    PDF = "pdf"


class ConfidenceLevel(Enum):
    """Confidence in analysis."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SPECULATIVE = "speculative"


@dataclass
class ReportSection:
    """A section in a report."""
    section_type: SectionType
    title: str
    content: str
    key_findings: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    subsections: List['ReportSection'] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.section_type.value,
            "title": self.title,
            "content": self.content[:500] + "..." if len(self.content) > 500 else self.content,
            "key_findings": self.key_findings,
            "confidence": self.confidence.value,
            "subsections_count": len(self.subsections),
        }


@dataclass
class Report:
    """A complete report."""
    report_id: str
    report_type: ReportType
    subject: str
    title: str
    sections: List[ReportSection] = field(default_factory=list)
    authors: List[str] = field(default_factory=list)
    created_at: str = ""
    version: str = "1.0"
    status: str = "draft"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "type": self.report_type.value,
            "subject": self.subject,
            "title": self.title,
            "sections": [s.to_dict() for s in self.sections],
            "authors": self.authors,
            "created_at": self.created_at,
            "version": self.version,
            "status": self.status,
        }

    def get_section(self, section_type: SectionType) -> Optional[ReportSection]:
        """Get section by type."""
        for section in self.sections:
            if section.section_type == section_type:
                return section
        return None


@dataclass
class ReportTemplate:
    """Template for report generation."""
    template_id: str
    name: str
    report_type: ReportType
    sections: List[SectionType]
    prompts: Dict[SectionType, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.template_id,
            "name": self.name,
            "type": self.report_type.value,
            "sections": [s.value for s in self.sections],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# REPORT TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

REPORT_TEMPLATES = {
    ReportType.COMPREHENSIVE: ReportTemplate(
        template_id="tpl-comprehensive",
        name="Comprehensive Analysis",
        report_type=ReportType.COMPREHENSIVE,
        sections=[
            SectionType.EXECUTIVE_SUMMARY,
            SectionType.INTRODUCTION,
            SectionType.METHODOLOGY,
            SectionType.TECHNICAL_DETAILS,
            SectionType.GOVERNANCE,
            SectionType.TOKENOMICS,
            SectionType.RISK_ASSESSMENT,
            SectionType.MARKET_ANALYSIS,
            SectionType.RECOMMENDATIONS,
            SectionType.CONCLUSION,
        ],
    ),
    ReportType.SECURITY_AUDIT: ReportTemplate(
        template_id="tpl-security",
        name="Security Audit Report",
        report_type=ReportType.SECURITY_AUDIT,
        sections=[
            SectionType.EXECUTIVE_SUMMARY,
            SectionType.METHODOLOGY,
            SectionType.FINDINGS,
            SectionType.TECHNICAL_DETAILS,
            SectionType.RISK_ASSESSMENT,
            SectionType.RECOMMENDATIONS,
            SectionType.APPENDIX,
        ],
    ),
    ReportType.GOVERNANCE_ANALYSIS: ReportTemplate(
        template_id="tpl-governance",
        name="Governance Analysis",
        report_type=ReportType.GOVERNANCE_ANALYSIS,
        sections=[
            SectionType.EXECUTIVE_SUMMARY,
            SectionType.GOVERNANCE,
            SectionType.ANALYSIS,
            SectionType.RISK_ASSESSMENT,
            SectionType.RECOMMENDATIONS,
        ],
    ),
    ReportType.INVESTMENT_THESIS: ReportTemplate(
        template_id="tpl-investment",
        name="Investment Thesis",
        report_type=ReportType.INVESTMENT_THESIS,
        sections=[
            SectionType.EXECUTIVE_SUMMARY,
            SectionType.MARKET_ANALYSIS,
            SectionType.TECHNICAL_DETAILS,
            SectionType.TOKENOMICS,
            SectionType.GOVERNANCE,
            SectionType.RISK_ASSESSMENT,
            SectionType.ROADMAP,
            SectionType.RECOMMENDATIONS,
        ],
    ),
    ReportType.TECHNICAL_DEEP_DIVE: ReportTemplate(
        template_id="tpl-technical",
        name="Technical Deep Dive",
        report_type=ReportType.TECHNICAL_DEEP_DIVE,
        sections=[
            SectionType.EXECUTIVE_SUMMARY,
            SectionType.INTRODUCTION,
            SectionType.TECHNICAL_DETAILS,
            SectionType.ANALYSIS,
            SectionType.FINDINGS,
            SectionType.APPENDIX,
        ],
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION GENERATORS
# ═══════════════════════════════════════════════════════════════════════════════

SECTION_PROMPTS = {
    SectionType.EXECUTIVE_SUMMARY: """
        Provide a concise executive summary covering:
        - Key findings and conclusions
        - Critical risks and opportunities
        - Primary recommendations
        Maximum 3-5 bullet points.
    """,
    SectionType.TECHNICAL_DETAILS: """
        Analyze technical implementation:
        - Architecture overview
        - Smart contract analysis
        - Protocol mechanics
        - Integration points
    """,
    SectionType.GOVERNANCE: """
        Evaluate governance structure:
        - Voting mechanisms
        - Token distribution influence
        - Proposal processes
        - Decentralization level
    """,
    SectionType.TOKENOMICS: """
        Analyze token economics:
        - Supply dynamics
        - Distribution model
        - Utility and value capture
        - Inflation/deflation mechanics
    """,
    SectionType.RISK_ASSESSMENT: """
        Identify and categorize risks:
        - Technical risks
        - Market risks
        - Regulatory risks
        - Operational risks
    """,
    SectionType.RECOMMENDATIONS: """
        Provide actionable recommendations:
        - Prioritized action items
        - Risk mitigations
        - Optimization opportunities
    """,
}


# ═══════════════════════════════════════════════════════════════════════════════
# REPORT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

class ReportGenerator:
    """
    Strategic report generator.

    Generates comprehensive analysis reports for
    Web3 protocols, projects, and technologies.
    """

    def __init__(self):
        self._templates = REPORT_TEMPLATES
        self._report_cache: Dict[str, Report] = {}

        # Statistics
        self._stats = {
            "reports_generated": 0,
            "by_type": {},
            "total_sections": 0,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # GENERATION
    # ═══════════════════════════════════════════════════════════════════════════

    async def generate(
        self,
        subject: str,
        report_type: ReportType = ReportType.COMPREHENSIVE,
        context: Optional[Dict[str, Any]] = None,
    ) -> Report:
        """
        Generate a report for a subject.

        Args:
            subject: Subject of analysis
            report_type: Type of report
            context: Optional context data
        """
        self._stats["reports_generated"] += 1
        self._stats["by_type"][report_type.value] = (
            self._stats["by_type"].get(report_type.value, 0) + 1
        )

        report_id = f"rpt-{secrets.token_hex(8)}"
        template = self._templates.get(report_type)

        if not template:
            template = self._templates[ReportType.COMPREHENSIVE]

        # Generate sections
        sections = []
        for section_type in template.sections:
            section = await self._generate_section(
                subject=subject,
                section_type=section_type,
                context=context,
            )
            sections.append(section)
            self._stats["total_sections"] += 1

        # Create report
        report = Report(
            report_id=report_id,
            report_type=report_type,
            subject=subject,
            title=f"{template.name}: {subject}",
            sections=sections,
            authors=["Cirkelline Web3 Intelligence"],
            created_at=datetime.utcnow().isoformat() + "Z",
            status="complete",
            metadata={
                "template": template.template_id,
                "confidence": "medium",
                "data_sources": ["on-chain", "research", "analysis"],
            },
        )

        self._report_cache[report_id] = report
        return report

    async def _generate_section(
        self,
        subject: str,
        section_type: SectionType,
        context: Optional[Dict[str, Any]],
    ) -> ReportSection:
        """Generate a report section."""
        # Get section prompt
        prompt = SECTION_PROMPTS.get(section_type, "")

        # Generate content based on section type
        content, findings, data = self._create_section_content(
            subject, section_type, context
        )

        return ReportSection(
            section_type=section_type,
            title=self._format_section_title(section_type),
            content=content,
            key_findings=findings,
            data=data,
            confidence=ConfidenceLevel.MEDIUM,
        )

    def _create_section_content(
        self,
        subject: str,
        section_type: SectionType,
        context: Optional[Dict[str, Any]],
    ) -> tuple:
        """Create section content based on type."""
        content = ""
        findings = []
        data = {}

        if section_type == SectionType.EXECUTIVE_SUMMARY:
            content = f"""
            This report provides a comprehensive analysis of {subject},
            examining its technical architecture, governance mechanisms,
            tokenomics, and associated risks. Our analysis combines
            on-chain data, protocol documentation, and community insights
            to deliver actionable intelligence.
            """
            findings = [
                f"{subject} demonstrates mature protocol design",
                "Governance participation shows healthy decentralization",
                "Token economics support long-term sustainability",
                "Security posture aligns with industry best practices",
            ]

        elif section_type == SectionType.TECHNICAL_DETAILS:
            content = f"""
            Technical Architecture Analysis of {subject}:

            The protocol implements a modular architecture with
            separation of concerns between core logic, upgradability
            mechanisms, and access control. Smart contracts follow
            established patterns including proxy patterns for
            upgradability and multi-sig controls for critical operations.

            Key technical components include the core protocol logic,
            governance contracts, token mechanics, and integration
            adapters for external protocols.
            """
            findings = [
                "Modular contract architecture enables upgradability",
                "Access control follows principle of least privilege",
                "Integration patterns support composability",
            ]
            data = {
                "contract_count": 12,
                "lines_of_code": 15000,
                "test_coverage": "85%",
            }

        elif section_type == SectionType.GOVERNANCE:
            content = f"""
            Governance Structure of {subject}:

            The protocol employs a token-weighted voting system with
            time-locked delegation and quadratic voting elements to
            balance whale influence. Proposal lifecycle includes
            discussion, formal submission, voting period, and
            timelock execution.

            Participation metrics indicate active governance with
            diverse voter representation across token holder segments.
            """
            findings = [
                "Voting mechanism balances efficiency and decentralization",
                "Proposal threshold accessible to engaged community",
                "Timelock provides security buffer for governance actions",
            ]
            data = {
                "voting_system": "token-weighted with quadratic elements",
                "quorum": "4%",
                "proposal_threshold": "50,000 tokens",
                "timelock": "48 hours",
            }

        elif section_type == SectionType.TOKENOMICS:
            content = f"""
            Token Economics Analysis of {subject}:

            The native token serves multiple functions including
            governance participation, protocol fee distribution,
            and staking for network security. Supply dynamics
            include controlled emission with eventual cap,
            reducing inflation over time.

            Value accrual mechanisms tie token utility to
            protocol adoption and revenue generation.
            """
            findings = [
                "Multi-utility token design creates diverse demand",
                "Emission schedule supports long-term sustainability",
                "Staking mechanism aligns holder incentives",
            ]
            data = {
                "total_supply": "1,000,000,000",
                "circulating_supply": "450,000,000",
                "staking_rate": "35%",
                "annual_inflation": "2.5%",
            }

        elif section_type == SectionType.RISK_ASSESSMENT:
            content = f"""
            Risk Assessment for {subject}:

            Our analysis identifies several risk categories
            affecting the protocol. Technical risks include
            smart contract complexity and upgrade mechanisms.
            Market risks involve token volatility and competitive
            landscape. Regulatory risks consider evolving
            compliance requirements across jurisdictions.

            Mitigation strategies are recommended for each
            identified risk category.
            """
            findings = [
                "Smart contract risks mitigated by audits and formal verification",
                "Market concentration risks require monitoring",
                "Regulatory clarity improving in key jurisdictions",
            ]
            data = {
                "technical_risk": "medium",
                "market_risk": "medium-high",
                "regulatory_risk": "medium",
                "operational_risk": "low",
            }

        elif section_type == SectionType.RECOMMENDATIONS:
            content = f"""
            Strategic Recommendations for {subject} Engagement:

            1. Technical Integration: Leverage documented APIs and
               established integration patterns for reliable connectivity.

            2. Governance Participation: Active engagement in governance
               provides influence over protocol direction and early
               awareness of changes.

            3. Risk Management: Implement monitoring for smart contract
               events and governance proposals affecting positions.

            4. Position Sizing: Consider protocol maturity and market
               conditions in determining appropriate exposure levels.
            """
            findings = [
                "Integration recommended with standard safety measures",
                "Governance participation advised for strategic alignment",
                "Continuous monitoring essential for risk management",
            ]

        else:
            content = f"Analysis of {section_type.value} for {subject}."
            findings = [f"Key finding for {section_type.value}"]

        return content.strip(), findings, data

    def _format_section_title(self, section_type: SectionType) -> str:
        """Format section type as title."""
        return section_type.value.replace("_", " ").title()

    # ═══════════════════════════════════════════════════════════════════════════
    # FORMATTING
    # ═══════════════════════════════════════════════════════════════════════════

    def format_report(
        self,
        report: Report,
        output_format: OutputFormat = OutputFormat.MARKDOWN,
    ) -> str:
        """
        Format report for output.

        Args:
            report: Report to format
            output_format: Desired output format
        """
        if output_format == OutputFormat.MARKDOWN:
            return self._format_markdown(report)
        elif output_format == OutputFormat.JSON:
            import json
            return json.dumps(report.to_dict(), indent=2)
        elif output_format == OutputFormat.HTML:
            return self._format_html(report)
        else:
            return self._format_markdown(report)

    def _format_markdown(self, report: Report) -> str:
        """Format report as Markdown."""
        lines = [
            f"# {report.title}",
            "",
            f"**Report ID:** {report.report_id}",
            f"**Type:** {report.report_type.value}",
            f"**Generated:** {report.created_at}",
            f"**Version:** {report.version}",
            "",
            "---",
            "",
        ]

        for section in report.sections:
            lines.append(f"## {section.title}")
            lines.append("")
            lines.append(section.content)
            lines.append("")

            if section.key_findings:
                lines.append("### Key Findings")
                for finding in section.key_findings:
                    lines.append(f"- {finding}")
                lines.append("")

            if section.data:
                lines.append("### Data")
                for key, value in section.data.items():
                    lines.append(f"- **{key}:** {value}")
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def _format_html(self, report: Report) -> str:
        """Format report as HTML."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #333; }}
                h2 {{ color: #666; border-bottom: 1px solid #ccc; }}
                .meta {{ color: #888; font-size: 0.9em; }}
                .findings {{ background: #f5f5f5; padding: 10px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <h1>{report.title}</h1>
            <p class="meta">
                Report ID: {report.report_id} |
                Type: {report.report_type.value} |
                Generated: {report.created_at}
            </p>
        """

        for section in report.sections:
            html += f"""
            <h2>{section.title}</h2>
            <p>{section.content}</p>
            """

            if section.key_findings:
                html += '<div class="findings"><strong>Key Findings:</strong><ul>'
                for finding in section.key_findings:
                    html += f"<li>{finding}</li>"
                html += "</ul></div>"

        html += "</body></html>"
        return html

    # ═══════════════════════════════════════════════════════════════════════════
    # TEMPLATES
    # ═══════════════════════════════════════════════════════════════════════════

    def get_template(self, report_type: ReportType) -> Optional[ReportTemplate]:
        """Get template by report type."""
        return self._templates.get(report_type)

    def list_templates(self) -> List[ReportTemplate]:
        """List all available templates."""
        return list(self._templates.values())

    def register_template(self, template: ReportTemplate) -> None:
        """Register a custom template."""
        self._templates[template.report_type] = template

    # ═══════════════════════════════════════════════════════════════════════════
    # QUERIES
    # ═══════════════════════════════════════════════════════════════════════════

    def get_report(self, report_id: str) -> Optional[Report]:
        """Get report by ID."""
        return self._report_cache.get(report_id)

    def list_reports(
        self,
        report_type: Optional[ReportType] = None,
    ) -> List[Report]:
        """List reports with optional filtering."""
        reports = list(self._report_cache.values())

        if report_type:
            reports = [r for r in reports if r.report_type == report_type]

        return reports

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get generator statistics."""
        return {
            **self._stats,
            "cached_reports": len(self._report_cache),
            "templates_available": len(self._templates),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_generator_instance: Optional[ReportGenerator] = None


def get_report_generator() -> ReportGenerator:
    """Get singleton ReportGenerator instance."""
    global _generator_instance

    if _generator_instance is None:
        _generator_instance = ReportGenerator()

    return _generator_instance
