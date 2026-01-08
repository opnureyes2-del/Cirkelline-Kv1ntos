"""
CKC MASTERMIND Context Management
=================================

Provides continuous context management across MASTERMIND sessions.

Key components:
- DirigentContextManager: Context aggregation and retrieval
- TaskTemplateEngine: Task instruction templates
- AutoDocumentationTrigger: Auto-documentation events

Reference: DEL D fra FASE_3_MASTERMIND_PLAN.md
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class ContextSource(Enum):
    """Sources of context information."""
    CURRENT_SESSION = "current_session"
    PREVIOUS_SESSION = "previous_session"
    KNOWLEDGE_BANK = "knowledge_bank"
    NOTION_DOC = "notion_doc"
    AGENT_MEMORY = "agent_memory"
    USER_PREFERENCE = "user_preference"


class DocumentationType(Enum):
    """Types of auto-generated documentation."""
    SESSION_REPORT = "session_report"
    ASSET_DOCUMENTATION = "asset_documentation"
    WORKFLOW_DOCUMENTATION = "workflow_documentation"
    INCIDENT_REPORT = "incident_report"
    PERFORMANCE_REPORT = "performance_report"


class TriggerEvent(Enum):
    """Events that trigger auto-documentation."""
    SESSION_COMPLETED = "session_completed"
    ASSET_CREATED = "asset_created"
    WORKFLOW_COMPLETED = "workflow_completed"
    PERFORMANCE_ANOMALY = "performance_anomaly"
    ERROR_OCCURRED = "error_occurred"
    MILESTONE_REACHED = "milestone_reached"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ContextItem:
    """A single piece of context information."""
    item_id: str
    source: ContextSource
    title: str
    content: str
    relevance_score: float = 0.0  # 0.0 - 1.0

    # Metadata
    source_id: Optional[str] = None  # session_id, doc_id, etc.
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "source": self.source.value,
            "title": self.title,
            "content": self.content,
            "relevance_score": self.relevance_score,
            "source_id": self.source_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "tags": self.tags,
        }


@dataclass
class ContextBundle:
    """A bundle of context items for a task."""
    bundle_id: str
    task_description: str
    items: List[ContextItem] = field(default_factory=list)

    # Summary
    summary: str = ""
    total_relevance: float = 0.0

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_item(self, item: ContextItem):
        self.items.append(item)
        self._update_relevance()

    def _update_relevance(self):
        if self.items:
            self.total_relevance = sum(i.relevance_score for i in self.items) / len(self.items)

    def get_top_items(self, n: int = 5) -> List[ContextItem]:
        """Get top N most relevant items."""
        sorted_items = sorted(self.items, key=lambda x: x.relevance_score, reverse=True)
        return sorted_items[:n]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "task_description": self.task_description,
            "items": [i.to_dict() for i in self.items],
            "summary": self.summary,
            "total_relevance": self.total_relevance,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Reference:
    """A reference to related content."""
    reference_id: str
    reference_type: str  # "session", "document", "asset", "task"
    target_id: str
    title: str
    description: str
    url: Optional[str] = None
    relevance_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "reference_type": self.reference_type,
            "target_id": self.target_id,
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "relevance_score": self.relevance_score,
        }


@dataclass
class TaskTemplate:
    """Template for task instructions."""
    template_id: str
    name: str
    template: str

    # Placeholders
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)

    def render(self, **kwargs) -> str:
        """Render template with provided values."""
        result = self.template
        for key, value in kwargs.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, str(value))
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "template": self.template,
            "required_fields": self.required_fields,
            "optional_fields": self.optional_fields,
        }


@dataclass
class DocumentationEvent:
    """An event that triggers documentation generation."""
    event_id: str
    event_type: TriggerEvent
    doc_type: DocumentationType

    # Context
    session_id: Optional[str] = None
    source_data: Dict[str, Any] = field(default_factory=dict)

    # Generated doc
    generated_doc: Optional[str] = None
    doc_path: Optional[str] = None

    # Timestamps
    triggered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "doc_type": self.doc_type.value,
            "session_id": self.session_id,
            "source_data": self.source_data,
            "generated_doc": self.generated_doc,
            "doc_path": self.doc_path,
            "triggered_at": self.triggered_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


# =============================================================================
# DIRIGENT CONTEXT MANAGER
# =============================================================================

class DirigentContextManager:
    """
    Manages context across MASTERMIND sessions.

    Responsibilities:
    - Aggregate relevant context from multiple sources
    - Create context summaries
    - Find cross-references between sessions and documents
    """

    def __init__(self):
        self._context_cache: Dict[str, ContextBundle] = {}
        self._reference_index: Dict[str, List[Reference]] = {}
        self._session_context: Dict[str, Dict[str, Any]] = {}

    async def get_relevant_context(
        self,
        task_description: str,
        session_id: Optional[str] = None,
        sources: Optional[List[ContextSource]] = None,
        max_items: int = 10,
    ) -> ContextBundle:
        """
        Get relevant context for a task.

        Args:
            task_description: Description of the task
            session_id: Current session ID
            sources: Which sources to query
            max_items: Maximum context items to return

        Returns:
            ContextBundle with relevant context
        """
        bundle = ContextBundle(
            bundle_id=f"ctx_{uuid.uuid4().hex[:12]}",
            task_description=task_description,
        )

        sources = sources or list(ContextSource)

        # Gather context from each source
        for source in sources:
            items = await self._gather_from_source(
                source=source,
                task_description=task_description,
                session_id=session_id,
            )
            for item in items:
                bundle.add_item(item)

        # Keep only top items
        bundle.items = bundle.get_top_items(max_items)

        # Generate summary
        bundle.summary = await self._generate_summary(bundle)

        # Cache
        self._context_cache[bundle.bundle_id] = bundle

        logger.info(f"Created context bundle {bundle.bundle_id} with {len(bundle.items)} items")
        return bundle

    async def _gather_from_source(
        self,
        source: ContextSource,
        task_description: str,
        session_id: Optional[str] = None,
    ) -> List[ContextItem]:
        """Gather context items from a specific source."""
        items = []

        if source == ContextSource.CURRENT_SESSION and session_id:
            # Get context from current session
            if session_id in self._session_context:
                ctx = self._session_context[session_id]
                items.append(ContextItem(
                    item_id=f"ctx_item_{uuid.uuid4().hex[:8]}",
                    source=source,
                    title=f"Current Session: {session_id[:12]}",
                    content=str(ctx.get("objective", "")),
                    relevance_score=1.0,  # Current session is always relevant
                    source_id=session_id,
                    tags=ctx.get("tags", []),
                ))

        elif source == ContextSource.PREVIOUS_SESSION:
            # Find related previous sessions
            for sid, ctx in self._session_context.items():
                if sid != session_id:
                    # Simple relevance check (in production: use embeddings)
                    relevance = self._calculate_relevance(
                        task_description,
                        ctx.get("objective", "")
                    )
                    if relevance > 0.3:
                        items.append(ContextItem(
                            item_id=f"ctx_item_{uuid.uuid4().hex[:8]}",
                            source=source,
                            title=f"Previous Session: {sid[:12]}",
                            content=ctx.get("objective", ""),
                            relevance_score=relevance,
                            source_id=sid,
                        ))

        elif source == ContextSource.KNOWLEDGE_BANK:
            # Stub: Would query knowledge bank
            items.append(ContextItem(
                item_id=f"ctx_item_{uuid.uuid4().hex[:8]}",
                source=source,
                title="Knowledge Bank Context",
                content="Relevant knowledge from CKC documentation",
                relevance_score=0.7,
            ))

        elif source == ContextSource.AGENT_MEMORY:
            # Stub: Would query agent memories
            pass

        return items

    def _calculate_relevance(self, query: str, text: str) -> float:
        """Calculate simple relevance score between query and text."""
        if not query or not text:
            return 0.0

        query_words = set(query.lower().split())
        text_words = set(text.lower().split())

        if not query_words:
            return 0.0

        intersection = query_words & text_words
        return len(intersection) / len(query_words)

    async def _generate_summary(self, bundle: ContextBundle) -> str:
        """Generate a summary of the context bundle."""
        if not bundle.items:
            return "No relevant context found."

        summaries = []
        for item in bundle.items[:3]:  # Top 3
            summaries.append(f"- {item.title}: {item.content[:100]}...")

        return f"Context summary for '{bundle.task_description}':\n" + "\n".join(summaries)

    async def create_context_summary(
        self,
        sources: List[str],
        max_length: int = 500,
    ) -> str:
        """Create a summary from multiple context sources."""
        summaries = []

        for source_id in sources:
            if source_id in self._context_cache:
                bundle = self._context_cache[source_id]
                summaries.append(bundle.summary)
            elif source_id in self._session_context:
                ctx = self._session_context[source_id]
                summaries.append(f"Session {source_id[:12]}: {ctx.get('objective', '')}")

        combined = " | ".join(summaries)
        return combined[:max_length]

    async def cross_reference(
        self,
        task_description: str,
        current_session_id: Optional[str] = None,
    ) -> List[Reference]:
        """Find cross-references to related sessions and documents."""
        references = []

        # Search in session context
        for sid, ctx in self._session_context.items():
            if sid == current_session_id:
                continue

            relevance = self._calculate_relevance(
                task_description,
                ctx.get("objective", "") + " " + " ".join(ctx.get("tags", []))
            )

            if relevance > 0.2:
                references.append(Reference(
                    reference_id=f"ref_{uuid.uuid4().hex[:8]}",
                    reference_type="session",
                    target_id=sid,
                    title=f"Session: {ctx.get('title', sid[:12])}",
                    description=ctx.get("objective", "")[:200],
                    relevance_score=relevance,
                ))

        # Search in reference index
        for key, refs in self._reference_index.items():
            if self._calculate_relevance(task_description, key) > 0.3:
                references.extend(refs)

        # Sort by relevance
        references.sort(key=lambda x: x.relevance_score, reverse=True)

        return references[:10]  # Return top 10

    def register_session_context(
        self,
        session_id: str,
        objective: str,
        tags: Optional[List[str]] = None,
        **extra_context
    ):
        """Register context for a session."""
        self._session_context[session_id] = {
            "objective": objective,
            "tags": tags or [],
            "title": extra_context.get("title", ""),
            **extra_context,
        }
        logger.debug(f"Registered context for session {session_id}")

    def add_reference(self, key: str, reference: Reference):
        """Add a reference to the index."""
        if key not in self._reference_index:
            self._reference_index[key] = []
        self._reference_index[key].append(reference)

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "cached_bundles": len(self._context_cache),
            "session_contexts": len(self._session_context),
            "reference_keys": len(self._reference_index),
            "total_references": sum(len(refs) for refs in self._reference_index.values()),
        }


# =============================================================================
# TASK TEMPLATE ENGINE
# =============================================================================

class TaskTemplateEngine:
    """
    Provides templates for creating structured task instructions.

    Reference: DEL D.1 fra FASE_3_MASTERMIND_PLAN.md
    """

    DEFAULT_TEMPLATE = """## OPGAVE: {title}

