"""
CKC MASTERMIND Module
======================

Kollaborativt intelligens-lag for realtidssamarbejde mellem
CKC-agenter under direktion af Super Admin og Systems Dirigent.

Komponenter:
- MastermindCoordinator: Central koordinator
- MastermindSession: Session state management
- SessionManager: Persistence og recovery
- MastermindMessageBus: Realtids kommunikation
- SuperAdminInterface: Super Admin kommandoer
- SystemsDirigent: Orkestrering og syntese
- FeedbackAggregator: Feedback behandling
- ResourceAllocator: Ressource allokering

Eksempel:
    from cirkelline.ckc.mastermind import (
        create_mastermind_coordinator,
        create_session_manager,
        create_message_bus,
        create_super_admin_interface,
        create_systems_dirigent,
    )

    # Setup
    coordinator = create_mastermind_coordinator()
    session_manager = create_session_manager()
    message_bus = create_message_bus()
    super_admin = create_super_admin_interface(message_bus)
    dirigent = create_systems_dirigent(message_bus)

    # Start session
    await message_bus.connect()
    session = await coordinator.create_session(
        objective="Generer komplet markedsføringsmateriale",
        budget_usd=50.0
    )
    await coordinator.start_session(session.session_id)
"""

# =============================================================================
# VERSION
# =============================================================================

__version__ = "1.0.0"
__author__ = "CKC Development Team"

# =============================================================================
# COORDINATOR
# =============================================================================

from .coordinator import (
    # Enums
    MastermindStatus,
    MastermindPriority,
    DirectiveType,
    ParticipantRole,
    TaskStatus,

    # Data classes
    Directive,
    AgentParticipation,
    MastermindTask,
    TaskResult,
    ExecutionPlan,
    FeedbackReport,
    MastermindSession,

    # Main class
    MastermindCoordinator,

    # Factory
    create_mastermind_coordinator,
    get_mastermind_coordinator,
)

# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

from .session import (
    # Data classes
    SessionCheckpoint,

    # Store classes
    SessionStore,
    FileSessionStore,
    InMemorySessionStore,

    # Main class
    SessionManager,

    # Factory
    create_session_manager,
    get_session_manager,
)

# =============================================================================
# MESSAGING
# =============================================================================

from .messaging import (
    # Enums
    MastermindMessageType,
    MessagePriority,
    MessageDelivery,

    # Data classes
    MastermindMessage,
    MessageAck,

    # Bus classes
    MastermindMessageBus,
    InMemoryMessageBus,
    RabbitMQMessageBus,

    # Builder
    MastermindMessageBuilder,

    # Convenience functions
    create_command_message,
    create_directive_message,
    create_status_message,
    create_result_message,

    # Factory
    create_message_bus,
    get_message_bus,
)

# =============================================================================
# ROLES
# =============================================================================

from .roles import (
    # Enums
    DirigentState,

    # Data classes
    SuperAdminCommand,
    DirigentPlan,

    # Main classes
    SuperAdminInterface,
    SystemsDirigent,
    MastermindCapableAgent,

    # Factory
    create_super_admin_interface,
    create_systems_dirigent,
)

# =============================================================================
# FEEDBACK
# =============================================================================

from .feedback import (
    # Enums
    FeedbackSeverity,
    AlertType,
    RecommendationType,

    # Data classes
    FeedbackItem,
    Alert,
    Recommendation,

    # Component classes
    ResultCollector,
    SynthesisEngine,
    DecisionEngine,
    AdjustmentDispatcher,

    # Main class
    FeedbackAggregator,

    # Factory
    create_feedback_aggregator,
    get_feedback_aggregator,
)

# =============================================================================
# RESOURCES
# =============================================================================

from .resources import (
    # Enums
    ResourceType,
    AllocationStrategy,

    # Data classes
    ResourcePool,
    ResourceAllocation,
    APIReservation,

    # Main classes
    ResourceAllocator,
    LoadBalancer,

    # Factory
    create_resource_allocator,
    get_resource_allocator,
    create_load_balancer,
    get_load_balancer,
)

# =============================================================================
# CONTEXT MANAGEMENT (DEL D)
# =============================================================================

from .context import (
    # Enums
    ContextSource,
    DocumentationType,
    TriggerEvent,

    # Data classes
    ContextItem,
    ContextBundle,
    Reference,
    TaskTemplate,
    DocumentationEvent,

    # Main classes
    DirigentContextManager,
    TaskTemplateEngine,
    AutoDocumentationTrigger,

    # Factory
    create_context_manager,
    get_context_manager,
    create_template_engine,
    get_template_engine,
    create_doc_trigger,
    get_doc_trigger,
)

# =============================================================================
# OS-DIRIGENT: LOCAL AGENT INTEGRATION (DEL E)
# =============================================================================

from .os_dirigent import (
    # Enums
    LocalAgentStatus,
    OffloadDecision,
    LocalCapability,
    TaskPriority,
    SyncDirection,

    # Data classes
    LocalAgentInfo,
    OffloadTask,
    SyncBatch,
    ResourceAllocationPlan,

    # Classes
    LocalCapabilityRegistry,
    TaskOffloader,
    ResourceCoordinator,
    LocalAgentBridge,
    WebSocketAgentBridge,
    OSDirigent,

    # Factory functions
    create_os_dirigent,
    get_os_dirigent,
    create_local_agent_bridge,
    get_local_agent_bridge,
)

# =============================================================================
# OPTIMIZATION: SYSTEM-WIDE PERFORMANCE (DEL F)
# =============================================================================

from .optimization import (
    # Enums
    MetricType,
    OptimizationStrategy,
    CacheEvictionPolicy,
    AlertLevel,

    # Data classes
    PerformanceMetric,
    PerformanceSnapshot,
    PerformanceAlert,
    CacheEntry,
    CacheStats,
    BatchJob,
    CostEstimate,
    OptimizationRecommendation,

    # Classes
    PerformanceMonitor,
    CacheManager,
    BatchProcessor,
    CostOptimizer,
    LatencyTracker,

    # Factory functions
    create_performance_monitor,
    get_performance_monitor,
    create_cache_manager,
    get_cache_manager,
    create_batch_processor,
    get_batch_processor,
    create_cost_optimizer,
    get_cost_optimizer,
    create_latency_tracker,
    get_latency_tracker,
)

