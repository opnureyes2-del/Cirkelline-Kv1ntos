"""
Web3 Backwards Engineering Specialist
======================================
Cirkelline's Web3 & AI Technology Adapter.

Mission: Ensure Cirkelline's ecosystem is agile, adaptive, and leading
in Web3 and AI technology through systematic identification, analysis,
and strategic integration of emerging technologies.

Modules:
- Scanner: Technology monitoring and trend detection
- Analysis: Protocol analysis and backwards engineering
- Governance: DAO analysis and game theory
- Identity: DIDs and machine-level trust
- Storage: Decentralized storage adapters
- Reporting: Strategic reports and risk analysis
"""

__version__ = "1.0.0"

# Scanner - Technology Intelligence
from cirkelline.web3.scanner import (
    GitHubMonitor,
    ResearchScanner,
    TrendAnalyzer,
    TechnologyFeed,
    get_scanner_manager,
)

# Analysis - Backwards Engineering
from cirkelline.web3.analysis import (
    ProtocolAnalyzer,
    SecurityAuditor,
    CompatibilityChecker,
    AnalysisResult,
    get_analysis_engine,
)

# Governance - DeGov & Game Theory
from cirkelline.web3.governance import (
    DAOAnalyzer,
    GameTheoryEngine,
    TokenomicsModeler,
    GovernanceProposal,
    get_governance_engine,
)

# Identity - DIDs & Trust
from cirkelline.web3.identity import (
    DIDManager,
    ZKPVerifier,
    TrustLayer,
    VerifiableCredential,
    get_identity_manager,
)

# Storage - Decentralized Storage
from cirkelline.web3.storage import (
    IPFSAdapter,
    ArweaveAdapter,
    StorageRouter,
    StorageResult,
    get_storage_router,
)

# Reporting - Strategic Output
from cirkelline.web3.reporting import (
    ReportGenerator,
    RiskAnalyzer,
    Report,
    ReportType,
    RiskAssessment,
    RiskLevel,
    ReportingEngine,
    get_report_generator,
    get_risk_analyzer,
    get_reporting_engine,
)

__all__ = [
    # Scanner
    'GitHubMonitor',
    'ResearchScanner',
    'TrendAnalyzer',
    'TechnologyFeed',
    'get_scanner_manager',
    # Analysis
    'ProtocolAnalyzer',
    'SecurityAuditor',
    'CompatibilityChecker',
    'AnalysisResult',
    'get_analysis_engine',
    # Governance
    'DAOAnalyzer',
    'GameTheoryEngine',
    'TokenomicsModeler',
    'GovernanceProposal',
    'get_governance_engine',
    # Identity
    'DIDManager',
    'ZKPVerifier',
    'TrustLayer',
    'VerifiableCredential',
    'get_identity_manager',
    # Storage
    'IPFSAdapter',
    'ArweaveAdapter',
    'StorageRouter',
    'StorageResult',
    'get_storage_router',
    # Reporting
    'ReportGenerator',
    'RiskAnalyzer',
    'Report',
    'ReportType',
    'RiskAssessment',
    'RiskLevel',
    'ReportingEngine',
    'get_report_generator',
    'get_risk_analyzer',
    'get_reporting_engine',
]
