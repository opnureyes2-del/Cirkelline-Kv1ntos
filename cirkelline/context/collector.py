"""
Context Collector
=================
Gathers and aggregates context from multiple sources.

Sources:
- Git repository context
- User session context
- System environment
- Active missions from HQ
- Recent agent activity

Context is injected into agent prompts for better responses.
"""

import os
import logging
import subprocess
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXT TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class ContextType(str, Enum):
    """Categories of context information."""
    GIT = "git"
    USER = "user"
    SESSION = "session"
    SYSTEM = "system"
    MISSION = "mission"
    ENVIRONMENT = "environment"
    TERMINAL = "terminal"


class ContextSource(str, Enum):
    """Where context originates from."""
    CLI = "cli"
    WEB = "web"
    API = "api"
    INTERNAL = "internal"
    SCHEDULED = "scheduled"


# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXT DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GitContext:
    """Git repository context."""
    is_git_repo: bool = False
    repo_name: Optional[str] = None
    current_branch: Optional[str] = None
    commit_hash: Optional[str] = None
    commit_short: Optional[str] = None
    commit_message: Optional[str] = None
    has_changes: bool = False
    staged_count: int = 0
    modified_count: int = 0
    untracked_count: int = 0
    remote_url: Optional[str] = None
    ahead_count: int = 0
    behind_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_git_repo": self.is_git_repo,
            "repo_name": self.repo_name,
            "current_branch": self.current_branch,
            "commit_hash": self.commit_hash,
            "commit_short": self.commit_short,
            "commit_message": self.commit_message,
            "has_changes": self.has_changes,
            "staged_count": self.staged_count,
            "modified_count": self.modified_count,
            "untracked_count": self.untracked_count,
            "remote_url": self.remote_url,
            "ahead_count": self.ahead_count,
            "behind_count": self.behind_count,
        }


@dataclass
class UserContext:
    """User session context."""
    user_id: Optional[str] = None
    email: Optional[str] = None
    tier: str = "member"
    is_admin: bool = False
    preferences: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    timezone: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "tier": self.tier,
            "is_admin": self.is_admin,
            "preferences": self.preferences,
            "session_id": self.session_id,
            "timezone": self.timezone,
        }


@dataclass
class SystemContext:
    """System environment context."""
    platform: str = ""
    hostname: str = ""
    working_directory: str = ""
    python_version: str = ""
    environment: str = "development"
    services_health: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "hostname": self.hostname,
            "working_directory": self.working_directory,
            "python_version": self.python_version,
            "environment": self.environment,
            "services_health": self.services_health,
        }


@dataclass
class AggregatedContext:
    """Combined context from all sources."""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    source: ContextSource = ContextSource.INTERNAL
    git: Optional[GitContext] = None
    user: Optional[UserContext] = None
    system: Optional[SystemContext] = None
    missions: List[Dict[str, Any]] = field(default_factory=list)
    custom: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "source": self.source.value,
            "git": self.git.to_dict() if self.git else None,
            "user": self.user.to_dict() if self.user else None,
            "system": self.system.to_dict() if self.system else None,
            "missions": self.missions,
            "custom": self.custom,
        }

    def to_prompt_string(self) -> str:
        """Format context for injection into agent prompts."""
        parts = []
        parts.append(f"[Context @ {self.timestamp}]")

        if self.user:
            parts.append(f"User: {self.user.email or self.user.user_id} (tier: {self.user.tier})")

        if self.git and self.git.is_git_repo:
            git_info = f"Repository: {self.git.repo_name} @ {self.git.current_branch}"
            if self.git.has_changes:
                git_info += f" (+{self.git.staged_count} staged, ~{self.git.modified_count} modified)"
            parts.append(git_info)

        if self.system:
            parts.append(f"Environment: {self.system.environment}")

        if self.missions:
            active = [m for m in self.missions if m.get("status") == "in_progress"]
            if active:
                parts.append(f"Active missions: {len(active)}")

        return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXT COLLECTOR
# ═══════════════════════════════════════════════════════════════════════════════

