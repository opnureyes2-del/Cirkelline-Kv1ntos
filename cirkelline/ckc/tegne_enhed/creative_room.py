"""
CKC Kreativt Lærerum (Creative Learning Room)
=============================================

Et specialiseret lærerum for kreative opgaver.

Det Kreative Lærerum koordinerer:
    - KreativKommandant til orkestrering
    - Kreative specialister til udførelse
    - Workflow management til komplekse opgaver
    - Budget og omkostningsstyring
    - Galleri til oprettede værker

Usage:
    room, kommandant = await create_creative_room(owner="admin")

    # Simple workflow
    result = await kommandant.generate_image("A sunset over mountains")

    # Complex workflow
    workflow = CreativeJourneyCommand()
    workflow.add_step("generate", prompt="A dragon")
    workflow.add_step("style", style_name="watercolor")
    workflow.add_step("animate", motion_type="zoom_out")
    results = await workflow.execute(kommandant)
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from enum import Enum

from .core import (
    KreativKommandant,
    create_kreativ_kommandant,
    CreativeRequest,
    CreativeResult,
    CreativeCapability,
    CreativeTaskType,
    OutputFormat,
    StyleConfig,
    AnimationConfig
)
from .specialists import (
    get_creative_specialist,
    list_creative_specialists,
    ImageStyle,
    AnimationMotion
)

logger = logging.getLogger(__name__)


# ========== Enums ==========

class RoomStatus(Enum):
    """Creative room status."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PROCESSING = "processing"
    PAUSED = "paused"
    CLOSED = "closed"


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ========== Data Classes ==========

@dataclass
class CreativeGalleryItem:
    """An item in the creative gallery."""
    item_id: str
    request_id: str
    title: str
    description: str
    capability: CreativeCapability
    output_paths: List[str]
    output_urls: List[str]
    thumbnail_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "request_id": self.request_id,
            "title": self.title,
            "description": self.description,
            "capability": self.capability.value,
            "output_paths": self.output_paths,
            "output_urls": self.output_urls,
            "thumbnail_url": self.thumbnail_url,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class WorkflowStep:
    """A step in a creative workflow."""
    step_id: str
    action: str
    params: Dict[str, Any]
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Optional[CreativeResult] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "action": self.action,
            "params": self.params,
            "status": self.status.value,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


# ========== Creative Learning Room ==========