# =============================================================================
# ETHICS & TRANSPARENCY (DEL G)
# =============================================================================

from .ethics import (
    # Enums
    BiasType,
    BiasLevel,
    DecisionType,
    ComplianceStandard,
    GuardrailType,
    ViolationSeverity,

    # Data classes
    BiasIndicator,
    BiasReport,
    DecisionLog,
    Explanation,
    GuardrailViolation,
    ComplianceStatus,
    ComplianceReport,

    # Classes
    BiasDetector,
    TransparencyLogger,
    ExplainabilityEngine,
    EthicsGuardrails,
    ComplianceReporter,

    # Factory functions
    create_bias_detector,
    get_bias_detector,
    create_transparency_logger,
    get_transparency_logger,
    create_explainability_engine,
    get_explainability_engine,
    create_ethics_guardrails,
    get_ethics_guardrails,
    create_compliance_reporter,
    get_compliance_reporter,
)

# =============================================================================
# USER EXPERIENCE (DEL H)
# =============================================================================

from .ux import (
    # Enums
    FeedbackType,
    FeedbackSentiment,
    UITheme,
    AccessibilityLevel,
    OnboardingStep,
    PreferenceCategory,

    # Data classes
    UserFeedback,
    FeedbackAnalysis,
    UIAdaptation,
    AccessibilityIssue,
    AccessibilityReport,
    OnboardingProgress,
    UserPreference,
    PreferenceProfile,

    # Classes
    UserFeedbackCollector,
    AdaptiveUI,
    AccessibilityChecker,
    OnboardingWizard,
    PreferenceManager,

    # Factory functions
    create_feedback_collector,
    get_feedback_collector,
    create_adaptive_ui,
    get_adaptive_ui,
    create_accessibility_checker,
    get_accessibility_checker,
    create_onboarding_wizard,
    get_onboarding_wizard,
    create_preference_manager,
    get_preference_manager,
)

# =============================================================================
# ECONOMICS (DEL I)
# =============================================================================

from .economics import (
    # Enums
    RevenueType,
    SubscriptionTier,
    SubscriptionStatus,
    UsageMetric,
    InvoiceStatus,
    Currency,

    # Data classes
    RevenueEntry,
    RevenueSummary,
    Subscription,
    UsageRecord,
    UsageSummary,
    Invoice,
    FinancialReport,

    # Classes
    RevenueTracker,
    SubscriptionManager,
    UsageMetering,
    InvoiceGenerator,
    FinancialReporter,

    # Factory functions
    create_revenue_tracker,
    get_revenue_tracker,
    create_subscription_manager,
    get_subscription_manager,
    create_usage_metering,
    get_usage_metering,
    create_invoice_generator,
    get_invoice_generator,
    create_financial_reporter,
    get_financial_reporter,
)

# =============================================================================
# TRAINING ROOM: COMMANDER AUTONOMI & OPTIMERING (DEL K)
# =============================================================================

from .training_room import (
    # Enums
    TrainingMode,
    AutonomyLevel,
    OptimizationTarget,
    TrainingStatus,

    # Data classes
    TrainingObjective,
    TrainingSession,
    AutonomyGuard,
    OptimizationSchedule,
    SystemInsight,

    # Main class
    CommanderTrainingRoom,

    # Factory functions
    create_training_room,
    get_training_room,
)

# =============================================================================
# SELF-OPTIMIZATION SCHEDULER (DEL K.2)
# =============================================================================

from .self_optimization import (
    # Enums
    SchedulerState,
    OptimizationPhase,
    ScheduleType,

    # Data classes
    OptimizationRun,
    SchedulerConfig,
    SchedulerStats,

    # Phase classes
    AnalysisPhase,
    PlanningPhase,
    ExecutionPhase,
    ValidationPhase,
    ReflectionPhase,

    # Main class
    SelfOptimizationScheduler,

    # Factory functions
    create_scheduler,
    get_scheduler,
)

# =============================================================================
# SUPER ADMIN CONTROL SYSTEM (DEL L)
# =============================================================================

from .super_admin_control import (
    # Enums
    DashboardZone,
    AlertLevel as NotificationAlertLevel,  # Aliased to avoid conflict with optimization.AlertLevel
    AlertCategory,
    DeliveryChannel,
    WorkflowRecommendationType,
    KnowledgeQueryType,
    FeedbackType as AdaptiveFeedbackType,  # Aliased to avoid conflict with ux.FeedbackType
    LearningAdaptationType,

    # Data classes
    ZoneStatus,
    Alert as NotificationAlert,  # Aliased to avoid conflict with feedback.Alert
    NotificationPreference,
    WorkflowRecommendation,
    KnowledgeQuery,
    KnowledgeResponse,
    UserFeedback as AdaptiveUserFeedback,  # Aliased to avoid conflict with ux.UserFeedback
    LearningAdaptation,

    # Main classes
    SuperAdminDashboard,
    IntelligentNotificationEngine,
    KV1NTTerminalPartner,
    AdaptiveLearningSystem,
    SuperAdminControlSystem,

    # Factory functions
    create_super_admin_control_system,
    get_super_admin_control_system,
    create_dashboard,
    create_notification_engine,
    create_kv1nt_partner,
    create_adaptive_learning_system,
)

# =============================================================================
# OUTPUT INTEGRITY PROTOCOL (DEL M)
# =============================================================================

from .output_integrity import (
    # Enums
    ValidationRuleType,
    ValidationResult,
    AuditDecision,
    QuarantineReason,
    QuarantineStatus,
    NotificationType as OutputNotificationType,  # Aliased to avoid conflicts
    NotificationPriority as OutputNotificationPriority,  # Aliased
    NotificationChannel,

    # Data classes
    ValidationRule,
    ValidationReport,
    AuditReport,
    QuarantineItem,
    Notification as OutputNotification,  # Aliased
    NotificationPreferences as OutputNotificationPreferences,  # Aliased

    # Main classes
    OutputValidationGateway,
    MastermindAuditSystem,
    QuarantineMechanism,
    SuperAdminNotification,
    OutputIntegritySystem,

    # Factory functions
    create_output_validation_gateway,
    create_mastermind_audit_system,
    create_quarantine_mechanism,
    create_super_admin_notification,
    create_output_integrity_system,
    get_output_integrity_system,
)

# =============================================================================
# MARKETPLACE (DEL J)
# =============================================================================

