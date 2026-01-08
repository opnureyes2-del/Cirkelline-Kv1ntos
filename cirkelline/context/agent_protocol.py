"""
Agent Communication Protocol
============================
Standardized message format for agent-to-agent communication.

Defines:
- Message types and structure
- Agent capabilities registry
- Request/Response patterns
- Error handling

Used by agents to communicate through the Event Bus.
"""

import logging
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# MESSAGE TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class MessageType(str, Enum):
    """Types of messages between agents."""

    # Request/Response
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"

    # Coordination
    DELEGATE = "delegate"
    ACCEPT = "accept"
    REJECT = "reject"
    COMPLETE = "complete"

    # Information
    NOTIFY = "notify"
    BROADCAST = "broadcast"
    HEARTBEAT = "heartbeat"

    # Control
    START = "start"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"


class MessagePriority(int, Enum):
    """Priority levels for message handling."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT CAPABILITIES
# ═══════════════════════════════════════════════════════════════════════════════

class AgentCapability(str, Enum):
    """Standard capabilities an agent can declare."""

    # Media Processing
    AUDIO_TRANSCRIPTION = "audio:transcription"
    AUDIO_ANALYSIS = "audio:analysis"
    VIDEO_ANALYSIS = "video:analysis"
    VIDEO_TRANSCRIPTION = "video:transcription"
    IMAGE_OCR = "image:ocr"
    IMAGE_ANALYSIS = "image:analysis"
    DOCUMENT_PROCESSING = "document:processing"
    DOCUMENT_OCR = "document:ocr"

    # Research
    WEB_SEARCH = "research:web_search"
    DEEP_RESEARCH = "research:deep_research"
    FACT_CHECK = "research:fact_check"
    SUMMARIZATION = "research:summarization"

    # Legal
    LEGAL_RESEARCH = "legal:research"
    LEGAL_ANALYSIS = "legal:analysis"
    CONTRACT_REVIEW = "legal:contract_review"

    # General
    CONVERSATION = "general:conversation"
    TRANSLATION = "general:translation"
    CODE_REVIEW = "code:review"
    CODE_GENERATION = "code:generation"

    # Integration
    GOOGLE_SERVICES = "integration:google"
    NOTION_SERVICES = "integration:notion"
    CALENDAR = "integration:calendar"
    EMAIL = "integration:email"


@dataclass
class AgentDescriptor:
    """Description of an agent's identity and capabilities."""
    agent_id: str
    name: str
    role: str
    capabilities: List[AgentCapability] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    max_concurrent_tasks: int = 1
    status: str = "idle"
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "capabilities": [c.value for c in self.capabilities],
            "tools": self.tools,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "status": self.status,
            "version": self.version,
        }

    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has a specific capability."""
        return capability in self.capabilities


# ═══════════════════════════════════════════════════════════════════════════════
# MESSAGE STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AgentMessage:
    """
    Standard message format for agent communication.

    All agent-to-agent communication uses this structure.
    Messages are sent through the Event Bus.
    """
    # Identifiers
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    correlation_id: Optional[str] = None  # For request/response tracking

    # Routing
    sender: str = ""
    recipient: str = ""  # Empty = broadcast

    # Content
    message_type: MessageType = MessageType.NOTIFY
    priority: MessagePriority = MessagePriority.NORMAL
    action: str = ""  # Specific action to perform
    payload: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    ttl: Optional[int] = None  # Time-to-live in seconds
    requires_response: bool = False

    # Context
    mission_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "message_id": self.message_id,
            "correlation_id": self.correlation_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "action": self.action,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "requires_response": self.requires_response,
            "mission_id": self.mission_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        """Reconstruct from dictionary."""
        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())[:12]),
            correlation_id=data.get("correlation_id"),
            sender=data.get("sender", ""),
            recipient=data.get("recipient", ""),
            message_type=MessageType(data.get("message_type", "notify")),
            priority=MessagePriority(data.get("priority", 1)),
            action=data.get("action", ""),
            payload=data.get("payload", {}),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            ttl=data.get("ttl"),
            requires_response=data.get("requires_response", False),
            mission_id=data.get("mission_id"),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
        )

    def create_response(
        self,
        sender: str,
        payload: Dict[str, Any],
        success: bool = True,
    ) -> "AgentMessage":
        """Create a response message to this request."""
        return AgentMessage(
            correlation_id=self.message_id,
            sender=sender,
            recipient=self.sender,
            message_type=MessageType.RESPONSE if success else MessageType.ERROR,
            priority=self.priority,
            action=f"{self.action}:response",
            payload=payload,
            mission_id=self.mission_id,
            session_id=self.session_id,
            user_id=self.user_id,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# MESSAGE FACTORIES
# ═══════════════════════════════════════════════════════════════════════════════

def create_agent_message(
    sender: str,
    recipient: str,
    action: str,
    payload: Dict[str, Any],
    message_type: MessageType = MessageType.REQUEST,
    priority: MessagePriority = MessagePriority.NORMAL,
    requires_response: bool = False,
    mission_id: Optional[str] = None,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> AgentMessage:
    """
    Factory function to create agent messages.

    Args:
        sender: ID of sending agent
        recipient: ID of receiving agent (empty for broadcast)
        action: Action to perform
        payload: Message payload
        message_type: Type of message
        priority: Message priority
        requires_response: Whether a response is expected
        mission_id: Associated mission ID
        session_id: Associated session ID
        user_id: Associated user ID

    Returns:
        AgentMessage ready to send
    """
    return AgentMessage(
        sender=sender,
        recipient=recipient,
        action=action,
        payload=payload,
        message_type=message_type,
        priority=priority,
        requires_response=requires_response,
        mission_id=mission_id,
        session_id=session_id,
        user_id=user_id,
    )


def create_delegation_request(
    sender: str,
    recipient: str,
    task: str,
    context: Dict[str, Any],
    mission_id: Optional[str] = None,
) -> AgentMessage:
    """Create a task delegation request."""
    return AgentMessage(
        sender=sender,
        recipient=recipient,
        message_type=MessageType.DELEGATE,
        action="delegate:task",
        payload={
            "task": task,
            "context": context,
        },
        requires_response=True,
        mission_id=mission_id,
    )


def create_broadcast(
    sender: str,
    topic: str,
    data: Dict[str, Any],
    priority: MessagePriority = MessagePriority.NORMAL,
) -> AgentMessage:
    """Create a broadcast message to all agents."""
    return AgentMessage(
        sender=sender,
        recipient="",  # Empty = broadcast
        message_type=MessageType.BROADCAST,
        action=f"broadcast:{topic}",
        payload=data,
        priority=priority,
    )


def create_heartbeat(agent_id: str, status: str = "healthy") -> AgentMessage:
    """Create a heartbeat message."""
    return AgentMessage(
        sender=agent_id,
        recipient="headquarters",
        message_type=MessageType.HEARTBEAT,
        action="heartbeat",
        payload={
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        },
        ttl=60,  # Heartbeats expire quickly
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CAPABILITY REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

class CapabilityRegistry:
    """
    Registry of agent capabilities for routing.

    Used by the orchestrator to find agents with specific capabilities.
    """

    def __init__(self):
        self._agents: Dict[str, AgentDescriptor] = {}
        self._capability_index: Dict[AgentCapability, List[str]] = {}

    def register(self, descriptor: AgentDescriptor) -> None:
        """Register an agent and its capabilities."""
        self._agents[descriptor.agent_id] = descriptor

        for capability in descriptor.capabilities:
            if capability not in self._capability_index:
                self._capability_index[capability] = []
            if descriptor.agent_id not in self._capability_index[capability]:
                self._capability_index[capability].append(descriptor.agent_id)

        logger.info(f"Registered agent {descriptor.agent_id} with {len(descriptor.capabilities)} capabilities")

    def unregister(self, agent_id: str) -> None:
        """Unregister an agent."""
        if agent_id not in self._agents:
            return

        descriptor = self._agents.pop(agent_id)

        for capability in descriptor.capabilities:
            if capability in self._capability_index:
                self._capability_index[capability] = [
                    aid for aid in self._capability_index[capability]
                    if aid != agent_id
                ]

    def find_by_capability(
        self,
        capability: AgentCapability,
        exclude: Optional[List[str]] = None,
    ) -> List[AgentDescriptor]:
        """Find all agents with a specific capability."""
        exclude = exclude or []
        agent_ids = self._capability_index.get(capability, [])

        return [
            self._agents[aid]
            for aid in agent_ids
            if aid not in exclude and aid in self._agents
        ]

    def get_agent(self, agent_id: str) -> Optional[AgentDescriptor]:
        """Get descriptor for a specific agent."""
        return self._agents.get(agent_id)

    def get_all_agents(self) -> List[AgentDescriptor]:
        """Get all registered agents."""
        return list(self._agents.values())

    def get_available_agents(self) -> List[AgentDescriptor]:
        """Get all agents with idle status."""
        return [a for a in self._agents.values() if a.status == "idle"]


# Singleton registry instance
_capability_registry: Optional[CapabilityRegistry] = None


def get_capability_registry() -> CapabilityRegistry:
    """Get the singleton CapabilityRegistry instance."""
    global _capability_registry

    if _capability_registry is None:
        _capability_registry = CapabilityRegistry()

    return _capability_registry