class CreativeLearningRoom:
    """
    Kreativt Lærerum - Environment for creative AI tasks.

    Features:
        - Attached KreativKommandant for orchestration
        - Gallery for created works
        - Workflow management
        - Budget tracking
        - Template library
    """

    def __init__(
        self,
        room_id: int,
        name: str = "Kreativt Lærerum",
        owner: str = "system",
        budget_limit_usd: float = 50.0
    ):
        self.room_id = room_id
        self.name = name
        self.owner = owner
        self.budget_limit_usd = budget_limit_usd

        # Status
        self.status = RoomStatus.INITIALIZING
        self.created_at = datetime.now(timezone.utc)
        self.last_activity = datetime.now(timezone.utc)

        # Kommandant (attached later)
        self.kommandant: Optional[KreativKommandant] = None

        # Gallery
        self._gallery: List[CreativeGalleryItem] = []

        # Active workflows
        self._workflows: Dict[str, "CreativeWorkflow"] = {}

        # Templates
        self._templates: Dict[str, Dict[str, Any]] = self._load_default_templates()

        # Statistics
        self.total_creations = 0
        self.total_cost_usd = 0.0

        logger.info(f"CreativeLearningRoom created: {name} (Room {room_id})")

    def _load_default_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load default creative templates."""
        return {
            "character_sheet": {
                "name": "Character Sheet",
                "description": "Generate character from multiple angles",
                "steps": [
                    {"action": "generate", "prompt_suffix": ", front view, full body"},
                    {"action": "generate", "prompt_suffix": ", side view, full body"},
                    {"action": "generate", "prompt_suffix": ", back view, full body"},
                    {"action": "generate", "prompt_suffix": ", close-up portrait"}
                ]
            },
            "animated_artwork": {
                "name": "Animated Artwork",
                "description": "Generate image and animate it",
                "steps": [
                    {"action": "generate", "params": {"size": "1024x1024"}},
                    {"action": "animate", "params": {"motion_type": "zoom_out", "duration_seconds": 5}}
                ]
            },
            "styled_variations": {
                "name": "Styled Variations",
                "description": "Create image in multiple styles",
                "steps": [
                    {"action": "generate", "params": {}},
                    {"action": "style", "params": {"style_name": "watercolor", "intensity": 0.8}},
                    {"action": "style", "params": {"style_name": "oil_painting", "intensity": 0.8}},
                    {"action": "style", "params": {"style_name": "anime", "intensity": 0.8}}
                ]
            },
            "logo_creator": {
                "name": "Logo Creator",
                "description": "Generate logo and vectorize",
                "steps": [
                    {"action": "generate", "prompt_suffix": ", logo design, minimalist, clean"},
                    {"action": "vectorize", "params": {"output_format": "svg", "detail_level": "high"}}
                ]
            }
        }

    async def initialize(self) -> bool:
        """Initialize the room and create Kommandant."""
        try:
            # Create attached Kommandant
            self.kommandant = await create_kreativ_kommandant(
                room_id=self.room_id,
                name=f"{self.name} Kommandant",
                description=f"Kommandant for {self.name}",
                budget_limit_usd=self.budget_limit_usd,
                auto_start=True
            )

            self.status = RoomStatus.ACTIVE
            logger.info(f"CreativeLearningRoom {self.name} initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize room {self.name}: {e}")
            return False

    async def close(self) -> None:
        """Close the room and cleanup."""
        if self.kommandant:
            await self.kommandant.stop()

        self.status = RoomStatus.CLOSED
        logger.info(f"CreativeLearningRoom {self.name} closed")

    # ========== Creative Operations ==========

    async def create_image(
        self,
        prompt: str,
        style: Optional[str] = None,
        **kwargs
    ) -> CreativeResult:
        """Create an image."""
        if not self.kommandant:
            raise ValueError("Room not initialized")

        self.status = RoomStatus.PROCESSING
        self.last_activity = datetime.now(timezone.utc)

        result = await self.kommandant.generate_image(
            prompt=prompt,
            style=style,
            **kwargs
        )

        if result.success:
            self._add_to_gallery(result, prompt, "Generated image")

        self.status = RoomStatus.ACTIVE
        return result

    async def animate_image(
        self,
        image_path: str,
        motion_type: str = "zoom_out",
        **kwargs
    ) -> CreativeResult:
        """Animate an image."""
        if not self.kommandant:
            raise ValueError("Room not initialized")

        self.status = RoomStatus.PROCESSING
        self.last_activity = datetime.now(timezone.utc)

        result = await self.kommandant.create_animation(
            image_path=image_path,
            motion_type=motion_type,
            **kwargs
        )

        if result.success:
            self._add_to_gallery(result, f"Animation: {motion_type}", "Animated image")

        self.status = RoomStatus.ACTIVE
        return result

    async def apply_style(
        self,
        image_path: str,
        style_name: str,
        **kwargs
    ) -> CreativeResult:
        """Apply style to an image."""
        if not self.kommandant:
            raise ValueError("Room not initialized")

        self.status = RoomStatus.PROCESSING
        self.last_activity = datetime.now(timezone.utc)

        result = await self.kommandant.apply_style(
            image_path=image_path,
            style_name=style_name,
            **kwargs
        )

        if result.success:
            self._add_to_gallery(result, f"Style: {style_name}", "Styled image")

        self.status = RoomStatus.ACTIVE
        return result

    async def vectorize_image(
        self,
        image_path: str,
        **kwargs
    ) -> CreativeResult:
        """Vectorize an image."""
        if not self.kommandant:
            raise ValueError("Room not initialized")

        self.status = RoomStatus.PROCESSING
        self.last_activity = datetime.now(timezone.utc)

        result = await self.kommandant.vectorize(
            image_path=image_path,
            **kwargs
        )

        if result.success:
            self._add_to_gallery(result, "Vectorized image", "Vector conversion")

        self.status = RoomStatus.ACTIVE
        return result

    async def run_template(
        self,
        template_name: str,
        prompt: str,
        **kwargs
    ) -> List[CreativeResult]:
        """Run a predefined template workflow."""
        if template_name not in self._templates:
            raise ValueError(f"Template not found: {template_name}")

        template = self._templates[template_name]
        results = []

        current_image = None

        for step_config in template["steps"]:
            action = step_config["action"]
            params = step_config.get("params", {}).copy()
            params.update(kwargs)

            # Add prompt suffix if specified
            if "prompt_suffix" in step_config:
                step_prompt = prompt + step_config["prompt_suffix"]
            else:
                step_prompt = prompt

            if action == "generate":
                result = await self.create_image(step_prompt, **params)
                if result.success and result.output_paths:
                    current_image = result.output_paths[0]

            elif action == "animate" and current_image:
                result = await self.animate_image(current_image, **params)

            elif action == "style" and current_image:
                result = await self.apply_style(current_image, **params)
                if result.success and result.output_paths:
                    current_image = result.output_paths[0]

            elif action == "vectorize" and current_image:
                result = await self.vectorize_image(current_image, **params)

            else:
                continue

            results.append(result)

        return results

    # ========== Gallery Management ==========

    def _add_to_gallery(
        self,
        result: CreativeResult,
        title: str,
        description: str
    ) -> CreativeGalleryItem:
        """Add a creation to the gallery."""
        item = CreativeGalleryItem(
            item_id=f"gal_{uuid.uuid4().hex[:12]}",
            request_id=result.request_id,
            title=title,
            description=description,
            capability=result.capability,
            output_paths=result.output_paths,
            output_urls=result.output_urls,
            thumbnail_url=result.output_urls[0] if result.output_urls else None,
            metadata=result.metadata
        )

        self._gallery.append(item)
        self.total_creations += 1
        self.total_cost_usd += result.cost_usd

        return item

    def get_gallery(
        self,
        limit: int = 50,
        capability: Optional[CreativeCapability] = None
    ) -> List[Dict[str, Any]]:
        """Get gallery items."""
        items = self._gallery

        if capability:
            items = [i for i in items if i.capability == capability]

        return [i.to_dict() for i in items[-limit:]]

    # ========== Status & Statistics ==========

    def get_status(self) -> Dict[str, Any]:
        """Get room status."""
        return {
            "room_id": self.room_id,
            "name": self.name,
            "owner": self.owner,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "budget_limit_usd": self.budget_limit_usd,
            "total_cost_usd": self.total_cost_usd,
            "budget_remaining_usd": self.budget_limit_usd - self.total_cost_usd,
            "total_creations": self.total_creations,
            "gallery_size": len(self._gallery),
            "templates_available": list(self._templates.keys()),
            "kommandant_status": self.kommandant.get_status() if self.kommandant else None
        }


# ========== Creative Workflow ==========

class CreativeWorkflow:
    """
    A multi-step creative workflow.

    Allows chaining multiple creative operations together.
    """

    def __init__(self, name: str = "Custom Workflow"):
        self.workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
        self.name = name
        self.status = WorkflowStatus.PENDING

        self._steps: List[WorkflowStep] = []
        self._results: List[CreativeResult] = []

        self.created_at = datetime.now(timezone.utc)
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    def add_step(
        self,
        action: str,
        **params
    ) -> "CreativeWorkflow":
        """
        Add a step to the workflow.

        Args:
            action: One of "generate", "animate", "style", "vectorize"
            **params: Parameters for the action

        Returns:
            Self for chaining
        """
        step = WorkflowStep(
            step_id=f"step_{len(self._steps)}",
            action=action,
            params=params
        )
        self._steps.append(step)
        return self

    async def execute(
        self,
        kommandant: KreativKommandant
    ) -> List[CreativeResult]:
        """
        Execute the workflow.

        Args:
            kommandant: KreativKommandant to use

        Returns:
            List of results from each step
        """
        self.status = WorkflowStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        self._results = []

        current_image = None

        try:
            for step in self._steps:
                step.status = WorkflowStatus.RUNNING
                step.started_at = datetime.now(timezone.utc)

                action = step.action
                params = step.params.copy()

                # Use output from previous step if applicable
                if current_image and "image_path" not in params:
                    if action in ["animate", "style", "vectorize"]:
                        params["image_path"] = current_image

                # Execute step
                if action == "generate":
                    result = await kommandant.generate_image(**params)
                elif action == "animate":
                    result = await kommandant.create_animation(**params)
                elif action == "style":
                    result = await kommandant.apply_style(**params)
                elif action == "vectorize":
                    result = await kommandant.vectorize(**params)
                else:
                    step.status = WorkflowStatus.FAILED
                    step.error = f"Unknown action: {action}"
                    continue

                step.result = result
                step.completed_at = datetime.now(timezone.utc)

                if result.success:
                    step.status = WorkflowStatus.COMPLETED
                    if result.output_paths:
                        current_image = result.output_paths[0]
                else:
                    step.status = WorkflowStatus.FAILED
                    step.error = result.error

                self._results.append(result)

            self.status = WorkflowStatus.COMPLETED

        except Exception as e:
            self.status = WorkflowStatus.FAILED
            logger.error(f"Workflow {self.workflow_id} failed: {e}")

        finally:
            self.completed_at = datetime.now(timezone.utc)

        return self._results

    def get_status(self) -> Dict[str, Any]:
        """Get workflow status."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self._steps],
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


