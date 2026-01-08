"""
Trust Layer
===========
Machine-to-machine trust and reputation.

Responsibilities:
- Calculate trust scores
- Manage trust relationships
- Track reputation history
- Enable agent-level trust
"""

import logging
import math
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class TrustLevel(Enum):
    """Trust level classifications."""
    UNTRUSTED = "untrusted"
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERIFIED = "verified"


class TrustFactor(Enum):
    """Factors contributing to trust score."""
    IDENTITY = "identity"           # DID verification
    CREDENTIALS = "credentials"     # Verified credentials
    HISTORY = "history"             # Transaction history
    REPUTATION = "reputation"       # Community reputation
    STAKE = "stake"                 # Economic stake
    ATTESTATION = "attestation"     # Third-party attestations
    BEHAVIOR = "behavior"           # Behavioral analysis
    NETWORK = "network"             # Network connections


class RelationType(Enum):
    """Types of trust relationships."""
    DIRECT = "direct"               # Direct trust
    DELEGATED = "delegated"         # Delegated trust
    TRANSITIVE = "transitive"       # Through network
    REVOKED = "revoked"             # Revoked trust


@dataclass
class TrustScore:
    """A calculated trust score."""
    entity_id: str
    score: float  # 0.0 - 1.0
    level: TrustLevel
    factors: Dict[TrustFactor, float] = field(default_factory=dict)
    confidence: float = 0.0  # Confidence in score
    calculated_at: str = ""
    valid_until: str = ""
    history: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "score": round(self.score, 3),
            "level": self.level.value,
            "factors": {k.value: round(v, 3) for k, v in self.factors.items()},
            "confidence": round(self.confidence, 3),
            "calculated_at": self.calculated_at,
        }


@dataclass
class TrustRelation:
    """A trust relationship between entities."""
    relation_id: str
    trustor: str  # Entity giving trust
    trustee: str  # Entity receiving trust
    relation_type: RelationType = RelationType.DIRECT
    trust_amount: float = 0.0  # 0.0 - 1.0
    context: str = ""  # Domain context
    created_at: str = ""
    expires_at: Optional[str] = None
    revoked: bool = False
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "trustor": self.trustor[:20] + "..." if len(self.trustor) > 20 else self.trustor,
            "trustee": self.trustee[:20] + "..." if len(self.trustee) > 20 else self.trustee,
            "type": self.relation_type.value,
            "amount": round(self.trust_amount, 3),
            "context": self.context,
            "revoked": self.revoked,
        }


@dataclass
class Attestation:
    """A trust attestation from a third party."""
    attestation_id: str
    attester: str
    subject: str
    claim: str
    value: Any
    signature: str = ""
    created_at: str = ""
    expires_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attestation_id": self.attestation_id,
            "attester": self.attester[:20] + "...",
            "subject": self.subject[:20] + "...",
            "claim": self.claim,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# TRUST WEIGHTS
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_TRUST_WEIGHTS = {
    TrustFactor.IDENTITY: 0.25,
    TrustFactor.CREDENTIALS: 0.20,
    TrustFactor.HISTORY: 0.15,
    TrustFactor.REPUTATION: 0.15,
    TrustFactor.STAKE: 0.10,
    TrustFactor.ATTESTATION: 0.10,
    TrustFactor.BEHAVIOR: 0.03,
    TrustFactor.NETWORK: 0.02,
}

TRUST_LEVEL_THRESHOLDS = {
    TrustLevel.UNTRUSTED: 0.0,
    TrustLevel.MINIMAL: 0.15,
    TrustLevel.LOW: 0.30,
    TrustLevel.MEDIUM: 0.50,
    TrustLevel.HIGH: 0.75,
    TrustLevel.VERIFIED: 0.90,
}


# ═══════════════════════════════════════════════════════════════════════════════
# TRUST LAYER
# ═══════════════════════════════════════════════════════════════════════════════

