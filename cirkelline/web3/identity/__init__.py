"""
Identity Module
===============
Decentralized identity and trust layer.

Components:
- DIDManager: Decentralized Identifiers (W3C DID)
- ZKPVerifier: Zero-Knowledge Proof verification
- TrustLayer: Machine-to-machine trust
"""

from cirkelline.web3.identity.did_manager import (
    DIDManager,
    DIDDocument,
    VerifiableCredential,
    VerificationMethod,
    get_did_manager,
)

from cirkelline.web3.identity.zkp_verifier import (
    ZKPVerifier,
    ZKProof,
    ProofType,
    VerificationResult,
    get_zkp_verifier,
)

from cirkelline.web3.identity.trust_layer import (
    TrustLayer,
    TrustScore,
    TrustRelation,
    get_trust_layer,
)

from typing import Optional, Dict, Any
from dataclasses import dataclass


__all__ = [
    # DID
    'DIDManager',
    'DIDDocument',
    'VerifiableCredential',
    'VerificationMethod',
    'get_did_manager',
    # ZKP
    'ZKPVerifier',
    'ZKProof',
    'ProofType',
    'VerificationResult',
    'get_zkp_verifier',
    # Trust
    'TrustLayer',
    'TrustScore',
    'TrustRelation',
    'get_trust_layer',
    # Manager
    'IdentityManager',
    'get_identity_manager',
]


# ═══════════════════════════════════════════════════════════════════════════════
# IDENTITY MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class IdentityManager:
    """
    Unified identity management.

    Coordinates DID operations, ZKP verification,
    and trust calculations.
    """

    def __init__(self):
        self._did = get_did_manager()
        self._zkp = get_zkp_verifier()
        self._trust = get_trust_layer()

    @property
    def did(self) -> DIDManager:
        return self._did

    @property
    def zkp(self) -> ZKPVerifier:
        return self._zkp

    @property
    def trust(self) -> TrustLayer:
        return self._trust

    async def verify_identity(
        self,
        did: str,
        proof: Optional[ZKProof] = None,
    ) -> Dict[str, Any]:
        """
        Verify an identity with optional ZKP.

        Args:
            did: Decentralized Identifier
            proof: Optional zero-knowledge proof
        """
        result = {
            "did": did,
            "did_valid": False,
            "proof_valid": None,
            "trust_score": 0.0,
            "verified": False,
        }

        # Resolve DID
        doc = await self._did.resolve(did)
        result["did_valid"] = doc is not None

        # Verify proof if provided
        if proof:
            verification = await self._zkp.verify(proof)
            result["proof_valid"] = verification.valid

        # Calculate trust
        trust_score = await self._trust.calculate_trust(did)
        result["trust_score"] = trust_score.score

        # Overall verification
        result["verified"] = (
            result["did_valid"] and
            (result["proof_valid"] is None or result["proof_valid"]) and
            result["trust_score"] > 0.3
        )

        return result

    async def issue_credential(
        self,
        issuer_did: str,
        subject_did: str,
        credential_type: str,
        claims: Dict[str, Any],
    ) -> Optional[VerifiableCredential]:
        """
        Issue a verifiable credential.

        Args:
            issuer_did: Issuer's DID
            subject_did: Subject's DID
            credential_type: Type of credential
            claims: Credential claims
        """
        return await self._did.issue_credential(
            issuer_did=issuer_did,
            subject_did=subject_did,
            credential_type=credential_type,
            claims=claims,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        return {
            "did": self._did.get_stats(),
            "zkp": self._zkp.get_stats(),
            "trust": self._trust.get_stats(),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_manager_instance: Optional[IdentityManager] = None


def get_identity_manager() -> IdentityManager:
    """Get singleton IdentityManager."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = IdentityManager()
    return _manager_instance