# ========== Creative Journey Command ==========

class CreativeJourneyCommand:
    """
    A "Rejsekommando" (Journey Command) for creative tasks.

    Implements the standard CKC journey command pattern
    for end-to-end creative workflows.
    """

    def __init__(self, journey_name: str = "Creative Journey"):
        self.journey_id = f"journey_{uuid.uuid4().hex[:12]}"
        self.journey_name = journey_name

        self._workflow = CreativeWorkflow(name=journey_name)

        # Journey-specific settings
        self.base_prompt: Optional[str] = None
        self.style_preset: Optional[str] = None
        self.output_preferences: Dict[str, Any] = {}

        self.created_at = datetime.now(timezone.utc)

    def set_base_prompt(self, prompt: str) -> "CreativeJourneyCommand":
        """Set the base prompt for all generations."""
        self.base_prompt = prompt
        return self

    def set_style(self, style: str) -> "CreativeJourneyCommand":
        """Set default style for generations."""
        self.style_preset = style
        return self

    def add_step(self, action: str, **params) -> "CreativeJourneyCommand":
        """Add a step to the journey."""
        # Apply base settings
        if self.base_prompt and action == "generate" and "prompt" not in params:
            params["prompt"] = self.base_prompt

        if self.style_preset and action == "generate" and "style" not in params:
            params["style"] = self.style_preset

        self._workflow.add_step(action, **params)
        return self

    async def execute(
        self,
        kommandant: KreativKommandant
    ) -> Dict[str, Any]:
        """
        Execute the creative journey.

        Args:
            kommandant: KreativKommandant to use

        Returns:
            Dict with journey results
        """
        logger.info(f"Starting Creative Journey: {self.journey_name}")

        results = await self._workflow.execute(kommandant)

        # Calculate totals
        total_cost = sum(r.cost_usd for r in results)
        successful = sum(1 for r in results if r.success)
        total_steps = len(results)

        return {
            "journey_id": self.journey_id,
            "journey_name": self.journey_name,
            "success": successful == total_steps,
            "steps_completed": successful,
            "total_steps": total_steps,
            "total_cost_usd": total_cost,
            "results": [r.to_dict() for r in results],
            "workflow_status": self._workflow.get_status()
        }


