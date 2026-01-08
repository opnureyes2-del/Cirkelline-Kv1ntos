"""
CKC Folder Switcher API Endpoints
==================================

REST API til CKC Folder Switcher.
10 endpoints til folder navigation og management.

Endpoints:
- GET  /api/ckc/folders              - List alle folders
- GET  /api/ckc/folders/current      - Current context
- POST /api/ckc/folders/switch       - Switch folder
- GET  /api/ckc/folders/{id}         - Folder detaljer
- GET  /api/ckc/folders/{id}/contents - Folder indhold
- POST /api/ckc/folders/custom       - Add custom folder
- DELETE /api/ckc/folders/custom/{id} - Remove custom folder
- GET  /api/ckc/folders/favorites    - List favorites
- POST /api/ckc/folders/favorites/{id} - Toggle favorite
- GET  /api/ckc/folders/recent       - Recent folders

Version: v1.3.5
Oprettet: 2025-12-16
Agent: Kommandør #4
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..folder_context import FolderCategory
from ..folder_switcher import get_folder_switcher, initialize_folder_switcher

logger = logging.getLogger(__name__)

# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(tags=["CKC Folder Switcher"])


# ============================================================================
# PYDANTIC MODELS - REQUEST
# ============================================================================

class FolderSwitchRequest(BaseModel):
    """Request model for folder switch."""
    folder_id: str = Field(..., description="ID på folder der skal skiftes til")
    method: str = Field(
        default="api",
        description="Switch metode: dropdown, sidebar, terminal, api"
    )


class AddCustomFolderRequest(BaseModel):
    """Request model for adding custom folder."""
    path: str = Field(..., description="Absolut sti til folderen")
    name: str = Field(..., description="Visningsnavn for folderen")


# ============================================================================
# PYDANTIC MODELS - RESPONSE
# ============================================================================

class FolderInfo(BaseModel):
    """Folder information."""
    folder_id: str
    name: str
    display_name: str
    path: str
    category: str
    status: str
    frozen: bool
    files_count: int
    python_files_count: int
    description: str
    version: str


class FolderListResponse(BaseModel):
    """Response for folder list."""
    folders: List[Dict[str, Any]]
    total: int
    categories: Dict[str, int]
    current_folder_id: Optional[str]


class FolderSwitchResponse(BaseModel):
    """Response for folder switch."""
    success: bool
    previous_folder: Optional[str]
    current_folder: Dict[str, Any]
    message: str
    event_id: str
    duration_ms: float


class FolderContextResponse(BaseModel):
    """Response for folder context."""
    user_id: str
    current_folder_id: Optional[str]
    current_folder: Optional[Dict[str, Any]]
    recent_folders: List[str]
    favorite_folders: List[str]
    custom_folders: List[str]
    switch_count: int


class FolderContentsResponse(BaseModel):
    """Response for folder contents."""
    folder_id: str
    path: str
    subfolders: List[Dict[str, str]]
    python_files: List[Dict[str, Any]]
    other_files: List[Dict[str, str]]
    total_files: int
    error: Optional[str] = None


class StatusResponse(BaseModel):
    """Response for status."""
    initialized: bool
    user_id: str
    total_folders: int
    by_category: Dict[str, int]
    current_folder_id: Optional[str]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _get_initialized_switcher():
    """Hent initialiseret folder switcher."""
    switcher = get_folder_switcher()
    if not switcher._initialized:
        await switcher.initialize()
    return switcher


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/folders", response_model=FolderListResponse)
async def list_folders(
    category: Optional[str] = Query(
        None,
        description="Filter på kategori: ckc_components, cirkelline_ckc, custom"
    )
):
    """
    List alle CKC folders.

    Returnerer alle tilgængelige CKC folders, eventuelt filtreret på kategori.
    Favorites vises først, derefter sorteret efter kategori og navn.
    """
    switcher = await _get_initialized_switcher()

    # Konverter kategori string til enum
    category_enum = None
    if category:
        try:
            category_enum = FolderCategory(category)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Ugyldig kategori: {category}. Vælg: ckc_components, cirkelline_ckc, custom"
            )

    folders = await switcher.list_folders(category_enum)
    context = await switcher.get_current_context()

    # Kategoriser
    by_category = {
        "ckc_components": 0,
        "cirkelline_ckc": 0,
        "custom": 0
    }
    for f in folders:
        by_category[f.category.value] += 1

    return FolderListResponse(
        folders=[f.to_dict() for f in folders],
        total=len(folders),
        categories=by_category,
        current_folder_id=context.current_folder_id
    )


@router.get("/folders/current", response_model=FolderContextResponse)
async def get_current_context():
    """
    Hent nuværende folder kontekst.

    Returnerer information om nuværende folder, recent folders, favorites, etc.
    """
    switcher = await _get_initialized_switcher()
    context = await switcher.get_current_context()

    return FolderContextResponse(
        user_id=context.user_id,
        current_folder_id=context.current_folder_id,
        current_folder=context.current_folder.to_dict() if context.current_folder else None,
        recent_folders=context.recent_folders,
        favorite_folders=list(context.favorite_folders),
        custom_folders=context.custom_folders,
        switch_count=context.switch_count
    )


@router.post("/folders/switch", response_model=FolderSwitchResponse)
async def switch_folder(request: FolderSwitchRequest):
    """
    Skift til en CKC folder.

    Skifter nuværende kontekst til den angivne folder.
    Gemmer automatisk til recent folders og persisterer state.
    """
    switcher = await _get_initialized_switcher()

    event = await switcher.switch_folder(
        folder_id=request.folder_id,
        method=request.method
    )

    if not event.success:
        raise HTTPException(
            status_code=400,
            detail=event.error_message or "Kunne ikke skifte folder"
        )

    context = await switcher.get_current_context()

    return FolderSwitchResponse(
        success=True,
        previous_folder=event.from_folder,
        current_folder=context.current_folder.to_dict() if context.current_folder else {},
        message=f"Skiftede til {context.current_folder.display_name if context.current_folder else request.folder_id}",
        event_id=event.event_id,
        duration_ms=event.duration_ms
    )


@router.get("/folders/{folder_id}")
async def get_folder_info(folder_id: str):
    """
    Hent information om en specifik folder.

    Args:
        folder_id: Folder ID

    Returns:
        Folder information inkl. metadata
    """
    switcher = await _get_initialized_switcher()
    folder = await switcher.get_folder_info(folder_id)

    if not folder:
        raise HTTPException(
            status_code=404,
            detail=f"Folder ikke fundet: {folder_id}"
        )

    context = await switcher.get_current_context()

    return {
        **folder.to_dict(),
        "is_current": folder_id == context.current_folder_id,
        "is_favorite": folder_id in context.favorite_folders
    }


@router.get("/folders/{folder_id}/contents", response_model=FolderContentsResponse)
async def get_folder_contents(folder_id: str):
    """
    Hent indholdet af en folder.

    Returnerer liste af subfolders, Python filer, og andre filer.
    """
    switcher = await _get_initialized_switcher()
    contents = await switcher.get_folder_contents(folder_id)

    if "error" in contents and contents.get("folder_id") is None:
        raise HTTPException(
            status_code=404,
            detail=contents["error"]
        )

    return FolderContentsResponse(**contents)


@router.post("/folders/custom")
async def add_custom_folder(request: AddCustomFolderRequest):
    """
    Tilføj en custom folder.

    Custom folders giver Super Admin mulighed for at tilføje
    egne CKC-lignende mapper til systemet.
    """
    switcher = await _get_initialized_switcher()

    folder = await switcher.add_custom_folder(
        path=request.path,
        name=request.name
    )

    if not folder:
        raise HTTPException(
            status_code=400,
            detail=f"Kunne ikke tilføje folder: {request.path}. Check at stien eksisterer og er en mappe."
        )

    return {
        "success": True,
        "message": f"Tilføjede custom folder: {request.name}",
        "folder": folder.to_dict()
    }


@router.delete("/folders/custom/{folder_id}")
async def remove_custom_folder(folder_id: str):
    """
    Fjern en custom folder.

    Kun custom folders (ID starter med "custom-") kan fjernes.
    CKC-COMPONENTS og cirkelline/ckc folders kan ikke fjernes.
    """
    if not folder_id.startswith("custom-"):
        raise HTTPException(
            status_code=400,
            detail="Kan kun fjerne custom folders (ID skal starte med 'custom-')"
        )

    switcher = await _get_initialized_switcher()
    success = await switcher.remove_custom_folder(folder_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Custom folder ikke fundet: {folder_id}"
        )

    return {
        "success": True,
        "message": f"Fjernede custom folder: {folder_id}"
    }


@router.get("/folders/favorites")
async def get_favorites():
    """
    Hent alle favorite folders.

    Returnerer liste af folders markeret som favorit.
    """
    switcher = await _get_initialized_switcher()
    favorites = await switcher.get_favorites()

    return {
        "favorites": [f.to_dict() for f in favorites],
        "total": len(favorites)
    }


@router.post("/folders/favorites/{folder_id}")
async def toggle_favorite(folder_id: str):
    """
    Toggle favorite status for en folder.

    Tilføjer folder til favorites hvis ikke der, ellers fjerner.
    """
    switcher = await _get_initialized_switcher()

    # Check folder eksisterer
    folder = await switcher.get_folder_info(folder_id)
    if not folder:
        raise HTTPException(
            status_code=404,
            detail=f"Folder ikke fundet: {folder_id}"
        )

    is_favorite = await switcher.toggle_favorite(folder_id)

    return {
        "success": True,
        "folder_id": folder_id,
        "is_favorite": is_favorite,
        "message": f"{'Tilføjede' if is_favorite else 'Fjernede'} {folder.display_name} {'til' if is_favorite else 'fra'} favorites"
    }


@router.get("/folders/recent")
async def get_recent():
    """
    Hent senest besøgte folders.

    Returnerer de 5 senest besøgte folders.
    """
    switcher = await _get_initialized_switcher()
    recent = await switcher.get_recent()

    return {
        "recent": [f.to_dict() for f in recent],
        "total": len(recent)
    }


@router.get("/folders/status", response_model=StatusResponse)
async def get_status():
    """
    Hent status for folder switcher.

    Returnerer diagnostisk information om folder switcher systemet.
    """
    switcher = await _get_initialized_switcher()
    status = switcher.get_status()

    return StatusResponse(
        initialized=status["initialized"],
        user_id=status["user_id"],
        total_folders=status["total_folders"],
        by_category=status["by_category"],
        current_folder_id=status["current_folder_id"]
    )


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ["router"]
