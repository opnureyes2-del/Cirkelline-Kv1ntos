"""
Contextual Advisor
==================
Intelligent recommendations based on multi-source context analysis.

Responsibilities:
- Analyze git context for development insights
- Monitor system health for operational advice
- Track user patterns for personalized suggestions
- Provide proactive recommendations
"""

import logging
from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import re

from cirkelline.context.collector import (
    ContextCollector,
    GitContext,
    UserContext,
    SystemContext,
    get_context_collector,
)
from cirkelline.context.system_status import (
    SystemStatus,
    HealthStatus,
    get_system_status,
)
from cirkelline.headquarters.event_bus import (
    EventBus,
    Event,
    EventType,
    get_event_bus,
)
from cirkelline.headquarters.knowledge_graph import (
    KnowledgeGraph,
    get_knowledge_graph,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# ADVICE TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class AdviceType(Enum):
    """Categories of advice."""
    GIT_WORKFLOW = "git_workflow"
    CODE_QUALITY = "code_quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    BEST_PRACTICE = "best_practice"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    COLLABORATION = "collaboration"
    SYSTEM_HEALTH = "system_health"


class AdvicePriority(Enum):
    """Priority levels for advice."""
    INFO = "info"
    SUGGESTION = "suggestion"
    RECOMMENDATION = "recommendation"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Advice:
    """A contextual recommendation."""
    advice_id: str
    advice_type: AdviceType
    priority: AdvicePriority
    title: str
    description: str
    action: Optional[str] = None  # Suggested action
    context_source: str = ""  # What triggered this advice
    confidence: float = 1.0  # 0-1 confidence score
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: Optional[str] = None
    dismissed: bool = False
    related_files: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "advice_id": self.advice_id,
            "advice_type": self.advice_type.value,
            "priority": self.priority.value,
            "title": self.title,
            "description": self.description,
            "action": self.action,
            "context_source": self.context_source,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "dismissed": self.dismissed,
            "related_files": self.related_files,
            "tags": list(self.tags),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# ADVICE RULES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AdviceRule:
    """A rule for generating advice."""
    rule_id: str
    name: str
    condition: str  # Python expression to evaluate
    advice_type: AdviceType
    priority: AdvicePriority
    title_template: str
    description_template: str
    action_template: Optional[str] = None
    tags: Set[str] = field(default_factory=set)


# Built-in rules
DEFAULT_RULES: List[AdviceRule] = [
    # Git workflow rules
    AdviceRule(
        rule_id="git-uncommitted-changes",
        name="Uncommitted Changes Warning",
        condition="git_context and git_context.has_changes and len(git_context.modified_files) > 5",
        advice_type=AdviceType.GIT_WORKFLOW,
        priority=AdvicePriority.SUGGESTION,
        title_template="You have {count} uncommitted files",
        description_template="Consider committing your changes to avoid losing work. Large changesets are harder to review.",
        action_template="Run: git add -p && git commit",
        tags={"git", "workflow"},
    ),
    AdviceRule(
        rule_id="git-behind-remote",
        name="Behind Remote Warning",
        condition="git_context and git_context.behind_count > 0",
        advice_type=AdviceType.GIT_WORKFLOW,
        priority=AdvicePriority.WARNING,
        title_template="Your branch is {count} commits behind remote",
        description_template="Pull the latest changes to avoid merge conflicts.",
        action_template="Run: git pull --rebase",
        tags={"git", "sync"},
    ),
    AdviceRule(
        rule_id="git-feature-branch",
        name="Feature Branch Suggestion",
        condition="git_context and git_context.current_branch in ['main', 'master'] and git_context.has_changes",
        advice_type=AdviceType.GIT_WORKFLOW,
        priority=AdvicePriority.RECOMMENDATION,
        title_template="Working directly on {branch}",
        description_template="Consider creating a feature branch for your changes.",
        action_template="Run: git checkout -b feature/your-feature-name",
        tags={"git", "workflow", "best-practice"},
    ),
    AdviceRule(
        rule_id="git-large-diff",
        name="Large Diff Warning",
        condition="git_context and len(git_context.modified_files) + len(git_context.staged_files) > 10",
        advice_type=AdviceType.CODE_QUALITY,
        priority=AdvicePriority.SUGGESTION,
        title_template="Large changeset detected ({count} files)",
        description_template="Consider breaking this into smaller, focused commits for easier review.",
        action_template="Use git add -p for selective staging",
        tags={"git", "code-review"},
    ),

    # Security rules
    AdviceRule(
        rule_id="sensitive-file-staged",
        name="Sensitive File Warning",
        condition="git_context and any(f for f in git_context.staged_files if any(s in f.lower() for s in ['.env', 'secret', 'password', 'credentials', 'key.json', 'token']))",
        advice_type=AdviceType.SECURITY,
        priority=AdvicePriority.CRITICAL,
        title_template="Potential sensitive file staged",
        description_template="Review staged files for sensitive data before committing.",
        action_template="Run: git reset HEAD <file> to unstage",
        tags={"security", "sensitive-data"},
    ),
    AdviceRule(
        rule_id="git-untracked-env",
        name="Untracked Env File",
        condition="git_context and any(f for f in git_context.untracked_files if '.env' in f and not f.endswith('.example'))",
        advice_type=AdviceType.SECURITY,
        priority=AdvicePriority.WARNING,
        title_template="Untracked .env file detected",
        description_template="Ensure .env files are in .gitignore to prevent accidental commits.",
        action_template="Add to .gitignore: echo '.env*' >> .gitignore",
        tags={"security", "gitignore"},
    ),

    # Testing rules
    AdviceRule(
        rule_id="test-file-modified",
        name="Test File Modified",
        condition="git_context and any(f for f in git_context.modified_files if 'test' in f.lower())",
        advice_type=AdviceType.TESTING,
        priority=AdvicePriority.INFO,
        title_template="Test files modified",
        description_template="Remember to run tests before committing.",
        action_template="Run: pytest or npm test",
        tags={"testing", "ci"},
    ),
    AdviceRule(
        rule_id="no-tests-for-feature",
        name="No Tests for Feature",
        condition="git_context and any(f for f in git_context.modified_files if f.endswith('.py') and 'test' not in f.lower()) and not any(f for f in git_context.modified_files if 'test' in f.lower())",
        advice_type=AdviceType.TESTING,
        priority=AdvicePriority.SUGGESTION,
        title_template="No test files in changeset",
        description_template="Consider adding tests for your changes.",
        tags={"testing", "quality"},
    ),

    # System health rules
    AdviceRule(
        rule_id="system-degraded",
        name="System Degraded",
        condition="system_health and system_health.get('overall') == 'degraded'",
        advice_type=AdviceType.SYSTEM_HEALTH,
        priority=AdvicePriority.WARNING,
        title_template="System health is degraded",
        description_template="Some services may not be functioning optimally.",
        action_template="Check system status for details",
        tags={"system", "health"},
    ),
    AdviceRule(
        rule_id="system-unhealthy",
        name="System Unhealthy",
        condition="system_health and system_health.get('overall') == 'unhealthy'",
        advice_type=AdviceType.SYSTEM_HEALTH,
        priority=AdvicePriority.CRITICAL,
        title_template="System health is critical",
        description_template="One or more services are down. Check logs immediately.",
        action_template="Run diagnostics and check service logs",
        tags={"system", "critical"},
    ),

    # Documentation rules
    AdviceRule(
        rule_id="readme-missing",
        name="README Missing",
        condition="git_context and git_context.is_git_repo and 'README.md' not in git_context.untracked_files + git_context.modified_files",
        advice_type=AdviceType.DOCUMENTATION,
        priority=AdvicePriority.INFO,
        title_template="No README changes",
        description_template="Consider updating documentation if your changes affect public APIs.",
        tags={"documentation"},
    ),
]


# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXTUAL ADVISOR
# ═══════════════════════════════════════════════════════════════════════════════

class ContextualAdvisor:
    """
    Provides intelligent recommendations based on context analysis.

    Analyzes git state, system health, and user patterns to generate
    actionable advice and suggestions.
    """

    def __init__(self):
        self._context_collector: Optional[ContextCollector] = None
        self._system_status: Optional[SystemStatus] = None
        self._event_bus: Optional[EventBus] = None
        self._graph: Optional[KnowledgeGraph] = None

        # Advice rules
        self._rules: List[AdviceRule] = DEFAULT_RULES.copy()

        # Current advice cache
        self._advice_cache: Dict[str, Advice] = {}

        # Dismissed advice (persisted per session)
        self._dismissed: Set[str] = set()

        # Pattern tracking
        self._user_patterns: Dict[str, Any] = {}

    async def initialize(self) -> bool:
        """Initialize connections."""
        try:
            self._context_collector = get_context_collector()
            self._system_status = get_system_status()
            self._event_bus = get_event_bus()
            self._graph = get_knowledge_graph()

            logger.info("ContextualAdvisor initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize ContextualAdvisor: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # ADVICE GENERATION
    # ═══════════════════════════════════════════════════════════════════════════

    async def analyze_context(
        self,
        user_id: Optional[str] = None,
        include_git: bool = True,
        include_system: bool = True,
    ) -> List[Advice]:
        """
        Analyze current context and generate advice.

        Args:
            user_id: Optional user ID for personalization
            include_git: Include git context analysis
            include_system: Include system health analysis

        Returns:
            List of contextual advice
        """
        advice_list = []
        context_data = {}

        # Collect git context
        git_context = None
        if include_git:
            try:
                git_context = self._context_collector.collect_git_context()
                context_data["git_context"] = git_context
            except Exception as e:
                logger.debug(f"Could not collect git context: {e}")

        # Collect system health
        system_health = None
        if include_system:
            try:
                system_health = await self._system_status.check_all()
                context_data["system_health"] = system_health
            except Exception as e:
                logger.debug(f"Could not collect system health: {e}")

        # Evaluate rules
        for rule in self._rules:
            try:
                advice = self._evaluate_rule(rule, context_data)
                if advice and advice.advice_id not in self._dismissed:
                    advice_list.append(advice)
            except Exception as e:
                logger.debug(f"Rule evaluation error ({rule.rule_id}): {e}")

        # Custom analysis
        if git_context:
            custom_advice = self._analyze_git_patterns(git_context)
            advice_list.extend(custom_advice)

        # Cache and sort by priority
        for advice in advice_list:
            self._advice_cache[advice.advice_id] = advice

        advice_list.sort(key=lambda a: self._priority_weight(a.priority), reverse=True)

        return advice_list

    def _evaluate_rule(
        self,
        rule: AdviceRule,
        context: Dict[str, Any],
    ) -> Optional[Advice]:
        """Evaluate a single rule against context."""
        # Create evaluation context
        eval_context = {
            "git_context": context.get("git_context"),
            "system_health": context.get("system_health"),
            "user_context": context.get("user_context"),
        }

        try:
            # Evaluate condition
            if not eval(rule.condition, {"__builtins__": {}}, eval_context):
                return None

            # Generate advice
            git_ctx = eval_context.get("git_context")

            # Format templates
            format_data = {
                "count": 0,
                "branch": "",
                "files": [],
            }

            if git_ctx:
                format_data["count"] = len(git_ctx.modified_files)
                format_data["branch"] = git_ctx.current_branch
                format_data["files"] = git_ctx.modified_files

            title = rule.title_template.format(**format_data)
            description = rule.description_template.format(**format_data)
            action = rule.action_template.format(**format_data) if rule.action_template else None

            import uuid
            return Advice(
                advice_id=f"adv-{rule.rule_id}-{uuid.uuid4().hex[:6]}",
                advice_type=rule.advice_type,
                priority=rule.priority,
                title=title,
                description=description,
                action=action,
                context_source=rule.rule_id,
                tags=rule.tags.copy(),
                related_files=format_data.get("files", [])[:5],
            )

        except Exception as e:
            logger.debug(f"Rule evaluation failed: {e}")
            return None

    def _analyze_git_patterns(self, git_context: GitContext) -> List[Advice]:
        """Analyze git patterns for additional insights."""
        advice_list = []

        if not git_context or not git_context.is_git_repo:
            return advice_list

        # Check commit message patterns
        if git_context.commit_message:
            msg = git_context.commit_message.lower()

            # WIP commits
            if msg.startswith("wip") or "work in progress" in msg:
                import uuid
                advice_list.append(Advice(
                    advice_id=f"adv-wip-{uuid.uuid4().hex[:6]}",
                    advice_type=AdviceType.GIT_WORKFLOW,
                    priority=AdvicePriority.INFO,
                    title="WIP commit detected",
                    description="Remember to squash or amend WIP commits before pushing.",
                    action="Run: git commit --amend",
                    context_source="git-pattern-analysis",
                    tags={"git", "workflow"},
                ))

            # Fix commits without issue reference
            if msg.startswith("fix") and not re.search(r'#\d+|[A-Z]+-\d+', msg):
                import uuid
                advice_list.append(Advice(
                    advice_id=f"adv-fix-ref-{uuid.uuid4().hex[:6]}",
                    advice_type=AdviceType.GIT_WORKFLOW,
                    priority=AdvicePriority.SUGGESTION,
                    title="Fix commit without issue reference",
                    description="Consider linking fixes to issue tracker (e.g., #123 or JIRA-456).",
                    context_source="git-pattern-analysis",
                    tags={"git", "tracking"},
                ))

        # Check branch naming
        branch = git_context.current_branch
        if branch and branch not in ['main', 'master', 'develop']:
            # Check for common patterns
            if not re.match(r'^(feature|fix|hotfix|release|chore)/[a-z0-9-]+$', branch):
                import uuid
                advice_list.append(Advice(
                    advice_id=f"adv-branch-name-{uuid.uuid4().hex[:6]}",
                    advice_type=AdviceType.BEST_PRACTICE,
                    priority=AdvicePriority.INFO,
                    title="Non-standard branch naming",
                    description="Consider using conventional branch names like feature/*, fix/*, etc.",
                    context_source="git-pattern-analysis",
                    tags={"git", "naming"},
                ))

        return advice_list

    def _priority_weight(self, priority: AdvicePriority) -> int:
        """Get numeric weight for priority sorting."""
        weights = {
            AdvicePriority.CRITICAL: 5,
            AdvicePriority.WARNING: 4,
            AdvicePriority.RECOMMENDATION: 3,
            AdvicePriority.SUGGESTION: 2,
            AdvicePriority.INFO: 1,
        }
        return weights.get(priority, 0)

    # ═══════════════════════════════════════════════════════════════════════════
    # ADVICE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def dismiss_advice(self, advice_id: str) -> bool:
        """Dismiss an advice (won't appear again this session)."""
        if advice_id in self._advice_cache:
            self._dismissed.add(advice_id)
            self._advice_cache[advice_id].dismissed = True
            return True
        return False

    def get_active_advice(self) -> List[Advice]:
        """Get all non-dismissed advice."""
        return [
            a for a in self._advice_cache.values()
            if not a.dismissed
        ]

    def get_advice_by_type(self, advice_type: AdviceType) -> List[Advice]:
        """Get advice filtered by type."""
        return [
            a for a in self._advice_cache.values()
            if a.advice_type == advice_type and not a.dismissed
        ]

    def clear_cache(self) -> None:
        """Clear advice cache."""
        self._advice_cache.clear()

    # ═══════════════════════════════════════════════════════════════════════════
    # RULE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def add_rule(self, rule: AdviceRule) -> None:
        """Add a custom advice rule."""
        self._rules.append(rule)

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID."""
        for i, rule in enumerate(self._rules):
            if rule.rule_id == rule_id:
                self._rules.pop(i)
                return True
        return False

    def get_rules(self) -> List[AdviceRule]:
        """Get all advice rules."""
        return self._rules.copy()

    # ═══════════════════════════════════════════════════════════════════════════
    # QUICK ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════

    async def get_quick_summary(self) -> Dict[str, Any]:
        """Get a quick summary of current advice."""
        advice_list = await self.analyze_context()

        by_priority = {}
        by_type = {}

        for advice in advice_list:
            # Count by priority
            p = advice.priority.value
            by_priority[p] = by_priority.get(p, 0) + 1

            # Count by type
            t = advice.advice_type.value
            by_type[t] = by_type.get(t, 0) + 1

        return {
            "total_advice": len(advice_list),
            "by_priority": by_priority,
            "by_type": by_type,
            "critical_count": by_priority.get("critical", 0),
            "warning_count": by_priority.get("warning", 0),
            "top_advice": [a.to_dict() for a in advice_list[:3]],
        }

    async def get_contextual_prompt_addition(self) -> str:
        """Generate context-aware prompt addition for agents."""
        advice_list = await self.analyze_context()

        if not advice_list:
            return ""

        critical = [a for a in advice_list if a.priority == AdvicePriority.CRITICAL]
        warnings = [a for a in advice_list if a.priority == AdvicePriority.WARNING]

        lines = ["## Current Context Insights"]

        if critical:
            lines.append("\n### Critical Issues:")
            for a in critical[:3]:
                lines.append(f"- {a.title}: {a.description}")

        if warnings:
            lines.append("\n### Warnings:")
            for a in warnings[:3]:
                lines.append(f"- {a.title}")

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_advisor_instance: Optional[ContextualAdvisor] = None


def get_advisor() -> ContextualAdvisor:
    """Get the singleton ContextualAdvisor instance."""
    global _advisor_instance

    if _advisor_instance is None:
        _advisor_instance = ContextualAdvisor()

    return _advisor_instance


async def init_advisor() -> ContextualAdvisor:
    """Initialize and return the advisor."""
    advisor = get_advisor()
    await advisor.initialize()
    return advisor