class TrustLayer:
    """
    Machine-to-machine trust layer.

    Calculates trust scores based on multiple factors
    and manages trust relationships between entities.
    """

    def __init__(self):
        self._trust_weights = DEFAULT_TRUST_WEIGHTS
        self._score_cache: Dict[str, TrustScore] = {}
        self._relations: Dict[str, TrustRelation] = {}
        self._attestations: Dict[str, List[Attestation]] = {}

        # Trusted entities (bootstrap trust)
        self._trusted_roots: Dict[str, float] = {}

        # Statistics
        self._stats = {
            "scores_calculated": 0,
            "relations_created": 0,
            "attestations_recorded": 0,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # TRUST CALCULATION
    # ═══════════════════════════════════════════════════════════════════════════

    async def calculate_trust(
        self,
        entity_id: str,
        context: Optional[str] = None,
    ) -> TrustScore:
        """
        Calculate trust score for an entity.

        Args:
            entity_id: Entity to calculate trust for
            context: Optional domain context
        """
        self._stats["scores_calculated"] += 1

        # Check cache
        cache_key = f"{entity_id}:{context or 'default'}"
        if cache_key in self._score_cache:
            cached = self._score_cache[cache_key]
            # Check if still valid
            if cached.valid_until:
                valid_until = datetime.fromisoformat(
                    cached.valid_until.replace("Z", "+00:00")
                )
                if datetime.now(valid_until.tzinfo) < valid_until:
                    return cached

        # Calculate factor scores
        factors = await self._calculate_factors(entity_id, context)

        # Calculate weighted score
        score = sum(
            factors.get(factor, 0) * weight
            for factor, weight in self._trust_weights.items()
        )

        # Normalize
        score = max(0.0, min(1.0, score))

        # Determine level
        level = self._score_to_level(score)

        # Calculate confidence based on factor coverage
        coverage = len(factors) / len(self._trust_weights)
        confidence = coverage * min(1.0, score + 0.2)

        now = datetime.utcnow()
        trust_score = TrustScore(
            entity_id=entity_id,
            score=score,
            level=level,
            factors=factors,
            confidence=confidence,
            calculated_at=now.isoformat() + "Z",
            valid_until=(now + timedelta(hours=1)).isoformat() + "Z",
        )

        # Cache result
        self._score_cache[cache_key] = trust_score

        return trust_score

    async def _calculate_factors(
        self,
        entity_id: str,
        context: Optional[str],
    ) -> Dict[TrustFactor, float]:
        """Calculate individual trust factors."""
        factors = {}

        # Identity factor (from DID resolution)
        identity_score = await self._evaluate_identity(entity_id)
        if identity_score > 0:
            factors[TrustFactor.IDENTITY] = identity_score

        # Credentials factor
        credential_score = await self._evaluate_credentials(entity_id)
        if credential_score > 0:
            factors[TrustFactor.CREDENTIALS] = credential_score

        # History factor
        history_score = self._evaluate_history(entity_id)
        if history_score > 0:
            factors[TrustFactor.HISTORY] = history_score

        # Reputation factor
        reputation_score = self._evaluate_reputation(entity_id)
        if reputation_score > 0:
            factors[TrustFactor.REPUTATION] = reputation_score

        # Stake factor
        stake_score = self._evaluate_stake(entity_id)
        if stake_score > 0:
            factors[TrustFactor.STAKE] = stake_score

        # Attestation factor
        attestation_score = self._evaluate_attestations(entity_id)
        if attestation_score > 0:
            factors[TrustFactor.ATTESTATION] = attestation_score

        # Network factor (transitive trust)
        network_score = self._evaluate_network(entity_id)
        if network_score > 0:
            factors[TrustFactor.NETWORK] = network_score

        return factors

    async def _evaluate_identity(self, entity_id: str) -> float:
        """Evaluate identity verification."""
        # Check if entity has verified DID
        if entity_id.startswith("did:"):
            # DID exists, base score
            score = 0.5

            # Bonus for specific methods
            if ":ethr:" in entity_id:
                score += 0.2  # Ethereum-based
            if ":key:" in entity_id:
                score += 0.1  # Key-based

            return min(1.0, score)

        return 0.0

    async def _evaluate_credentials(self, entity_id: str) -> float:
        """Evaluate verified credentials."""
        # In production, check credential registry
        attestations = self._attestations.get(entity_id, [])
        if not attestations:
            return 0.0

        # More attestations = higher score
        count = len(attestations)
        return min(1.0, 0.3 + count * 0.1)

    def _evaluate_history(self, entity_id: str) -> float:
        """Evaluate transaction/interaction history."""
        # Check relations where entity is trustee
        incoming = [
            r for r in self._relations.values()
            if r.trustee == entity_id and not r.revoked
        ]

        if not incoming:
            return 0.0

        # Average trust from relations
        avg_trust = sum(r.trust_amount for r in incoming) / len(incoming)
        return avg_trust

    def _evaluate_reputation(self, entity_id: str) -> float:
        """Evaluate community reputation."""
        # Check cached score history
        if entity_id in self._score_cache:
            history = self._score_cache[entity_id].history
            if history:
                # Trend analysis
                return sum(history[-10:]) / min(len(history), 10)

        return 0.0

    def _evaluate_stake(self, entity_id: str) -> float:
        """Evaluate economic stake."""
        # In production, check on-chain stake
        return 0.3  # Default minimal stake

    def _evaluate_attestations(self, entity_id: str) -> float:
        """Evaluate third-party attestations."""
        attestations = self._attestations.get(entity_id, [])
        if not attestations:
            return 0.0

        # Check attesters' trust
        total_weight = 0.0
        for att in attestations:
            # Weight by attester's own trust
            attester_score = self._score_cache.get(att.attester)
            if attester_score:
                total_weight += attester_score.score
            else:
                total_weight += 0.3  # Default weight

        return min(1.0, total_weight / max(1, len(attestations)))

    def _evaluate_network(self, entity_id: str) -> float:
        """Evaluate network trust (transitive)."""
        # Simple transitive trust calculation
        direct_trusts = [
            r.trust_amount for r in self._relations.values()
            if r.trustee == entity_id and r.relation_type == RelationType.DIRECT
        ]

        if not direct_trusts:
            return 0.0

        # PageRank-like calculation (simplified)
        return min(1.0, sum(direct_trusts) / (1 + len(direct_trusts)))

    def _score_to_level(self, score: float) -> TrustLevel:
        """Convert score to trust level."""
        for level, threshold in sorted(
            TRUST_LEVEL_THRESHOLDS.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if score >= threshold:
                return level
        return TrustLevel.UNTRUSTED

    # ═══════════════════════════════════════════════════════════════════════════
    # TRUST RELATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    async def create_relation(
        self,
        trustor: str,
        trustee: str,
        trust_amount: float,
        relation_type: RelationType = RelationType.DIRECT,
        context: str = "",
        expires_days: Optional[int] = None,
    ) -> TrustRelation:
        """
        Create a trust relationship.

        Args:
            trustor: Entity giving trust
            trustee: Entity receiving trust
            trust_amount: Amount of trust (0-1)
            relation_type: Type of relation
            context: Domain context
            expires_days: Days until expiration
        """
        import secrets
        self._stats["relations_created"] += 1

        relation_id = f"rel-{secrets.token_hex(8)}"
        now = datetime.utcnow()

        relation = TrustRelation(
            relation_id=relation_id,
            trustor=trustor,
            trustee=trustee,
            relation_type=relation_type,
            trust_amount=max(0.0, min(1.0, trust_amount)),
            context=context,
            created_at=now.isoformat() + "Z",
            expires_at=(
                (now + timedelta(days=expires_days)).isoformat() + "Z"
                if expires_days else None
            ),
        )

        self._relations[relation_id] = relation

        # Invalidate cached scores for trustee
        self._invalidate_cache(trustee)

        return relation

    async def revoke_relation(self, relation_id: str) -> bool:
        """Revoke a trust relationship."""
        if relation_id not in self._relations:
            return False

        self._relations[relation_id].revoked = True
        self._relations[relation_id].relation_type = RelationType.REVOKED

        # Invalidate caches
        self._invalidate_cache(self._relations[relation_id].trustee)

        return True

    def get_relations_for(
        self,
        entity_id: str,
        as_trustor: bool = False,
    ) -> List[TrustRelation]:
        """Get trust relations for an entity."""
        if as_trustor:
            return [
                r for r in self._relations.values()
                if r.trustor == entity_id and not r.revoked
            ]
        else:
            return [
                r for r in self._relations.values()
                if r.trustee == entity_id and not r.revoked
            ]

    # ═══════════════════════════════════════════════════════════════════════════
    # ATTESTATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    async def add_attestation(
        self,
        attester: str,
        subject: str,
        claim: str,
        value: Any,
        expires_days: int = 365,
    ) -> Attestation:
        """
        Add an attestation about an entity.

        Args:
            attester: Entity making attestation
            subject: Entity being attested
            claim: Type of claim
            value: Claim value
            expires_days: Days until expiration
        """
        import secrets
        self._stats["attestations_recorded"] += 1

        now = datetime.utcnow()
        attestation = Attestation(
            attestation_id=f"att-{secrets.token_hex(8)}",
            attester=attester,
            subject=subject,
            claim=claim,
            value=value,
            created_at=now.isoformat() + "Z",
            expires_at=(now + timedelta(days=expires_days)).isoformat() + "Z",
        )

        if subject not in self._attestations:
            self._attestations[subject] = []
        self._attestations[subject].append(attestation)

        # Invalidate cache
        self._invalidate_cache(subject)

        return attestation

    def get_attestations(self, entity_id: str) -> List[Attestation]:
        """Get attestations for an entity."""
        return self._attestations.get(entity_id, [])

    # ═══════════════════════════════════════════════════════════════════════════
    # TRUSTED ROOTS
    # ═══════════════════════════════════════════════════════════════════════════

    def add_trusted_root(self, entity_id: str, trust: float = 1.0) -> None:
        """Add a trusted root entity (bootstrap trust)."""
        self._trusted_roots[entity_id] = max(0.0, min(1.0, trust))

    def is_trusted_root(self, entity_id: str) -> bool:
        """Check if entity is a trusted root."""
        return entity_id in self._trusted_roots

    # ═══════════════════════════════════════════════════════════════════════════
    # CACHE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def _invalidate_cache(self, entity_id: str) -> None:
        """Invalidate cached scores for an entity."""
        keys_to_remove = [
            k for k in self._score_cache.keys()
            if k.startswith(f"{entity_id}:")
        ]
        for key in keys_to_remove:
            del self._score_cache[key]

    def clear_cache(self) -> None:
        """Clear all cached scores."""
        self._score_cache.clear()

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get trust layer statistics."""
        return {
            **self._stats,
            "cached_scores": len(self._score_cache),
            "active_relations": sum(
                1 for r in self._relations.values() if not r.revoked
            ),
            "total_attestations": sum(
                len(atts) for atts in self._attestations.values()
            ),
            "trusted_roots": len(self._trusted_roots),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_layer_instance: Optional[TrustLayer] = None


def get_trust_layer() -> TrustLayer:
    """Get singleton TrustLayer instance."""
    global _layer_instance

    if _layer_instance is None:
        _layer_instance = TrustLayer()

    return _layer_instance
