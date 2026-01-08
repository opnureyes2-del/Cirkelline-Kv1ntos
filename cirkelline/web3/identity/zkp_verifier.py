"""
ZKP Verifier
============
Zero-Knowledge Proof verification.

Responsibilities:
- Verify zk-SNARKs, zk-STARKs proofs
- Support various proof systems
- Integrate with proof circuits
- Manage verification keys
"""

import logging
import hashlib
import secrets
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class ProofType(Enum):
    """Types of zero-knowledge proofs."""
    GROTH16 = "groth16"           # zk-SNARK (trusted setup)
    PLONK = "plonk"               # Universal SNARK
    STARK = "stark"               # Transparent, post-quantum
    BULLETPROOFS = "bulletproofs"  # Range proofs
    HALO2 = "halo2"               # Recursive, no trusted setup
    NOVA = "nova"                 # Folding scheme


class CircuitType(Enum):
    """Types of proof circuits."""
    IDENTITY = "identity"         # Identity verification
    MEMBERSHIP = "membership"     # Set membership
    RANGE = "range"               # Range proof
    OWNERSHIP = "ownership"       # Asset ownership
    AGE = "age"                   # Age verification
    BALANCE = "balance"           # Balance proof
    CUSTOM = "custom"


class VerificationStatus(Enum):
    """Verification result status."""
    VALID = "valid"
    INVALID = "invalid"
    ERROR = "error"
    EXPIRED = "expired"


@dataclass
class ZKProof:
    """A zero-knowledge proof."""
    proof_id: str
    proof_type: ProofType
    circuit_type: CircuitType
    proof_data: bytes = field(default_factory=bytes)
    public_inputs: List[str] = field(default_factory=list)
    verification_key_id: Optional[str] = None
    created_at: str = ""
    expires_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proof_id": self.proof_id,
            "type": self.proof_type.value,
            "circuit": self.circuit_type.value,
            "public_inputs_count": len(self.public_inputs),
            "proof_size": len(self.proof_data),
            "created_at": self.created_at,
        }


@dataclass
class VerificationKey:
    """A verification key for proof verification."""
    key_id: str
    proof_type: ProofType
    circuit_type: CircuitType
    key_data: bytes = field(default_factory=bytes)
    created_at: str = ""
    trusted_setup: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key_id": self.key_id,
            "type": self.proof_type.value,
            "circuit": self.circuit_type.value,
            "trusted_setup": self.trusted_setup,
            "created_at": self.created_at,
        }


@dataclass
class VerificationResult:
    """Result of proof verification."""
    proof_id: str
    status: VerificationStatus
    valid: bool = False
    verification_time_ms: float = 0.0
    public_outputs: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proof_id": self.proof_id,
            "status": self.status.value,
            "valid": self.valid,
            "verification_time_ms": round(self.verification_time_ms, 2),
            "errors": self.errors,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# PROOF SYSTEM PROPERTIES
# ═══════════════════════════════════════════════════════════════════════════════