from .marketplace import (
    # Enums
    AssetType,
    AssetStatus,
    PricingModel,
    CommunityRole,
    ReviewStatus,
    DiscoverySort,

    # Data classes
    Asset,
    AssetVersion,
    CommunityMember,
    Review,
    SearchResult,
    DiscoveryQuery,
    DiscoveryResponse,

    # Classes
    MarketplaceConnector,
    CommunityHub,
    AssetListing,
    ReviewSystem,
    DiscoveryEngine,

    # Factory functions
    create_marketplace_connector,
    get_marketplace_connector,
    create_community_hub,
    get_community_hub,
    create_asset_listing,
    get_asset_listing,
    create_review_system,
    get_review_system,
    create_discovery_engine,
    get_discovery_engine,
)

# =============================================================================
# WAVE COLLECTOR: Bølge-samler (DEL O)
# =============================================================================

from .wave_collector import (
    # Enums
    WaveType,
    WaveOrigin,
    WaveIntensity,
    StreamState,

    # Data classes
    Wave,
    WaveStream,
    WavePattern,
    CollectedWaves,

    # Abstract/Base classes
    WaveSource,
    WaveAggregator,

    # Main classes
    WaveCollector,
    KommandantWaveSource,

    # Factory functions
    create_wave_collector,
    get_wave_collector,
)

# =============================================================================
# COLLECTIVE AWARENESS: Fælles opmærksomhed (DEL P)
# =============================================================================

from .collective_awareness import (
    # Constants
    CoreWisdom,

    # Enums
    AwarenessLevel,
    MemoryType,
    InsightPriority,

    # Data classes
    SharedMemory,
    CollectiveInsight,
    AwarenessState,

    # Classes
    SharedMemoryBank,
    CollectiveAwareness,

    # Factory functions
    create_collective_awareness,
    get_collective_awareness,
)

# =============================================================================
# THINK ALOUD STREAM: Tænk højt strøm (DEL Q)
# =============================================================================

from .think_aloud_stream import (
    # Enums
    ThoughtType,
    ReasoningStyle,
    StreamState as ThinkAloudStreamState,  # Aliased to avoid conflict with wave_collector

    # Data classes
    ThoughtFragment,
    ReasoningChain,
    ThinkAloudSession,

    # Classes
    ThinkAloudBroadcaster,
    ThinkAloudStream,

    # Factory functions
    create_think_aloud_stream,
    get_think_aloud_stream,
)

# =============================================================================
# RITUAL EXECUTOR: Rutine eksekutor (DEL R)
# =============================================================================

from .ritual_executor import (
    # Enums
    RitualType,
    RitualState,
    StepType,
    TriggerType,

    # Data classes
    RitualStep,
    RitualTrigger,
    Ritual,
    StepResult,
    RitualExecution,

    # Classes
    RitualBuilder,
    RitualExecutor,

    # Factory functions
    create_ritual_executor,
    get_ritual_executor,

    # Pre-built rituals
    create_startup_ritual,
    create_shutdown_ritual,
    create_daily_reflection_ritual,
)

# =============================================================================
# THINK ALOUD API: SSE endpoint til real-time tanke streaming (DEL U)
# =============================================================================

from .think_aloud_api import (
    # Enums
    SubscriptionType,
    ConnectionState as SSEConnectionState,  # Aliased to avoid conflict
    EventType,

    # Data classes
    SSEMessage,
    SubscriptionFilter,
    ClientSubscription,
    StreamChannel,
    APIStats,

    # Main class
    ThinkAloudAPI,

    # Factory functions
    create_think_aloud_api,
    get_think_aloud_api,
    set_think_aloud_api,

    # FastAPI helpers
    create_sse_response_headers,
    sse_event_generator,
)

# =============================================================================
# WAVE DATA CONNECTOR: Live data stream forbindelse (DEL T)
# =============================================================================

from .wave_data_connector import (
    # Enums
    DataSourceType,
    ConnectionState,
    DataFormat,
    RetryStrategy,

    # Data classes
    DataSource,
    ConnectionInfo,
    StreamBuffer,
    DataTransform,
    ConnectorStats,

    # Adapter classes
    DataAdapter,
    InternalEventAdapter,
    WebhookAdapter,
    PollingAdapter,

    # Main class
    WaveDataConnector,

    # Factory functions
    create_wave_data_connector,
    get_wave_data_connector,
    set_wave_data_connector,

    # Convenience functions
    create_internal_source,
    create_webhook_source,
    create_api_source,
)

# =============================================================================
# RITUAL SCHEDULER: Planlagt ritual udførelse (DEL S)
# =============================================================================

from .ritual_scheduler import (
    # Enums
    ScheduleType as RitualScheduleType,  # Aliased to avoid conflict with self_optimization.ScheduleType

    # Data classes
    ScheduledRitual,
    ExecutionRecord,

    # Main class
    RitualScheduler,

    # Factory functions
    create_ritual_scheduler,
    get_ritual_scheduler,
    set_ritual_scheduler,
)

# =============================================================================
# DECISION ENGINE: Struktureret beslutningstagning (DEL W)
# =============================================================================

from .decision_engine import (
    # Enums
    DecisionCategory,
    DecisionComplexity,
    DecisionStatus as StructuredDecisionStatus,
    CriterionType,
    EvaluationMethod,
    DecisionOutcome,

    # Data classes
    Criterion,
    Option,
    DecisionContext,
    DecisionRationale,
    DecisionRecord,
    EvaluationResult,
    DecisionEngineStats,

    # Builder
    DecisionBuilder,

    # Main class
    DecisionEngine as StructuredDecisionEngine,

    # Factory functions
    create_decision_engine,
    get_decision_engine,
    set_decision_engine,

    # Helper functions
    quick_decision,
    create_strategic_decision,
)

# =============================================================================
# LIFECYCLE HOOKS: System startup/shutdown integration (DEL V)
# =============================================================================

from .lifecycle_hooks import (
    # Enums
    LifecyclePhase,
    HookPriority,
    HookType,
    ComponentState,
    ShutdownReason,

    # Data classes
    LifecycleHook,
    HookResult,
    ComponentRegistration,
    LifecycleStats,
    LifecycleEvent,

    # Main class
    LifecycleHooks,

    # Factory functions
    create_lifecycle_hooks,
    get_lifecycle_hooks,
    set_lifecycle_hooks,

    # Decorators
    on_startup,
    on_shutdown,

    # MASTERMIND integration
    create_mastermind_lifecycle,
)

