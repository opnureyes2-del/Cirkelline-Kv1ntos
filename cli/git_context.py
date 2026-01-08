"""
Git Context Module
==================
Git repository context extraction for Cirkelline Terminal CLI.
Provides intelligent context about current repository state.
"""

import os
import subprocess
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class GitContext:
    """Git repository context."""

    # Repository info
    is_git_repo: bool = False
    repo_root: Optional[str] = None
    repo_name: Optional[str] = None

    # Branch info
    current_branch: Optional[str] = None
    default_branch: Optional[str] = None
    is_detached_head: bool = False

    # Commit info
    commit_hash: Optional[str] = None
    commit_short: Optional[str] = None
    commit_message: Optional[str] = None
    commit_author: Optional[str] = None
    commit_date: Optional[str] = None

    # Status
    has_changes: bool = False
    staged_files: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    untracked_files: List[str] = field(default_factory=list)

    # Remote info
    remote_url: Optional[str] = None
    remote_name: Optional[str] = None
    ahead_count: int = 0
    behind_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API payload."""
        return {
            "is_git_repo": self.is_git_repo,
            "repo_name": self.repo_name,
            "current_branch": self.current_branch,
            "commit_hash": self.commit_hash,
            "commit_short": self.commit_short,
            "commit_message": self.commit_message,
            "has_changes": self.has_changes,
            "staged_count": len(self.staged_files),
            "modified_count": len(self.modified_files),
            "untracked_count": len(self.untracked_files),
            "remote_url": self.remote_url,
            "ahead_count": self.ahead_count,
            "behind_count": self.behind_count,
        }


class GitContextCollector:
    """Collects Git repository context."""

    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = working_dir or os.getcwd()

    def _run_git(self, args: List[str], capture_error: bool = False) -> Optional[str]:
        """Run git command and return output."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            elif capture_error:
                return None
            return None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None
        except Exception as e:
            logger.debug(f"Git command failed: {e}")
            return None

    def is_git_repo(self) -> bool:
        """Check if current directory is in a git repository."""
        result = self._run_git(["rev-parse", "--is-inside-work-tree"])
        return result == "true"

    def collect(self) -> GitContext:
        """Collect full git context."""
        context = GitContext()

        if not self.is_git_repo():
            return context

        context.is_git_repo = True

        # Repository root and name
        context.repo_root = self._run_git(["rev-parse", "--show-toplevel"])
        if context.repo_root:
            context.repo_name = Path(context.repo_root).name

        # Branch information
        branch = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if branch == "HEAD":
            context.is_detached_head = True
            context.current_branch = self._run_git(["rev-parse", "--short", "HEAD"])
        else:
            context.current_branch = branch

        # Default branch (try common names)
        for default in ["main", "master", "develop"]:
            if self._run_git(["rev-parse", "--verify", default], capture_error=True):
                context.default_branch = default
                break

        # Commit information
        context.commit_hash = self._run_git(["rev-parse", "HEAD"])
        context.commit_short = self._run_git(["rev-parse", "--short", "HEAD"])
        context.commit_message = self._run_git(["log", "-1", "--format=%s"])
        context.commit_author = self._run_git(["log", "-1", "--format=%an"])
        context.commit_date = self._run_git(["log", "-1", "--format=%ci"])

        # Status
        status_output = self._run_git(["status", "--porcelain"])
        if status_output:
            context.has_changes = True
            for line in status_output.split("\n"):
                if len(line) >= 3:
                    status = line[:2]
                    filename = line[3:]

                    if status[0] != " " and status[0] != "?":
                        context.staged_files.append(filename)
                    if status[1] != " " and status[1] != "?":
                        context.modified_files.append(filename)
                    if status == "??":
                        context.untracked_files.append(filename)

        # Remote information
        context.remote_name = self._run_git(["remote"])
        if context.remote_name:
            # Use first remote if multiple
            context.remote_name = context.remote_name.split("\n")[0]
            context.remote_url = self._run_git(["remote", "get-url", context.remote_name])

            # Ahead/behind count
            if context.current_branch and not context.is_detached_head:
                tracking = self._run_git([
                    "rev-list", "--left-right", "--count",
                    f"{context.remote_name}/{context.current_branch}...HEAD"
                ])
                if tracking:
                    parts = tracking.split()
                    if len(parts) == 2:
                        context.behind_count = int(parts[0])
                        context.ahead_count = int(parts[1])

        return context

    def get_file_diff(self, filepath: str, staged: bool = False) -> Optional[str]:
        """Get diff for a specific file."""
        args = ["diff"]
        if staged:
            args.append("--staged")
        args.append("--")
        args.append(filepath)
        return self._run_git(args)

    def get_recent_commits(self, count: int = 5) -> List[Dict[str, str]]:
        """Get recent commits."""
        log_output = self._run_git([
            "log", f"-{count}",
            "--format=%H|%h|%s|%an|%ci"
        ])

        commits = []
        if log_output:
            for line in log_output.split("\n"):
                parts = line.split("|")
                if len(parts) == 5:
                    commits.append({
                        "hash": parts[0],
                        "short": parts[1],
                        "message": parts[2],
                        "author": parts[3],
                        "date": parts[4],
                    })

        return commits


def get_git_context(working_dir: Optional[str] = None) -> GitContext:
    """Get git context for current or specified directory."""
    collector = GitContextCollector(working_dir)
    return collector.collect()
