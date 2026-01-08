"""
CKC Folder Switcher - Core Logic
=================================

Hovedlogik til at skifte mellem CKC mapper.
Giver Super Admin mulighed for at navigere mellem alle CKC kontekster.

Features:
- Scan CKC-COMPONENTS (6 frozen)
- Scan cirkelline/ckc subfolders (9 aktive)
- Custom folder support
- State persistence til ~/.ckc/folder_preferences.json
- Event broadcasting

Version: v1.3.5
Oprettet: 2025-12-16
Agent: Kommandør #4
"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from .folder_context import (
    CKCFolderInfo,
    FolderCategory,
    FolderContextState,
    FolderStatus,
    FolderSwitchEvent,
    SwitchMethod,
    CKC_COMPONENTS_FOLDERS,
    CIRKELLINE_CKC_FOLDERS
)

logger = logging.getLogger(__name__)


# ============================================================================
# CKC FOLDER SWITCHER CLASS
# ============================================================================

class CKCFolderSwitcher:
    """
    Håndterer skift mellem CKC mapper for Super Admin.

    Understøtter tre switch-metoder:
    - Dropdown (UI)
    - Sidebar (træ-visning)
    - Terminal (KV1NT kommandoer)

    Attributes:
        _user_id: Super Admin bruger ID
        _state: FolderContextState med nuværende kontekst
        _folders: Registry af alle kendte folders
        _event_handlers: Callbacks for folder events
    """

    # Default stier
    CKC_COMPONENTS_BASE = Path("/home/rasmus/Desktop/projekts/projects/cirkelline-system/CKC-COMPONENTS")
    CIRKELLINE_CKC_BASE = Path("/home/rasmus/Desktop/projekts/projects/cirkelline-system/cirkelline/ckc")
    PREFERENCES_DIR = Path.home() / ".ckc"
    PREFERENCES_FILE = "folder_preferences.json"

    def __init__(self, user_id: str = "rasmus_super_admin"):
        """
        Initialiser folder switcher.

        Args:
            user_id: Bruger ID (default: rasmus_super_admin)
        """
        self._user_id = user_id
        self._folders: Dict[str, CKCFolderInfo] = {}
        self._state: FolderContextState = FolderContextState(user_id=user_id)
        self._event_handlers: List[Callable[[str, Dict[str, Any]], None]] = []
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialiser folder switcher.
        Loader state og scanner alle folders.
        """
        if self._initialized:
            return

        logger.info(f"Initialiserer CKCFolderSwitcher for {self._user_id}")

        # Scan alle folders
        self._scan_all_folders()

        # Load saved state
        await self.load_state()

        # Restore current_folder reference
        if self._state.current_folder_id:
            self._state.current_folder = self._folders.get(self._state.current_folder_id)

        self._initialized = True
        logger.info(f"CKCFolderSwitcher initialiseret: {len(self._folders)} folders fundet")

    def _scan_all_folders(self) -> None:
        """Scan alle CKC folders."""
        self._folders.clear()

        # Scan CKC-COMPONENTS
        ckc_components = self.scan_ckc_components()
        for folder in ckc_components:
            self._folders[folder.folder_id] = folder

        # Scan cirkelline/ckc
        cirkelline_ckc = self.scan_cirkelline_ckc()
        for folder in cirkelline_ckc:
            self._folders[folder.folder_id] = folder

        # Scan custom folders fra state
        for custom_path in self._state.custom_folders:
            folder = self._scan_custom_folder(custom_path)
            if folder:
                self._folders[folder.folder_id] = folder

    def scan_ckc_components(self) -> List[CKCFolderInfo]:
        """
        Scan CKC-COMPONENTS mappen for frozen komponenter.

        Returns:
            Liste af CKCFolderInfo for hver komponent
        """
        folders = []

        for folder_id, config in CKC_COMPONENTS_FOLDERS.items():
            # Bestem kategori-sti
            category = config.get("category", "systems")
            folder_path = self.CKC_COMPONENTS_BASE / category / folder_id

            if not folder_path.exists():
                logger.warning(f"CKC-COMPONENTS folder ikke fundet: {folder_path}")
                continue

            # Tæl filer
            files = list(folder_path.rglob("*"))
            py_files = list(folder_path.rglob("*.py"))

            # Check for manifest
            manifest_path = folder_path / "manifest.json"
            metadata = {}
            version = "1.0.0"
            if manifest_path.exists():
                try:
                    with open(manifest_path, 'r') as f:
                        metadata = json.load(f)
                        version = metadata.get("version", "1.0.0")
                except Exception as e:
                    logger.warning(f"Kunne ikke læse manifest: {e}")

            folder_info = CKCFolderInfo(
                folder_id=f"ckc-{folder_id}",  # Prefix for at undgå konflikt med cirkelline/ckc
                name=folder_id,
                display_name=config.get("display_name", folder_id),
                path=folder_path,
                category=FolderCategory.CKC_COMPONENTS,
                status=FolderStatus.FROZEN if config.get("frozen", True) else FolderStatus.ACTIVE,
                frozen=config.get("frozen", True),
                files_count=len(files),
                python_files_count=len(py_files),
                metadata=metadata,
                description=config.get("description", ""),
                version=version
            )
            folders.append(folder_info)

        logger.info(f"Scannede {len(folders)} CKC-COMPONENTS folders")
        return folders

    def scan_cirkelline_ckc(self) -> List[CKCFolderInfo]:
        """
        Scan cirkelline/ckc subfolders for aktive moduler.

        Returns:
            Liste af CKCFolderInfo for hver subfolder
        """
        folders = []

        for folder_id, config in CIRKELLINE_CKC_FOLDERS.items():
            folder_path = self.CIRKELLINE_CKC_BASE / folder_id

            if not folder_path.exists():
                logger.warning(f"cirkelline/ckc folder ikke fundet: {folder_path}")
                continue

            # Tæl filer
            files = list(folder_path.rglob("*"))
            py_files = list(folder_path.rglob("*.py"))

            # Check for __init__.py version
            version = ""
            init_path = folder_path / "__init__.py"
            if init_path.exists():
                try:
                    with open(init_path, 'r') as f:
                        content = f.read()
                        for line in content.split('\n'):
                            if '__version__' in line:
                                version = line.split('=')[1].strip().strip('"\'')
                                break
                except Exception as e:
                    logger.warning(f"Kunne ikke læse __init__.py: {e}")

            folder_info = CKCFolderInfo(
                folder_id=folder_id,
                name=folder_id,
                display_name=config.get("display_name", folder_id.replace("_", " ").title()),
                path=folder_path,
                category=FolderCategory.CIRKELLINE_CKC,
                status=FolderStatus.ACTIVE,
                frozen=False,
                files_count=len(files),
                python_files_count=len(py_files),
                description=config.get("description", ""),
                version=version
            )
            folders.append(folder_info)

        logger.info(f"Scannede {len(folders)} cirkelline/ckc folders")
        return folders

    def _scan_custom_folder(self, folder_path_str: str) -> Optional[CKCFolderInfo]:
        """
        Scan en custom folder.

        Args:
            folder_path_str: Sti til custom folder

        Returns:
            CKCFolderInfo eller None hvis ikke fundet
        """
        folder_path = Path(folder_path_str)

        if not folder_path.exists():
            logger.warning(f"Custom folder ikke fundet: {folder_path}")
            return None

        # Tæl filer
        files = list(folder_path.rglob("*"))
        py_files = list(folder_path.rglob("*.py"))

        # Generer ID fra sti
        folder_id = f"custom-{folder_path.name}"

        return CKCFolderInfo(
            folder_id=folder_id,
            name=folder_path.name,
            display_name=folder_path.name.replace("_", " ").replace("-", " ").title(),
            path=folder_path,
            category=FolderCategory.CUSTOM,
            status=FolderStatus.ACTIVE,
            frozen=False,
            files_count=len(files),
            python_files_count=len(py_files),
            description=f"Custom folder: {folder_path}"
        )

    async def switch_folder(
        self,
        folder_id: str,
        method: str = "api"
    ) -> FolderSwitchEvent:
        """
        Skift til en anden CKC folder.

        Args:
            folder_id: ID på folder der skal skiftes til
            method: Switch metode ("dropdown", "sidebar", "terminal", "api")

        Returns:
            FolderSwitchEvent med resultat
        """
        start_time = time.time()

        # Konverter method string til enum
        try:
            switch_method = SwitchMethod(method)
        except ValueError:
            switch_method = SwitchMethod.API

        # Gem tidligere folder
        from_folder = self._state.current_folder_id

        # Valider folder eksisterer
        if folder_id not in self._folders:
            event = FolderSwitchEvent.create(
                user_id=self._user_id,
                from_folder=from_folder,
                to_folder=folder_id,
                method=switch_method,
                success=False,
                error_message=f"Folder ikke fundet: {folder_id}"
            )
            await self._broadcast_event("folder.switch_failed", event.to_dict())
            return event

        # Hent folder info
        folder = self._folders[folder_id]

        # Opdater state
        self._state.current_folder_id = folder_id
        self._state.current_folder = folder
        self._state.last_switch = datetime.now(timezone.utc)
        self._state.switch_count += 1
        self._state.add_to_recent(folder_id)

        # Beregn duration
        duration_ms = (time.time() - start_time) * 1000

        # Opret event
        event = FolderSwitchEvent.create(
            user_id=self._user_id,
            from_folder=from_folder,
            to_folder=folder_id,
            method=switch_method,
            success=True
        )
        event.duration_ms = duration_ms

        # Gem state
        await self.save_state()

        # Broadcast event
        await self._broadcast_event("folder.switched", {
            **event.to_dict(),
            "folder_info": folder.to_dict()
        })

        logger.info(f"Skiftede folder: {from_folder} → {folder_id} via {method} ({duration_ms:.1f}ms)")
        return event

    async def get_current_context(self) -> FolderContextState:
        """
        Hent nuværende folder kontekst.

        Returns:
            FolderContextState med nuværende tilstand
        """
        return self._state

    async def list_folders(
        self,
        category: Optional[FolderCategory] = None
    ) -> List[CKCFolderInfo]:
        """
        List alle folders, eventuelt filtreret på kategori.

        Args:
            category: Optional kategori at filtrere på

        Returns:
            Liste af CKCFolderInfo
        """
        folders = list(self._folders.values())

        if category:
            folders = [f for f in folders if f.category == category]

        # Sorter: favorites først, så efter display_name
        favorites = self._state.favorite_folders

        def sort_key(f: CKCFolderInfo) -> tuple:
            is_favorite = f.folder_id in favorites
            return (not is_favorite, f.category.value, f.display_name.lower())

        return sorted(folders, key=sort_key)

    async def get_folder_info(self, folder_id: str) -> Optional[CKCFolderInfo]:
        """
        Hent information om en specifik folder.

        Args:
            folder_id: Folder ID

        Returns:
            CKCFolderInfo eller None
        """
        return self._folders.get(folder_id)

    async def get_folder_contents(self, folder_id: str) -> Dict[str, Any]:
        """
        Hent indholdet af en folder.

        Args:
            folder_id: Folder ID

        Returns:
            Dict med folder indhold (filer, subfolders, etc.)
        """
        folder = self._folders.get(folder_id)
        if not folder:
            return {"error": f"Folder ikke fundet: {folder_id}"}

        path = folder.path
        contents = {
            "folder_id": folder_id,
            "path": str(path),
            "subfolders": [],
            "python_files": [],
            "other_files": [],
            "total_files": 0
        }

        if not path.exists():
            contents["error"] = "Folder sti eksisterer ikke"
            return contents

        try:
            for item in path.iterdir():
                if item.is_dir():
                    contents["subfolders"].append({
                        "name": item.name,
                        "path": str(item)
                    })
                elif item.suffix == ".py":
                    contents["python_files"].append({
                        "name": item.name,
                        "path": str(item),
                        "size": item.stat().st_size
                    })
                else:
                    contents["other_files"].append({
                        "name": item.name,
                        "path": str(item)
                    })

            contents["total_files"] = len(contents["python_files"]) + len(contents["other_files"])

        except Exception as e:
            contents["error"] = str(e)

        return contents

    async def add_custom_folder(
        self,
        path: str,
        name: str
    ) -> Optional[CKCFolderInfo]:
        """
        Tilføj en custom folder.

        Args:
            path: Sti til folderen
            name: Visningsnavn

        Returns:
            CKCFolderInfo eller None hvis fejl
        """
        folder_path = Path(path)

        if not folder_path.exists():
            logger.error(f"Custom folder sti eksisterer ikke: {path}")
            return None

        if not folder_path.is_dir():
            logger.error(f"Custom folder sti er ikke en mappe: {path}")
            return None

        # Check om allerede tilføjet
        if path in self._state.custom_folders:
            logger.warning(f"Custom folder allerede tilføjet: {path}")
            # Return existing
            folder_id = f"custom-{folder_path.name}"
            return self._folders.get(folder_id)

        # Scan folder
        folder = self._scan_custom_folder(path)
        if not folder:
            return None

        # Override display name
        folder.display_name = name

        # Tilføj til registry og state
        self._folders[folder.folder_id] = folder
        self._state.custom_folders.append(path)

        # Gem state
        await self.save_state()

        # Broadcast event
        await self._broadcast_event("folder.custom_added", folder.to_dict())

        logger.info(f"Tilføjede custom folder: {name} ({path})")
        return folder

    async def remove_custom_folder(self, folder_id: str) -> bool:
        """
        Fjern en custom folder.

        Args:
            folder_id: Folder ID (skal starte med "custom-")

        Returns:
            True hvis fjernet, False ellers
        """
        if not folder_id.startswith("custom-"):
            logger.error(f"Kan kun fjerne custom folders: {folder_id}")
            return False

        folder = self._folders.get(folder_id)
        if not folder:
            logger.error(f"Custom folder ikke fundet: {folder_id}")
            return False

        # Fjern fra registry
        del self._folders[folder_id]

        # Fjern fra state custom_folders liste
        path_str = str(folder.path)
        if path_str in self._state.custom_folders:
            self._state.custom_folders.remove(path_str)

        # Fjern fra favorites hvis der
        self._state.favorite_folders.discard(folder_id)

        # Fjern fra recent
        if folder_id in self._state.recent_folders:
            self._state.recent_folders.remove(folder_id)

        # Hvis det var current folder, clear
        if self._state.current_folder_id == folder_id:
            self._state.current_folder_id = None
            self._state.current_folder = None

        # Gem state
        await self.save_state()

        # Broadcast event
        await self._broadcast_event("folder.custom_removed", {"folder_id": folder_id})

        logger.info(f"Fjernede custom folder: {folder_id}")
        return True

    async def toggle_favorite(self, folder_id: str) -> bool:
        """
        Toggle favorite status for en folder.

        Args:
            folder_id: Folder ID

        Returns:
            True hvis tilføjet til favorites, False hvis fjernet
        """
        if folder_id not in self._folders:
            logger.error(f"Folder ikke fundet: {folder_id}")
            return False

        was_added = self._state.toggle_favorite(folder_id)

        # Gem state
        await self.save_state()

        # Broadcast event
        await self._broadcast_event("folder.favorite_toggled", {
            "folder_id": folder_id,
            "is_favorite": was_added
        })

        return was_added

    async def get_favorites(self) -> List[CKCFolderInfo]:
        """
        Hent alle favorite folders.

        Returns:
            Liste af CKCFolderInfo for favorites
        """
        return [
            self._folders[folder_id]
            for folder_id in self._state.favorite_folders
            if folder_id in self._folders
        ]

    async def get_recent(self) -> List[CKCFolderInfo]:
        """
        Hent senest besøgte folders.

        Returns:
            Liste af CKCFolderInfo (max 5)
        """
        return [
            self._folders[folder_id]
            for folder_id in self._state.recent_folders
            if folder_id in self._folders
        ]

    # =========================================================================
    # STATE PERSISTENCE
    # =========================================================================

    def _get_preferences_path(self) -> Path:
        """Hent sti til preferences fil."""
        self.PREFERENCES_DIR.mkdir(parents=True, exist_ok=True)
        return self.PREFERENCES_DIR / self.PREFERENCES_FILE

    async def save_state(self) -> None:
        """Gem state til fil."""
        pref_path = self._get_preferences_path()

        data = {
            "user_id": self._state.user_id,
            "current_folder_id": self._state.current_folder_id,
            "recent_folders": self._state.recent_folders[:5],
            "favorite_folders": list(self._state.favorite_folders),
            "custom_folders": self._state.custom_folders,
            "last_switch": self._state.last_switch.isoformat() if self._state.last_switch else None,
            "switch_count": self._state.switch_count,
            "saved_at": datetime.now(timezone.utc).isoformat()
        }

        try:
            with open(pref_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"State gemt til {pref_path}")
        except Exception as e:
            logger.error(f"Kunne ikke gemme state: {e}")

    async def load_state(self) -> None:
        """Load state fra fil."""
        pref_path = self._get_preferences_path()

        if not pref_path.exists():
            logger.info("Ingen eksisterende preferences - starter med defaults")
            return

        try:
            with open(pref_path, 'r') as f:
                data = json.load(f)

            self._state = FolderContextState(
                user_id=data.get("user_id", self._user_id),
                current_folder_id=data.get("current_folder_id"),
                recent_folders=data.get("recent_folders", []),
                favorite_folders=set(data.get("favorite_folders", [])),
                custom_folders=data.get("custom_folders", []),
                last_switch=datetime.fromisoformat(data["last_switch"]) if data.get("last_switch") else None,
                switch_count=data.get("switch_count", 0)
            )

            # Scan custom folders
            for custom_path in self._state.custom_folders:
                folder = self._scan_custom_folder(custom_path)
                if folder:
                    self._folders[folder.folder_id] = folder

            logger.info(f"State loaded fra {pref_path}")

        except Exception as e:
            logger.error(f"Kunne ikke loade state: {e}")

    # =========================================================================
    # EVENT BROADCASTING
    # =========================================================================

    def add_event_handler(self, handler: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        Tilføj event handler.

        Args:
            handler: Callback funktion (event_type, data)
        """
        self._event_handlers.append(handler)

    def remove_event_handler(self, handler: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        Fjern event handler.

        Args:
            handler: Handler at fjerne
        """
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)

    async def _broadcast_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Broadcast event til alle handlers.

        Args:
            event_type: Event type (f.eks. "folder.switched")
            data: Event data
        """
        for handler in self._event_handlers:
            try:
                handler(event_type, data)
            except Exception as e:
                logger.error(f"Event handler fejl: {e}")

    # =========================================================================
    # STATUS & DIAGNOSTICS
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """
        Hent status for folder switcher.

        Returns:
            Status dictionary
        """
        return {
            "initialized": self._initialized,
            "user_id": self._user_id,
            "total_folders": len(self._folders),
            "by_category": {
                "ckc_components": len([f for f in self._folders.values() if f.category == FolderCategory.CKC_COMPONENTS]),
                "cirkelline_ckc": len([f for f in self._folders.values() if f.category == FolderCategory.CIRKELLINE_CKC]),
                "custom": len([f for f in self._folders.values() if f.category == FolderCategory.CUSTOM])
            },
            "current_folder_id": self._state.current_folder_id,
            "recent_count": len(self._state.recent_folders),
            "favorites_count": len(self._state.favorite_folders),
            "switch_count": self._state.switch_count,
            "last_switch": self._state.last_switch.isoformat() if self._state.last_switch else None
        }


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_folder_switcher_instance: Optional[CKCFolderSwitcher] = None


def get_folder_switcher(user_id: str = "rasmus_super_admin") -> CKCFolderSwitcher:
    """
    Hent folder switcher singleton.

    Args:
        user_id: Bruger ID

    Returns:
        CKCFolderSwitcher instance
    """
    global _folder_switcher_instance

    if _folder_switcher_instance is None:
        _folder_switcher_instance = CKCFolderSwitcher(user_id)

    return _folder_switcher_instance


async def initialize_folder_switcher(user_id: str = "rasmus_super_admin") -> CKCFolderSwitcher:
    """
    Initialiser og returner folder switcher.

    Args:
        user_id: Bruger ID

    Returns:
        Initialiseret CKCFolderSwitcher
    """
    switcher = get_folder_switcher(user_id)
    await switcher.initialize()
    return switcher


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "CKCFolderSwitcher",
    "get_folder_switcher",
    "initialize_folder_switcher"
]