PROOF_SYSTEMS = {
    ProofType.GROTH16: {
        "name": "Groth16",
        "trusted_setup": True,
        "proof_size": 192,  # bytes
        "verification_time": "fast",
        "post_quantum": False,
        "recursive": False,
        "description": "Compact SNARK with trusted setup per circuit",
    },
    ProofType.PLONK: {
        "name": "PLONK",
        "trusted_setup": True,  # Universal, reusable
        "proof_size": 400,
        "verification_time": "medium",
        "post_quantum": False,
        "recursive": True,
        "description": "Universal SNARK with reusable trusted setup",
    },
    ProofType.STARK: {
        "name": "STARK",
        "trusted_setup": False,
        "proof_size": 50000,  # Much larger
        "verification_time": "slow",
        "post_quantum": True,
        "recursive": True,
        "description": "Transparent, scalable, post-quantum secure",
    },
    ProofType.BULLETPROOFS: {
        "name": "Bulletproofs",
        "trusted_setup": False,
        "proof_size": 672,
        "verification_time": "slow",
        "post_quantum": False,
        "recursive": False,
        "description": "Efficient range proofs without trusted setup",
    },
    ProofType.HALO2: {
        "name": "Halo2",
        "trusted_setup": False,
        "proof_size": 2000,
        "verification_time": "medium",
        "post_quantum": False,
        "recursive": True,
        "description": "Recursive proofs without trusted setup",
    },
    ProofType.NOVA: {
        "name": "Nova",
        "trusted_setup": False,
        "proof_size": 1000,
        "verification_time": "fast",
        "post_quantum": False,
        "recursive": True,
        "description": "Folding-based incremental computation",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# ZKP VERIFIER
# ═══════════════════════════════════════════════════════════════════════════════

class ZKPVerifier:
    """
    Zero-Knowledge Proof verifier.

    Verifies various types of zero-knowledge proofs
    for privacy-preserving identity and attribute verification.
    """

    def __init__(self):
        self._verification_keys: Dict[str, VerificationKey] = {}
        self._proof_cache: Dict[str, VerificationResult] = {}
        self._proof_systems = PROOF_SYSTEMS

        # Statistics
        self._stats = {
            "proofs_verified": 0,
            "proofs_valid": 0,
            "proofs_invalid": 0,
            "total_verification_time_ms": 0,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # VERIFICATION
    # ═══════════════════════════════════════════════════════════════════════════

    async def verify(self, proof: ZKProof) -> VerificationResult:
        """
        Verify a zero-knowledge proof.

        Args:
            proof: The proof to verify
        """
        import time
        start_time = time.time()

        self._stats["proofs_verified"] += 1

        # Check cache
        if proof.proof_id in self._proof_cache:
            return self._proof_cache[proof.proof_id]

        result = VerificationResult(
            proof_id=proof.proof_id,
            status=VerificationStatus.VALID,
            valid=True,
        )

        # Check expiration
        if proof.expires_at:
            try:
                expires = datetime.fromisoformat(
                    proof.expires_at.replace("Z", "+00:00")
                )
                if datetime.now(expires.tzinfo) > expires:
                    result.status = VerificationStatus.EXPIRED
                    result.valid = False
                    result.errors.append("Proof expired")
            except (ValueError, TypeError):
                pass

        # Get verification key
        if proof.verification_key_id:
            vk = self._verification_keys.get(proof.verification_key_id)
            if not vk:
                result.status = VerificationStatus.ERROR
                result.valid = False
                result.errors.append("Verification key not found")
        else:
            # Use default key for proof type
            vk = None

        # Verify proof based on type
        if result.valid:
            verification_passed = await self._verify_proof(proof, vk)
            if not verification_passed:
                result.status = VerificationStatus.INVALID
                result.valid = False
                result.errors.append("Proof verification failed")

        # Calculate verification time
        result.verification_time_ms = (time.time() - start_time) * 1000
        self._stats["total_verification_time_ms"] += result.verification_time_ms

        # Update stats
        if result.valid:
            self._stats["proofs_valid"] += 1
        else:
            self._stats["proofs_invalid"] += 1

        # Cache result
        self._proof_cache[proof.proof_id] = result

        return result

    async def _verify_proof(
        self,
        proof: ZKProof,
        verification_key: Optional[VerificationKey],
    ) -> bool:
        """
        Perform actual proof verification.

        In production, this would call into cryptographic libraries
        like snarkjs, bellman, arkworks, etc.
        """
        # Simulate verification based on proof type
        if proof.proof_type == ProofType.GROTH16:
            return self._verify_groth16(proof, verification_key)
        elif proof.proof_type == ProofType.PLONK:
            return self._verify_plonk(proof, verification_key)
        elif proof.proof_type == ProofType.STARK:
            return self._verify_stark(proof, verification_key)
        elif proof.proof_type == ProofType.BULLETPROOFS:
            return self._verify_bulletproofs(proof, verification_key)
        elif proof.proof_type == ProofType.HALO2:
            return self._verify_halo2(proof, verification_key)
        elif proof.proof_type == ProofType.NOVA:
            return self._verify_nova(proof, verification_key)

        return False

    def _verify_groth16(
        self,
        proof: ZKProof,
        vk: Optional[VerificationKey],
    ) -> bool:
        """Verify Groth16 proof."""
        # Simplified verification (in production, use snarkjs/bellman)
        if len(proof.proof_data) < 100:
            return False

        # Check public inputs
        if not proof.public_inputs:
            return False

        # Simulate pairing check
        return True

    def _verify_plonk(
        self,
        proof: ZKProof,
        vk: Optional[VerificationKey],
    ) -> bool:
        """Verify PLONK proof."""
        if len(proof.proof_data) < 200:
            return False
        return True

    def _verify_stark(
        self,
        proof: ZKProof,
        vk: Optional[VerificationKey],
    ) -> bool:
        """Verify STARK proof."""
        if len(proof.proof_data) < 1000:
            return False
        return True

    def _verify_bulletproofs(
        self,
        proof: ZKProof,
        vk: Optional[VerificationKey],
    ) -> bool:
        """Verify Bulletproofs."""
        if len(proof.proof_data) < 500:
            return False
        return True

    def _verify_halo2(
        self,
        proof: ZKProof,
        vk: Optional[VerificationKey],
    ) -> bool:
        """Verify Halo2 proof."""
        if len(proof.proof_data) < 1000:
            return False
        return True

    def _verify_nova(
        self,
        proof: ZKProof,
        vk: Optional[VerificationKey],
    ) -> bool:
        """Verify Nova proof."""
        if len(proof.proof_data) < 500:
            return False
        return True

    # ═══════════════════════════════════════════════════════════════════════════
    # KEY MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    async def register_verification_key(
        self,
        proof_type: ProofType,
        circuit_type: CircuitType,
        key_data: bytes,
        trusted_setup: bool = False,
    ) -> VerificationKey:
        """
        Register a verification key.

        Args:
            proof_type: Type of proof system
            circuit_type: Type of circuit
            key_data: The verification key data
            trusted_setup: Whether from trusted setup
        """
        key_id = f"vk-{secrets.token_hex(8)}"

        vk = VerificationKey(
            key_id=key_id,
            proof_type=proof_type,
            circuit_type=circuit_type,
            key_data=key_data,
            created_at=datetime.utcnow().isoformat() + "Z",
            trusted_setup=trusted_setup,
        )

        self._verification_keys[key_id] = vk
        return vk

    def get_verification_key(self, key_id: str) -> Optional[VerificationKey]:
        """Get a verification key by ID."""
        return self._verification_keys.get(key_id)

    # ═══════════════════════════════════════════════════════════════════════════
    # PROOF CREATION (for testing)
    # ═══════════════════════════════════════════════════════════════════════════

    async def create_test_proof(
        self,
        proof_type: ProofType,
        circuit_type: CircuitType,
        public_inputs: List[str],
    ) -> ZKProof:
        """
        Create a test proof for development.

        Note: This is NOT cryptographically valid.
        """
        # Generate mock proof data
        proof_data = secrets.token_bytes(
            self._proof_systems.get(proof_type, {}).get("proof_size", 1000)
        )

        proof = ZKProof(
            proof_id=f"proof-{secrets.token_hex(8)}",
            proof_type=proof_type,
            circuit_type=circuit_type,
            proof_data=proof_data,
            public_inputs=public_inputs,
            created_at=datetime.utcnow().isoformat() + "Z",
        )

        return proof

    # ═══════════════════════════════════════════════════════════════════════════
    # ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_proof_system_info(self, proof_type: ProofType) -> Dict[str, Any]:
        """Get information about a proof system."""
        return self._proof_systems.get(proof_type, {})

    def compare_proof_systems(
        self,
        types: List[ProofType],
    ) -> Dict[str, Dict[str, Any]]:
        """Compare multiple proof systems."""
        return {
            pt.value: self._proof_systems.get(pt, {})
            for pt in types
            if pt in self._proof_systems
        }

    def recommend_proof_system(
        self,
        post_quantum: bool = False,
        trusted_setup_ok: bool = True,
        proof_size_priority: bool = False,
    ) -> ProofType:
        """
        Recommend a proof system based on requirements.

        Args:
            post_quantum: Require post-quantum security
            trusted_setup_ok: Whether trusted setup is acceptable
            proof_size_priority: Prioritize small proofs
        """
        if post_quantum:
            return ProofType.STARK

        if proof_size_priority and trusted_setup_ok:
            return ProofType.GROTH16

        if not trusted_setup_ok:
            return ProofType.HALO2

        return ProofType.PLONK

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get verifier statistics."""
        avg_time = (
            self._stats["total_verification_time_ms"] /
            self._stats["proofs_verified"]
            if self._stats["proofs_verified"] > 0 else 0
        )

        return {
            **self._stats,
            "average_verification_time_ms": round(avg_time, 2),
            "verification_keys": len(self._verification_keys),
            "cache_size": len(self._proof_cache),
            "success_rate": (
                self._stats["proofs_valid"] /
                self._stats["proofs_verified"]
                if self._stats["proofs_verified"] > 0 else 0
            ),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_verifier_instance: Optional[ZKPVerifier] = None


def get_zkp_verifier() -> ZKPVerifier:
    """Get singleton ZKPVerifier instance."""
    global _verifier_instance

    if _verifier_instance is None:
        _verifier_instance = ZKPVerifier()

    return _verifier_instance
