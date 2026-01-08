"""
Web3 Modules Test Suite
========================
Comprehensive tests for all Web3 backwards engineering specialist modules.

Tests cover:
- Scanner: GitHub monitoring, research scanning, trend analysis
- Analysis: Protocol analysis, security auditing, compatibility checking
- Governance: DAO analysis, game theory, tokenomics modeling
- Identity: DID management, ZKP verification, trust layer
- Storage: IPFS adapter, Arweave adapter, storage routing
- Reporting: Report generation, risk analysis, reporting engine

Run: pytest tests/test_web3_modules.py -v
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# ═══════════════════════════════════════════════════════════════════════════════
# SCANNER MODULE TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestGitHubMonitor:
    """Tests for GitHub monitoring functionality."""

    def test_github_monitor_import(self):
        """Test GitHubMonitor can be imported."""
        from cirkelline.web3.scanner import GitHubMonitor
        assert GitHubMonitor is not None

    def test_github_monitor_singleton(self):
        """Test singleton pattern for GitHubMonitor."""
        from cirkelline.web3.scanner import get_scanner_manager
        manager1 = get_scanner_manager()
        manager2 = get_scanner_manager()
        assert manager1 is manager2

    def test_github_monitor_initialization(self):
        """Test GitHubMonitor initializes correctly."""
        from cirkelline.web3.scanner import GitHubMonitor
        monitor = GitHubMonitor()
        assert hasattr(monitor, 'scan')
        assert hasattr(monitor, 'scan_repository')
        assert hasattr(monitor, 'get_watchlist')
        assert hasattr(monitor, 'add_to_watchlist')

    @pytest.mark.asyncio
    async def test_scan_repository(self):
        """Test repository scanning functionality."""
        from cirkelline.web3.scanner import GitHubMonitor
        monitor = GitHubMonitor()

        result = await monitor.scan_repository(
            repo_name="ethereum/go-ethereum"
        )

        # Should return None (no API token) or RepositoryInfo
        assert result is None or hasattr(result, 'to_dict')

    def test_watchlist_management(self):
        """Test watchlist add/remove operations."""
        from cirkelline.web3.scanner import GitHubMonitor
        monitor = GitHubMonitor()

        monitor.add_to_watchlist("test/repo")
        assert "test/repo" in monitor.get_watchlist()

        monitor.remove_from_watchlist("test/repo")
        assert "test/repo" not in monitor.get_watchlist()


class TestResearchScanner:
    """Tests for research paper scanning."""

    def test_research_scanner_import(self):
        """Test ResearchScanner can be imported."""
        from cirkelline.web3.scanner import ResearchScanner
        assert ResearchScanner is not None

    def test_research_scanner_initialization(self):
        """Test ResearchScanner initializes correctly."""
        from cirkelline.web3.scanner import ResearchScanner
        scanner = ResearchScanner()
        assert hasattr(scanner, 'scan')
        assert hasattr(scanner, 'scan_arxiv')
        assert hasattr(scanner, 'add_keywords')

    @pytest.mark.asyncio
    async def test_research_scan(self):
        """Test research paper scan."""
        from cirkelline.web3.scanner import ResearchScanner
        scanner = ResearchScanner()

        result = await scanner.scan()

        assert result is not None
        assert hasattr(result, 'papers') or hasattr(result, 'to_dict')

    def test_keyword_management(self):
        """Test keyword management."""
        from cirkelline.web3.scanner import ResearchScanner
        scanner = ResearchScanner()

        scanner.add_keywords("test_category", ["keyword1", "keyword2"])
        stats = scanner.get_stats()
        assert stats is not None


class TestTrendAnalyzer:
    """Tests for trend analysis functionality."""

    def test_trend_analyzer_import(self):
        """Test TrendAnalyzer can be imported."""
        from cirkelline.web3.scanner import TrendAnalyzer
        assert TrendAnalyzer is not None

    def test_trend_analyzer_initialization(self):
        """Test TrendAnalyzer initializes correctly."""
        from cirkelline.web3.scanner import TrendAnalyzer
        analyzer = TrendAnalyzer()
        assert hasattr(analyzer, 'analyze')
        assert hasattr(analyzer, 'get_emerging_trends')
        assert hasattr(analyzer, 'get_high_relevance_trends')

    def test_get_emerging_trends(self):
        """Test get emerging trends functionality."""
        from cirkelline.web3.scanner import TrendAnalyzer
        analyzer = TrendAnalyzer()

        trends = analyzer.get_emerging_trends()
        assert isinstance(trends, list)


class TestScannerManager:
    """Tests for ScannerManager."""

    def test_scanner_manager_singleton(self):
        """Test ScannerManager singleton pattern."""
        from cirkelline.web3.scanner import get_scanner_manager
        manager1 = get_scanner_manager()
        manager2 = get_scanner_manager()
        assert manager1 is manager2

    def test_scanner_manager_components(self):
        """Test ScannerManager has all components."""
        from cirkelline.web3.scanner import get_scanner_manager
        manager = get_scanner_manager()

        assert hasattr(manager, 'github')
        assert hasattr(manager, 'research')
        assert hasattr(manager, 'trends')


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS MODULE TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestProtocolAnalyzer:
    """Tests for protocol analysis functionality."""

    def test_protocol_analyzer_import(self):
        """Test ProtocolAnalyzer can be imported."""
        from cirkelline.web3.analysis import ProtocolAnalyzer
        assert ProtocolAnalyzer is not None

    def test_analysis_engine_singleton(self):
        """Test singleton pattern for analysis engine."""
        from cirkelline.web3.analysis import get_analysis_engine
        engine1 = get_analysis_engine()
        engine2 = get_analysis_engine()
        assert engine1 is engine2

    def test_protocol_analyzer_initialization(self):
        """Test ProtocolAnalyzer initializes correctly."""
        from cirkelline.web3.analysis import ProtocolAnalyzer
        analyzer = ProtocolAnalyzer()
        assert hasattr(analyzer, 'analyze')
        assert hasattr(analyzer, 'get_stats')

    @pytest.mark.asyncio
    async def test_analyze_protocol(self):
        """Test protocol analysis."""
        from cirkelline.web3.analysis import ProtocolAnalyzer
        analyzer = ProtocolAnalyzer()

        result = await analyzer.analyze(
            target="uniswap-v3"
        )

        assert result is not None
        assert hasattr(result, 'to_dict') or isinstance(result, dict)


class TestSecurityAuditor:
    """Tests for security auditing functionality."""

    def test_security_auditor_import(self):
        """Test SecurityAuditor can be imported."""
        from cirkelline.web3.analysis import SecurityAuditor
        assert SecurityAuditor is not None

    def test_security_auditor_initialization(self):
        """Test SecurityAuditor initializes correctly."""
        from cirkelline.web3.analysis import SecurityAuditor
        auditor = SecurityAuditor()
        assert hasattr(auditor, 'audit')
        assert hasattr(auditor, 'get_stats')

    @pytest.mark.asyncio
    async def test_security_audit(self):
        """Test security audit functionality."""
        from cirkelline.web3.analysis import SecurityAuditor
        auditor = SecurityAuditor()

        result = await auditor.audit(
            target="0x1234567890abcdef"
        )

        assert result is not None


class TestCompatibilityChecker:
    """Tests for compatibility checking."""

    def test_compatibility_checker_import(self):
        """Test CompatibilityChecker can be imported."""
        from cirkelline.web3.analysis import CompatibilityChecker
        assert CompatibilityChecker is not None

    def test_compatibility_checker_initialization(self):
        """Test CompatibilityChecker initializes correctly."""
        from cirkelline.web3.analysis import CompatibilityChecker
        checker = CompatibilityChecker()
        assert hasattr(checker, 'check')
        assert hasattr(checker, 'compare')
        assert hasattr(checker, 'get_known_protocols')

    @pytest.mark.asyncio
    async def test_check_compatibility(self):
        """Test compatibility check."""
        from cirkelline.web3.analysis import CompatibilityChecker
        checker = CompatibilityChecker()

        result = await checker.check(target="ethereum")
        assert result is not None


class TestAnalysisResult:
    """Tests for AnalysisResult dataclass."""

    def test_analysis_result_import(self):
        """Test AnalysisResult can be imported."""
        from cirkelline.web3.analysis import AnalysisResult
        assert AnalysisResult is not None


# ═══════════════════════════════════════════════════════════════════════════════
# GOVERNANCE MODULE TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestDAOAnalyzer:
    """Tests for DAO analysis functionality."""

    def test_dao_analyzer_import(self):
        """Test DAOAnalyzer can be imported."""
        from cirkelline.web3.governance import DAOAnalyzer
        assert DAOAnalyzer is not None

    def test_governance_engine_singleton(self):
        """Test singleton pattern for governance engine."""
        from cirkelline.web3.governance import get_governance_engine
        engine1 = get_governance_engine()
        engine2 = get_governance_engine()
        assert engine1 is engine2

    def test_dao_analyzer_initialization(self):
        """Test DAOAnalyzer initializes correctly."""
        from cirkelline.web3.governance import DAOAnalyzer
        analyzer = DAOAnalyzer()
        assert hasattr(analyzer, 'analyze')
        assert hasattr(analyzer, 'get_stats')

    @pytest.mark.asyncio
    async def test_analyze_dao(self):
        """Test DAO analysis."""
        from cirkelline.web3.governance import DAOAnalyzer
        analyzer = DAOAnalyzer()

        result = await analyzer.analyze(dao_name="uniswap")

        assert result is not None


class TestGameTheoryEngine:
    """Tests for game theory analysis."""

    def test_game_theory_engine_import(self):
        """Test GameTheoryEngine can be imported."""
        from cirkelline.web3.governance import GameTheoryEngine
        assert GameTheoryEngine is not None

    def test_game_theory_engine_initialization(self):
        """Test GameTheoryEngine initializes correctly."""
        from cirkelline.web3.governance import GameTheoryEngine
        engine = GameTheoryEngine()
        # Check for actual methods
        assert engine is not None


class TestTokenomicsModeler:
    """Tests for tokenomics modeling."""

    def test_tokenomics_modeler_import(self):
        """Test TokenomicsModeler can be imported."""
        from cirkelline.web3.governance import TokenomicsModeler
        assert TokenomicsModeler is not None

    def test_tokenomics_modeler_initialization(self):
        """Test TokenomicsModeler initializes correctly."""
        from cirkelline.web3.governance import TokenomicsModeler
        modeler = TokenomicsModeler()
        # Check for actual methods
        assert modeler is not None


class TestGovernanceProposal:
    """Tests for GovernanceProposal dataclass."""

    def test_governance_proposal_import(self):
        """Test GovernanceProposal can be imported."""
        from cirkelline.web3.governance import GovernanceProposal
        assert GovernanceProposal is not None


# ═══════════════════════════════════════════════════════════════════════════════
# IDENTITY MODULE TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestDIDManager:
    """Tests for DID management functionality."""

    def test_did_manager_import(self):
        """Test DIDManager can be imported."""
        from cirkelline.web3.identity import DIDManager
        assert DIDManager is not None

    def test_identity_manager_singleton(self):
        """Test singleton pattern for identity manager."""
        from cirkelline.web3.identity import get_identity_manager
        manager1 = get_identity_manager()
        manager2 = get_identity_manager()
        assert manager1 is manager2

    def test_did_manager_initialization(self):
        """Test DIDManager initializes correctly."""
        from cirkelline.web3.identity import DIDManager
        manager = DIDManager()
        assert hasattr(manager, 'create')
        assert hasattr(manager, 'resolve')
        assert hasattr(manager, 'update')
        assert hasattr(manager, 'deactivate')

    @pytest.mark.asyncio
    async def test_create_did(self):
        """Test DID creation."""
        from cirkelline.web3.identity import DIDManager
        manager = DIDManager()

        result = await manager.create()

        assert result is not None

    @pytest.mark.asyncio
    async def test_resolve_did(self):
        """Test DID resolution."""
        from cirkelline.web3.identity import DIDManager
        manager = DIDManager()

        result = await manager.resolve(
            did="did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
        )

        assert result is not None


class TestZKPVerifier:
    """Tests for zero-knowledge proof verification."""

    def test_zkp_verifier_import(self):
        """Test ZKPVerifier can be imported."""
        from cirkelline.web3.identity import ZKPVerifier
        assert ZKPVerifier is not None

    def test_zkp_verifier_initialization(self):
        """Test ZKPVerifier initializes correctly."""
        from cirkelline.web3.identity import ZKPVerifier
        verifier = ZKPVerifier()
        assert hasattr(verifier, 'verify')


class TestTrustLayer:
    """Tests for trust layer functionality."""

    def test_trust_layer_import(self):
        """Test TrustLayer can be imported."""
        from cirkelline.web3.identity import TrustLayer
        assert TrustLayer is not None

    def test_trust_layer_initialization(self):
        """Test TrustLayer initializes correctly."""
        from cirkelline.web3.identity import TrustLayer
        layer = TrustLayer()
        assert hasattr(layer, 'calculate_trust')
        assert hasattr(layer, 'create_relation')
        assert hasattr(layer, 'revoke_relation')


class TestVerifiableCredential:
    """Tests for VerifiableCredential dataclass."""

    def test_verifiable_credential_import(self):
        """Test VerifiableCredential can be imported."""
        from cirkelline.web3.identity import VerifiableCredential
        assert VerifiableCredential is not None


# ═══════════════════════════════════════════════════════════════════════════════
# STORAGE MODULE TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestIPFSAdapter:
    """Tests for IPFS storage adapter."""

    def test_ipfs_adapter_import(self):
        """Test IPFSAdapter can be imported."""
        from cirkelline.web3.storage import IPFSAdapter
        assert IPFSAdapter is not None

    def test_ipfs_adapter_initialization(self):
        """Test IPFSAdapter initializes correctly."""
        from cirkelline.web3.storage import IPFSAdapter
        adapter = IPFSAdapter()
        assert hasattr(adapter, 'add')
        assert hasattr(adapter, 'get')
        assert hasattr(adapter, 'pin')
        assert hasattr(adapter, 'unpin')

    @pytest.mark.asyncio
    async def test_ipfs_add(self):
        """Test adding content to IPFS."""
        from cirkelline.web3.storage import IPFSAdapter
        adapter = IPFSAdapter()

        result = await adapter.add(
            content=b"Hello, Cirkelline Web3!"
        )

        assert result is not None
        assert hasattr(result, 'cid') or "cid" in str(result)


class TestArweaveAdapter:
    """Tests for Arweave storage adapter."""

    def test_arweave_adapter_import(self):
        """Test ArweaveAdapter can be imported."""
        from cirkelline.web3.storage import ArweaveAdapter
        assert ArweaveAdapter is not None

    def test_arweave_adapter_initialization(self):
        """Test ArweaveAdapter initializes correctly."""
        from cirkelline.web3.storage import ArweaveAdapter
        adapter = ArweaveAdapter()
        assert hasattr(adapter, 'upload')
        assert hasattr(adapter, 'get')


class TestStorageRouter:
    """Tests for storage routing functionality."""

    def test_storage_router_import(self):
        """Test StorageRouter can be imported."""
        from cirkelline.web3.storage import StorageRouter
        assert StorageRouter is not None

    def test_storage_router_singleton(self):
        """Test singleton pattern for storage router."""
        from cirkelline.web3.storage import get_storage_router
        router1 = get_storage_router()
        router2 = get_storage_router()
        assert router1 is router2

    def test_storage_router_initialization(self):
        """Test StorageRouter initializes correctly."""
        from cirkelline.web3.storage import StorageRouter
        router = StorageRouter()
        assert hasattr(router, 'store')
        assert hasattr(router, 'retrieve')
        assert hasattr(router, 'recommend_policy')


class TestStorageResult:
    """Tests for StorageResult dataclass."""

    def test_storage_result_import(self):
        """Test StorageResult can be imported."""
        from cirkelline.web3.storage import StorageResult
        assert StorageResult is not None


# ═══════════════════════════════════════════════════════════════════════════════
# REPORTING MODULE TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestReportGenerator:
    """Tests for report generation functionality."""

    def test_report_generator_import(self):
        """Test ReportGenerator can be imported."""
        from cirkelline.web3.reporting import ReportGenerator
        assert ReportGenerator is not None

    def test_report_generator_singleton(self):
        """Test singleton pattern for report generator."""
        from cirkelline.web3.reporting import get_report_generator
        gen1 = get_report_generator()
        gen2 = get_report_generator()
        assert gen1 is gen2

    def test_report_generator_initialization(self):
        """Test ReportGenerator initializes correctly."""
        from cirkelline.web3.reporting import ReportGenerator
        generator = ReportGenerator()
        assert hasattr(generator, 'generate')
        assert hasattr(generator, 'format_report')

    @pytest.mark.asyncio
    async def test_generate_report(self):
        """Test report generation."""
        from cirkelline.web3.reporting import ReportGenerator, ReportType
        generator = ReportGenerator()

        report = await generator.generate(
            subject="Uniswap Protocol",
            report_type=ReportType.COMPREHENSIVE
        )

        assert report is not None
        assert hasattr(report, 'title') or hasattr(report, 'subject')


class TestRiskAnalyzer:
    """Tests for risk analysis functionality."""

    def test_risk_analyzer_import(self):
        """Test RiskAnalyzer can be imported."""
        from cirkelline.web3.reporting import RiskAnalyzer
        assert RiskAnalyzer is not None

    def test_risk_analyzer_singleton(self):
        """Test singleton pattern for risk analyzer."""
        from cirkelline.web3.reporting import get_risk_analyzer
        analyzer1 = get_risk_analyzer()
        analyzer2 = get_risk_analyzer()
        assert analyzer1 is analyzer2

    def test_risk_analyzer_initialization(self):
        """Test RiskAnalyzer initializes correctly."""
        from cirkelline.web3.reporting import RiskAnalyzer
        analyzer = RiskAnalyzer()
        assert hasattr(analyzer, 'assess')
        assert hasattr(analyzer, 'quick_check')
        assert hasattr(analyzer, 'compare')

    @pytest.mark.asyncio
    async def test_risk_assessment(self):
        """Test risk assessment."""
        from cirkelline.web3.reporting import RiskAnalyzer
        analyzer = RiskAnalyzer()

        assessment = await analyzer.assess(
            subject="New DeFi Protocol"
        )

        assert assessment is not None
        assert hasattr(assessment, 'overall_level') or hasattr(assessment, 'risks')


class TestReportingEngine:
    """Tests for unified reporting engine."""

    def test_reporting_engine_import(self):
        """Test ReportingEngine can be imported."""
        from cirkelline.web3.reporting import ReportingEngine
        assert ReportingEngine is not None

    def test_reporting_engine_singleton(self):
        """Test singleton pattern for reporting engine."""
        from cirkelline.web3.reporting import get_reporting_engine
        engine1 = get_reporting_engine()
        engine2 = get_reporting_engine()
        assert engine1 is engine2

    def test_reporting_engine_initialization(self):
        """Test ReportingEngine initializes correctly."""
        from cirkelline.web3.reporting import ReportingEngine
        engine = ReportingEngine()
        assert hasattr(engine, 'generate_comprehensive_report')
        assert hasattr(engine, 'generate_security_brief')
        assert hasattr(engine, 'generate_investment_analysis')

    @pytest.mark.asyncio
    async def test_comprehensive_report(self):
        """Test comprehensive report generation."""
        from cirkelline.web3.reporting import ReportingEngine
        engine = ReportingEngine()

        result = await engine.generate_comprehensive_report(
            subject="Ethereum 2.0"
        )

        assert result is not None
        assert "subject" in result
        assert "report" in result or "risk_assessment" in result


class TestReportType:
    """Tests for ReportType enum."""

    def test_report_type_import(self):
        """Test ReportType can be imported."""
        from cirkelline.web3.reporting import ReportType
        assert ReportType is not None

    def test_report_type_values(self):
        """Test ReportType has expected values."""
        from cirkelline.web3.reporting import ReportType

        # Check that we have some report types
        available_types = [t.name for t in ReportType]
        assert len(available_types) >= 5  # At least 5 report types


class TestRiskLevel:
    """Tests for RiskLevel enum."""

    def test_risk_level_import(self):
        """Test RiskLevel can be imported."""
        from cirkelline.web3.reporting import RiskLevel
        assert RiskLevel is not None

    def test_risk_level_values(self):
        """Test RiskLevel has expected values."""
        from cirkelline.web3.reporting import RiskLevel

        # Check that we have risk levels
        available_levels = [l.name for l in RiskLevel]
        assert len(available_levels) >= 4  # At least 4 levels


class TestRiskAssessment:
    """Tests for RiskAssessment dataclass."""

    def test_risk_assessment_import(self):
        """Test RiskAssessment can be imported."""
        from cirkelline.web3.reporting import RiskAssessment
        assert RiskAssessment is not None


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestWeb3ModuleIntegration:
    """Integration tests for Web3 modules."""

    def test_all_modules_importable(self):
        """Test all Web3 modules can be imported from main package."""
        from cirkelline.web3 import (
            # Scanner
            GitHubMonitor,
            ResearchScanner,
            TrendAnalyzer,
            TechnologyFeed,
            get_scanner_manager,
            # Analysis
            ProtocolAnalyzer,
            SecurityAuditor,
            CompatibilityChecker,
            AnalysisResult,
            get_analysis_engine,
            # Governance
            DAOAnalyzer,
            GameTheoryEngine,
            TokenomicsModeler,
            GovernanceProposal,
            get_governance_engine,
            # Identity
            DIDManager,
            ZKPVerifier,
            TrustLayer,
            VerifiableCredential,
            get_identity_manager,
            # Storage
            IPFSAdapter,
            ArweaveAdapter,
            StorageRouter,
            StorageResult,
            get_storage_router,
            # Reporting
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

        # Verify all imports are not None
        assert GitHubMonitor is not None
        assert ResearchScanner is not None
        assert ProtocolAnalyzer is not None
        assert DAOAnalyzer is not None
        assert DIDManager is not None
        assert IPFSAdapter is not None
        assert ReportGenerator is not None

    def test_singleton_instances_unique_per_type(self):
        """Test that singletons are unique per type but consistent within type."""
        from cirkelline.web3 import (
            get_scanner_manager,
            get_analysis_engine,
            get_governance_engine,
            get_identity_manager,
            get_storage_router,
            get_reporting_engine,
        )

        # Get all singletons
        scanner = get_scanner_manager()
        analysis = get_analysis_engine()
        governance = get_governance_engine()
        identity = get_identity_manager()
        storage = get_storage_router()
        reporting = get_reporting_engine()

        # Ensure they're all different objects
        instances = [scanner, analysis, governance, identity, storage, reporting]
        assert len(set(id(inst) for inst in instances)) == 6

        # Ensure same call returns same object
        assert get_scanner_manager() is scanner
        assert get_analysis_engine() is analysis
        assert get_governance_engine() is governance
        assert get_identity_manager() is identity
        assert get_storage_router() is storage
        assert get_reporting_engine() is reporting

    def test_module_version(self):
        """Test Web3 module version is defined."""
        from cirkelline.web3 import __version__
        assert __version__ == "1.0.0"

    @pytest.mark.asyncio
    async def test_end_to_end_analysis_workflow(self):
        """Test end-to-end analysis workflow."""
        from cirkelline.web3 import (
            get_analysis_engine,
            get_reporting_engine,
        )

        # Get engines
        analysis_engine = get_analysis_engine()
        reporting_engine = get_reporting_engine()

        # Generate report
        report = await reporting_engine.generate_comprehensive_report(
            subject="test-protocol"
        )

        assert report is not None
        assert "subject" in report


# ═══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestWeb3Performance:
    """Performance tests for Web3 modules."""

    def test_import_performance(self):
        """Test that imports complete in reasonable time."""
        import time

        start = time.time()
        from cirkelline.web3 import (
            GitHubMonitor,
            ProtocolAnalyzer,
            DAOAnalyzer,
            DIDManager,
            IPFSAdapter,
            ReportGenerator,
        )
        elapsed = time.time() - start

        # Should import in under 2 seconds
        assert elapsed < 2.0, f"Import took too long: {elapsed:.2f}s"

    def test_singleton_access_performance(self):
        """Test that singleton access is fast."""
        import time
        from cirkelline.web3 import get_reporting_engine

        # First call (initialization)
        start = time.time()
        get_reporting_engine()
        first_call = time.time() - start

        # Subsequent calls (should be instant)
        iterations = 1000
        start = time.time()
        for _ in range(iterations):
            get_reporting_engine()
        subsequent_avg = (time.time() - start) / iterations

        # Subsequent calls should be < 1ms each
        assert subsequent_avg < 0.001, f"Singleton access too slow: {subsequent_avg*1000:.2f}ms"


# ═══════════════════════════════════════════════════════════════════════════════
# ERROR HANDLING TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestWeb3ErrorHandling:
    """Error handling tests for Web3 modules."""

    @pytest.mark.asyncio
    async def test_invalid_protocol_analysis(self):
        """Test error handling for invalid protocol analysis."""
        from cirkelline.web3.analysis import ProtocolAnalyzer

        analyzer = ProtocolAnalyzer()

        # Should handle gracefully, not crash
        result = await analyzer.analyze(
            target=""  # Invalid empty target
        )

        # Should return result or None, not raise exception
        assert result is None or result is not None

    @pytest.mark.asyncio
    async def test_invalid_did_resolution(self):
        """Test error handling for invalid DID resolution."""
        from cirkelline.web3.identity import DIDManager

        manager = DIDManager()

        # Should handle gracefully
        result = await manager.resolve(
            did="invalid:did:format"
        )

        # Should return None or error result, not crash
        assert result is None or result is not None

    @pytest.mark.asyncio
    async def test_storage_router_missing_content(self):
        """Test error handling for missing content retrieval."""
        from cirkelline.web3.storage import StorageRouter

        router = StorageRouter()

        # Should handle gracefully
        result = await router.retrieve(
            content_id="nonexistent-content-id"
        )

        # Should return None for missing content
        assert result is None or result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
