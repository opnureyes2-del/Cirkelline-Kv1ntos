"""
LIFECYCLE HOOKS - DEL V
========================

Central lifecycle management for the entire MASTERMIND system.

This module:
- Coordinates startup/shutdown of all MASTERMIND modules
- Integrates with FastAPI lifespan context manager
- Provides hook registration for custom lifecycle callbacks
- Ensures proper ordering of startup/shutdown operations
- Logs all lifecycle events via KV1NT

Follows CoreWisdom principle NATURAL_RHYTHM:
"Routines and rituals create flow, not restriction."
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Callable, Coroutine, Dict, List, Optional, Set, TypeVar
from uuid import uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class LifecyclePhase(Enum):
    """Lifecycle phase."""
    PRE_STARTUP = "pre_startup"
    STARTUP = "startup"
    POST_STARTUP = "post_startup"
    RUNNING = "running"
    PRE_SHUTDOWN = "pre_shutdown"
    SHUTDOWN = "shutdown"
    POST_SHUTDOWN = "post_shutdown"
    TERMINATED = "terminated"


class HookPriority(Enum):
    """Hook execution priority (lower = earlier)."""
    CRITICAL = 0      # Database connections, core services
    HIGH = 25         # Essential services
    NORMAL = 50       # Standard services
    LOW = 75          # Optional services
    CLEANUP = 100     # Cleanup tasks


class HookType(Enum):
    """Type of lifecycle hook."""
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    HEALTH_CHECK = "health_check"
    ERROR_RECOVERY = "error_recovery"


class ComponentState(Enum):
    """State of a managed component."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class ShutdownReason(Enum):
    """Reason for shutdown."""
    NORMAL = "normal"
    SIGNAL = "signal"
    ERROR = "error"
    TIMEOUT = "timeout"
    MANUAL = "manual"


# =============================================================================
# TYPE ALIASES
# =============================================================================

HookCallback = Callable[[], Coroutine[Any, Any, None]]
ErrorHandler = Callable[[Exception], Coroutine[Any, Any, bool]]
T = TypeVar("T")


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class LifecycleHook:
    """A registered lifecycle hook."""
    id: str
    name: str
    hook_type: HookType
    callback: HookCallback
    priority: HookPriority = HookPriority.NORMAL
    timeout_seconds: float = 30.0
    required: bool = True  # If True, failure blocks lifecycle
    enabled: bool = True
    retries: int = 3
    retry_delay: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HookResult:
    """Result of hook execution."""
    hook_id: str
    hook_name: str
    success: bool
    duration_ms: float
    error: Optional[str] = None
    retries_used: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ComponentRegistration:
    """Registration of a managed component."""
    id: str
    name: str
    component: Any
    start_method: Optional[str] = "start"
    stop_method: Optional[str] = "stop"
    health_method: Optional[str] = None
    priority: HookPriority = HookPriority.NORMAL
    state: ComponentState = ComponentState.UNINITIALIZED
    dependencies: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None


@dataclass
class LifecycleStats:
    """Statistics for lifecycle operations."""
    startup_hooks_executed: int = 0
    shutdown_hooks_executed: int = 0
    startup_time_ms: float = 0.0
    shutdown_time_ms: float = 0.0
    components_registered: int = 0
    components_running: int = 0
    errors_during_startup: int = 0
    errors_during_shutdown: int = 0
    last_health_check: Optional[datetime] = None
    health_check_failures: int = 0


@dataclass
class LifecycleEvent:
    """Event during lifecycle transition."""
    id: str
    phase: LifecyclePhase
    event_type: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# MAIN CLASS
# =============================================================================