# =============================================================================
# DEL X: LearningLoop - Kontinuerlig læring fra erfaring
# =============================================================================
from .learning_loop import (
    # Enums
    ExperienceType,
    PatternType,
    InsightPriority,
    LearningPhase,
    ImprovementStatus,

    # Data classes
    Experience,
    Pattern,
    LearningInsight,
    Improvement,
    LearningCycle,
    LearningLoopStats,

    # Main class
    LearningLoop,

    # Factory functions
    create_learning_loop,
    get_learning_loop,
    set_learning_loop,

    # Convenience functions
    learn_from_success,
    learn_from_failure,
    learn_from_feedback,

    # MASTERMIND integration
    create_mastermind_learning_loop,
)

# =============================================================================
# DEL Y: AutonomyController - Niveau 0-4 styring
# =============================================================================
from .autonomy_controller import (
    # Enums
    AutonomyLevel,
    ActionCategory,
    ApprovalStatus,
    EscalationLevel,

    # Data classes
    ActionPolicy,
    ApprovalRequest,
    AutonomyOverride,
    ActionRecord,
    AutonomyStats,

    # Main class
    AutonomyController,

    # Factory functions
    create_autonomy_controller,
    get_autonomy_controller,
    set_autonomy_controller,

    # Convenience functions
    check_autonomy,
    execute_controlled,
    requires_approval,

    # MASTERMIND integration
    create_mastermind_autonomy,
)

# =============================================================================
# DEL Z: InsightSynthesizer - Indsigt syntetisering
# =============================================================================
from .insight_synthesizer import (
    # Enums
    InsightSourceType,
    SynthesisMethod,
    InsightConfidence,
    ActionUrgency,
    RecommendationCategory,
    ImpactLevel,

    # Data classes
    SourceInsight,
    SynthesisContext,
    SynthesizedInsight,
    ActionRecommendation,
    InsightCorrelation,
    KnowledgeNugget,
    SynthesizerStats,

    # Strategy classes
    SynthesisStrategy,
    AggregationStrategy,
    CorrelationStrategy,
    DistillationStrategy,
    CausalAnalysisStrategy,

    # Main class
    InsightSynthesizer,

    # Factory functions
    create_insight_synthesizer,
    get_insight_synthesizer,
    set_insight_synthesizer,

    # Convenience functions
    ingest_insight,
    synthesize_insights,
    get_actionable_recommendations,

    # MASTERMIND integration
    create_mastermind_insight_synthesizer,
)

# =============================================================================
# DEL AA: COSMIC LIBRARY BRIDGE - Platform forbindelse
# =============================================================================

from cirkelline.ckc.mastermind.cosmic_library_bridge import (
    # Enums
    BridgeConnectionState,
    SyncDirection,
    EventPriority,
    AssetSyncStatus,
    PlatformEventType,

    # Data classes
    BridgeConfig,
    PlatformEvent,
    SyncTask,
    RemoteAsset,
    SearchRequest,
    SearchResult,
    BridgeStats,

    # Classes
    CosmicAPIClient,
    CosmicLibraryBridge,

    # Factory functions
    create_cosmic_library_bridge,
    get_cosmic_library_bridge,
    set_cosmic_library_bridge,

    # Convenience functions
    push_to_cosmic,
    search_cosmic,

    # MASTERMIND integration
    create_mastermind_cosmic_bridge,
)

# =============================================================================
# DEL AB: LIB-ADMIN CONNECTOR - Admin platform forbindelse
# =============================================================================

from cirkelline.ckc.mastermind.lib_admin_connector import (
    # Enums
    AdminConnectionState,
    AdminEventType,
    AdminRole,
    AuditCategory,
    AuditSeverity,
    NotificationPriority,

    # Data classes
    LibAdminConfig,
    AdminEvent,
    AdminUser,
    AuditLogEntry,
    AdminNotification,
    PlatformStatus,
    ConnectorStats,

    # Classes
    LibAdminAPIClient,
    LibAdminConnector,

    # Factory functions
    create_lib_admin_connector,
    get_lib_admin_connector,
    set_lib_admin_connector,

    # Convenience functions
    log_admin_audit,
    notify_admins,
    validate_admin_access,

    # MASTERMIND integration
    create_mastermind_lib_admin_connector,
)

# =============================================================================
# DEL AC: CLA FRONTEND SSE - Frontend real-time events
# =============================================================================

from cirkelline.ckc.mastermind.cla_frontend_sse import (
    # Enums
    FrontendEventType,
    SubscriptionTopic,
    ClientPriority,
    ConnectionState,
    StreamFormat,

    # Data classes
    SSEConfig,
    FrontendEvent,
    ClientSubscription,
    StreamMetrics,
    SSEClient,

    # Classes
    FrontendEventBus,
    CLAFrontendSSE,

    # Factory functions
    create_cla_frontend_sse,
    get_cla_frontend_sse,
    set_cla_frontend_sse,

    # Convenience functions
    broadcast_frontend_event,
    notify_frontend_user,
    update_frontend_dashboard,

    # MASTERMIND integration
    create_mastermind_frontend_sse,
)

# =============================================================================
# DEL AD: CROSS PLATFORM EVENTS - Event distribution
# =============================================================================

from cirkelline.ckc.mastermind.cross_platform_events import (
    # Enums
    PlatformSource,
    CrossEventType,
    EventPriority as CrossEventPriority,  # Alias to avoid conflict
    DeliveryStatus,
    SubscriptionFilter,

    # Data classes
    CrossPlatformEventConfig,
    CrossPlatformEvent,
    EventDelivery,
    EventSubscription,
    EventRoute,
    EventMetrics,

    # Classes
    CrossPlatformEventBus,
    EventAggregator,

    # Factory functions
    create_cross_platform_bus,
    get_cross_platform_bus,
    set_cross_platform_bus,

    # Convenience functions
    emit_cross_platform_event,
    subscribe_to_all_events,

    # MASTERMIND integration
    create_mastermind_cross_platform_bus,
)

# =============================================================================
# DEL AE: QUERY OPTIMIZER - Database optimering
# =============================================================================