### MÅL
{objective}

### KONTEKST
- Mastermind Session: {session_id}
- Relaterede sessioner: {related_sessions}
- Relevant dokumentation: {documentation}

### TRIN
{steps}

### BEGRÆNSNINGER
{constraints}

### FORVENTET OUTPUT
{expected_output}

### RESSOURCER
{resources}
"""

    def __init__(self):
        self._templates: Dict[str, TaskTemplate] = {}
        self._register_default_templates()

    def _register_default_templates(self):
        """Register default task templates."""
        # Standard task template
        self._templates["standard"] = TaskTemplate(
            template_id="tmpl_standard",
            name="Standard Task",
            template=self.DEFAULT_TEMPLATE,
            required_fields=["title", "objective"],
            optional_fields=[
                "session_id", "related_sessions", "documentation",
                "steps", "constraints", "expected_output", "resources"
            ],
        )

        # Creative task template
        self._templates["creative"] = TaskTemplate(
            template_id="tmpl_creative",
            name="Creative Task",
            template="""## KREATIV OPGAVE: {title}

### VISION
{vision}

### STIL & TONE
- Stil: {style}
- Tone: {tone}
- Inspiration: {inspiration}

### TEKNISKE SPECIFIKATIONER
- Format: {format}
- Dimensioner: {dimensions}
- Kvalitet: {quality}

