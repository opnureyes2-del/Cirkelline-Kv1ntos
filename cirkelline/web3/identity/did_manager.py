"""
DID Manager
===========
Decentralized Identifier (W3C DID) management.

Responsibilities:
- Create and manage DIDs
- Resolve DID Documents
- Issue and verify credentials
- Handle DID methods (did:web, did:key, did:ethr)
"""

import logging
import hashlib
import json
import secrets
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class DIDMethod(Enum):
    """Supported DID methods."""
    WEB = "web"         # did:web
    KEY = "key"         # did:key
    ETHR = "ethr"       # did:ethr (Ethereum)
    ION = "ion"         # did:ion (Bitcoin/Sidetree)
    PKH = "pkh"         # did:pkh (blockchain address)
    CIRKELLINE = "cirkelline"  # Custom Cirkelline DID


class KeyType(Enum):
    """Cryptographic key types."""
    ED25519 = "Ed25519VerificationKey2020"
    SECP256K1 = "EcdsaSecp256k1VerificationKey2019"
    RSA = "RsaVerificationKey2018"
    BLS = "Bls12381G2Key2020"


class CredentialStatus(Enum):
    """Credential lifecycle status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass
class VerificationMethod:
    """A verification method in a DID Document."""
    id: str
    method_type: KeyType
    controller: str
    public_key: str
    purposes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.method_type.value,
            "controller": self.controller,
            "publicKeyMultibase": self.public_key[:20] + "...",
        }


@dataclass
class Service:
    """A service endpoint in a DID Document."""
    id: str
    service_type: str
    endpoint: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.service_type,
            "serviceEndpoint": self.endpoint,
        }


@dataclass
class DIDDocument:
    """W3C DID Document."""
    did: str
    method: DIDMethod = DIDMethod.KEY
    controller: Optional[str] = None
    verification_methods: List[VerificationMethod] = field(default_factory=list)
    authentication: List[str] = field(default_factory=list)
    assertion_method: List[str] = field(default_factory=list)
    key_agreement: List[str] = field(default_factory=list)
    services: List[Service] = field(default_factory=list)
    created: str = ""
    updated: str = ""
    deactivated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "@context": [
                "https://www.w3.org/ns/did/v1",
                "https://w3id.org/security/suites/ed25519-2020/v1",
            ],
            "id": self.did,
            "controller": self.controller or self.did,
            "verificationMethod": [vm.to_dict() for vm in self.verification_methods],
            "authentication": self.authentication,
            "assertionMethod": self.assertion_method,
            "service": [s.to_dict() for s in self.services],
            "created": self.created,
            "updated": self.updated,
        }


@dataclass
class CredentialClaim:
    """A claim within a credential."""
    claim_type: str
    value: Any
    evidence: Optional[str] = None


@dataclass
class VerifiableCredential:
    """W3C Verifiable Credential."""
    credential_id: str
    credential_type: List[str] = field(default_factory=list)
    issuer: str = ""
    subject: str = ""
    issuance_date: str = ""
    expiration_date: Optional[str] = None
    claims: Dict[str, Any] = field(default_factory=dict)
    proof: Optional[Dict[str, Any]] = None
    status: CredentialStatus = CredentialStatus.ACTIVE

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
            ],
            "id": self.credential_id,
            "type": ["VerifiableCredential"] + self.credential_type,
            "issuer": self.issuer,
            "credentialSubject": {
                "id": self.subject,
                **self.claims,
            },
            "issuanceDate": self.issuance_date,
        }
        if self.expiration_date:
            result["expirationDate"] = self.expiration_date
        if self.proof:
            result["proof"] = self.proof
        return result


# ═══════════════════════════════════════════════════════════════════════════════
# DID MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class DIDManager:
    """
    Decentralized Identifier manager.

    Handles DID creation, resolution, and credential management
    following W3C DID Core specification.
    """

    def __init__(self):
        self._did_cache: Dict[str, DIDDocument] = {}
        self._credential_cache: Dict[str, VerifiableCredential] = {}
        self._revocation_list: set = set()

        # Statistics
        self._stats = {
            "dids_created": 0,
            "dids_resolved": 0,
            "credentials_issued": 0,
            "credentials_verified": 0,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # DID OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    async def create(
        self,
        method: DIDMethod = DIDMethod.KEY,
        key_type: KeyType = KeyType.ED25519,
        services: Optional[List[Dict[str, str]]] = None,
    ) -> DIDDocument:
        """
        Create a new DID.

        Args:
            method: DID method to use
            key_type: Key type for verification
            services: Optional service endpoints
        """
        self._stats["dids_created"] += 1

        # Generate key material
        key_bytes = secrets.token_bytes(32)
        public_key = hashlib.sha256(key_bytes).hexdigest()

        # Create DID identifier
        if method == DIDMethod.KEY:
            did = f"did:key:z{public_key[:48]}"
        elif method == DIDMethod.WEB:
            did = f"did:web:cirkelline.com:dids:{public_key[:16]}"
        elif method == DIDMethod.ETHR:
            did = f"did:ethr:0x{public_key[:40]}"
        elif method == DIDMethod.CIRKELLINE:
            did = f"did:cirkelline:{public_key[:32]}"
        else:
            did = f"did:{method.value}:{public_key[:32]}"

        # Create verification method
        vm = VerificationMethod(
            id=f"{did}#key-1",
            method_type=key_type,
            controller=did,
            public_key=f"z{public_key}",
            purposes=["authentication", "assertionMethod"],
        )

        # Create DID Document
        now = datetime.utcnow().isoformat() + "Z"
        doc = DIDDocument(
            did=did,
            method=method,
            verification_methods=[vm],
            authentication=[f"{did}#key-1"],
            assertion_method=[f"{did}#key-1"],
            created=now,
            updated=now,
        )

        # Add services
        if services:
            for i, svc in enumerate(services):
                doc.services.append(Service(
                    id=f"{did}#service-{i+1}",
                    service_type=svc.get("type", "LinkedDomains"),
                    endpoint=svc.get("endpoint", ""),
                ))

        # Cache the document
        self._did_cache[did] = doc

        return doc

    async def resolve(self, did: str) -> Optional[DIDDocument]:
        """
        Resolve a DID to its DID Document.

        Args:
            did: DID to resolve
        """
        self._stats["dids_resolved"] += 1

        # Check cache first
        if did in self._did_cache:
            return self._did_cache[did]

        # Parse DID method
        parts = did.split(":")
        if len(parts) < 3:
            logger.warning(f"Invalid DID format: {did}")
            return None

        method_name = parts[1]

        # Resolve based on method
        try:
            method = DIDMethod(method_name)
        except ValueError:
            logger.warning(f"Unsupported DID method: {method_name}")
            return None

        # For now, create a basic document for unknown DIDs
        doc = DIDDocument(
            did=did,
            method=method,
            created=datetime.utcnow().isoformat() + "Z",
            updated=datetime.utcnow().isoformat() + "Z",
        )

        self._did_cache[did] = doc
        return doc

    async def update(
        self,
        did: str,
        updates: Dict[str, Any],
    ) -> Optional[DIDDocument]:
        """
        Update a DID Document.

        Args:
            did: DID to update
            updates: Fields to update
        """
        doc = await self.resolve(did)
        if not doc:
            return None

        # Apply updates
        if "services" in updates:
            for svc in updates["services"]:
                doc.services.append(Service(
                    id=f"{did}#service-{len(doc.services)+1}",
                    service_type=svc.get("type", ""),
                    endpoint=svc.get("endpoint", ""),
                ))

        doc.updated = datetime.utcnow().isoformat() + "Z"
        self._did_cache[did] = doc

        return doc

    async def deactivate(self, did: str) -> bool:
        """
        Deactivate a DID.

        Args:
            did: DID to deactivate
        """
        doc = await self.resolve(did)
        if not doc:
            return False

        doc.deactivated = True
        doc.updated = datetime.utcnow().isoformat() + "Z"
        self._did_cache[did] = doc

        return True

    # ═══════════════════════════════════════════════════════════════════════════
    # CREDENTIAL OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    async def issue_credential(
        self,
        issuer_did: str,
        subject_did: str,
        credential_type: str,
        claims: Dict[str, Any],
        expiration_days: int = 365,
    ) -> VerifiableCredential:
        """
        Issue a Verifiable Credential.

        Args:
            issuer_did: Issuer's DID
            subject_did: Subject's DID
            credential_type: Type of credential
            claims: Credential claims
            expiration_days: Days until expiration
        """
        self._stats["credentials_issued"] += 1

        credential_id = f"urn:uuid:{secrets.token_hex(16)}"
        now = datetime.utcnow()
        expiration = now + timedelta(days=expiration_days)

        # Create proof
        proof_value = hashlib.sha256(
            json.dumps(claims, sort_keys=True).encode()
        ).hexdigest()

        credential = VerifiableCredential(
            credential_id=credential_id,
            credential_type=[credential_type],
            issuer=issuer_did,
            subject=subject_did,
            issuance_date=now.isoformat() + "Z",
            expiration_date=expiration.isoformat() + "Z",
            claims=claims,
            proof={
                "type": "Ed25519Signature2020",
                "created": now.isoformat() + "Z",
                "verificationMethod": f"{issuer_did}#key-1",
                "proofPurpose": "assertionMethod",
                "proofValue": proof_value,
            },
        )

        self._credential_cache[credential_id] = credential
        return credential

    async def verify_credential(
        self,
        credential: VerifiableCredential,
    ) -> Dict[str, Any]:
        """
        Verify a Verifiable Credential.

        Args:
            credential: Credential to verify
        """
        self._stats["credentials_verified"] += 1

        result = {
            "valid": True,
            "checks": [],
            "errors": [],
        }

        # Check expiration
        if credential.expiration_date:
            expiration = datetime.fromisoformat(
                credential.expiration_date.replace("Z", "+00:00")
            )
            if datetime.now(expiration.tzinfo) > expiration:
                result["valid"] = False
                result["errors"].append("Credential expired")
            else:
                result["checks"].append("Expiration: valid")

        # Check revocation
        if credential.credential_id in self._revocation_list:
            result["valid"] = False
            result["errors"].append("Credential revoked")
        else:
            result["checks"].append("Revocation: not revoked")

        # Check issuer
        issuer_doc = await self.resolve(credential.issuer)
        if issuer_doc and not issuer_doc.deactivated:
            result["checks"].append("Issuer: active")
        else:
            result["valid"] = False
            result["errors"].append("Issuer DID invalid or deactivated")

        # Check proof (simplified)
        if credential.proof:
            result["checks"].append("Proof: present")
        else:
            result["valid"] = False
            result["errors"].append("Missing proof")

        return result

    async def revoke_credential(self, credential_id: str) -> bool:
        """
        Revoke a credential.

        Args:
            credential_id: Credential to revoke
        """
        if credential_id in self._credential_cache:
            self._credential_cache[credential_id].status = CredentialStatus.REVOKED
        self._revocation_list.add(credential_id)
        return True

    # ═══════════════════════════════════════════════════════════════════════════
    # PRESENTATION
    # ═══════════════════════════════════════════════════════════════════════════

    async def create_presentation(
        self,
        holder_did: str,
        credentials: List[VerifiableCredential],
        challenge: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a Verifiable Presentation.

        Args:
            holder_did: Holder's DID
            credentials: Credentials to include
            challenge: Optional challenge for the presentation
        """
        presentation_id = f"urn:uuid:{secrets.token_hex(16)}"
        now = datetime.utcnow()

        presentation = {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
            ],
            "id": presentation_id,
            "type": ["VerifiablePresentation"],
            "holder": holder_did,
            "verifiableCredential": [c.to_dict() for c in credentials],
            "proof": {
                "type": "Ed25519Signature2020",
                "created": now.isoformat() + "Z",
                "verificationMethod": f"{holder_did}#key-1",
                "challenge": challenge or secrets.token_hex(16),
                "proofPurpose": "authentication",
            },
        }

        return presentation

    # ═══════════════════════════════════════════════════════════════════════════
    # QUERIES
    # ═══════════════════════════════════════════════════════════════════════════

    def get_supported_methods(self) -> List[str]:
        """Get list of supported DID methods."""
        return [m.value for m in DIDMethod]

    def get_credentials_by_subject(
        self,
        subject_did: str,
    ) -> List[VerifiableCredential]:
        """Get all credentials for a subject."""
        return [
            c for c in self._credential_cache.values()
            if c.subject == subject_did and c.status == CredentialStatus.ACTIVE
        ]

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        return {
            **self._stats,
            "cached_dids": len(self._did_cache),
            "cached_credentials": len(self._credential_cache),
            "revoked_credentials": len(self._revocation_list),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_manager_instance: Optional[DIDManager] = None


def get_did_manager() -> DIDManager:
    """Get singleton DIDManager instance."""
    global _manager_instance

    if _manager_instance is None:
        _manager_instance = DIDManager()

    return _manager_instance
