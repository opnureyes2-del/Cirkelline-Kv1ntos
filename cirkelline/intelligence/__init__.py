"""
Intelligence Module
====================
Advanced AI capabilities for contextual awareness and proactive assistance.

Components:
- Contextual Advisor: Intelligent recommendations based on context
- Anomaly Detector: Proactive error and issue detection
- Collaboration Engine: Multi-agent problem solving
- Semantic Search: Vector-based knowledge retrieval
"""

__version__ = "1.0.0"

from cirkelline.intelligence.advisor import (
    ContextualAdvisor,
    Advice,
    AdviceType,
    AdvicePriority,
    get_advisor,
)

from cirkelline.intelligence.anomaly_detector import (
    AnomalyDetector,
    Anomaly,
    AnomalyType,
    AnomalySeverity,
    get_detector,
)

from cirkelline.intelligence.collaboration import (
    CollaborationEngine,
    CollaborationSession,
    CollaborationMode,
    CollaborationStatus,
    AgentContribution,
    get_collaboration_engine,
)

from cirkelline.intelligence.semantic_search import (
    SemanticSearch,
    SearchResult,
    SearchMode,
    Document,
    get_semantic_search,
)

__all__ = [
    # Advisor
    'ContextualAdvisor',
    'Advice',
    'AdviceType',
    'AdvicePriority',
    'get_advisor',
    # Anomaly Detector
    'AnomalyDetector',
    'Anomaly',
    'AnomalyType',
    'AnomalySeverity',
    'get_detector',
    # Collaboration Engine
    'CollaborationEngine',
    'CollaborationSession',
    'CollaborationMode',
    'CollaborationStatus',
    'AgentContribution',
    'get_collaboration_engine',
    # Semantic Search
    'SemanticSearch',
    'SearchResult',
    'SearchMode',
    'Document',
    'get_semantic_search',
]