from cirkelline.ckc.mastermind.query_optimizer import (
    # Enums
    QueryType,
    OptimizationLevel,
    QueryPriority as DBQueryPriority,  # Alias to avoid conflict
    IndexStatus,
    QueryHealth,

    # Data classes
    QueryOptimizerConfig,
    QueryInfo,
    QueryPlan,
    BatchedQuery,
    NPlusOnePattern,
    QueryMetrics,
    IndexRecommendation,

    # Classes
    QueryAnalyzer,
    QueryBatcher,
    QueryOptimizer,

    # Factory functions
    create_query_optimizer,
    get_query_optimizer,
    set_query_optimizer,

    # Convenience functions
    track_query,
    get_slow_queries,

    # MASTERMIND integration
    create_mastermind_query_optimizer,
)

# -----------------------------------------------------------------------------
# Cache Layer: Multi-tier caching (DEL AF)
# -----------------------------------------------------------------------------
from cirkelline.ckc.mastermind.cache_layer import (
    # Enums
    CacheTier,
    WriteStrategy,
    InvalidationStrategy,
    CacheStatus as CacheEntryStatus,  # Alias to avoid conflict with CacheStatus in other modules
    CompressionType,

    # Config
    CacheLayerConfig,

    # Data classes
    CacheEntry as TieredCacheEntry,  # Alias to avoid conflict with CacheEntry in optimization
    CacheNamespace,
    WarmingTask,
    CacheMetrics as TieredCacheMetrics,  # Alias to avoid conflict
    InvalidationEvent,

    # Backend classes
    CacheBackend,
    L1MemoryCache,
    L2RedisCache,

    # Main class
    CacheLayer,

    # Decorator
    cached,

    # Factory functions
    create_cache_layer,
    get_cache_layer,
    set_cache_layer,
    invalidate_cache,
    create_mastermind_cache_layer,
)

# -----------------------------------------------------------------------------
# Connection Pool: Connection management (DEL AG)
# -----------------------------------------------------------------------------
from cirkelline.ckc.mastermind.connection_pool import (
    # Enums
    PoolState,
    ConnectionState as PoolConnectionState,  # Alias to avoid conflict
    LoadBalanceStrategy,
    PoolEventType,

    # Config
    ConnectionPoolConfig,
    HTTPClientConfig,

    # Data classes
    ConnectionInfo as PoolConnectionInfo,  # Alias to avoid conflict
    PoolMetrics,
    PoolEvent,

    # Connection wrapper
    PooledConnection,

    # Pool classes
    ConnectionPool,
    GenericConnectionPool,
    HTTPConnectionPool,

    # Manager
    ConnectionPoolManager,

    # Factory functions
    get_pool_manager,
    set_pool_manager,
    create_connection_pool,
    create_http_pool,
    create_mastermind_connection_pools,
)

# Metrics Dashboard: Performance monitoring (DEL AH)
from cirkelline.ckc.mastermind.metrics_dashboard import (
    # Enums
    MetricType,
    MetricSource,
    AlertSeverity,
    AlertState,
    DashboardLayout,
    TimeRange,

    # Config
    MetricsDashboardConfig,

    # Data classes
    MetricDatapoint,
    MetricDefinition,
    MetricSeries,
    AlertRule,
    Alert as DashboardAlert,  # Alias to avoid conflict with existing Alert
    DashboardPanel,
    Dashboard,
    SystemHealth,

    # Components
    MetricsCollector,
    AlertManager,
    MetricsStreamer,
    DashboardManager,
    PrometheusExporter,

    # Main class
    MetricsDashboard,

    # Factory functions
    create_metrics_dashboard,
    get_metrics_dashboard,
    set_metrics_dashboard,
    create_mastermind_metrics_dashboard,
)

# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    # Version
    "__version__",

    # Coordinator
    "MastermindStatus",
    "MastermindPriority",
    "DirectiveType",
    "ParticipantRole",
    "TaskStatus",
    "Directive",
    "AgentParticipation",
    "MastermindTask",
    "TaskResult",
    "ExecutionPlan",
    "FeedbackReport",
    "MastermindSession",
    "MastermindCoordinator",
    "create_mastermind_coordinator",
    "get_mastermind_coordinator",

    # Session
    "SessionCheckpoint",
    "SessionStore",
    "FileSessionStore",
    "InMemorySessionStore",
    "SessionManager",
    "create_session_manager",
    "get_session_manager",

    # Messaging
    "MastermindMessageType",
    "MessagePriority",
    "MessageDelivery",
    "MastermindMessage",
    "MessageAck",
    "MastermindMessageBus",
    "InMemoryMessageBus",
    "RabbitMQMessageBus",
    "MastermindMessageBuilder",
    "create_command_message",
    "create_directive_message",
    "create_status_message",
    "create_result_message",
    "create_message_bus",
    "get_message_bus",

    # Roles
    "DirigentState",
    "SuperAdminCommand",
    "DirigentPlan",
    "SuperAdminInterface",
    "SystemsDirigent",
    "MastermindCapableAgent",
    "create_super_admin_interface",
    "create_systems_dirigent",

    # Feedback
    "FeedbackSeverity",
    "AlertType",
    "RecommendationType",
    "FeedbackItem",
    "Alert",
    "Recommendation",
    "ResultCollector",
    "SynthesisEngine",
    "DecisionEngine",
    "AdjustmentDispatcher",
    "FeedbackAggregator",
    "create_feedback_aggregator",
    "get_feedback_aggregator",

    # Resources
    "ResourceType",
    "AllocationStrategy",
    "ResourcePool",
    "ResourceAllocation",
    "APIReservation",
    "ResourceAllocator",
    "LoadBalancer",
    "create_resource_allocator",
    "get_resource_allocator",
    "create_load_balancer",
    "get_load_balancer",

    # Context Management (DEL D)
    "ContextSource",
    "DocumentationType",
    "TriggerEvent",
    "ContextItem",
    "ContextBundle",
    "Reference",
    "TaskTemplate",
    "DocumentationEvent",
    "DirigentContextManager",
    "TaskTemplateEngine",
    "AutoDocumentationTrigger",
    "create_context_manager",
    "get_context_manager",
    "create_template_engine",
    "get_template_engine",
    "create_doc_trigger",
    "get_doc_trigger",

    # OS-Dirigent: Local Agent Integration (DEL E)
    "LocalAgentStatus",
    "OffloadDecision",
    "LocalCapability",
    "TaskPriority",
    "SyncDirection",
    "LocalAgentInfo",
    "OffloadTask",
    "SyncBatch",
    "ResourceAllocationPlan",
    "LocalCapabilityRegistry",
    "TaskOffloader",
    "ResourceCoordinator",
    "LocalAgentBridge",
    "WebSocketAgentBridge",
    "OSDirigent",
    "create_os_dirigent",
    "get_os_dirigent",
    "create_local_agent_bridge",
    "get_local_agent_bridge",

    # Optimization: System-wide Performance (DEL F)
    "MetricType",
    "OptimizationStrategy",
    "CacheEvictionPolicy",
    "AlertLevel",
    "PerformanceMetric",
    "PerformanceSnapshot",
    "PerformanceAlert",
    "CacheEntry",
    "CacheStats",
    "BatchJob",
    "CostEstimate",
    "OptimizationRecommendation",
    "PerformanceMonitor",
    "CacheManager",
    "BatchProcessor",
    "CostOptimizer",
    "LatencyTracker",
    "create_performance_monitor",
    "get_performance_monitor",
    "create_cache_manager",
    "get_cache_manager",
    "create_batch_processor",
    "get_batch_processor",
    "create_cost_optimizer",
    "get_cost_optimizer",
    "create_latency_tracker",
    "get_latency_tracker",

    # Ethics & Transparency (DEL G)
    "BiasType",
    "BiasLevel",
    "DecisionType",
    "ComplianceStandard",
    "GuardrailType",
    "ViolationSeverity",
    "BiasIndicator",
    "BiasReport",
    "DecisionLog",
    "Explanation",
    "GuardrailViolation",
    "ComplianceStatus",
    "ComplianceReport",
    "BiasDetector",
    "TransparencyLogger",
    "ExplainabilityEngine",
    "EthicsGuardrails",
    "ComplianceReporter",
    "create_bias_detector",
    "get_bias_detector",
    "create_transparency_logger",
    "get_transparency_logger",
    "create_explainability_engine",
    "get_explainability_engine",
    "create_ethics_guardrails",
    "get_ethics_guardrails",
    "create_compliance_reporter",
    "get_compliance_reporter",

    # User Experience (DEL H)
    "FeedbackType",
    "FeedbackSentiment",
    "UITheme",
    "AccessibilityLevel",
    "OnboardingStep",
    "PreferenceCategory",
    "UserFeedback",
    "FeedbackAnalysis",
    "UIAdaptation",
    "AccessibilityIssue",
    "AccessibilityReport",
    "OnboardingProgress",
    "UserPreference",
    "PreferenceProfile",
    "UserFeedbackCollector",
    "AdaptiveUI",
    "AccessibilityChecker",
    "OnboardingWizard",
    "PreferenceManager",
    "create_feedback_collector",
    "get_feedback_collector",
    "create_adaptive_ui",
    "get_adaptive_ui",
    "create_accessibility_checker",
    "get_accessibility_checker",
    "create_onboarding_wizard",
    "get_onboarding_wizard",
    "create_preference_manager",
    "get_preference_manager",

    # Economics (DEL I)
    "RevenueType",
    "SubscriptionTier",
    "SubscriptionStatus",
    "UsageMetric",
    "InvoiceStatus",
    "Currency",
    "RevenueEntry",
    "RevenueSummary",
    "Subscription",
    "UsageRecord",
    "UsageSummary",
    "Invoice",
    "FinancialReport",
    "RevenueTracker",
    "SubscriptionManager",
    "UsageMetering",
    "InvoiceGenerator",
    "FinancialReporter",
    "create_revenue_tracker",
    "get_revenue_tracker",
    "create_subscription_manager",
    "get_subscription_manager",
    "create_usage_metering",
    "get_usage_metering",
    "create_invoice_generator",
    "get_invoice_generator",
    "create_financial_reporter",
    "get_financial_reporter",

    # Marketplace (DEL J)
    "AssetType",
    "AssetStatus",
    "PricingModel",
    "CommunityRole",
    "ReviewStatus",
    "DiscoverySort",
    "Asset",
    "AssetVersion",
    "CommunityMember",
    "Review",
    "SearchResult",
    "DiscoveryQuery",
    "DiscoveryResponse",
    "MarketplaceConnector",
    "CommunityHub",
    "AssetListing",
    "ReviewSystem",
    "DiscoveryEngine",
    "create_marketplace_connector",
    "get_marketplace_connector",
    "create_community_hub",
    "get_community_hub",
    "create_asset_listing",
    "get_asset_listing",
    "create_review_system",
    "get_review_system",
    "create_discovery_engine",
    "get_discovery_engine",

    # Training Room: Commander Autonomi & Optimering (DEL K)
    "TrainingMode",
    "AutonomyLevel",
    "OptimizationTarget",
    "TrainingStatus",
    "TrainingObjective",
    "TrainingSession",
    "AutonomyGuard",
    "OptimizationSchedule",
    "SystemInsight",
    "CommanderTrainingRoom",
    "create_training_room",
    "get_training_room",

    # Self-Optimization Scheduler (DEL K.2)
    "SchedulerState",
    "OptimizationPhase",
    "ScheduleType",
    "OptimizationRun",
    "SchedulerConfig",
    "SchedulerStats",
    "AnalysisPhase",
    "PlanningPhase",
    "ExecutionPhase",
    "ValidationPhase",
    "ReflectionPhase",
    "SelfOptimizationScheduler",
    "create_scheduler",
    "get_scheduler",

    # Super Admin Control System (DEL L)
    "DashboardZone",
    "NotificationAlertLevel",
    "AlertCategory",
    "DeliveryChannel",
    "WorkflowRecommendationType",
    "KnowledgeQueryType",
    "AdaptiveFeedbackType",
    "LearningAdaptationType",
    "ZoneStatus",
    "NotificationAlert",
    "NotificationPreference",
    "WorkflowRecommendation",
    "KnowledgeQuery",
    "KnowledgeResponse",
    "AdaptiveUserFeedback",
    "LearningAdaptation",
    "SuperAdminDashboard",
    "IntelligentNotificationEngine",
    "KV1NTTerminalPartner",
    "AdaptiveLearningSystem",
    "SuperAdminControlSystem",
    "create_super_admin_control_system",
    "get_super_admin_control_system",
    "create_dashboard",
    "create_notification_engine",
    "create_kv1nt_partner",
    "create_adaptive_learning_system",

    # Output Integrity Protocol (DEL M)
    "ValidationRuleType",
    "ValidationResult",
    "AuditDecision",
    "QuarantineReason",
    "QuarantineStatus",
    "OutputNotificationType",
    "OutputNotificationPriority",
    "NotificationChannel",
    "ValidationRule",
    "ValidationReport",
    "AuditReport",
    "QuarantineItem",
    "OutputNotification",
    "OutputNotificationPreferences",
    "OutputValidationGateway",
    "MastermindAuditSystem",
    "QuarantineMechanism",
    "SuperAdminNotification",
    "OutputIntegritySystem",
    "create_output_validation_gateway",
    "create_mastermind_audit_system",
    "create_quarantine_mechanism",
    "create_super_admin_notification",
    "create_output_integrity_system",
    "get_output_integrity_system",

    # Wave Collector: Bølge-samler (DEL O)
    "WaveType",
    "WaveOrigin",
    "WaveIntensity",
    "StreamState",
    "Wave",
    "WaveStream",
    "WavePattern",
    "CollectedWaves",
    "WaveSource",
    "WaveAggregator",
    "WaveCollector",
    "KommandantWaveSource",
    "create_wave_collector",
    "get_wave_collector",

    # Collective Awareness: Fælles opmærksomhed (DEL P)
    "CoreWisdom",
    "AwarenessLevel",
    "MemoryType",
    "InsightPriority",
    "SharedMemory",
    "CollectiveInsight",
    "AwarenessState",
    "SharedMemoryBank",
    "CollectiveAwareness",
    "create_collective_awareness",
    "get_collective_awareness",

    # Think Aloud Stream: Tænk højt strøm (DEL Q)
    "ThoughtType",
    "ReasoningStyle",
    "ThinkAloudStreamState",
    "ThoughtFragment",
    "ReasoningChain",
    "ThinkAloudSession",
    "ThinkAloudBroadcaster",
    "ThinkAloudStream",
    "create_think_aloud_stream",
    "get_think_aloud_stream",

    # Ritual Executor: Rutine eksekutor (DEL R)
    "RitualType",
    "RitualState",
    "StepType",
    "TriggerType",
    "RitualStep",
    "RitualTrigger",
    "Ritual",
    "StepResult",
    "RitualExecution",
    "RitualBuilder",
    "RitualExecutor",
    "create_ritual_executor",
    "get_ritual_executor",
    "create_startup_ritual",
    "create_shutdown_ritual",
    "create_daily_reflection_ritual",

    # Ritual Scheduler: Planlagt ritual udførelse (DEL S)
    "RitualScheduleType",
    "ScheduledRitual",
    "ExecutionRecord",
    "RitualScheduler",
    "create_ritual_scheduler",
    "get_ritual_scheduler",
    "set_ritual_scheduler",

    # Wave Data Connector: Live data stream forbindelse (DEL T)
    "DataSourceType",
    "ConnectionState",
    "DataFormat",
    "RetryStrategy",
    "DataSource",
    "ConnectionInfo",
    "StreamBuffer",
    "DataTransform",
    "ConnectorStats",
    "DataAdapter",
    "InternalEventAdapter",
    "WebhookAdapter",
    "PollingAdapter",
    "WaveDataConnector",
    "create_wave_data_connector",
    "get_wave_data_connector",
    "set_wave_data_connector",
    "create_internal_source",
    "create_webhook_source",
    "create_api_source",

    # Think Aloud API: SSE endpoint til real-time tanke streaming (DEL U)
    "SubscriptionType",
    "SSEConnectionState",
    "EventType",
    "SSEMessage",
    "SubscriptionFilter",
    "ClientSubscription",
    "StreamChannel",
    "APIStats",
    "ThinkAloudAPI",
    "create_think_aloud_api",
    "get_think_aloud_api",
    "set_think_aloud_api",
    "create_sse_response_headers",
    "sse_event_generator",

    # Decision Engine: Struktureret beslutningstagning (DEL W)
    "DecisionCategory",
    "DecisionComplexity",
    "StructuredDecisionStatus",
    "CriterionType",
    "EvaluationMethod",
    "DecisionOutcome",
    "Criterion",
    "Option",
    "DecisionContext",
    "DecisionRationale",
    "DecisionRecord",
    "EvaluationResult",
    "DecisionEngineStats",
    "DecisionBuilder",
    "StructuredDecisionEngine",
    "create_decision_engine",
    "get_decision_engine",
    "set_decision_engine",
    "quick_decision",
    "create_strategic_decision",

    # Lifecycle Hooks: System startup/shutdown integration (DEL V)
    "LifecyclePhase",
    "HookPriority",
    "HookType",
    "ComponentState",
    "ShutdownReason",
    "LifecycleHook",
    "HookResult",
    "ComponentRegistration",
    "LifecycleStats",
    "LifecycleEvent",
    "LifecycleHooks",
    "create_lifecycle_hooks",
    "get_lifecycle_hooks",
    "set_lifecycle_hooks",
    "on_startup",
    "on_shutdown",
    "create_mastermind_lifecycle",

    # Learning Loop: Kontinuerlig læring fra erfaring (DEL X)
    "ExperienceType",
    "PatternType",
    "InsightPriority",
    "LearningPhase",
    "ImprovementStatus",
    "Experience",
    "Pattern",
    "LearningInsight",
    "Improvement",
    "LearningCycle",
    "LearningLoopStats",
    "LearningLoop",
    "create_learning_loop",
    "get_learning_loop",
    "set_learning_loop",
    "learn_from_success",
    "learn_from_failure",
    "learn_from_feedback",
    "create_mastermind_learning_loop",

    # Autonomy Controller: Niveau 0-4 styring (DEL Y)
    "AutonomyLevel",
    "ActionCategory",
    "ApprovalStatus",
    "EscalationLevel",
    "ActionPolicy",
    "ApprovalRequest",
    "AutonomyOverride",
    "ActionRecord",
    "AutonomyStats",
    "AutonomyController",
    "create_autonomy_controller",
    "get_autonomy_controller",
    "set_autonomy_controller",
    "check_autonomy",
    "execute_controlled",
    "requires_approval",
    "create_mastermind_autonomy",

    # Insight Synthesizer: Indsigt syntetisering (DEL Z)
    "InsightSourceType",
    "SynthesisMethod",
    "InsightConfidence",
    "ActionUrgency",
    "RecommendationCategory",
    "ImpactLevel",
    "SourceInsight",
    "SynthesisContext",
    "SynthesizedInsight",
    "ActionRecommendation",
    "InsightCorrelation",
    "KnowledgeNugget",
    "SynthesizerStats",
    "SynthesisStrategy",
    "AggregationStrategy",
    "CorrelationStrategy",
    "DistillationStrategy",
    "CausalAnalysisStrategy",
    "InsightSynthesizer",
    "create_insight_synthesizer",
    "get_insight_synthesizer",
    "set_insight_synthesizer",
    "ingest_insight",
    "synthesize_insights",
    "get_actionable_recommendations",
    "create_mastermind_insight_synthesizer",

    # Cosmic Library Bridge: Platform forbindelse (DEL AA)
    "BridgeConnectionState",
    "SyncDirection",
    "EventPriority",
    "AssetSyncStatus",
    "PlatformEventType",
    "BridgeConfig",
    "PlatformEvent",
    "SyncTask",
    "RemoteAsset",
    "SearchRequest",
    "SearchResult",
    "BridgeStats",
    "CosmicAPIClient",
    "CosmicLibraryBridge",
    "create_cosmic_library_bridge",
    "get_cosmic_library_bridge",
    "set_cosmic_library_bridge",
    "push_to_cosmic",
    "search_cosmic",
    "create_mastermind_cosmic_bridge",

    # Lib-Admin Connector: Admin platform forbindelse (DEL AB)
    "AdminConnectionState",
    "AdminEventType",
    "AdminRole",
    "AuditCategory",
    "AuditSeverity",
    "NotificationPriority",
    "LibAdminConfig",
    "AdminEvent",
    "AdminUser",
    "AuditLogEntry",
    "AdminNotification",
    "PlatformStatus",
    "ConnectorStats",
    "LibAdminAPIClient",
    "LibAdminConnector",
    "create_lib_admin_connector",
    "get_lib_admin_connector",
    "set_lib_admin_connector",
    "log_admin_audit",
    "notify_admins",
    "validate_admin_access",
    "create_mastermind_lib_admin_connector",

    # CLA Frontend SSE: Frontend real-time events (DEL AC)
    "FrontendEventType",
    "SubscriptionTopic",
    "ClientPriority",
    "ConnectionState",
    "StreamFormat",
    "SSEConfig",
    "FrontendEvent",
    "ClientSubscription",
    "StreamMetrics",
    "SSEClient",
    "FrontendEventBus",
    "CLAFrontendSSE",
    "create_cla_frontend_sse",
    "get_cla_frontend_sse",
    "set_cla_frontend_sse",
    "broadcast_frontend_event",
    "notify_frontend_user",
    "update_frontend_dashboard",
    "create_mastermind_frontend_sse",

    # Cross Platform Events: Event distribution (DEL AD)
    "PlatformSource",
    "CrossEventType",
    "CrossEventPriority",
    "DeliveryStatus",
    "SubscriptionFilter",
    "CrossPlatformEventConfig",
    "CrossPlatformEvent",
    "EventDelivery",
    "EventSubscription",
    "EventRoute",
    "EventMetrics",
    "CrossPlatformEventBus",
    "EventAggregator",
    "create_cross_platform_bus",
    "get_cross_platform_bus",
    "set_cross_platform_bus",
    "emit_cross_platform_event",
    "subscribe_to_all_events",
    "create_mastermind_cross_platform_bus",

    # Query Optimizer: Database optimering (DEL AE)
    "QueryType",
    "OptimizationLevel",
    "DBQueryPriority",
    "IndexStatus",
    "QueryHealth",
    "QueryOptimizerConfig",
    "QueryInfo",
    "QueryPlan",
    "BatchedQuery",
    "NPlusOnePattern",
    "QueryMetrics",
    "IndexRecommendation",
    "QueryAnalyzer",
    "QueryBatcher",
    "QueryOptimizer",
    "create_query_optimizer",
    "get_query_optimizer",
    "set_query_optimizer",
    "track_query",
    "get_slow_queries",
    "create_mastermind_query_optimizer",

    # Cache Layer: Multi-tier caching (DEL AF)
    "CacheTier",
    "WriteStrategy",
    "InvalidationStrategy",
    "CacheEntryStatus",
    "CompressionType",
    "CacheLayerConfig",
    "TieredCacheEntry",
    "CacheNamespace",
    "WarmingTask",
    "TieredCacheMetrics",
    "InvalidationEvent",
    "CacheBackend",
    "L1MemoryCache",
    "L2RedisCache",
    "CacheLayer",
    "cached",
    "create_cache_layer",
    "get_cache_layer",
    "set_cache_layer",
    "invalidate_cache",
    "create_mastermind_cache_layer",

    # Connection Pool: Connection management (DEL AG)
    "PoolState",
    "PoolConnectionState",
    "LoadBalanceStrategy",
    "PoolEventType",
    "ConnectionPoolConfig",
    "HTTPClientConfig",
    "PoolConnectionInfo",
    "PoolMetrics",
    "PoolEvent",
    "PooledConnection",
    "ConnectionPool",
    "GenericConnectionPool",
    "HTTPConnectionPool",
    "ConnectionPoolManager",
    "get_pool_manager",
    "set_pool_manager",
    "create_connection_pool",
    "create_http_pool",
    "create_mastermind_connection_pools",

    # Metrics Dashboard: Performance monitoring (DEL AH)
    "MetricType",
    "MetricSource",
    "AlertSeverity",
    "AlertState",
    "DashboardLayout",
    "TimeRange",
    "MetricsDashboardConfig",
    "MetricDatapoint",
    "MetricDefinition",
    "MetricSeries",
    "AlertRule",
    "DashboardAlert",
    "DashboardPanel",
    "Dashboard",
    "SystemHealth",
    "MetricsCollector",
    "AlertManager",
    "MetricsStreamer",
    "DashboardManager",
    "PrometheusExporter",
    "MetricsDashboard",
    "create_metrics_dashboard",
    "get_metrics_dashboard",
    "set_metrics_dashboard",
    "create_mastermind_metrics_dashboard",
]
