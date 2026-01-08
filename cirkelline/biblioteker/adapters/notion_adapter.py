"""
Notion Adapter
==============

FASE 6: Multi-Bibliotek Arkitektur

Adapter for integration med Notion databaser.
Bruger den eksisterende Notion integration i Cirkelline.

Features:
    - Dynamisk database discovery
    - Multi-database søgning
    - Automatic type mapping
"""

import os
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..base import (
    BibliotekSource,
    BibliotekAdapter,
    LibraryItem,
    SearchQuery,
    SearchResult,
    SyncStatus,
    ItemType,
)


class NotionAdapter(BibliotekAdapter):
    """
    Adapter for Notion integration.

    Integrerer med brugerens Notion workspace via
    den eksisterende OAuth integration.

    Database typer understøttet:
        - tasks: Opgaver og to-dos
        - projects: Projekter
        - documentation: Dokumentation
        - companies: Firma/kontakt databaser
        - custom: Andre databaser
    """

    def __init__(self, source: BibliotekSource = BibliotekSource.NOTION):
        super().__init__(source)
        self._user_id: Optional[str] = None
        self._databases: Dict[str, Dict[str, Any]] = {}
        self._notion_client = None

    async def connect(self) -> bool:
        """
        Opret forbindelse til Notion.

        Kræver at bruger har OAuth-autoriseret Notion.
        """
        try:
            # Import Notion client
            from notion_client import AsyncClient

            # Hent token fra database (kræver user_id)
            if not self._user_id:
                # Vi venter med at forbinde til vi har user context
                self._connected = False
                return False

            # Her ville vi normalt hente token fra notion_tokens table
            # For nu antager vi klienten er pre-konfigureret
            notion_token = os.getenv("NOTION_INTEGRATION_TOKEN")
            if notion_token:
                self._notion_client = AsyncClient(auth=notion_token)
                self._connected = True
                return True

            self._connected = False
            return False

        except ImportError:
            print("notion-client package ikke installeret")
            self._connected = False
            return False
        except Exception as e:
            print(f"Notion forbindelsesfejl: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Afbryd forbindelse."""
        self._notion_client = None
        self._connected = False

    def set_user_context(self, user_id: str) -> None:
        """
        Sæt bruger-kontekst for Notion queries.

        Args:
            user_id: Bruger ID fra JWT
        """
        self._user_id = user_id

    async def search(self, query: SearchQuery) -> SearchResult:
        """
        Søg i Notion databaser.

        Søger på tværs af alle brugerens registrerede
        Notion databaser.
        """
        if not self._connected or not self._notion_client:
            return SearchResult(
                items=[],
                total_count=0,
                query=query.query,
                sources_searched=[self.source]
            )

        try:
            # Brug Notion search API
            response = await self._notion_client.search(
                query=query.query,
                page_size=query.limit
            )

            items = []
            for result in response.get("results", []):
                item = self._convert_notion_to_library_item(result)
                if item:
                    items.append(item)

            return SearchResult(
                items=items,
                total_count=len(items),
                query=query.query,
                sources_searched=[self.source]
            )

        except Exception as e:
            print(f"Notion søgefejl: {e}")
            return SearchResult(
                items=[],
                total_count=0,
                query=query.query,
                sources_searched=[self.source]
            )

    async def get_item(self, item_id: str) -> Optional[LibraryItem]:
        """Hent specifikt item fra Notion."""
        if not self._connected or not self._notion_client:
            return None

        try:
            # Prøv som page først
            try:
                page = await self._notion_client.pages.retrieve(page_id=item_id)
                return self._convert_notion_to_library_item(page)
            except Exception:
                pass

            # Prøv som database
            try:
                db = await self._notion_client.databases.retrieve(database_id=item_id)
                return self._convert_notion_to_library_item(db)
            except Exception:
                pass

            return None

        except Exception as e:
            print(f"Notion get_item fejl: {e}")
            return None

    async def list_items(
        self,
        domain: Optional[str] = None,
        item_type: Optional[ItemType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[LibraryItem]:
        """List items fra Notion."""
        if not self._connected or not self._notion_client:
            return []

        try:
            # List brugerens databaser
            response = await self._notion_client.search(
                filter={"property": "object", "value": "database"},
                page_size=limit
            )

            items = []
            for db in response.get("results", []):
                item = self._convert_notion_to_library_item(db)
                if item:
                    items.append(item)

            return items

        except Exception as e:
            print(f"Notion list_items fejl: {e}")
            return []

    async def save_item(self, item: LibraryItem) -> str:
        """
        Gem item i Notion.

        Kræver en parent database eller page ID.
        """
        if not self._connected or not self._notion_client:
            raise ConnectionError("Ikke forbundet til Notion")

        # Notion kræver en parent - vi understøtter det ikke direkte
        # i denne adapter, da det kræver database-specifik konfiguration
        raise NotImplementedError(
            "Notion gem kræver parent database. "
            "Brug cirkelline.integrations.notion endpoints direkte."
        )

    async def delete_item(self, item_id: str) -> bool:
        """Slet/arkivér item i Notion."""
        if not self._connected or not self._notion_client:
            return False

        try:
            # Notion understøtter kun arkivering, ikke sletning
            await self._notion_client.pages.update(
                page_id=item_id,
                archived=True
            )
            return True

        except Exception:
            return False

    async def sync(self) -> SyncStatus:
        """Synkroniser database liste fra Notion."""
        if not self._connected or not self._notion_client:
            return SyncStatus(
                source=self.source,
                status="disconnected"
            )

        try:
            # Hent alle databaser
            response = await self._notion_client.search(
                filter={"property": "object", "value": "database"},
                page_size=100
            )

            self._databases = {}
            for db in response.get("results", []):
                db_id = db["id"]
                self._databases[db_id] = {
                    "id": db_id,
                    "title": self._get_notion_title(db),
                    "type": "database"
                }

            self._last_sync = datetime.utcnow()
            return SyncStatus(
                source=self.source,
                last_sync=self._last_sync,
                items_synced=len(self._databases),
                status="success"
            )

        except Exception as e:
            return SyncStatus(
                source=self.source,
                status="failed",
                error=str(e)
            )

    async def get_databases(self) -> List[Dict[str, Any]]:
        """
        Hent liste af brugerens Notion databaser.

        Returns:
            Liste af database info
        """
        if not self._databases:
            await self.sync()
        return list(self._databases.values())

    def _convert_notion_to_library_item(
        self,
        notion_obj: Dict[str, Any]
    ) -> Optional[LibraryItem]:
        """Konverter Notion objekt til LibraryItem."""
        try:
            obj_type = notion_obj.get("object", "unknown")

            # Bestem item type baseret på Notion object type
            if obj_type == "database":
                item_type = ItemType.PROJECT
            elif obj_type == "page":
                item_type = ItemType.DOCUMENT
            else:
                item_type = ItemType.NOTE

            # Hent titel
            title = self._get_notion_title(notion_obj)

            # Hent content (for pages med content)
            content = ""
            if "properties" in notion_obj:
                # Flad properties til content
                props = notion_obj["properties"]
                content_parts = []
                for key, value in props.items():
                    prop_value = self._extract_notion_property_value(value)
                    if prop_value:
                        content_parts.append(f"{key}: {prop_value}")
                content = "\n".join(content_parts)

            return LibraryItem(
                id=notion_obj["id"],
                title=title,
                content=content,
                source=self.source,
                item_type=item_type,
                source_id=notion_obj["id"],
                url=notion_obj.get("url"),
                created_at=datetime.fromisoformat(
                    notion_obj.get("created_time", "").replace("Z", "+00:00")
                ) if notion_obj.get("created_time") else datetime.utcnow(),
                updated_at=datetime.fromisoformat(
                    notion_obj.get("last_edited_time", "").replace("Z", "+00:00")
                ) if notion_obj.get("last_edited_time") else datetime.utcnow(),
                metadata={
                    "notion_type": obj_type,
                    "parent": notion_obj.get("parent", {})
                }
            )

        except Exception as e:
            print(f"Notion konverteringsfejl: {e}")
            return None

    def _get_notion_title(self, notion_obj: Dict[str, Any]) -> str:
        """Udtræk titel fra Notion objekt."""
        # Database title
        if "title" in notion_obj:
            title_array = notion_obj["title"]
            if isinstance(title_array, list) and title_array:
                return title_array[0].get("plain_text", "Untitled")

        # Page title (i properties)
        if "properties" in notion_obj:
            props = notion_obj["properties"]
            # Søg efter title property
            for key, value in props.items():
                if value.get("type") == "title":
                    title_array = value.get("title", [])
                    if title_array:
                        return title_array[0].get("plain_text", "Untitled")

        return "Untitled"

    def _extract_notion_property_value(self, prop: Dict[str, Any]) -> Optional[str]:
        """Udtræk værdi fra en Notion property."""
        prop_type = prop.get("type")

        if prop_type == "title":
            arr = prop.get("title", [])
            return arr[0].get("plain_text") if arr else None

        elif prop_type == "rich_text":
            arr = prop.get("rich_text", [])
            return arr[0].get("plain_text") if arr else None

        elif prop_type == "number":
            return str(prop.get("number")) if prop.get("number") is not None else None

        elif prop_type == "select":
            sel = prop.get("select")
            return sel.get("name") if sel else None

        elif prop_type == "multi_select":
            items = prop.get("multi_select", [])
            return ", ".join(i.get("name", "") for i in items) if items else None

        elif prop_type == "date":
            date = prop.get("date")
            return date.get("start") if date else None

        elif prop_type == "checkbox":
            return "Yes" if prop.get("checkbox") else "No"

        elif prop_type == "url":
            return prop.get("url")

        elif prop_type == "email":
            return prop.get("email")

        return None
