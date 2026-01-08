"""
Protocol Analyzer
=================
Smart contract and protocol backwards engineering.

Responsibilities:
- Analyze protocol architecture and mechanics
- Extract governance patterns and tokenomics
- Understand smart contract interactions
- Identify design patterns and anti-patterns
"""

import logging
import asyncio
import hashlib
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class ProtocolType(Enum):
    """Protocol classification types."""
    DEX = "dex"                    # Decentralized exchange
    LENDING = "lending"            # Lending/borrowing
    STAKING = "staking"            # Staking protocols
    BRIDGE = "bridge"              # Cross-chain bridges
    ORACLE = "oracle"              # Data oracles
    DAO = "dao"                    # Governance DAOs
    NFT = "nft"                    # NFT marketplaces
    IDENTITY = "identity"          # Identity protocols
    STORAGE = "storage"            # Decentralized storage
    LAYER2 = "layer2"              # L2 scaling solutions
    PRIVACY = "privacy"            # Privacy protocols
    YIELD = "yield"                # Yield aggregators
    OTHER = "other"


class ContractPattern(Enum):
    """Smart contract design patterns."""
    PROXY = "proxy"                # Upgradeable proxy pattern
    FACTORY = "factory"            # Contract factory pattern
    DIAMOND = "diamond"            # EIP-2535 Diamond
    OWNABLE = "ownable"            # Single owner
    ACCESS_CONTROL = "access_control"  # Role-based access
    PAUSABLE = "pausable"          # Emergency pause
    REENTRANCY_GUARD = "reentrancy_guard"  # Reentrancy protection
    TIMELOCK = "timelock"          # Time-delayed execution
    MULTISIG = "multisig"          # Multi-signature control
    UPGRADEABLE = "upgradeable"    # Upgrade mechanism


class BlockchainNetwork(Enum):
    """Supported blockchain networks."""
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"
    BSC = "bsc"
    AVALANCHE = "avalanche"
    SOLANA = "solana"
    COSMOS = "cosmos"


@dataclass
class ContractInfo:
    """Information about a smart contract."""
    address: str
    name: str
    network: BlockchainNetwork = BlockchainNetwork.ETHEREUM
    verified: bool = False
    compiler_version: str = ""
    patterns: List[ContractPattern] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "address": self.address,
            "name": self.name,
            "network": self.network.value,
            "verified": self.verified,
            "patterns": [p.value for p in self.patterns],
            "function_count": len(self.functions),
            "event_count": len(self.events),
        }


@dataclass
class GovernanceInfo:
    """Protocol governance information."""
    model: str = "unknown"  # token-voting, multisig, hybrid
    token_address: Optional[str] = None
    voting_period: int = 0  # in blocks or seconds
    proposal_threshold: float = 0.0
    quorum: float = 0.0
    timelock_delay: int = 0
    governor_contract: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "token_address": self.token_address,
            "voting_period": self.voting_period,
            "quorum": f"{self.quorum * 100:.1f}%",
            "timelock_delay": self.timelock_delay,
        }


@dataclass
class TokenomicsInfo:
    """Protocol tokenomics information."""
    token_address: Optional[str] = None
    token_symbol: str = ""
    total_supply: float = 0
    circulating_supply: float = 0
    max_supply: Optional[float] = None
    inflation_rate: float = 0.0
    utility: List[str] = field(default_factory=list)
    distribution: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.token_symbol,
            "total_supply": self.total_supply,
            "circulating_supply": self.circulating_supply,
            "inflation_rate": f"{self.inflation_rate * 100:.2f}%",
            "utility": self.utility[:5],
        }


@dataclass
class ProtocolInfo:
    """Complete protocol analysis information."""
    name: str
    protocol_type: ProtocolType = ProtocolType.OTHER
    description: str = ""
    networks: List[BlockchainNetwork] = field(default_factory=list)
    contracts: List[ContractInfo] = field(default_factory=list)
    governance: Optional[GovernanceInfo] = None
    tokenomics: Optional[TokenomicsInfo] = None
    tvl: float = 0.0  # Total Value Locked
    users: int = 0
    launch_date: str = ""
    website: str = ""
    docs: str = ""
    github: str = ""
    audit_reports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # External protocols

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.protocol_type.value,
            "description": self.description[:200],
            "networks": [n.value for n in self.networks],
            "contracts_count": len(self.contracts),
            "tvl": self.tvl,
            "users": self.users,
            "governance": self.governance.to_dict() if self.governance else None,
            "tokenomics": self.tokenomics.to_dict() if self.tokenomics else None,
            "audit_count": len(self.audit_reports),
        }