### KREATIVE BEGRÆNSNINGER
{constraints}

### FORVENTET RESULTAT
{expected_output}
""",
            required_fields=["title", "vision"],
            optional_fields=[
                "style", "tone", "inspiration", "format",
                "dimensions", "quality", "constraints", "expected_output"
            ],
        )

        # Research task template
        self._templates["research"] = TaskTemplate(
            template_id="tmpl_research",
            name="Research Task",
            template="""## RESEARCH: {title}

### FORSKNINGSSPØRGSMÅL
{research_question}

### SCOPE
- Domæne: {domain}
- Dybde: {depth}
- Tidsramme: {timeframe}

### KILDER
{sources}

### FORVENTET OUTPUT
- Format: {output_format}
- Længde: {length}
- Struktur: {structure}
""",
            required_fields=["title", "research_question"],
            optional_fields=[
                "domain", "depth", "timeframe", "sources",
                "output_format", "length", "structure"
            ],
        )

    def get_template(self, template_name: str) -> Optional[TaskTemplate]:
        """Get a template by name."""
        return self._templates.get(template_name)

    def list_templates(self) -> List[str]:
        """List available template names."""
        return list(self._templates.keys())

    def render_task(
        self,
        template_name: str,
        **kwargs
    ) -> str:
        """Render a task instruction from template."""
        template = self._templates.get(template_name)
        if not template:
            template = self._templates["standard"]

        # Fill in defaults for missing optional fields
        for field in template.optional_fields:
            if field not in kwargs:
                kwargs[field] = "[Ikke specificeret]"

        return template.render(**kwargs)

    def register_template(self, name: str, template: TaskTemplate):
        """Register a custom template."""
        self._templates[name] = template
        logger.info(f"Registered template: {name}")


# =============================================================================
# AUTO-DOCUMENTATION TRIGGER
# =============================================================================

class AutoDocumentationTrigger:
    """
    Handles automatic documentation generation based on events.

    Reference: DEL D.3 fra FASE_3_MASTERMIND_PLAN.md
    """

    def __init__(self):
        self._event_handlers: Dict[TriggerEvent, List[Callable]] = {}
        self._event_history: List[DocumentationEvent] = []
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default event handlers."""
        for event_type in TriggerEvent:
            self._event_handlers[event_type] = []

    async def trigger(
        self,
        event_type: TriggerEvent,
        session_id: Optional[str] = None,
        source_data: Optional[Dict[str, Any]] = None,
    ) -> DocumentationEvent:
        """
        Trigger an auto-documentation event.

        Args:
            event_type: Type of event
            session_id: Related session ID
            source_data: Data for documentation generation

        Returns:
            DocumentationEvent with generated documentation
        """
        # Determine doc type from event
        doc_type = self._event_to_doc_type(event_type)

        event = DocumentationEvent(
            event_id=f"doc_evt_{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            doc_type=doc_type,
            session_id=session_id,
            source_data=source_data or {},
        )

        # Generate documentation
        event.generated_doc = await self._generate_documentation(event)
        event.completed_at = datetime.now(timezone.utc)

        # Call registered handlers
        for handler in self._event_handlers.get(event_type, []):
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Handler error for {event_type}: {e}")

        # Store in history
        self._event_history.append(event)

        logger.info(f"Documentation triggered: {event_type.value} -> {doc_type.value}")
        return event

    def _event_to_doc_type(self, event_type: TriggerEvent) -> DocumentationType:
        """Map event type to documentation type."""
        mapping = {
            TriggerEvent.SESSION_COMPLETED: DocumentationType.SESSION_REPORT,
            TriggerEvent.ASSET_CREATED: DocumentationType.ASSET_DOCUMENTATION,
            TriggerEvent.WORKFLOW_COMPLETED: DocumentationType.WORKFLOW_DOCUMENTATION,
            TriggerEvent.PERFORMANCE_ANOMALY: DocumentationType.PERFORMANCE_REPORT,
            TriggerEvent.ERROR_OCCURRED: DocumentationType.INCIDENT_REPORT,
            TriggerEvent.MILESTONE_REACHED: DocumentationType.SESSION_REPORT,
        }
        return mapping.get(event_type, DocumentationType.SESSION_REPORT)

    async def _generate_documentation(self, event: DocumentationEvent) -> str:
        """Generate documentation based on event."""
        doc_type = event.doc_type
        data = event.source_data

        if doc_type == DocumentationType.SESSION_REPORT:
            return self._generate_session_report(data)
        elif doc_type == DocumentationType.ASSET_DOCUMENTATION:
            return self._generate_asset_doc(data)
        elif doc_type == DocumentationType.WORKFLOW_DOCUMENTATION:
            return self._generate_workflow_doc(data)
        elif doc_type == DocumentationType.INCIDENT_REPORT:
            return self._generate_incident_report(data)
        elif doc_type == DocumentationType.PERFORMANCE_REPORT:
            return self._generate_performance_report(data)
        else:
            return "Dokumentation ikke tilgængelig."

    def _generate_session_report(self, data: Dict[str, Any]) -> str:
        return f"""# Session Rapport

**Session ID:** {data.get('session_id', 'N/A')}
**Status:** {data.get('status', 'Completed')}
**Objektiv:** {data.get('objective', 'N/A')}

## Resultater
{data.get('results_summary', 'Ingen resultater registreret.')}

## Metrics
- Varighed: {data.get('duration', 'N/A')}
- Tasks udført: {data.get('tasks_completed', 0)}
- Budget brugt: ${data.get('budget_used', 0):.2f}

---
*Auto-genereret af CKC MASTERMIND*
"""

    def _generate_asset_doc(self, data: Dict[str, Any]) -> str:
        return f"""# Asset Dokumentation

**Asset ID:** {data.get('asset_id', 'N/A')}
**Type:** {data.get('asset_type', 'N/A')}
**Oprettet:** {data.get('created_at', 'N/A')}

## Beskrivelse
{data.get('description', 'Ingen beskrivelse.')}

## Metadata
- Prompt: {data.get('prompt', 'N/A')}
- Model: {data.get('model', 'N/A')}
- Kvalitet: {data.get('quality_score', 'N/A')}

---
*Auto-genereret af CKC MASTERMIND*
"""

    def _generate_workflow_doc(self, data: Dict[str, Any]) -> str:
        return f"""# Workflow Dokumentation

**Workflow:** {data.get('workflow_name', 'N/A')}
**Status:** {data.get('status', 'Completed')}

## Trin
{data.get('steps_summary', 'Ingen trin registreret.')}

## Outputs
{data.get('outputs_summary', 'Ingen outputs.')}

---
*Auto-genereret af CKC MASTERMIND*
"""

    def _generate_incident_report(self, data: Dict[str, Any]) -> str:
        return f"""# Incident Rapport

**Severity:** {data.get('severity', 'Unknown')}
**Tidspunkt:** {data.get('timestamp', 'N/A')}

## Beskrivelse
{data.get('description', 'Ingen beskrivelse.')}

## Årsag
{data.get('cause', 'Under undersøgelse.')}

## Handling
{data.get('action_taken', 'Ingen handling registreret.')}

---
*Auto-genereret af CKC MASTERMIND*
"""

    def _generate_performance_report(self, data: Dict[str, Any]) -> str:
        return f"""# Performance Rapport

**Periode:** {data.get('period', 'N/A')}

## Metrics
- Latency: {data.get('avg_latency', 'N/A')}ms
- Throughput: {data.get('throughput', 'N/A')} req/s
- Error rate: {data.get('error_rate', 'N/A')}%

## Anomalier
{data.get('anomalies', 'Ingen anomalier detekteret.')}

---
*Auto-genereret af CKC MASTERMIND*
"""

    def register_handler(
        self,
        event_type: TriggerEvent,
        handler: Callable,
    ):
        """Register a custom handler for an event type."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def get_history(
        self,
        event_type: Optional[TriggerEvent] = None,
        limit: int = 100,
    ) -> List[DocumentationEvent]:
        """Get event history."""
        events = self._event_history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_events": len(self._event_history),
            "by_type": {
                et.value: len([e for e in self._event_history if e.event_type == et])
                for et in TriggerEvent
            },
            "registered_handlers": {
                et.value: len(handlers)
                for et, handlers in self._event_handlers.items()
            },
        }


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

_context_manager: Optional[DirigentContextManager] = None
_template_engine: Optional[TaskTemplateEngine] = None
_doc_trigger: Optional[AutoDocumentationTrigger] = None


async def create_context_manager() -> DirigentContextManager:
    """Create or get DirigentContextManager instance."""
    global _context_manager
    if _context_manager is None:
        _context_manager = DirigentContextManager()
    return _context_manager


def get_context_manager() -> Optional[DirigentContextManager]:
    """Get existing context manager."""
    return _context_manager


def create_template_engine() -> TaskTemplateEngine:
    """Create or get TaskTemplateEngine instance."""
    global _template_engine
    if _template_engine is None:
        _template_engine = TaskTemplateEngine()
    return _template_engine


def get_template_engine() -> Optional[TaskTemplateEngine]:
    """Get existing template engine."""
    return _template_engine


async def create_doc_trigger() -> AutoDocumentationTrigger:
    """Create or get AutoDocumentationTrigger instance."""
    global _doc_trigger
    if _doc_trigger is None:
        _doc_trigger = AutoDocumentationTrigger()
    return _doc_trigger


def get_doc_trigger() -> Optional[AutoDocumentationTrigger]:
    """Get existing doc trigger."""
    return _doc_trigger


logger.info("CKC MASTERMIND context module loaded")
