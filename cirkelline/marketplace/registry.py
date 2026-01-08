"""
API Registry
============

FASE 6: API Marketplace

Central registrering og versionering af API'er.

Features:
    - Semantisk versionering (semver)
    - API discovery og katalog
    - Deprecation tracking
    - Endpoint dokumentation
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid


class APIStatus(Enum):
    """API livscyklus status."""
    DRAFT = "draft"           # Under udvikling
    BETA = "beta"             # Beta test
    ACTIVE = "active"         # Produktions-klar
    DEPRECATED = "deprecated"  # Udgået men stadig tilgængelig
    RETIRED = "retired"       # Fjernet


class HTTPMethod(Enum):
    """HTTP metoder."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


@dataclass
class APIEndpoint:
    """
    En API endpoint definition.

    Attributes:
        path: URL sti (fx /api/v1/research)
        method: HTTP metode
        description: Kort beskrivelse
        parameters: Query/path parametre
        request_body: Request body schema
        response: Response schema
        rate_limit: Endpoint-specifik rate limit
    """
    path: str
    method: HTTPMethod
    description: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    response: Optional[Dict[str, Any]] = None
    rate_limit: Optional[int] = None  # Requests per minute
    requires_auth: bool = True
    scopes: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class APIVersion:
    """
    En specifik version af en API.

    Attributes:
        version: Semver version (fx 1.0.0)
        status: Livscyklus status
        endpoints: Liste af endpoints
        changelog: Ændringslog
        released_at: Frigivelsestidspunkt
        deprecated_at: Tidspunkt for deprecation
        sunset_at: Tidspunkt hvor API fjernes helt
    """
    version: str
    status: APIStatus
    endpoints: List[APIEndpoint] = field(default_factory=list)
    changelog: str = ""
    released_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None
    sunset_at: Optional[datetime] = None
    breaking_changes: bool = False
    min_supported_client: Optional[str] = None

    @property
    def is_available(self) -> bool:
        """Tjek om versionen er tilgængelig."""
        return self.status in (APIStatus.BETA, APIStatus.ACTIVE, APIStatus.DEPRECATED)

    @property
    def major(self) -> int:
        """Hent major version number."""
        parts = self.version.split(".")
        return int(parts[0]) if parts else 0

    @property
    def minor(self) -> int:
        """Hent minor version number."""
        parts = self.version.split(".")
        return int(parts[1]) if len(parts) > 1 else 0

    @property
    def patch(self) -> int:
        """Hent patch version number."""
        parts = self.version.split(".")
        return int(parts[2]) if len(parts) > 2 else 0


@dataclass
class APIDefinition:
    """
    Komplet API definition.

    Attributes:
        id: Unik identifikator
        name: API navn (fx web3-research)
        display_name: Human-readable navn
        description: Fuld beskrivelse
        category: Kategori (research, training, etc.)
        versions: Liste af versioner
        default_rate_limit: Default rate limit
        base_path: Base URL sti
    """
    name: str
    display_name: str
    description: str
    category: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    versions: List[APIVersion] = field(default_factory=list)
    default_rate_limit: int = 100  # Requests per minute
    base_path: str = "/api"
    owner: Optional[str] = None
    documentation_url: Optional[str] = None
    support_email: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_latest_version(self) -> Optional[APIVersion]:
        """Hent den seneste aktive version."""
        active = [v for v in self.versions if v.status == APIStatus.ACTIVE]
        if not active:
            active = [v for v in self.versions if v.is_available]
        if not active:
            return None
        return max(active, key=lambda v: (v.major, v.minor, v.patch))

    def get_version(self, version: str) -> Optional[APIVersion]:
        """Hent specifik version."""
        for v in self.versions:
            if v.version == version:
                return v
        return None

    def add_version(self, version: APIVersion) -> None:
        """Tilføj en ny version."""
        self.versions.append(version)
        self.updated_at = datetime.utcnow()