# ========== Factory Functions ==========

_creative_rooms: Dict[int, CreativeLearningRoom] = {}
_room_counter = 0


async def create_creative_room(
    owner: str = "system",
    name: Optional[str] = None,
    budget_limit_usd: float = 50.0
) -> tuple[CreativeLearningRoom, KreativKommandant]:
    """
    Create a new Creative Learning Room.

    Args:
        owner: Room owner
        name: Room name (auto-generated if not provided)
        budget_limit_usd: Budget limit

    Returns:
        Tuple of (CreativeLearningRoom, KreativKommandant)
    """
    global _room_counter
    _room_counter += 1

    room_id = _room_counter
    room_name = name or f"Kreativt Lærerum #{room_id}"

    room = CreativeLearningRoom(
        room_id=room_id,
        name=room_name,
        owner=owner,
        budget_limit_usd=budget_limit_usd
    )

    await room.initialize()

    _creative_rooms[room_id] = room

    logger.info(f"Creative room created: {room_name} (ID: {room_id})")

    return room, room.kommandant


async def get_creative_room(room_id: int) -> Optional[CreativeLearningRoom]:
    """Get a Creative Learning Room by ID."""
    return _creative_rooms.get(room_id)


def list_creative_rooms() -> List[Dict[str, Any]]:
    """List all Creative Learning Rooms."""
    return [room.get_status() for room in _creative_rooms.values()]


logger.info("CKC Tegne-enhed Creative Room module loaded")
