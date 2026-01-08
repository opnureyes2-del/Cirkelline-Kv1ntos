"""
CKC Folder Context - Data Models & Enums
=========================================

Datamodeller til CKC Folder Switcher systemet.
Giver Super Admin mulighed for at skifte mellem alle CKC mapper.

Version: v1.3.5
Oprettet: 2025-12-16
Agent: Kommandør #4
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import uuid


# ============================================================================
# ENUMS
# ============================================================================

class FolderCategory(Enum):
    """
    Kategorier af CKC mapper.

    - CKC_COMPONENTS: Frozen komponenter (6 stk)
    - CIRKELLINE_CKC: Aktive subfolders i cirkelline/ckc (9 stk)
    - CUSTOM: Brugerdefinerede mapper
    """
    CKC_COMPONENTS = "ckc_components"    # Frozen (6): legal-kommandant, web3-kommandant, research-team, law-team, mastermind, kv1nt
    CIRKELLINE_CKC = "cirkelline_ckc"    # Active (9): mastermind, tegne_enhed, kommandant, infrastructure, integrations, web3, connectors, api, aws
    CUSTOM = "custom"                     # User-defined folders


class FolderStatus(Enum):
    """
    Status for en CKC folder.

    - ACTIVE: Folder er aktiv og kan modificeres
    - FROZEN: Folder er låst (kun læsning)
    - DEVELOPMENT: Folder er under udvikling
    """
    ACTIVE = "active"
    FROZEN = "frozen"
    DEVELOPMENT = "development"


class SwitchMethod(Enum):
    """
    Metode brugt til at skifte folder.

    - DROPDOWN: Via UI dropdown i Dashboard
    - SIDEBAR: Via sidebar træ-visning
    - TERMINAL: Via KV1NT terminal kommando
    - API: Via direkte API kald
    """
    DROPDOWN = "dropdown"
    SIDEBAR = "sidebar"
    TERMINAL = "terminal"
    API = "api"


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class CKCFolderInfo:
    """
    Information om en CKC folder.

    Attributes:
        folder_id: Unik identifikator (f.eks. "mastermind", "legal-kommandant")
        name: Intern navn
        display_name: Visningsnavn til UI
        path: Fuld sti til mappen
        category: FolderCategory enum
        status: FolderStatus enum
        frozen: Om mappen er frozen (read-only)
        components_count: Antal komponenter i mappen
        files_count: Antal filer i mappen
        python_files_count: Antal Python filer
        metadata: Ekstra metadata fra manifest.json etc.
        description: Beskrivelse af mappen
        version: Version hvis tilgængelig
        last_modified: Seneste ændring
    """
    folder_id: str
    name: str
    display_name: str
    path: Path
    category: FolderCategory
    status: FolderStatus
    frozen: bool = False
    components_count: int = 0
    files_count: int = 0
    python_files_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    version: str = ""
    last_modified: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konverter til dictionary for JSON serialisering."""
        return {
            "folder_id": self.folder_id,
            "name": self.name,
            "display_name": self.display_name,
            "path": str(self.path),
            "category": self.category.value,
            "status": self.status.value,
            "frozen": self.frozen,
            "components_count": self.components_count,
            "files_count": self.files_count,
            "python_files_count": self.python_files_count,
            "metadata": self.metadata,
            "description": self.description,
            "version": self.version,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CKCFolderInfo":
        """Opret fra dictionary."""
        return cls(
            folder_id=data["folder_id"],
            name=data["name"],
            display_name=data["display_name"],
            path=Path(data["path"]),
            category=FolderCategory(data["category"]),
            status=FolderStatus(data["status"]),
            frozen=data.get("frozen", False),
            components_count=data.get("components_count", 0),
            files_count=data.get("files_count", 0),
            python_files_count=data.get("python_files_count", 0),
            metadata=data.get("metadata", {}),
            description=data.get("description", ""),
            version=data.get("version", ""),
            last_modified=datetime.fromisoformat(data["last_modified"]) if data.get("last_modified") else None
        )


@dataclass
class FolderSwitchEvent:
    """
    Event der repræsenterer et folder-skift.

    Attributes:
        event_id: Unik event ID
        user_id: Bruger der skiftede
        from_folder: Tidligere folder (None hvis første gang)
        to_folder: Ny folder
        switch_method: Hvordan skiftet skete
        timestamp: Tidspunkt for skift
        success: Om skiftet lykkedes
        error_message: Fejlbesked hvis ikke success
        duration_ms: Hvor lang tid skiftet tog
    """
    event_id: str
    user_id: str
    from_folder: Optional[str]
    to_folder: str
    switch_method: SwitchMethod
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    duration_ms: float = 0.0

    @classmethod
    def create(
        cls,
        user_id: str,
        from_folder: Optional[str],
        to_folder: str,
        method: SwitchMethod,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> "FolderSwitchEvent":
        """Factory metode til at oprette event."""
        return cls(
            event_id=str(uuid.uuid4()),
            user_id=user_id,
            from_folder=from_folder,
            to_folder=to_folder,
            switch_method=method,
            timestamp=datetime.now(timezone.utc),
            success=success,
            error_message=error_message
        )

    def to_dict(self) -> Dict[str, Any]:
        """Konverter til dictionary for JSON serialisering."""
        return {
            "event_id": self.event_id,
            "user_id": self.user_id,
            "from_folder": self.from_folder,
            "to_folder": self.to_folder,
            "switch_method": self.switch_method.value,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms
        }


@dataclass
class FolderContextState:
    """
    Fuld tilstand for en brugers folder-kontekst.

    Attributes:
        user_id: Bruger ID
        current_folder_id: ID på nuværende folder (None hvis ingen valgt)
        current_folder: CKCFolderInfo for nuværende folder
        recent_folders: Liste af senest besøgte folders (max 5)
        favorite_folders: Set af favorit folder IDs
        custom_folders: Liste af custom folder stier
        last_switch: Tidspunkt for seneste skift
        switch_count: Antal skift i denne session
    """
    user_id: str
    current_folder_id: Optional[str] = None
    current_folder: Optional[CKCFolderInfo] = None
    recent_folders: List[str] = field(default_factory=list)
    favorite_folders: Set[str] = field(default_factory=set)
    custom_folders: List[str] = field(default_factory=list)
    last_switch: Optional[datetime] = None
    switch_count: int = 0

    def add_to_recent(self, folder_id: str) -> None:
        """Tilføj folder til recent liste (max 5, ingen dubletter)."""
        if folder_id in self.recent_folders:
            self.recent_folders.remove(folder_id)
        self.recent_folders.insert(0, folder_id)
        self.recent_folders = self.recent_folders[:5]

    def toggle_favorite(self, folder_id: str) -> bool:
        """Toggle favorite status. Returner True hvis tilføjet, False hvis fjernet."""
        if folder_id in self.favorite_folders:
            self.favorite_folders.discard(folder_id)
            return False
        else:
            self.favorite_folders.add(folder_id)
            return True

    def to_dict(self) -> Dict[str, Any]:
        """Konverter til dictionary for JSON serialisering."""
        return {
            "user_id": self.user_id,
            "current_folder_id": self.current_folder_id,
            "current_folder": self.current_folder.to_dict() if self.current_folder else None,
            "recent_folders": self.recent_folders,
            "favorite_folders": list(self.favorite_folders),
            "custom_folders": self.custom_folders,
            "last_switch": self.last_switch.isoformat() if self.last_switch else None,
            "switch_count": self.switch_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FolderContextState":
        """Opret fra dictionary."""
        state = cls(
            user_id=data["user_id"],
            current_folder_id=data.get("current_folder_id"),
            recent_folders=data.get("recent_folders", []),
            favorite_folders=set(data.get("favorite_folders", [])),
            custom_folders=data.get("custom_folders", []),
            last_switch=datetime.fromisoformat(data["last_switch"]) if data.get("last_switch") else None,
            switch_count=data.get("switch_count", 0)
        )
        # current_folder skal loades separat da det kræver folder registry
        return state


# ============================================================================
# CONSTANTS - CKC FOLDER DEFINITIONS
# ============================================================================

# CKC-COMPONENTS (6 frozen komponenter)
CKC_COMPONENTS_FOLDERS = {
    "legal-kommandant": {
        "display_name": "Legal Kommandant",
        "category": "kommandanter",
        "description": "Juridisk specialist kommandant",
        "frozen": True
    },
    "web3-kommandant": {
        "display_name": "Web3 Kommandant",
        "category": "kommandanter",
        "description": "Web3/Blockchain specialist kommandant",
        "frozen": True
    },
    "research-team": {
        "display_name": "Research Team",
        "category": "teams",
        "description": "Research og analyse team",
        "frozen": True
    },
    "law-team": {
        "display_name": "Law Team",
        "category": "teams",
        "description": "Juridisk team",
        "frozen": True
    },
    "mastermind": {
        "display_name": "Mastermind",
        "category": "systems",
        "description": "Mastermind strategisk system",
        "frozen": True
    },
    "kv1nt": {
        "display_name": "KV1NT",
        "category": "systems",
        "description": "KV1NT terminal partner system",
        "frozen": True
    }
}

# cirkelline/ckc subfolders (9 aktive mapper)
CIRKELLINE_CKC_FOLDERS = {
    "mastermind": {
        "display_name": "Mastermind",
        "description": "Mastermind orchestration og kontrol",
        "frozen": False
    },
    "tegne_enhed": {
        "display_name": "Tegne Enhed",
        "description": "Visuel output generation",
        "frozen": False
    },
    "kommandant": {
        "display_name": "Kommandant",
        "description": "Kommandant base system",
        "frozen": False
    },
    "infrastructure": {
        "display_name": "Infrastructure",
        "description": "Infrastruktur komponenter",
        "frozen": False
    },
    "integrations": {
        "display_name": "Integrations",
        "description": "Eksterne integrationer",
        "frozen": False
    },
    "web3": {
        "display_name": "Web3",
        "description": "Web3/Blockchain moduler",
        "frozen": False
    },
    "connectors": {
        "display_name": "Connectors",
        "description": "System connectors",
        "frozen": False
    },
    "api": {
        "display_name": "API",
        "description": "API endpoints og routes",
        "frozen": False
    },
    "aws": {
        "display_name": "AWS",
        "description": "AWS cloud integration",
        "frozen": False
    }
}


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "FolderCategory",
    "FolderStatus",
    "SwitchMethod",
    # Dataclasses
    "CKCFolderInfo",
    "FolderSwitchEvent",
    "FolderContextState",
    # Constants
    "CKC_COMPONENTS_FOLDERS",
    "CIRKELLINE_CKC_FOLDERS"
]