@dataclass
class ContractAnalysis:
    """Detailed contract analysis result."""
    contract: ContractInfo
    code_quality: float = 0.0  # 0-1
    complexity: str = "low"  # low, medium, high
    patterns_detected: List[ContractPattern] = field(default_factory=list)
    potential_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract": self.contract.to_dict(),
            "code_quality": round(self.code_quality, 2),
            "complexity": self.complexity,
            "patterns": [p.value for p in self.patterns_detected],
            "issues_count": len(self.potential_issues),
            "recommendations": self.recommendations[:3],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# KNOWN PROTOCOLS DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

KNOWN_PROTOCOLS = {
    "uniswap": ProtocolInfo(
        name="Uniswap",
        protocol_type=ProtocolType.DEX,
        description="Decentralized exchange with automated market maker (AMM)",
        networks=[BlockchainNetwork.ETHEREUM, BlockchainNetwork.ARBITRUM, BlockchainNetwork.POLYGON],
        website="https://uniswap.org",
        github="https://github.com/Uniswap",
    ),
    "aave": ProtocolInfo(
        name="Aave",
        protocol_type=ProtocolType.LENDING,
        description="Decentralized lending and borrowing protocol",
        networks=[BlockchainNetwork.ETHEREUM, BlockchainNetwork.POLYGON, BlockchainNetwork.ARBITRUM],
        website="https://aave.com",
        github="https://github.com/aave",
    ),
    "compound": ProtocolInfo(
        name="Compound",
        protocol_type=ProtocolType.LENDING,
        description="Algorithmic money market protocol",
        networks=[BlockchainNetwork.ETHEREUM],
        website="https://compound.finance",
        github="https://github.com/compound-finance",
    ),
    "chainlink": ProtocolInfo(
        name="Chainlink",
        protocol_type=ProtocolType.ORACLE,
        description="Decentralized oracle network",
        networks=[BlockchainNetwork.ETHEREUM, BlockchainNetwork.POLYGON, BlockchainNetwork.ARBITRUM],
        website="https://chain.link",
        github="https://github.com/smartcontractkit",
    ),
    "maker": ProtocolInfo(
        name="MakerDAO",
        protocol_type=ProtocolType.DAO,
        description="Decentralized credit platform and DAI stablecoin",
        networks=[BlockchainNetwork.ETHEREUM],
        website="https://makerdao.com",
        github="https://github.com/makerdao",
    ),
    "lido": ProtocolInfo(
        name="Lido",
        protocol_type=ProtocolType.STAKING,
        description="Liquid staking solution for Ethereum",
        networks=[BlockchainNetwork.ETHEREUM],
        website="https://lido.fi",
        github="https://github.com/lidofinance",
    ),
    "optimism": ProtocolInfo(
        name="Optimism",
        protocol_type=ProtocolType.LAYER2,
        description="Optimistic rollup Layer 2 scaling solution",
        networks=[BlockchainNetwork.ETHEREUM, BlockchainNetwork.OPTIMISM],
        website="https://optimism.io",
        github="https://github.com/ethereum-optimism",
    ),
    "arbitrum": ProtocolInfo(
        name="Arbitrum",
        protocol_type=ProtocolType.LAYER2,
        description="Optimistic rollup Layer 2 with fraud proofs",
        networks=[BlockchainNetwork.ETHEREUM, BlockchainNetwork.ARBITRUM],
        website="https://arbitrum.io",
        github="https://github.com/OffchainLabs",
    ),
    "polygon": ProtocolInfo(
        name="Polygon",
        protocol_type=ProtocolType.LAYER2,
        description="Ethereum scaling with PoS sidechain and zkEVM",
        networks=[BlockchainNetwork.ETHEREUM, BlockchainNetwork.POLYGON],
        website="https://polygon.technology",
        github="https://github.com/maticnetwork",
    ),
    "ens": ProtocolInfo(
        name="Ethereum Name Service",
        protocol_type=ProtocolType.IDENTITY,
        description="Decentralized naming system for Ethereum",
        networks=[BlockchainNetwork.ETHEREUM],
        website="https://ens.domains",
        github="https://github.com/ensdomains",
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# PROTOCOL ANALYZER
# ═══════════════════════════════════════════════════════════════════════════════

class ProtocolAnalyzer:
    """
    Protocol and smart contract analyzer.

    Performs backwards engineering of DeFi protocols,
    smart contracts, and blockchain systems.
    """

    def __init__(self):
        self._known_protocols = KNOWN_PROTOCOLS
        self._analysis_cache: Dict[str, ProtocolInfo] = {}
        self._contract_cache: Dict[str, ContractInfo] = {}

        # Statistics
        self._stats = {
            "total_analyses": 0,
            "protocols_analyzed": 0,
            "contracts_analyzed": 0,
            "cache_hits": 0,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════

    async def analyze(self, target: str) -> ProtocolInfo:
        """
        Analyze a protocol or contract.

        Args:
            target: Protocol name or contract address

        Returns:
            Protocol information
        """
        self._stats["total_analyses"] += 1

        # Check if it's a known protocol
        target_lower = target.lower()
        if target_lower in self._known_protocols:
            self._stats["cache_hits"] += 1
            return self._known_protocols[target_lower]

        # Check analysis cache
        if target_lower in self._analysis_cache:
            self._stats["cache_hits"] += 1
            return self._analysis_cache[target_lower]

        # Check if it's a contract address
        if self._is_contract_address(target):
            protocol = await self._analyze_contract_address(target)
        else:
            protocol = await self._analyze_protocol_name(target)

        self._analysis_cache[target_lower] = protocol
        self._stats["protocols_analyzed"] += 1

        return protocol

    async def analyze_contract(
        self,
        address: str,
        network: BlockchainNetwork = BlockchainNetwork.ETHEREUM,
    ) -> ContractAnalysis:
        """
        Perform detailed contract analysis.

        Args:
            address: Contract address
            network: Blockchain network
        """
        self._stats["contracts_analyzed"] += 1

        # Get or create contract info
        contract = await self._fetch_contract_info(address, network)

        # Analyze patterns
        patterns = self._detect_patterns(contract)

        # Assess complexity
        complexity = self._assess_complexity(contract)

        # Identify potential issues
        issues = self._identify_issues(contract, patterns)

        # Generate recommendations
        recommendations = self._generate_recommendations(contract, patterns, issues)

        # Calculate code quality
        quality = self._calculate_code_quality(contract, patterns, issues)

        return ContractAnalysis(
            contract=contract,
            code_quality=quality,
            complexity=complexity,
            patterns_detected=patterns,
            potential_issues=issues,
            recommendations=recommendations,
        )

    async def _analyze_contract_address(self, address: str) -> ProtocolInfo:
        """Analyze a contract address to determine protocol."""
        # In production, this would fetch from Etherscan/block explorer
        contract = await self._fetch_contract_info(address)

        return ProtocolInfo(
            name=f"Contract {address[:10]}...",
            protocol_type=self._infer_protocol_type(contract),
            description=f"Smart contract at {address}",
            networks=[contract.network],
            contracts=[contract],
        )

    async def _analyze_protocol_name(self, name: str) -> ProtocolInfo:
        """Analyze a protocol by name (fetch from sources)."""
        # In production, this would fetch from DeFiLlama, DefiPulse, etc.
        return ProtocolInfo(
            name=name.title(),
            protocol_type=ProtocolType.OTHER,
            description=f"Protocol: {name}",
            networks=[BlockchainNetwork.ETHEREUM],
        )

    async def _fetch_contract_info(
        self,
        address: str,
        network: BlockchainNetwork = BlockchainNetwork.ETHEREUM,
    ) -> ContractInfo:
        """Fetch contract information from blockchain."""
        # Check cache
        cache_key = f"{network.value}:{address}"
        if cache_key in self._contract_cache:
            return self._contract_cache[cache_key]

        # Mock data (in production, fetch from Etherscan API)
        contract = ContractInfo(
            address=address,
            name=f"Contract_{address[:8]}",
            network=network,
            verified=True,
            compiler_version="0.8.20",
            functions=[
                "transfer", "approve", "transferFrom",
                "balanceOf", "allowance",
            ],
            events=["Transfer", "Approval"],
        )

        self._contract_cache[cache_key] = contract
        return contract

    def _is_contract_address(self, target: str) -> bool:
        """Check if target is a contract address."""
        # Ethereum address pattern
        return bool(re.match(r'^0x[a-fA-F0-9]{40}$', target))

    # ═══════════════════════════════════════════════════════════════════════════
    # PATTERN DETECTION
    # ═══════════════════════════════════════════════════════════════════════════

    def _detect_patterns(self, contract: ContractInfo) -> List[ContractPattern]:
        """Detect design patterns in contract."""
        patterns = []

        # Check for common patterns based on functions
        function_lower = [f.lower() for f in contract.functions]

        if any("upgrade" in f for f in function_lower):
            patterns.append(ContractPattern.UPGRADEABLE)

        if any("proxy" in f for f in function_lower):
            patterns.append(ContractPattern.PROXY)

        if any("pause" in f for f in function_lower):
            patterns.append(ContractPattern.PAUSABLE)

        if any("owner" in f for f in function_lower):
            patterns.append(ContractPattern.OWNABLE)

        if any("role" in f or "access" in f for f in function_lower):
            patterns.append(ContractPattern.ACCESS_CONTROL)

        if any("timelock" in f for f in function_lower):
            patterns.append(ContractPattern.TIMELOCK)

        return patterns

    def _infer_protocol_type(self, contract: ContractInfo) -> ProtocolType:
        """Infer protocol type from contract analysis."""
        function_lower = [f.lower() for f in contract.functions]

        # DEX indicators
        if any(f in function_lower for f in ["swap", "addliquidity", "removeliquidity"]):
            return ProtocolType.DEX

        # Lending indicators
        if any(f in function_lower for f in ["borrow", "repay", "liquidate"]):
            return ProtocolType.LENDING

        # Staking indicators
        if any(f in function_lower for f in ["stake", "unstake", "claim"]):
            return ProtocolType.STAKING

        # NFT indicators
        if any(f in function_lower for f in ["mint", "tokenuuri", "safetransferfrom"]):
            return ProtocolType.NFT

        # Bridge indicators
        if any(f in function_lower for f in ["bridge", "crosschain", "relay"]):
            return ProtocolType.BRIDGE

        return ProtocolType.OTHER

    # ═══════════════════════════════════════════════════════════════════════════
    # QUALITY ASSESSMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def _assess_complexity(self, contract: ContractInfo) -> str:
        """Assess contract complexity."""
        function_count = len(contract.functions)
        pattern_count = len(contract.patterns)

        if function_count < 10 and pattern_count < 3:
            return "low"
        elif function_count < 30 and pattern_count < 5:
            return "medium"
        else:
            return "high"

    def _identify_issues(
        self,
        contract: ContractInfo,
        patterns: List[ContractPattern],
    ) -> List[str]:
        """Identify potential issues in contract."""
        issues = []

        # Check for missing safety patterns
        if ContractPattern.REENTRANCY_GUARD not in patterns:
            if any("transfer" in f.lower() for f in contract.functions):
                issues.append("Missing reentrancy guard on transfer functions")

        if ContractPattern.PAUSABLE not in patterns:
            issues.append("No emergency pause mechanism")

        if not contract.verified:
            issues.append("Contract source not verified")

        # Check for centralization risks
        if ContractPattern.OWNABLE in patterns:
            if ContractPattern.MULTISIG not in patterns:
                issues.append("Single owner without multisig protection")

        return issues

    def _calculate_code_quality(
        self,
        contract: ContractInfo,
        patterns: List[ContractPattern],
        issues: List[str],
    ) -> float:
        """Calculate overall code quality score."""
        score = 0.5  # Base score

        # Positive factors
        if contract.verified:
            score += 0.1
        if ContractPattern.ACCESS_CONTROL in patterns:
            score += 0.1
        if ContractPattern.PAUSABLE in patterns:
            score += 0.05
        if ContractPattern.REENTRANCY_GUARD in patterns:
            score += 0.1

        # Negative factors
        score -= len(issues) * 0.05

        return max(0.0, min(1.0, score))

    def _generate_recommendations(
        self,
        contract: ContractInfo,
        patterns: List[ContractPattern],
        issues: List[str],
    ) -> List[str]:
        """Generate recommendations for contract."""
        recommendations = []

        if not contract.verified:
            recommendations.append("Verify contract source on block explorer")

        if ContractPattern.PAUSABLE not in patterns:
            recommendations.append("Consider implementing emergency pause functionality")

        if ContractPattern.TIMELOCK not in patterns:
            if ContractPattern.UPGRADEABLE in patterns:
                recommendations.append("Add timelock for upgrades to allow user exit")

        if ContractPattern.OWNABLE in patterns:
            recommendations.append("Consider migrating to role-based access control")

        return recommendations

    # ═══════════════════════════════════════════════════════════════════════════
    # QUERIES
    # ═══════════════════════════════════════════════════════════════════════════

    def get_known_protocols(self) -> List[str]:
        """Get list of known protocol names."""
        return list(self._known_protocols.keys())

    def get_protocol_by_type(self, protocol_type: ProtocolType) -> List[ProtocolInfo]:
        """Get protocols by type."""
        return [
            p for p in self._known_protocols.values()
            if p.protocol_type == protocol_type
        ]

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get analyzer statistics."""
        return {
            **self._stats,
            "known_protocols": len(self._known_protocols),
            "analysis_cache_size": len(self._analysis_cache),
            "contract_cache_size": len(self._contract_cache),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_analyzer_instance: Optional[ProtocolAnalyzer] = None


def get_protocol_analyzer() -> ProtocolAnalyzer:
    """Get singleton ProtocolAnalyzer instance."""
    global _analyzer_instance

    if _analyzer_instance is None:
        _analyzer_instance = ProtocolAnalyzer()

    return _analyzer_instance
