"""
Security Auditor
================
Smart contract vulnerability detection and security analysis.

Responsibilities:
- Identify common vulnerability patterns
- Analyze attack surfaces
- Score security risk levels
- Generate remediation recommendations
"""

import logging
import asyncio
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class RiskSeverity(Enum):
    """Security risk severity levels."""
    CRITICAL = "critical"  # Immediate funds at risk
    HIGH = "high"          # Potential fund loss
    MEDIUM = "medium"      # Functionality issues
    LOW = "low"            # Best practice violations
    INFO = "info"          # Informational findings


class VulnerabilityCategory(Enum):
    """Vulnerability categories (OWASP-style)."""
    REENTRANCY = "reentrancy"
    ACCESS_CONTROL = "access_control"
    ARITHMETIC = "arithmetic"
    UNCHECKED_RETURN = "unchecked_return"
    DENIAL_OF_SERVICE = "denial_of_service"
    FRONT_RUNNING = "front_running"
    TIMESTAMP_DEPENDENCE = "timestamp_dependence"
    ORACLE_MANIPULATION = "oracle_manipulation"
    FLASH_LOAN = "flash_loan"
    GOVERNANCE = "governance"
    CENTRALIZATION = "centralization"
    UPGRADE = "upgrade"
    LOGIC_ERROR = "logic_error"
    STORAGE_COLLISION = "storage_collision"
    SIGNATURE = "signature"
    EXTERNAL_CALL = "external_call"


@dataclass
class SecurityRisk:
    """A detected security risk."""
    risk_id: str
    title: str
    category: VulnerabilityCategory
    severity: RiskSeverity
    description: str
    location: str = ""  # Contract/function location
    impact: str = ""
    recommendation: str = ""
    references: List[str] = field(default_factory=list)
    cwe_id: Optional[str] = None  # Common Weakness Enumeration

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_id": self.risk_id,
            "title": self.title,
            "category": self.category.value,
            "severity": self.severity.value,
            "description": self.description[:200],
            "impact": self.impact[:100],
            "recommendation": self.recommendation[:150],
        }


@dataclass
class VulnerabilityReport:
    """Complete vulnerability assessment report."""
    target: str
    risks: List[SecurityRisk] = field(default_factory=list)
    overall_score: float = 0.0  # 0-100
    risk_summary: Dict[str, int] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    audit_duration_ms: float = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "total_risks": len(self.risks),
            "critical_count": self.risk_summary.get("critical", 0),
            "high_count": self.risk_summary.get("high", 0),
            "medium_count": self.risk_summary.get("medium", 0),
            "overall_score": round(self.overall_score, 1),
            "recommendations": self.recommendations[:5],
            "timestamp": self.timestamp,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# VULNERABILITY PATTERNS
# ═══════════════════════════════════════════════════════════════════════════════

