"""
CKC Tegne-enhed (Drawing Unit)
==============================

Kreative agenter til billede-generering, animation, stil-overførsel og vektorisering.

Den Kreative Kommandant koordinerer:
    - Text-to-Image generering (via Replicate/SDXL)
    - Image-to-Animation (via Luma AI)
    - Style Transfer (via Prodia API)
    - Vektorisering (via Vectorizer.AI)

Usage:
    from cirkelline.ckc.tegne_enhed import (
        create_creative_room,
        get_creative_kommandant,
        KreativKommandant,
        ImageGeneratorSpecialist,
        AnimatorSpecialist,
        StyleTransferSpecialist,
        VectorizerSpecialist,
    )

    # Create a creative learning room
    room, kommandant = await create_creative_room(owner="admin")

    # Generate an image
    result = await kommandant.generate_image(
        prompt="A majestic dragon flying over mountains at sunset",
        style="fantasy",
        size="1024x1024"
    )

    # Create animation from image
    animation = await kommandant.create_animation(
        image_path=result["image_path"],
        duration_seconds=5,
        motion_type="zoom_out"
    )
"""

from .core import (
    # Main class
    KreativKommandant,
    # Enums
    CreativeCapability,
    CreativeTaskType,
    OutputFormat,
    # Data classes
    CreativeRequest,
    CreativeResult,
    StyleConfig,
    AnimationConfig,
    # Factory functions
    create_kreativ_kommandant,
    get_kreativ_kommandant,
)

from .specialists import (
    # Base
    CreativeSpecialist,
    # Specialists
    ImageGeneratorSpecialist,
    AnimatorSpecialist,
    StyleTransferSpecialist,
    VectorizerSpecialist,
    # Enums
    ImageStyle,
    AnimationMotion,
    VectorFormat,
    # Factory
    get_creative_specialist,
    list_creative_specialists,
)

from .api_integrations import (
    # API Clients
    ReplicateClient,
    LumaAIClient,
    ProdiaClient,
    VectorizerAIClient,
    # Base
    CreativeAPIClient,
    APIResponse,
    # Factory
    get_api_client,
    # Utilities
    estimate_cost,
    check_api_health,
)

from .creative_room import (
    # Main
    CreativeLearningRoom,
    # Functions
    create_creative_room,
    get_creative_room,
    list_creative_rooms,
    # Commands
    CreativeJourneyCommand,
    CreativeWorkflow,
)

__all__ = [
    # Core
    "KreativKommandant",
    "CreativeCapability",
    "CreativeTaskType",
    "OutputFormat",
    "CreativeRequest",
    "CreativeResult",
    "StyleConfig",
    "AnimationConfig",
    "create_kreativ_kommandant",
    "get_kreativ_kommandant",
    # Specialists
    "CreativeSpecialist",
    "ImageGeneratorSpecialist",
    "AnimatorSpecialist",
    "StyleTransferSpecialist",
    "VectorizerSpecialist",
    "ImageStyle",
    "AnimationMotion",
    "VectorFormat",
    "get_creative_specialist",
    "list_creative_specialists",
    # API
    "ReplicateClient",
    "LumaAIClient",
    "ProdiaClient",
    "VectorizerAIClient",
    "CreativeAPIClient",
    "APIResponse",
    "get_api_client",
    "estimate_cost",
    "check_api_health",
    # Room
    "CreativeLearningRoom",
    "create_creative_room",
    "get_creative_room",
    "list_creative_rooms",
    "CreativeJourneyCommand",
    "CreativeWorkflow",
]
