"""
CKC Folder Switcher Tests
=========================

Unit tests for the CKC Folder Switcher system.

Tests cover:
- Data models (folder_context.py)
- Core switching logic (folder_switcher.py)
- State persistence
- API endpoint models

Version: v1.3.5
Created: 2025-12-17
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

# Import data models
from cirkelline.ckc.folder_context import (
    FolderCategory,
    FolderStatus,
    SwitchMethod,
    CKCFolderInfo,
    FolderSwitchEvent,
    FolderContextState,
    CKC_COMPONENTS_FOLDERS,
    CIRKELLINE_CKC_FOLDERS
)

# Import folder switcher
from cirkelline.ckc.folder_switcher import (
    CKCFolderSwitcher,
    get_folder_switcher,
    initialize_folder_switcher
)


# ============================================================================
# TEST: ENUMS
# ============================================================================

class TestFolderEnums:
    """Test folder-related enums."""

    def test_folder_category_values(self):
        """Test FolderCategory enum has correct values."""
        assert FolderCategory.CKC_COMPONENTS.value == "ckc_components"
        assert FolderCategory.CIRKELLINE_CKC.value == "cirkelline_ckc"
        assert FolderCategory.CUSTOM.value == "custom"

    def test_folder_status_values(self):
        """Test FolderStatus enum has correct values."""
        assert FolderStatus.ACTIVE.value == "active"
        assert FolderStatus.FROZEN.value == "frozen"
        assert FolderStatus.DEVELOPMENT.value == "development"

    def test_switch_method_values(self):
        """Test SwitchMethod enum has correct values."""
        assert SwitchMethod.DROPDOWN.value == "dropdown"
        assert SwitchMethod.SIDEBAR.value == "sidebar"
        assert SwitchMethod.TERMINAL.value == "terminal"
        assert SwitchMethod.API.value == "api"


# ============================================================================
# TEST: CKC FOLDER INFO
# ============================================================================

class TestCKCFolderInfo:
    """Test CKCFolderInfo dataclass."""

    def test_create_folder_info(self):
        """Test creating a CKCFolderInfo instance."""
        folder = CKCFolderInfo(
            folder_id="mastermind",
            name="mastermind",
            display_name="Mastermind",
            path=Path("/test/path"),
            category=FolderCategory.CIRKELLINE_CKC,
            status=FolderStatus.ACTIVE,
            frozen=False,
            files_count=10,
            python_files_count=5
        )

        assert folder.folder_id == "mastermind"
        assert folder.display_name == "Mastermind"
        assert folder.category == FolderCategory.CIRKELLINE_CKC
        assert folder.status == FolderStatus.ACTIVE
        assert folder.frozen is False
        assert folder.files_count == 10

    def test_folder_info_to_dict(self):
        """Test CKCFolderInfo.to_dict() serialization."""
        folder = CKCFolderInfo(
            folder_id="test",
            name="test",
            display_name="Test Folder",
            path=Path("/test"),
            category=FolderCategory.CUSTOM,
            status=FolderStatus.ACTIVE
        )

        data = folder.to_dict()

        assert data["folder_id"] == "test"
        assert data["display_name"] == "Test Folder"
        assert data["category"] == "custom"
        assert data["status"] == "active"
        assert data["path"] == "/test"

    def test_folder_info_from_dict(self):
        """Test CKCFolderInfo.from_dict() deserialization."""
        data = {
            "folder_id": "test",
            "name": "test",
            "display_name": "Test Folder",
            "path": "/test/path",
            "category": "ckc_components",
            "status": "frozen",
            "frozen": True,
            "files_count": 20
        }

        folder = CKCFolderInfo.from_dict(data)

        assert folder.folder_id == "test"
        assert folder.category == FolderCategory.CKC_COMPONENTS
        assert folder.status == FolderStatus.FROZEN
        assert folder.frozen is True
        assert folder.files_count == 20


# ============================================================================
# TEST: FOLDER SWITCH EVENT
# ============================================================================

class TestFolderSwitchEvent:
    """Test FolderSwitchEvent dataclass."""

    def test_create_switch_event(self):
        """Test creating a switch event via factory method."""
        event = FolderSwitchEvent.create(
            user_id="test_user",
            from_folder="folder_a",
            to_folder="folder_b",
            method=SwitchMethod.TERMINAL,
            success=True
        )

        assert event.user_id == "test_user"
        assert event.from_folder == "folder_a"
        assert event.to_folder == "folder_b"
        assert event.switch_method == SwitchMethod.TERMINAL
        assert event.success is True
        assert event.event_id is not None
        assert event.timestamp is not None

    def test_failed_switch_event(self):
        """Test creating a failed switch event."""
        event = FolderSwitchEvent.create(
            user_id="test_user",
            from_folder=None,
            to_folder="nonexistent",
            method=SwitchMethod.API,
            success=False,
            error_message="Folder not found"
        )

        assert event.success is False
        assert event.error_message == "Folder not found"

    def test_switch_event_to_dict(self):
        """Test FolderSwitchEvent.to_dict() serialization."""
        event = FolderSwitchEvent.create(
            user_id="test",
            from_folder="a",
            to_folder="b",
            method=SwitchMethod.DROPDOWN
        )

        data = event.to_dict()

        assert data["user_id"] == "test"
        assert data["switch_method"] == "dropdown"
        assert "timestamp" in data
        assert "event_id" in data


# ============================================================================
# TEST: FOLDER CONTEXT STATE
# ============================================================================

class TestFolderContextState:
    """Test FolderContextState dataclass."""

    def test_create_state(self):
        """Test creating initial state."""
        state = FolderContextState(user_id="test_user")

        assert state.user_id == "test_user"
        assert state.current_folder_id is None
        assert state.recent_folders == []
        assert len(state.favorite_folders) == 0

    def test_add_to_recent(self):
        """Test adding folders to recent list."""
        state = FolderContextState(user_id="test")

        # Add folders
        state.add_to_recent("folder_a")
        state.add_to_recent("folder_b")
        state.add_to_recent("folder_c")

        assert state.recent_folders == ["folder_c", "folder_b", "folder_a"]

    def test_recent_max_5(self):
        """Test recent list max 5 items."""
        state = FolderContextState(user_id="test")

        # Add 7 folders
        for i in range(7):
            state.add_to_recent(f"folder_{i}")

        assert len(state.recent_folders) == 5
        assert state.recent_folders[0] == "folder_6"  # Most recent

    def test_recent_no_duplicates(self):
        """Test recent list removes duplicates."""
        state = FolderContextState(user_id="test")

        state.add_to_recent("folder_a")
        state.add_to_recent("folder_b")
        state.add_to_recent("folder_a")  # Re-add folder_a

        assert state.recent_folders == ["folder_a", "folder_b"]
        assert len(state.recent_folders) == 2

    def test_toggle_favorite(self):
        """Test toggling favorite status."""
        state = FolderContextState(user_id="test")

        # Add favorite
        added = state.toggle_favorite("folder_a")
        assert added is True
        assert "folder_a" in state.favorite_folders

        # Remove favorite
        removed = state.toggle_favorite("folder_a")
        assert removed is False
        assert "folder_a" not in state.favorite_folders

    def test_state_to_dict(self):
        """Test FolderContextState.to_dict() serialization."""
        state = FolderContextState(user_id="test")
        state.add_to_recent("folder_a")
        state.toggle_favorite("folder_b")

        data = state.to_dict()

        assert data["user_id"] == "test"
        assert "folder_a" in data["recent_folders"]
        assert "folder_b" in data["favorite_folders"]


# ============================================================================
# TEST: FOLDER CONSTANTS
# ============================================================================

class TestFolderConstants:
    """Test folder constant definitions."""

    def test_ckc_components_count(self):
        """Test CKC_COMPONENTS_FOLDERS has 6 entries."""
        assert len(CKC_COMPONENTS_FOLDERS) == 6

    def test_ckc_components_frozen(self):
        """Test all CKC_COMPONENTS are frozen."""
        for folder_id, config in CKC_COMPONENTS_FOLDERS.items():
            assert config.get("frozen", True) is True, f"{folder_id} should be frozen"

    def test_ckc_components_folders(self):
        """Test expected CKC_COMPONENTS folders exist."""
        expected = [
            "legal-kommandant",
            "web3-kommandant",
            "research-team",
            "law-team",
            "mastermind",
            "kv1nt"
        ]
        for folder in expected:
            assert folder in CKC_COMPONENTS_FOLDERS

    def test_cirkelline_ckc_count(self):
        """Test CIRKELLINE_CKC_FOLDERS has 9 entries."""
        assert len(CIRKELLINE_CKC_FOLDERS) == 9

    def test_cirkelline_ckc_active(self):
        """Test all cirkelline/ckc folders are active."""
        for folder_id, config in CIRKELLINE_CKC_FOLDERS.items():
            assert config.get("frozen", False) is False, f"{folder_id} should be active"

    def test_cirkelline_ckc_folders(self):
        """Test expected cirkelline/ckc folders exist."""
        expected = [
            "mastermind",
            "tegne_enhed",
            "kommandant",
            "infrastructure",
            "integrations",
            "web3",
            "connectors",
            "api",
            "aws"
        ]
        for folder in expected:
            assert folder in CIRKELLINE_CKC_FOLDERS


# ============================================================================
# TEST: CKC FOLDER SWITCHER
# ============================================================================

class TestCKCFolderSwitcher:
    """Test CKCFolderSwitcher class."""

    def test_create_switcher(self):
        """Test creating a CKCFolderSwitcher instance."""
        switcher = CKCFolderSwitcher("test_user")

        assert switcher._user_id == "test_user"
        assert switcher._initialized is False
        assert len(switcher._folders) == 0

    def test_scan_ckc_components(self):
        """Test scanning CKC-COMPONENTS folders."""
        switcher = CKCFolderSwitcher("test")
        folders = switcher.scan_ckc_components()

        # Should find 6 frozen folders
        assert len(folders) == 6

        for folder in folders:
            assert folder.category == FolderCategory.CKC_COMPONENTS
            assert folder.frozen is True
            assert folder.status == FolderStatus.FROZEN

    def test_scan_cirkelline_ckc(self):
        """Test scanning cirkelline/ckc folders."""
        switcher = CKCFolderSwitcher("test")
        folders = switcher.scan_cirkelline_ckc()

        # Should find 9 active folders
        assert len(folders) == 9

        for folder in folders:
            assert folder.category == FolderCategory.CIRKELLINE_CKC
            assert folder.frozen is False
            assert folder.status == FolderStatus.ACTIVE

    def test_get_status(self):
        """Test getting switcher status."""
        switcher = CKCFolderSwitcher("test")
        status = switcher.get_status()

        assert status["user_id"] == "test"
        assert status["initialized"] is False
        assert "by_category" in status


# ============================================================================
# TEST: SINGLETON
# ============================================================================

class TestSingleton:
    """Test singleton pattern."""

    def test_get_folder_switcher_returns_same_instance(self):
        """Test get_folder_switcher returns same instance."""
        # Note: This test may fail if run after other tests due to singleton
        # In a real test suite, you'd reset the singleton between tests
        switcher1 = get_folder_switcher("user1")
        switcher2 = get_folder_switcher("user2")  # Same instance, different user ignored

        assert switcher1 is switcher2


# ============================================================================
# ASYNC TESTS
# ============================================================================

class TestAsyncFolderSwitcher:
    """Async tests for folder switcher."""

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test async initialization."""
        switcher = CKCFolderSwitcher("async_test")
        await switcher.initialize()

        assert switcher._initialized is True
        assert len(switcher._folders) > 0

    @pytest.mark.asyncio
    async def test_list_folders(self):
        """Test listing folders."""
        switcher = CKCFolderSwitcher("async_test")
        await switcher.initialize()

        folders = await switcher.list_folders()

        assert len(folders) == 15  # 6 CKC + 9 cirkelline

    @pytest.mark.asyncio
    async def test_list_folders_by_category(self):
        """Test listing folders filtered by category."""
        switcher = CKCFolderSwitcher("async_test")
        await switcher.initialize()

        ckc_folders = await switcher.list_folders(FolderCategory.CKC_COMPONENTS)
        cirkelline_folders = await switcher.list_folders(FolderCategory.CIRKELLINE_CKC)

        assert len(ckc_folders) == 6
        assert len(cirkelline_folders) == 9

    @pytest.mark.asyncio
    async def test_switch_folder(self):
        """Test switching folders."""
        switcher = CKCFolderSwitcher("switch_test")
        await switcher.initialize()

        # Switch to mastermind
        event = await switcher.switch_folder("mastermind", "terminal")

        assert event.success is True
        assert event.to_folder == "mastermind"
        assert switcher._state.current_folder_id == "mastermind"

    @pytest.mark.asyncio
    async def test_switch_nonexistent_folder(self):
        """Test switching to non-existent folder fails."""
        switcher = CKCFolderSwitcher("switch_test")
        await switcher.initialize()

        event = await switcher.switch_folder("nonexistent_folder", "api")

        assert event.success is False
        assert event.error_message is not None

    @pytest.mark.asyncio
    async def test_get_folder_info(self):
        """Test getting folder info."""
        switcher = CKCFolderSwitcher("info_test")
        await switcher.initialize()

        folder = await switcher.get_folder_info("mastermind")

        assert folder is not None
        assert folder.folder_id == "mastermind"
        assert folder.category == FolderCategory.CIRKELLINE_CKC

    @pytest.mark.asyncio
    async def test_toggle_favorite(self):
        """Test toggling favorites."""
        switcher = CKCFolderSwitcher("fav_test")
        await switcher.initialize()

        # Add to favorites
        was_added = await switcher.toggle_favorite("mastermind")
        assert was_added is True

        favorites = await switcher.get_favorites()
        assert any(f.folder_id == "mastermind" for f in favorites)

        # Remove from favorites
        was_removed = await switcher.toggle_favorite("mastermind")
        assert was_removed is False


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