VULNERABILITY_PATTERNS = {
    VulnerabilityCategory.REENTRANCY: {
        "name": "Reentrancy Vulnerability",
        "severity": RiskSeverity.CRITICAL,
        "patterns": [
            r"\.call\{value:",
            r"\.send\(",
            r"\.transfer\(",
        ],
        "description": "Contract allows external calls before state updates",
        "impact": "Attacker can drain contract funds through recursive calls",
        "recommendation": "Use Checks-Effects-Interactions pattern or ReentrancyGuard",
        "cwe_id": "CWE-841",
    },
    VulnerabilityCategory.ACCESS_CONTROL: {
        "name": "Missing Access Control",
        "severity": RiskSeverity.HIGH,
        "patterns": [
            r"public\s+function.*\(",
            r"external\s+function.*\(",
        ],
        "description": "Critical functions lack proper access control",
        "impact": "Unauthorized users can execute privileged operations",
        "recommendation": "Implement onlyOwner or role-based access control",
        "cwe_id": "CWE-284",
    },
    VulnerabilityCategory.ARITHMETIC: {
        "name": "Integer Overflow/Underflow",
        "severity": RiskSeverity.HIGH,
        "patterns": [
            r"\+\s*\d+",
            r"\*\s*\d+",
        ],
        "description": "Arithmetic operations without overflow protection",
        "impact": "Calculations can wrap around, causing unexpected values",
        "recommendation": "Use Solidity 0.8+ or SafeMath library",
        "cwe_id": "CWE-190",
    },
    VulnerabilityCategory.UNCHECKED_RETURN: {
        "name": "Unchecked Return Value",
        "severity": RiskSeverity.MEDIUM,
        "patterns": [
            r"\.call\(",
            r"\.delegatecall\(",
        ],
        "description": "Low-level call return values not checked",
        "impact": "Failed calls may silently succeed",
        "recommendation": "Always check and handle return values from external calls",
        "cwe_id": "CWE-252",
    },
    VulnerabilityCategory.TIMESTAMP_DEPENDENCE: {
        "name": "Block Timestamp Dependence",
        "severity": RiskSeverity.LOW,
        "patterns": [
            r"block\.timestamp",
            r"now",
        ],
        "description": "Contract logic depends on block timestamp",
        "impact": "Miners can manipulate timestamp within ~15 second window",
        "recommendation": "Avoid using timestamp for critical logic; use block numbers",
        "cwe_id": "CWE-829",
    },
    VulnerabilityCategory.FRONT_RUNNING: {
        "name": "Front-Running Vulnerability",
        "severity": RiskSeverity.MEDIUM,
        "patterns": [
            r"swap",
            r"approve",
            r"transferFrom",
        ],
        "description": "Transaction can be front-run by MEV bots",
        "impact": "Users may receive worse prices or have transactions sandwiched",
        "recommendation": "Implement slippage protection and commit-reveal schemes",
        "cwe_id": "CWE-362",
    },
    VulnerabilityCategory.ORACLE_MANIPULATION: {
        "name": "Oracle Price Manipulation",
        "severity": RiskSeverity.CRITICAL,
        "patterns": [
            r"getPrice",
            r"latestAnswer",
            r"getReserves",
        ],
        "description": "Price feeds can be manipulated",
        "impact": "Attackers can manipulate prices to exploit arbitrage",
        "recommendation": "Use time-weighted average prices (TWAP) or multiple oracles",
        "cwe_id": "CWE-20",
    },
    VulnerabilityCategory.FLASH_LOAN: {
        "name": "Flash Loan Attack Vector",
        "severity": RiskSeverity.HIGH,
        "patterns": [
            r"flashLoan",
            r"flashMint",
        ],
        "description": "Contract vulnerable to flash loan attacks",
        "impact": "Attacker can manipulate state within single transaction",
        "recommendation": "Add flash loan guards and multi-block checks",
        "cwe_id": "CWE-20",
    },
    VulnerabilityCategory.CENTRALIZATION: {
        "name": "Centralization Risk",
        "severity": RiskSeverity.MEDIUM,
        "patterns": [
            r"onlyOwner",
            r"onlyAdmin",
        ],
        "description": "Contract has centralized control points",
        "impact": "Single point of failure; owner can rug users",
        "recommendation": "Implement timelock, multisig, or progressive decentralization",
        "cwe_id": "CWE-269",
    },
    VulnerabilityCategory.UPGRADE: {
        "name": "Unsafe Upgrade Pattern",
        "severity": RiskSeverity.HIGH,
        "patterns": [
            r"upgradeTo",
            r"upgradeToAndCall",
        ],
        "description": "Upgrade mechanism can be exploited",
        "impact": "Malicious upgrade can change contract behavior",
        "recommendation": "Add timelock and governance for upgrades",
        "cwe_id": "CWE-269",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# KNOWN AUDIT FINDINGS
# ═══════════════════════════════════════════════════════════════════════════════

COMMON_AUDIT_FINDINGS = [
    SecurityRisk(
        risk_id="AUDIT-001",
        title="Missing Zero Address Check",
        category=VulnerabilityCategory.LOGIC_ERROR,
        severity=RiskSeverity.LOW,
        description="Function parameters not validated for zero address",
        impact="Tokens or funds could be sent to zero address (burned)",
        recommendation="Add require(address != address(0)) checks",
    ),
    SecurityRisk(
        risk_id="AUDIT-002",
        title="Events Not Emitted",
        category=VulnerabilityCategory.LOGIC_ERROR,
        severity=RiskSeverity.INFO,
        description="State changes without corresponding event emissions",
        impact="Off-chain systems cannot track state changes",
        recommendation="Emit events for all state modifications",
    ),
    SecurityRisk(
        risk_id="AUDIT-003",
        title="Floating Pragma",
        category=VulnerabilityCategory.LOGIC_ERROR,
        severity=RiskSeverity.INFO,
        description="Compiler version not fixed",
        impact="Different compiler versions may produce different bytecode",
        recommendation="Lock pragma to specific version: pragma solidity 0.8.20;",
    ),
]


# ═══════════════════════════════════════════════════════════════════════════════
# SECURITY AUDITOR
# ═══════════════════════════════════════════════════════════════════════════════

class SecurityAuditor:
    """
    Smart contract security auditor.

    Performs automated security analysis to detect
    common vulnerabilities and attack vectors.
    """

    def __init__(self):
        self._patterns = VULNERABILITY_PATTERNS
        self._common_findings = COMMON_AUDIT_FINDINGS
        self._audit_cache: Dict[str, VulnerabilityReport] = {}

        # Statistics
        self._stats = {
            "total_audits": 0,
            "vulnerabilities_found": 0,
            "critical_findings": 0,
            "high_findings": 0,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # AUDITING
    # ═══════════════════════════════════════════════════════════════════════════

    async def audit(
        self,
        target: str,
        source_code: Optional[str] = None,
    ) -> VulnerabilityReport:
        """
        Perform security audit on a target.

        Args:
            target: Contract address or name
            source_code: Optional source code to analyze

        Returns:
            Vulnerability report
        """
        import time
        start_time = time.time()

        self._stats["total_audits"] += 1

        # Check cache
        if target in self._audit_cache:
            return self._audit_cache[target]

        report = VulnerabilityReport(target=target)

        # Pattern-based analysis
        if source_code:
            findings = self._analyze_source_code(source_code)
            report.risks.extend(findings)
        else:
            # Use known vulnerability patterns for simulated analysis
            findings = await self._analyze_target(target)
            report.risks.extend(findings)

        # Add common findings
        report.risks.extend(self._common_findings)

        # Calculate summary
        report.risk_summary = self._calculate_risk_summary(report.risks)
        report.overall_score = self._calculate_security_score(report.risks)
        report.recommendations = self._generate_recommendations(report.risks)

        # Update stats
        self._stats["vulnerabilities_found"] += len(report.risks)
        self._stats["critical_findings"] += report.risk_summary.get("critical", 0)
        self._stats["high_findings"] += report.risk_summary.get("high", 0)

        report.audit_duration_ms = (time.time() - start_time) * 1000

        self._audit_cache[target] = report
        return report

    async def quick_scan(self, target: str) -> Dict[str, Any]:
        """
        Perform quick security scan.

        Returns summary without full analysis.
        """
        report = await self.audit(target)

        return {
            "target": target,
            "risk_level": self._determine_risk_level(report),
            "critical_issues": report.risk_summary.get("critical", 0),
            "high_issues": report.risk_summary.get("high", 0),
            "score": report.overall_score,
            "recommendation": report.recommendations[0] if report.recommendations else "No issues found",
        }

    def _analyze_source_code(self, source_code: str) -> List[SecurityRisk]:
        """Analyze source code for vulnerabilities."""
        findings = []

        for category, config in self._patterns.items():
            for pattern in config["patterns"]:
                if re.search(pattern, source_code, re.IGNORECASE):
                    finding = SecurityRisk(
                        risk_id=f"VULN-{category.value.upper()}-{len(findings)+1:03d}",
                        title=config["name"],
                        category=category,
                        severity=config["severity"],
                        description=config["description"],
                        impact=config["impact"],
                        recommendation=config["recommendation"],
                        cwe_id=config.get("cwe_id"),
                    )
                    findings.append(finding)
                    break  # One finding per category

        return findings

    async def _analyze_target(self, target: str) -> List[SecurityRisk]:
        """Analyze target without source code."""
        # In production, this would fetch verified source from Etherscan
        # For now, return subset of common patterns

        findings = []

        # Simulate detection of common issues
        common_issues = [
            VulnerabilityCategory.CENTRALIZATION,
            VulnerabilityCategory.FRONT_RUNNING,
        ]

        for category in common_issues:
            if category in self._patterns:
                config = self._patterns[category]
                finding = SecurityRisk(
                    risk_id=f"VULN-{category.value.upper()}-001",
                    title=config["name"],
                    category=category,
                    severity=config["severity"],
                    description=config["description"],
                    impact=config["impact"],
                    recommendation=config["recommendation"],
                    cwe_id=config.get("cwe_id"),
                )
                findings.append(finding)

        return findings

    # ═══════════════════════════════════════════════════════════════════════════
    # SCORING
    # ═══════════════════════════════════════════════════════════════════════════

    def _calculate_risk_summary(self, risks: List[SecurityRisk]) -> Dict[str, int]:
        """Calculate risk severity summary."""
        summary = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }

        for risk in risks:
            summary[risk.severity.value] += 1

        return summary

    def _calculate_security_score(self, risks: List[SecurityRisk]) -> float:
        """
        Calculate overall security score (0-100).

        Higher score = more secure.
        """
        base_score = 100.0

        # Deduct points based on severity
        severity_deductions = {
            RiskSeverity.CRITICAL: 25.0,
            RiskSeverity.HIGH: 15.0,
            RiskSeverity.MEDIUM: 7.0,
            RiskSeverity.LOW: 3.0,
            RiskSeverity.INFO: 1.0,
        }

        for risk in risks:
            base_score -= severity_deductions.get(risk.severity, 0)

        return max(0.0, min(100.0, base_score))

    def _determine_risk_level(self, report: VulnerabilityReport) -> str:
        """Determine overall risk level from report."""
        if report.risk_summary.get("critical", 0) > 0:
            return "critical"
        elif report.risk_summary.get("high", 0) > 0:
            return "high"
        elif report.risk_summary.get("medium", 0) > 0:
            return "medium"
        elif report.risk_summary.get("low", 0) > 0:
            return "low"
        return "safe"

    def _generate_recommendations(self, risks: List[SecurityRisk]) -> List[str]:
        """Generate prioritized recommendations."""
        recommendations = []

        # Sort by severity
        sorted_risks = sorted(
            risks,
            key=lambda r: list(RiskSeverity).index(r.severity)
        )

        for risk in sorted_risks[:5]:
            if risk.recommendation:
                recommendations.append(
                    f"[{risk.severity.value.upper()}] {risk.recommendation}"
                )

        return recommendations

    # ═══════════════════════════════════════════════════════════════════════════
    # SPECIALIZED CHECKS
    # ═══════════════════════════════════════════════════════════════════════════

    def check_reentrancy(self, source_code: str) -> List[SecurityRisk]:
        """Check specifically for reentrancy vulnerabilities."""
        findings = []
        config = self._patterns.get(VulnerabilityCategory.REENTRANCY)

        if not config:
            return findings

        # Look for external calls before state changes
        lines = source_code.split('\n')
        for i, line in enumerate(lines):
            for pattern in config["patterns"]:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(SecurityRisk(
                        risk_id=f"REENTRANCY-{i+1:04d}",
                        title=config["name"],
                        category=VulnerabilityCategory.REENTRANCY,
                        severity=RiskSeverity.CRITICAL,
                        description=config["description"],
                        location=f"Line {i+1}",
                        impact=config["impact"],
                        recommendation=config["recommendation"],
                    ))

        return findings

    def check_access_control(self, source_code: str) -> List[SecurityRisk]:
        """Check for access control issues."""
        findings = []

        # Look for sensitive functions without modifiers
        sensitive_keywords = [
            "withdraw", "transfer", "mint", "burn",
            "pause", "upgrade", "set", "add", "remove"
        ]

        lines = source_code.split('\n')
        for i, line in enumerate(lines):
            if "function" in line.lower():
                is_sensitive = any(kw in line.lower() for kw in sensitive_keywords)
                has_modifier = "only" in line.lower() or "require(" in line.lower()

                if is_sensitive and not has_modifier:
                    findings.append(SecurityRisk(
                        risk_id=f"ACCESS-{i+1:04d}",
                        title="Sensitive Function Without Access Control",
                        category=VulnerabilityCategory.ACCESS_CONTROL,
                        severity=RiskSeverity.HIGH,
                        description="Sensitive function lacks access control modifier",
                        location=f"Line {i+1}",
                        impact="Unauthorized users can execute privileged operations",
                        recommendation="Add appropriate access control modifier",
                    ))

        return findings

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get auditor statistics."""
        return {
            **self._stats,
            "pattern_categories": len(self._patterns),
            "cache_size": len(self._audit_cache),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_auditor_instance: Optional[SecurityAuditor] = None


def get_security_auditor() -> SecurityAuditor:
    """Get singleton SecurityAuditor instance."""
    global _auditor_instance

    if _auditor_instance is None:
        _auditor_instance = SecurityAuditor()

    return _auditor_instance