class APIRegistry:
    """
    Central registry for API'er.

    Singleton der holder styr på alle registrerede API'er
    og deres versioner.

    Eksempel:
        registry = APIRegistry()

        # Registrer API
        api = APIDefinition(
            name="web3-research",
            display_name="Web3 Research API",
            description="Research API for Web3 and blockchain",
            category="research"
        )
        registry.register(api)

        # Hent API
        api = registry.get("web3-research")
    """

    _instance: Optional["APIRegistry"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._apis: Dict[str, APIDefinition] = {}
            cls._instance._by_category: Dict[str, List[str]] = {}
        return cls._instance

    def register(self, api: APIDefinition) -> None:
        """
        Registrer en API.

        Args:
            api: API definition
        """
        self._apis[api.name] = api

        # Opdater kategori-index
        if api.category not in self._by_category:
            self._by_category[api.category] = []
        if api.name not in self._by_category[api.category]:
            self._by_category[api.category].append(api.name)

    def unregister(self, name: str) -> bool:
        """
        Fjern en API fra registret.

        Args:
            name: API navn

        Returns:
            True hvis fjernet
        """
        if name not in self._apis:
            return False

        api = self._apis[name]
        if api.category in self._by_category:
            self._by_category[api.category].remove(name)

        del self._apis[name]
        return True

    def get(self, name: str) -> Optional[APIDefinition]:
        """
        Hent API by name.

        Args:
            name: API navn

        Returns:
            APIDefinition eller None
        """
        return self._apis.get(name)

    def list_all(self) -> List[APIDefinition]:
        """List alle API'er."""
        return list(self._apis.values())

    def list_by_category(self, category: str) -> List[APIDefinition]:
        """
        List API'er i en kategori.

        Args:
            category: Kategori navn

        Returns:
            Liste af API'er
        """
        names = self._by_category.get(category, [])
        return [self._apis[name] for name in names if name in self._apis]

    def get_categories(self) -> List[str]:
        """List alle kategorier."""
        return list(self._by_category.keys())

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        status: Optional[APIStatus] = None
    ) -> List[APIDefinition]:
        """
        Søg i API registret.

        Args:
            query: Søgetekst
            category: Filtrer på kategori
            status: Filtrer på status

        Returns:
            Liste af matchende API'er
        """
        results = []
        query_lower = query.lower()

        for api in self._apis.values():
            # Kategori filter
            if category and api.category != category:
                continue

            # Status filter
            if status:
                latest = api.get_latest_version()
                if not latest or latest.status != status:
                    continue

            # Søg i navn og beskrivelse
            if (query_lower in api.name.lower() or
                query_lower in api.display_name.lower() or
                query_lower in api.description.lower() or
                any(query_lower in tag.lower() for tag in api.tags)):
                results.append(api)

        return results

    def to_openapi(self, api_name: str) -> Dict[str, Any]:
        """
        Generer OpenAPI spec for en API.

        Args:
            api_name: API navn

        Returns:
            OpenAPI specification dict
        """
        api = self.get(api_name)
        if not api:
            return {}

        version = api.get_latest_version()
        if not version:
            return {}

        spec = {
            "openapi": "3.0.3",
            "info": {
                "title": api.display_name,
                "description": api.description,
                "version": version.version,
                "contact": {
                    "email": api.support_email
                } if api.support_email else {}
            },
            "servers": [
                {"url": f"{api.base_path}/v{version.major}"}
            ],
            "paths": {},
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                }
            }
        }

        # Tilføj endpoints
        for endpoint in version.endpoints:
            path = endpoint.path
            if path not in spec["paths"]:
                spec["paths"][path] = {}

            method_spec = {
                "summary": endpoint.description,
                "tags": endpoint.tags,
                "parameters": endpoint.parameters,
                "responses": {
                    "200": {
                        "description": "Success",
                        "content": {
                            "application/json": {
                                "schema": endpoint.response or {}
                            }
                        }
                    }
                }
            }

            if endpoint.requires_auth:
                method_spec["security"] = [{"bearerAuth": []}]

            if endpoint.request_body:
                method_spec["requestBody"] = {
                    "content": {
                        "application/json": {
                            "schema": endpoint.request_body
                        }
                    }
                }

            spec["paths"][path][endpoint.method.value.lower()] = method_spec

        return spec


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

_registry: Optional[APIRegistry] = None


def get_registry() -> APIRegistry:
    """Hent singleton registry."""
    global _registry
    if _registry is None:
        _registry = APIRegistry()
    return _registry


def register_api(
    name: str,
    display_name: str,
    description: str,
    category: str,
    version: str = "1.0.0",
    endpoints: Optional[List[Dict[str, Any]]] = None,
    rate_limit: int = 100,
    **kwargs
) -> APIDefinition:
    """
    Convenience function til at registrere en API.

    Args:
        name: API navn
        display_name: Human-readable navn
        description: Beskrivelse
        category: Kategori
        version: Initial version
        endpoints: Liste af endpoint dicts
        rate_limit: Default rate limit
        **kwargs: Yderligere API attributter

    Returns:
        Den registrerede APIDefinition
    """
    api = APIDefinition(
        name=name,
        display_name=display_name,
        description=description,
        category=category,
        default_rate_limit=rate_limit,
        **kwargs
    )

    # Tilføj initial version
    api_version = APIVersion(
        version=version,
        status=APIStatus.ACTIVE,
        released_at=datetime.utcnow()
    )

    # Konverter endpoint dicts til APIEndpoint
    if endpoints:
        for ep_dict in endpoints:
            method = ep_dict.get("method", "GET")
            if isinstance(method, str):
                method = HTTPMethod(method.upper())

            endpoint = APIEndpoint(
                path=ep_dict.get("path", "/"),
                method=method,
                description=ep_dict.get("description", ""),
                parameters=ep_dict.get("parameters", []),
                request_body=ep_dict.get("request_body"),
                response=ep_dict.get("response"),
                rate_limit=ep_dict.get("rate_limit"),
                requires_auth=ep_dict.get("requires_auth", True),
                tags=ep_dict.get("tags", [])
            )
            api_version.endpoints.append(endpoint)

    api.add_version(api_version)

    # Registrer
    get_registry().register(api)
    return api


def get_api(name: str) -> Optional[APIDefinition]:
    """Hent API by name."""
    return get_registry().get(name)


def list_apis(category: Optional[str] = None) -> List[APIDefinition]:
    """List API'er, optionalt filtreret på kategori."""
    registry = get_registry()
    if category:
        return registry.list_by_category(category)
    return registry.list_all()