class ContextCollector:
    """
    Collects and aggregates context from multiple sources.

    Usage:
        collector = get_context_collector()
        context = await collector.collect(
            include_git=True,
            include_system=True,
            user_id="user-123",
        )
        prompt_context = context.to_prompt_string()
    """

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 60  # seconds

    def _run_git_command(self, args: List[str], cwd: Optional[str] = None) -> Optional[str]:
        """Run a git command and return output."""
        try:
            result = subprocess.run(
                ["git"] + args,
                capture_output=True,
                text=True,
                cwd=cwd or os.getcwd(),
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    def collect_git_context(self, path: Optional[str] = None) -> GitContext:
        """Collect git repository context."""
        context = GitContext()

        # Check if in git repo
        git_dir = self._run_git_command(["rev-parse", "--git-dir"], path)
        if not git_dir:
            return context

        context.is_git_repo = True

        # Repository name
        toplevel = self._run_git_command(["rev-parse", "--show-toplevel"], path)
        if toplevel:
            context.repo_name = os.path.basename(toplevel)

        # Current branch
        branch = self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"], path)
        if branch:
            context.current_branch = branch

        # Commit info
        commit_hash = self._run_git_command(["rev-parse", "HEAD"], path)
        if commit_hash:
            context.commit_hash = commit_hash
            context.commit_short = commit_hash[:7]

        commit_msg = self._run_git_command(["log", "-1", "--format=%s"], path)
        if commit_msg:
            context.commit_message = commit_msg

        # Changes
        status = self._run_git_command(["status", "--porcelain"], path)
        if status:
            context.has_changes = True
            lines = status.split("\n")
            for line in lines:
                if line.startswith("A ") or line.startswith("M ") or line.startswith("D "):
                    context.staged_count += 1
                elif line.startswith(" M") or line.startswith(" D"):
                    context.modified_count += 1
                elif line.startswith("??"):
                    context.untracked_count += 1

        # Remote
        remote = self._run_git_command(["remote", "get-url", "origin"], path)
        if remote:
            context.remote_url = remote

        # Ahead/behind
        upstream = self._run_git_command(
            ["rev-list", "--left-right", "--count", "@{upstream}...HEAD"],
            path
        )
        if upstream:
            parts = upstream.split()
            if len(parts) == 2:
                context.behind_count = int(parts[0])
                context.ahead_count = int(parts[1])

        return context

    def collect_system_context(self) -> SystemContext:
        """Collect system environment context."""
        import platform
        import socket
        import sys

        return SystemContext(
            platform=platform.system(),
            hostname=socket.gethostname(),
            working_directory=os.getcwd(),
            python_version=sys.version.split()[0],
            environment=os.getenv("ENVIRONMENT", "development"),
            services_health={},  # Filled by SystemStatus
        )

    async def collect_user_context(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> UserContext:
        """Collect user session context from database."""
        context = UserContext(
            user_id=user_id,
            session_id=session_id,
        )

        if not user_id:
            return context

        # TODO: Fetch from database
        # This would query users table for email, tier, admin status
        # For now, return basic context

        return context

    async def collect_mission_context(
        self,
        user_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Collect active missions from HQ."""
        try:
            from cirkelline.headquarters import get_shared_memory

            memory = get_shared_memory()
            if not memory.is_connected:
                return []

            from cirkelline.headquarters.shared_memory import MissionStatus
            missions = await memory.get_missions_by_status(
                MissionStatus.IN_PROGRESS,
                limit=limit,
            )

            return [m.to_dict() for m in missions]

        except Exception as e:
            logger.warning(f"Failed to collect mission context: {e}")
            return []

    async def collect(
        self,
        source: ContextSource = ContextSource.INTERNAL,
        include_git: bool = True,
        include_system: bool = True,
        include_missions: bool = True,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        git_path: Optional[str] = None,
        custom_context: Optional[Dict[str, Any]] = None,
    ) -> AggregatedContext:
        """
        Collect and aggregate context from all sources.

        Args:
            source: Where the context request originates
            include_git: Include git repository context
            include_system: Include system environment context
            include_missions: Include active missions from HQ
            user_id: User ID for user context
            session_id: Session ID for session context
            git_path: Path to git repository
            custom_context: Additional custom context

        Returns:
            AggregatedContext with all collected information
        """
        context = AggregatedContext(source=source)

        # Git context
        if include_git:
            context.git = self.collect_git_context(git_path)

        # System context
        if include_system:
            context.system = self.collect_system_context()

        # User context
        if user_id:
            context.user = await self.collect_user_context(user_id, session_id)

        # Mission context
        if include_missions:
            context.missions = await self.collect_mission_context(user_id)

        # Custom context
        if custom_context:
            context.custom = custom_context

        return context

    def collect_sync(
        self,
        include_git: bool = True,
        include_system: bool = True,
        git_path: Optional[str] = None,
    ) -> AggregatedContext:
        """
        Synchronous context collection (no async calls).

        Useful for CLI where async may not be available.
        """
        context = AggregatedContext(source=ContextSource.CLI)

        if include_git:
            context.git = self.collect_git_context(git_path)

        if include_system:
            context.system = self.collect_system_context()

        return context


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_collector_instance: Optional[ContextCollector] = None


def get_context_collector() -> ContextCollector:
    """Get the singleton ContextCollector instance."""
    global _collector_instance

    if _collector_instance is None:
        _collector_instance = ContextCollector()

    return _collector_instance