class LifecycleHooks:
    """
    Central lifecycle management for MASTERMIND.

    Coordinates startup/shutdown of all modules with proper ordering,
    error handling, and logging.

    Usage:
        lifecycle = LifecycleHooks()

        # Register hooks
        lifecycle.register_startup_hook(
            "init_database",
            init_db,
            priority=HookPriority.CRITICAL
        )

        # Register components
        lifecycle.register_component(
            "wave_collector",
            wave_collector,
            start_method="start",
            stop_method="stop"
        )

        # Use with FastAPI
        app = FastAPI(lifespan=lifecycle.fastapi_lifespan)
    """

    def __init__(
        self,
        name: str = "mastermind",
        graceful_timeout: float = 30.0,
        enable_signal_handlers: bool = True,
    ):
        self.name = name
        self.graceful_timeout = graceful_timeout
        self._phase = LifecyclePhase.PRE_STARTUP

        # Registries
        self._startup_hooks: Dict[str, LifecycleHook] = {}
        self._shutdown_hooks: Dict[str, LifecycleHook] = {}
        self._health_hooks: Dict[str, LifecycleHook] = {}
        self._components: Dict[str, ComponentRegistration] = {}

        # State tracking
        self._started = False
        self._stopping = False
        self._shutdown_event = asyncio.Event()
        self._startup_complete = asyncio.Event()

        # Results and events
        self._hook_results: List[HookResult] = []
        self._events: List[LifecycleEvent] = []
        self._stats = LifecycleStats()

        # Error handling
        self._error_handlers: List[ErrorHandler] = []
        self._last_error: Optional[Exception] = None

        # Signal handling
        self._signal_handlers_installed = False
        self._original_signal_handlers: Dict[int, Any] = {}
        if enable_signal_handlers:
            self._install_signal_handlers()

        logger.info(f"LifecycleHooks initialized: {name}")

    # =========================================================================
    # PROPERTIES
    # =========================================================================

    @property
    def phase(self) -> LifecyclePhase:
        """Current lifecycle phase."""
        return self._phase

    @property
    def is_running(self) -> bool:
        """Check if lifecycle is in running state."""
        return self._phase == LifecyclePhase.RUNNING

    @property
    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress."""
        return self._stopping

    @property
    def stats(self) -> LifecycleStats:
        """Get lifecycle statistics."""
        return self._stats

    @property
    def events(self) -> List[LifecycleEvent]:
        """Get lifecycle events."""
        return self._events.copy()

    # =========================================================================
    # HOOK REGISTRATION
    # =========================================================================

    def register_startup_hook(
        self,
        name: str,
        callback: HookCallback,
        priority: HookPriority = HookPriority.NORMAL,
        timeout_seconds: float = 30.0,
        required: bool = True,
        retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register a startup hook.

        Args:
            name: Human-readable hook name
            callback: Async function to call on startup
            priority: Execution priority (lower = earlier)
            timeout_seconds: Maximum execution time
            required: If True, failure blocks startup
            retries: Number of retry attempts
            metadata: Additional metadata

        Returns:
            Hook ID
        """
        hook_id = f"startup_{uuid4().hex[:8]}"

        hook = LifecycleHook(
            id=hook_id,
            name=name,
            hook_type=HookType.STARTUP,
            callback=callback,
            priority=priority,
            timeout_seconds=timeout_seconds,
            required=required,
            retries=retries,
            metadata=metadata or {},
        )

        self._startup_hooks[hook_id] = hook
        self._emit_event(
            LifecyclePhase.PRE_STARTUP,
            "hook_registered",
            f"Startup hook registered: {name}",
            {"hook_id": hook_id, "priority": priority.value}
        )

        logger.debug(f"Registered startup hook: {name} (priority={priority.name})")
        return hook_id

    def register_shutdown_hook(
        self,
        name: str,
        callback: HookCallback,
        priority: HookPriority = HookPriority.NORMAL,
        timeout_seconds: float = 30.0,
        required: bool = False,
        retries: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register a shutdown hook.

        Args:
            name: Human-readable hook name
            callback: Async function to call on shutdown
            priority: Execution priority (lower = earlier)
            timeout_seconds: Maximum execution time
            required: If True, failure logs error but continues
            retries: Number of retry attempts
            metadata: Additional metadata

        Returns:
            Hook ID
        """
        hook_id = f"shutdown_{uuid4().hex[:8]}"

        hook = LifecycleHook(
            id=hook_id,
            name=name,
            hook_type=HookType.SHUTDOWN,
            callback=callback,
            priority=priority,
            timeout_seconds=timeout_seconds,
            required=required,
            retries=retries,
            metadata=metadata or {},
        )

        self._shutdown_hooks[hook_id] = hook
        self._emit_event(
            LifecyclePhase.PRE_STARTUP,
            "hook_registered",
            f"Shutdown hook registered: {name}",
            {"hook_id": hook_id, "priority": priority.value}
        )

        logger.debug(f"Registered shutdown hook: {name} (priority={priority.name})")
        return hook_id

    def register_health_hook(
        self,
        name: str,
        callback: HookCallback,
        timeout_seconds: float = 5.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register a health check hook.

        Args:
            name: Human-readable hook name
            callback: Async function to check health
            timeout_seconds: Maximum execution time
            metadata: Additional metadata

        Returns:
            Hook ID
        """
        hook_id = f"health_{uuid4().hex[:8]}"

        hook = LifecycleHook(
            id=hook_id,
            name=name,
            hook_type=HookType.HEALTH_CHECK,
            callback=callback,
            timeout_seconds=timeout_seconds,
            required=False,
            retries=1,
            metadata=metadata or {},
        )

        self._health_hooks[hook_id] = hook
        logger.debug(f"Registered health hook: {name}")
        return hook_id

    def unregister_hook(self, hook_id: str) -> bool:
        """Unregister a hook by ID."""
        for registry in [self._startup_hooks, self._shutdown_hooks, self._health_hooks]:
            if hook_id in registry:
                del registry[hook_id]
                logger.debug(f"Unregistered hook: {hook_id}")
                return True
        return False

    # =========================================================================
    # COMPONENT REGISTRATION
    # =========================================================================

    def register_component(
        self,
        name: str,
        component: Any,
        start_method: Optional[str] = "start",
        stop_method: Optional[str] = "stop",
        health_method: Optional[str] = None,
        priority: HookPriority = HookPriority.NORMAL,
        dependencies: Optional[List[str]] = None,
    ) -> str:
        """
        Register a managed component.

        The component will be automatically started/stopped during lifecycle.

        Args:
            name: Component name
            component: The component instance
            start_method: Method name to call on startup (None to skip)
            stop_method: Method name to call on shutdown (None to skip)
            health_method: Method name for health checks (None to skip)
            priority: Start/stop priority
            dependencies: List of component names this depends on

        Returns:
            Component ID
        """
        comp_id = f"comp_{uuid4().hex[:8]}"

        registration = ComponentRegistration(
            id=comp_id,
            name=name,
            component=component,
            start_method=start_method,
            stop_method=stop_method,
            health_method=health_method,
            priority=priority,
            dependencies=dependencies or [],
        )

        self._components[comp_id] = registration
        self._stats.components_registered += 1

        # Register startup hook if component has start method
        if start_method and hasattr(component, start_method):
            self.register_startup_hook(
                f"{name}_start",
                self._create_component_start_callback(comp_id),
                priority=priority,
                metadata={"component_id": comp_id}
            )

        # Register shutdown hook if component has stop method
        if stop_method and hasattr(component, stop_method):
            self.register_shutdown_hook(
                f"{name}_stop",
                self._create_component_stop_callback(comp_id),
                priority=priority,
                metadata={"component_id": comp_id}
            )

        # Register health hook if component has health method
        if health_method and hasattr(component, health_method):
            self.register_health_hook(
                f"{name}_health",
                self._create_component_health_callback(comp_id),
                metadata={"component_id": comp_id}
            )

        self._emit_event(
            LifecyclePhase.PRE_STARTUP,
            "component_registered",
            f"Component registered: {name}",
            {"component_id": comp_id}
        )

        logger.info(f"Registered component: {name} (priority={priority.name})")
        return comp_id

    def _create_component_start_callback(self, comp_id: str) -> HookCallback:
        """Create startup callback for component."""
        async def start_component():
            reg = self._components.get(comp_id)
            if not reg:
                return

            reg.state = ComponentState.INITIALIZING
            method = getattr(reg.component, reg.start_method)

            if asyncio.iscoroutinefunction(method):
                await method()
            else:
                method()

            reg.state = ComponentState.RUNNING
            reg.started_at = datetime.now()
            self._stats.components_running += 1

        return start_component

    def _create_component_stop_callback(self, comp_id: str) -> HookCallback:
        """Create shutdown callback for component."""
        async def stop_component():
            reg = self._components.get(comp_id)
            if not reg or reg.state != ComponentState.RUNNING:
                return

            reg.state = ComponentState.STOPPING
            method = getattr(reg.component, reg.stop_method)

            if asyncio.iscoroutinefunction(method):
                await method()
            else:
                method()

            reg.state = ComponentState.STOPPED
            reg.stopped_at = datetime.now()
            self._stats.components_running -= 1

        return stop_component

    def _create_component_health_callback(self, comp_id: str) -> HookCallback:
        """Create health check callback for component."""
        async def check_health():
            reg = self._components.get(comp_id)
            if not reg:
                return

            method = getattr(reg.component, reg.health_method)

            if asyncio.iscoroutinefunction(method):
                result = await method()
            else:
                result = method()

            if not result:
                raise RuntimeError(f"Health check failed for {reg.name}")

        return check_health

    def get_component(self, name: str) -> Optional[Any]:
        """Get a registered component by name."""
        for reg in self._components.values():
            if reg.name == name:
                return reg.component
        return None

    def get_component_state(self, name: str) -> Optional[ComponentState]:
        """Get state of a registered component."""
        for reg in self._components.values():
            if reg.name == name:
                return reg.state
        return None

    # =========================================================================
    # LIFECYCLE OPERATIONS
    # =========================================================================

    async def startup(self) -> bool:
        """
        Execute all startup hooks in priority order.

        Returns:
            True if all required hooks succeeded
        """
        if self._started:
            logger.warning("Startup already executed")
            return True

        start_time = datetime.now()
        self._phase = LifecyclePhase.STARTUP
        self._emit_event(LifecyclePhase.STARTUP, "started", "System startup initiated")

        logger.info(f"=== MASTERMIND STARTUP: {self.name} ===")

        # Sort hooks by priority
        sorted_hooks = sorted(
            [h for h in self._startup_hooks.values() if h.enabled],
            key=lambda h: h.priority.value
        )

        all_success = True

        for hook in sorted_hooks:
            result = await self._execute_hook(hook)
            self._hook_results.append(result)
            self._stats.startup_hooks_executed += 1

            if not result.success:
                self._stats.errors_during_startup += 1
                if hook.required:
                    logger.error(f"Required startup hook failed: {hook.name}")
                    all_success = False
                    break
                else:
                    logger.warning(f"Optional startup hook failed: {hook.name}")

        self._started = all_success
        self._stats.startup_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        if all_success:
            self._phase = LifecyclePhase.POST_STARTUP
            self._emit_event(
                LifecyclePhase.POST_STARTUP,
                "completed",
                f"Startup completed in {self._stats.startup_time_ms:.0f}ms"
            )

            # Transition to running
            self._phase = LifecyclePhase.RUNNING
            self._startup_complete.set()
            logger.info(f"=== MASTERMIND RUNNING ({self._stats.startup_time_ms:.0f}ms) ===")
        else:
            self._phase = LifecyclePhase.TERMINATED
            self._emit_event(
                LifecyclePhase.TERMINATED,
                "startup_failed",
                "Startup failed, system terminated"
            )
            logger.error("=== MASTERMIND STARTUP FAILED ===")

        return all_success

    async def shutdown(self, reason: ShutdownReason = ShutdownReason.NORMAL) -> bool:
        """
        Execute all shutdown hooks in reverse priority order.

        Args:
            reason: Why shutdown was initiated

        Returns:
            True if all hooks executed (regardless of individual failures)
        """
        if self._stopping:
            logger.warning("Shutdown already in progress")
            await self._shutdown_event.wait()
            return True

        self._stopping = True
        start_time = datetime.now()
        self._phase = LifecyclePhase.PRE_SHUTDOWN

        self._emit_event(
            LifecyclePhase.PRE_SHUTDOWN,
            "initiated",
            f"Shutdown initiated: {reason.value}"
        )

        logger.info(f"=== MASTERMIND SHUTDOWN: {reason.value} ===")

        self._phase = LifecyclePhase.SHUTDOWN

        # Sort hooks by priority (reversed for shutdown - high priority stops last)
        sorted_hooks = sorted(
            [h for h in self._shutdown_hooks.values() if h.enabled],
            key=lambda h: -h.priority.value  # Negative for reverse order
        )

        for hook in sorted_hooks:
            try:
                result = await asyncio.wait_for(
                    self._execute_hook(hook),
                    timeout=self.graceful_timeout
                )
                self._hook_results.append(result)
                self._stats.shutdown_hooks_executed += 1

                if not result.success:
                    self._stats.errors_during_shutdown += 1
                    logger.warning(f"Shutdown hook failed: {hook.name}")
            except asyncio.TimeoutError:
                logger.error(f"Shutdown hook timed out: {hook.name}")
                self._stats.errors_during_shutdown += 1

        self._stats.shutdown_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        self._phase = LifecyclePhase.POST_SHUTDOWN
        self._emit_event(
            LifecyclePhase.POST_SHUTDOWN,
            "completed",
            f"Shutdown completed in {self._stats.shutdown_time_ms:.0f}ms"
        )

        self._phase = LifecyclePhase.TERMINATED
        self._shutdown_event.set()

        logger.info(f"=== MASTERMIND TERMINATED ({self._stats.shutdown_time_ms:.0f}ms) ===")

        # Restore signal handlers
        self._restore_signal_handlers()

        return True

    async def _execute_hook(self, hook: LifecycleHook) -> HookResult:
        """Execute a single hook with retry and timeout handling."""
        start_time = datetime.now()
        last_error: Optional[str] = None
        retries_used = 0

        for attempt in range(hook.retries + 1):
            try:
                await asyncio.wait_for(
                    hook.callback(),
                    timeout=hook.timeout_seconds
                )

                duration_ms = (datetime.now() - start_time).total_seconds() * 1000
                logger.debug(f"Hook executed: {hook.name} ({duration_ms:.0f}ms)")

                return HookResult(
                    hook_id=hook.id,
                    hook_name=hook.name,
                    success=True,
                    duration_ms=duration_ms,
                    retries_used=retries_used,
                )

            except asyncio.TimeoutError:
                last_error = f"Timeout after {hook.timeout_seconds}s"
                retries_used = attempt + 1
                logger.warning(f"Hook timeout: {hook.name} (attempt {attempt + 1})")

            except Exception as e:
                last_error = str(e)
                retries_used = attempt + 1
                logger.warning(f"Hook error: {hook.name} - {e} (attempt {attempt + 1})")

                # Call error handlers
                await self._handle_error(e)

            # Wait before retry
            if attempt < hook.retries:
                await asyncio.sleep(hook.retry_delay)

        duration_ms = (datetime.now() - start_time).total_seconds() * 1000

        return HookResult(
            hook_id=hook.id,
            hook_name=hook.name,
            success=False,
            duration_ms=duration_ms,
            error=last_error,
            retries_used=retries_used,
        )

    # =========================================================================
    # HEALTH CHECKS
    # =========================================================================

    async def check_health(self) -> Dict[str, Any]:
        """
        Execute all health check hooks.

        Returns:
            Health status dictionary
        """
        results = {}
        all_healthy = True

        for hook in self._health_hooks.values():
            if not hook.enabled:
                continue

            result = await self._execute_hook(hook)
            results[hook.name] = {
                "healthy": result.success,
                "duration_ms": result.duration_ms,
                "error": result.error,
            }

            if not result.success:
                all_healthy = False
                self._stats.health_check_failures += 1

        self._stats.last_health_check = datetime.now()

        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "phase": self._phase.value,
            "checks": results,
            "components": {
                reg.name: reg.state.value
                for reg in self._components.values()
            },
            "timestamp": datetime.now().isoformat(),
        }

    # =========================================================================
    # ERROR HANDLING
    # =========================================================================

    def register_error_handler(self, handler: ErrorHandler) -> None:
        """Register an error handler."""
        self._error_handlers.append(handler)

    async def _handle_error(self, error: Exception) -> None:
        """Call all registered error handlers."""
        self._last_error = error

        for handler in self._error_handlers:
            try:
                handled = await handler(error)
                if handled:
                    return
            except Exception as e:
                logger.error(f"Error handler failed: {e}")

    # =========================================================================
    # SIGNAL HANDLING
    # =========================================================================

    def _install_signal_handlers(self) -> None:
        """Install signal handlers for graceful shutdown."""
        if self._signal_handlers_installed:
            return

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop yet
            return

        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                self._original_signal_handlers[sig] = signal.getsignal(sig)
                loop.add_signal_handler(
                    sig,
                    lambda s=sig: asyncio.create_task(self._signal_shutdown(s))
                )
            except (ValueError, OSError):
                # Signal handling not supported on this platform
                pass

        self._signal_handlers_installed = True
        logger.debug("Signal handlers installed")

    async def _signal_shutdown(self, sig: signal.Signals) -> None:
        """Handle shutdown signal."""
        logger.info(f"Received signal: {sig.name}")
        await self.shutdown(reason=ShutdownReason.SIGNAL)

    def _restore_signal_handlers(self) -> None:
        """Restore original signal handlers."""
        for sig, handler in self._original_signal_handlers.items():
            try:
                signal.signal(sig, handler)
            except (ValueError, OSError):
                pass

        self._signal_handlers_installed = False

    # =========================================================================
    # FASTAPI INTEGRATION
    # =========================================================================

    @asynccontextmanager
    async def fastapi_lifespan(self, app: Any) -> AsyncIterator[None]:
        """
        FastAPI lifespan context manager.

        Usage:
            lifecycle = LifecycleHooks()
            app = FastAPI(lifespan=lifecycle.fastapi_lifespan)
        """
        # Startup
        success = await self.startup()
        if not success:
            raise RuntimeError("MASTERMIND startup failed")

        try:
            yield
        finally:
            # Shutdown
            await self.shutdown(reason=ShutdownReason.NORMAL)

    def create_fastapi_lifespan(self) -> Callable:
        """
        Create a FastAPI lifespan function.

        Alternative to fastapi_lifespan for when you need to pass
        additional parameters.
        """
        @asynccontextmanager
        async def lifespan(app: Any) -> AsyncIterator[None]:
            async with self.fastapi_lifespan(app):
                yield

        return lifespan

    # =========================================================================
    # EVENTS
    # =========================================================================

    def _emit_event(
        self,
        phase: LifecyclePhase,
        event_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit a lifecycle event."""
        event = LifecycleEvent(
            id=f"evt_{uuid4().hex[:8]}",
            phase=phase,
            event_type=event_type,
            message=message,
            details=details or {},
        )

        self._events.append(event)

        # Keep only last 1000 events
        if len(self._events) > 1000:
            self._events = self._events[-1000:]

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    async def wait_for_startup(self, timeout: Optional[float] = None) -> bool:
        """Wait for startup to complete."""
        try:
            await asyncio.wait_for(
                self._startup_complete.wait(),
                timeout=timeout
            )
            return True
        except asyncio.TimeoutError:
            return False

    async def wait_for_shutdown(self, timeout: Optional[float] = None) -> bool:
        """Wait for shutdown to complete."""
        try:
            await asyncio.wait_for(
                self._shutdown_event.wait(),
                timeout=timeout
            )
            return True
        except asyncio.TimeoutError:
            return False

    def get_hook_results(self) -> List[HookResult]:
        """Get all hook execution results."""
        return self._hook_results.copy()

    def get_recent_events(self, limit: int = 50) -> List[LifecycleEvent]:
        """Get recent lifecycle events."""
        return self._events[-limit:]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize lifecycle state to dictionary."""
        return {
            "name": self.name,
            "phase": self._phase.value,
            "is_running": self.is_running,
            "is_shutting_down": self.is_shutting_down,
            "stats": {
                "startup_hooks_executed": self._stats.startup_hooks_executed,
                "shutdown_hooks_executed": self._stats.shutdown_hooks_executed,
                "startup_time_ms": self._stats.startup_time_ms,
                "shutdown_time_ms": self._stats.shutdown_time_ms,
                "components_registered": self._stats.components_registered,
                "components_running": self._stats.components_running,
                "errors_during_startup": self._stats.errors_during_startup,
                "errors_during_shutdown": self._stats.errors_during_shutdown,
            },
            "components": {
                reg.name: {
                    "state": reg.state.value,
                    "started_at": reg.started_at.isoformat() if reg.started_at else None,
                    "stopped_at": reg.stopped_at.isoformat() if reg.stopped_at else None,
                }
                for reg in self._components.values()
            },
            "hooks": {
                "startup": len(self._startup_hooks),
                "shutdown": len(self._shutdown_hooks),
                "health": len(self._health_hooks),
            },
        }


# =============================================================================
# SINGLETON MANAGEMENT
# =============================================================================

_lifecycle_hooks: Optional[LifecycleHooks] = None


def create_lifecycle_hooks(
    name: str = "mastermind",
    graceful_timeout: float = 30.0,
    enable_signal_handlers: bool = True,
) -> LifecycleHooks:
    """
    Create a new LifecycleHooks instance.

    Args:
        name: Lifecycle name
        graceful_timeout: Timeout for graceful shutdown
        enable_signal_handlers: Whether to install signal handlers

    Returns:
        New LifecycleHooks instance
    """
    return LifecycleHooks(
        name=name,
        graceful_timeout=graceful_timeout,
        enable_signal_handlers=enable_signal_handlers,
    )


def get_lifecycle_hooks() -> Optional[LifecycleHooks]:
    """Get the global lifecycle hooks instance."""
    return _lifecycle_hooks


def set_lifecycle_hooks(hooks: LifecycleHooks) -> None:
    """Set the global lifecycle hooks instance."""
    global _lifecycle_hooks
    _lifecycle_hooks = hooks


# =============================================================================
# DECORATOR HELPERS
# =============================================================================

def on_startup(
    name: Optional[str] = None,
    priority: HookPriority = HookPriority.NORMAL,
    required: bool = True,
) -> Callable[[HookCallback], HookCallback]:
    """
    Decorator to register a startup hook.

    Usage:
        @on_startup("init_database", priority=HookPriority.CRITICAL)
        async def init_db():
            await db.connect()
    """
    def decorator(func: HookCallback) -> HookCallback:
        hooks = get_lifecycle_hooks()
        if hooks:
            hook_name = name or func.__name__
            hooks.register_startup_hook(hook_name, func, priority=priority, required=required)
        return func
    return decorator


def on_shutdown(
    name: Optional[str] = None,
    priority: HookPriority = HookPriority.NORMAL,
) -> Callable[[HookCallback], HookCallback]:
    """
    Decorator to register a shutdown hook.

    Usage:
        @on_shutdown("close_connections")
        async def close_db():
            await db.disconnect()
    """
    def decorator(func: HookCallback) -> HookCallback:
        hooks = get_lifecycle_hooks()
        if hooks:
            hook_name = name or func.__name__
            hooks.register_shutdown_hook(hook_name, func, priority=priority)
        return func
    return decorator


# =============================================================================
# MASTERMIND INTEGRATION
# =============================================================================

async def create_mastermind_lifecycle() -> LifecycleHooks:
    """
    Create a fully configured lifecycle for MASTERMIND.

    This integrates all standard MASTERMIND components:
    - WaveCollector
    - CollectiveAwareness
    - ThinkAloudStream
    - RitualExecutor
    - RitualScheduler
    - WaveDataConnector
    - ThinkAloudAPI

    Returns:
        Configured LifecycleHooks instance
    """
    lifecycle = create_lifecycle_hooks(name="mastermind")

    # Import and register MASTERMIND components
    try:
        # These imports are optional - may not exist yet
        from .wave_collector import get_wave_collector, create_wave_collector
        from .collective_awareness import get_collective_awareness, create_collective_awareness
        from .think_aloud_stream import get_think_aloud_stream, create_think_aloud_stream
        from .ritual_executor import get_ritual_executor, create_ritual_executor
        from .ritual_scheduler import get_ritual_scheduler, create_ritual_scheduler
        from .wave_data_connector import get_wave_data_connector, create_wave_data_connector
        from .think_aloud_api import get_think_aloud_api, create_think_aloud_api

        # Register startup hooks in dependency order
        @lifecycle.register_startup_hook(
            "wave_collector",
            priority=HookPriority.CRITICAL
        )
        async def start_wave_collector():
            collector = get_wave_collector() or create_wave_collector()
            await collector.start()

        @lifecycle.register_startup_hook(
            "collective_awareness",
            priority=HookPriority.HIGH
        )
        async def start_collective_awareness():
            awareness = get_collective_awareness() or create_collective_awareness()
            await awareness.start()

        @lifecycle.register_startup_hook(
            "think_aloud_stream",
            priority=HookPriority.HIGH
        )
        async def start_think_aloud():
            stream = get_think_aloud_stream() or create_think_aloud_stream()
            await stream.start()

        @lifecycle.register_startup_hook(
            "ritual_scheduler",
            priority=HookPriority.NORMAL
        )
        async def start_ritual_scheduler():
            scheduler = get_ritual_scheduler() or create_ritual_scheduler()
            await scheduler.start()

        @lifecycle.register_startup_hook(
            "wave_data_connector",
            priority=HookPriority.NORMAL
        )
        async def start_wave_data_connector():
            connector = get_wave_data_connector() or create_wave_data_connector()
            await connector.start()

        @lifecycle.register_startup_hook(
            "think_aloud_api",
            priority=HookPriority.LOW
        )
        async def start_think_aloud_api():
            api = get_think_aloud_api() or create_think_aloud_api()
            await api.start()

        # Register shutdown hooks in reverse dependency order
        @lifecycle.register_shutdown_hook(
            "think_aloud_api",
            priority=HookPriority.LOW
        )
        async def stop_think_aloud_api():
            api = get_think_aloud_api()
            if api:
                await api.stop()

        @lifecycle.register_shutdown_hook(
            "wave_data_connector",
            priority=HookPriority.NORMAL
        )
        async def stop_wave_data_connector():
            connector = get_wave_data_connector()
            if connector:
                await connector.stop()

        @lifecycle.register_shutdown_hook(
            "ritual_scheduler",
            priority=HookPriority.NORMAL
        )
        async def stop_ritual_scheduler():
            scheduler = get_ritual_scheduler()
            if scheduler:
                await scheduler.stop()

        @lifecycle.register_shutdown_hook(
            "think_aloud_stream",
            priority=HookPriority.HIGH
        )
        async def stop_think_aloud():
            stream = get_think_aloud_stream()
            if stream:
                await stream.stop()

        @lifecycle.register_shutdown_hook(
            "collective_awareness",
            priority=HookPriority.HIGH
        )
        async def stop_collective_awareness():
            awareness = get_collective_awareness()
            if awareness:
                await awareness.stop()

        @lifecycle.register_shutdown_hook(
            "wave_collector",
            priority=HookPriority.CRITICAL
        )
        async def stop_wave_collector():
            collector = get_wave_collector()
            if collector:
                await collector.stop()

        logger.info("MASTERMIND lifecycle configured with all components")

    except ImportError as e:
        logger.warning(f"Some MASTERMIND components not available: {e}")

    set_lifecycle_hooks(lifecycle)
    return lifecycle


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "LifecyclePhase",
    "HookPriority",
    "HookType",
    "ComponentState",
    "ShutdownReason",

    # Data classes
    "LifecycleHook",
    "HookResult",
    "ComponentRegistration",
    "LifecycleStats",
    "LifecycleEvent",

    # Main class
    "LifecycleHooks",

    # Factory functions
    "create_lifecycle_hooks",
    "get_lifecycle_hooks",
    "set_lifecycle_hooks",

    # Decorators
    "on_startup",
    "on_shutdown",

    # MASTERMIND integration
    "create_mastermind_lifecycle",
]
