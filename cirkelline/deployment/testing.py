"""
Test Runner
===========
Validation and testing infrastructure.

Responsibilities:
- Run system validation tests
- Support test suites and cases
- Generate test reports
- Integration testing helpers
"""

import logging
import asyncio
import time
import traceback
from typing import Optional, Dict, Any, List, Callable, Awaitable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class TestStatus(Enum):
    """Test execution status."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """Result of a test execution."""
    name: str
    status: TestStatus
    duration_ms: float = 0
    message: str = ""
    error: Optional[str] = None
    traceback: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    assertions: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "duration_ms": round(self.duration_ms, 2),
            "message": self.message,
            "error": self.error,
            "timestamp": self.timestamp,
            "assertions": self.assertions,
        }


@dataclass
class TestCase:
    """A test case definition."""
    name: str
    test_func: Union[Callable[[], bool], Callable[[], Awaitable[bool]]]
    description: str = ""
    tags: List[str] = field(default_factory=list)
    timeout_seconds: float = 30.0
    skip: bool = False
    skip_reason: str = ""


@dataclass
class TestSuite:
    """A collection of test cases."""
    name: str
    tests: List[TestCase] = field(default_factory=list)
    setup: Optional[Callable[[], Awaitable[None]]] = None
    teardown: Optional[Callable[[], Awaitable[None]]] = None
    description: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# ASSERTIONS
# ═══════════════════════════════════════════════════════════════════════════════

class AssertionError(Exception):
    """Custom assertion error."""
    pass


class Assertions:
    """Test assertions helper."""

    def __init__(self):
        self.count = 0

    def assertTrue(self, condition: bool, message: str = "") -> None:
        """Assert condition is True."""
        self.count += 1
        if not condition:
            raise AssertionError(message or "Expected True but got False")

    def assertFalse(self, condition: bool, message: str = "") -> None:
        """Assert condition is False."""
        self.count += 1
        if condition:
            raise AssertionError(message or "Expected False but got True")

    def assertEqual(self, actual: Any, expected: Any, message: str = "") -> None:
        """Assert values are equal."""
        self.count += 1
        if actual != expected:
            raise AssertionError(
                message or f"Expected {expected} but got {actual}"
            )

    def assertNotEqual(self, actual: Any, expected: Any, message: str = "") -> None:
        """Assert values are not equal."""
        self.count += 1
        if actual == expected:
            raise AssertionError(
                message or f"Expected values to differ but both are {actual}"
            )

    def assertIsNone(self, value: Any, message: str = "") -> None:
        """Assert value is None."""
        self.count += 1
        if value is not None:
            raise AssertionError(message or f"Expected None but got {value}")

    def assertIsNotNone(self, value: Any, message: str = "") -> None:
        """Assert value is not None."""
        self.count += 1
        if value is None:
            raise AssertionError(message or "Expected non-None value")

    def assertIn(self, item: Any, container: Any, message: str = "") -> None:
        """Assert item is in container."""
        self.count += 1
        if item not in container:
            raise AssertionError(message or f"Expected {item} to be in {container}")

    def assertNotIn(self, item: Any, container: Any, message: str = "") -> None:
        """Assert item is not in container."""
        self.count += 1
        if item in container:
            raise AssertionError(
                message or f"Expected {item} to not be in {container}"
            )

    def assertGreater(self, a: Any, b: Any, message: str = "") -> None:
        """Assert a > b."""
        self.count += 1
        if not (a > b):
            raise AssertionError(message or f"Expected {a} > {b}")

    def assertLess(self, a: Any, b: Any, message: str = "") -> None:
        """Assert a < b."""
        self.count += 1
        if not (a < b):
            raise AssertionError(message or f"Expected {a} < {b}")

    def assertRaises(
        self,
        exception_type: type,
        func: Callable,
        *args,
        **kwargs,
    ) -> None:
        """Assert function raises exception."""
        self.count += 1
        try:
            func(*args, **kwargs)
            raise AssertionError(
                f"Expected {exception_type.__name__} to be raised"
            )
        except exception_type:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
# TEST RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

class TestRunner:
    """
    System test runner.

    Executes test suites and cases with detailed reporting.
    """

    def __init__(self):
        self._suites: Dict[str, TestSuite] = {}
        self._results: List[TestResult] = []
        self._assertions = Assertions()

    # ═══════════════════════════════════════════════════════════════════════════
    # REGISTRATION
    # ═══════════════════════════════════════════════════════════════════════════

    def register_suite(self, suite: TestSuite) -> None:
        """Register a test suite."""
        self._suites[suite.name] = suite
        logger.debug(f"Registered test suite: {suite.name}")

    def register_test(
        self,
        name: str,
        test_func: Union[Callable[[], bool], Callable[[], Awaitable[bool]]],
        suite_name: str = "default",
        **kwargs,
    ) -> None:
        """Register a single test."""
        if suite_name not in self._suites:
            self._suites[suite_name] = TestSuite(name=suite_name)

        test_case = TestCase(name=name, test_func=test_func, **kwargs)
        self._suites[suite_name].tests.append(test_case)

    def test(
        self,
        name: str = "",
        suite_name: str = "default",
        **kwargs,
    ):
        """Decorator to register a test function."""
        def decorator(func):
            test_name = name or func.__name__
            self.register_test(
                name=test_name,
                test_func=func,
                suite_name=suite_name,
                **kwargs,
            )

            @wraps(func)
            async def wrapper(*args, **kw):
                return await func(*args, **kw)

            return wrapper
        return decorator

    # ═══════════════════════════════════════════════════════════════════════════
    # EXECUTION
    # ═══════════════════════════════════════════════════════════════════════════

    async def run_all(
        self,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Run all registered tests.

        Args:
            tags: Optional filter by tags

        Returns:
            Test report
        """
        self._results.clear()
        start_time = time.time()

        for suite_name, suite in self._suites.items():
            await self.run_suite(suite, tags)

        duration = (time.time() - start_time) * 1000
        return self._generate_report(duration)

    async def run_suite(
        self,
        suite: TestSuite,
        tags: Optional[List[str]] = None,
    ) -> List[TestResult]:
        """Run a test suite."""
        results = []

        # Setup
        if suite.setup:
            try:
                await suite.setup()
            except Exception as e:
                logger.error(f"Suite setup failed: {e}")
                return results

        # Run tests
        for test_case in suite.tests:
            # Filter by tags
            if tags and not any(t in test_case.tags for t in tags):
                continue

            result = await self.run_test(test_case)
            results.append(result)
            self._results.append(result)

        # Teardown
        if suite.teardown:
            try:
                await suite.teardown()
            except Exception as e:
                logger.error(f"Suite teardown failed: {e}")

        return results

    async def run_test(self, test_case: TestCase) -> TestResult:
        """Run a single test case."""
        if test_case.skip:
            return TestResult(
                name=test_case.name,
                status=TestStatus.SKIPPED,
                message=test_case.skip_reason or "Test skipped",
            )

        self._assertions.count = 0
        start_time = time.time()

        try:
            # Run test with timeout
            if asyncio.iscoroutinefunction(test_case.test_func):
                await asyncio.wait_for(
                    test_case.test_func(),
                    timeout=test_case.timeout_seconds,
                )
            else:
                test_case.test_func()

            duration = (time.time() - start_time) * 1000

            return TestResult(
                name=test_case.name,
                status=TestStatus.PASSED,
                duration_ms=duration,
                assertions=self._assertions.count,
            )

        except asyncio.TimeoutError:
            duration = (time.time() - start_time) * 1000
            return TestResult(
                name=test_case.name,
                status=TestStatus.ERROR,
                duration_ms=duration,
                message=f"Test timed out after {test_case.timeout_seconds}s",
            )

        except AssertionError as e:
            duration = (time.time() - start_time) * 1000
            return TestResult(
                name=test_case.name,
                status=TestStatus.FAILED,
                duration_ms=duration,
                message=str(e),
                assertions=self._assertions.count,
            )

        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return TestResult(
                name=test_case.name,
                status=TestStatus.ERROR,
                duration_ms=duration,
                error=str(e),
                traceback=traceback.format_exc(),
            )

    def _generate_report(self, duration_ms: float) -> Dict[str, Any]:
        """Generate test report."""
        passed = sum(1 for r in self._results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self._results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in self._results if r.status == TestStatus.SKIPPED)
        errors = sum(1 for r in self._results if r.status == TestStatus.ERROR)

        return {
            "summary": {
                "total": len(self._results),
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "errors": errors,
                "success_rate": passed / len(self._results) if self._results else 0,
                "duration_ms": round(duration_ms, 2),
            },
            "results": [r.to_dict() for r in self._results],
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # BUILT-IN TESTS
    # ═══════════════════════════════════════════════════════════════════════════

    def register_system_tests(self) -> None:
        """Register built-in system validation tests."""

        async def test_imports():
            """Test that all modules can be imported."""
            modules = [
                "cirkelline.terminal",
                "cirkelline.headquarters",
                "cirkelline.intelligence",
                "cirkelline.security",
                "cirkelline.performance",
                "cirkelline.deployment",
            ]
            for module in modules:
                __import__(module)

        async def test_security_validation():
            """Test security validation works."""
            from cirkelline.security import get_validator
            v = get_validator()
            result = v.validate_string("test", min_length=1)
            assert result.valid, "Validation should pass"

        async def test_cache_operations():
            """Test cache basic operations."""
            from cirkelline.performance import get_cache_manager
            cache = get_cache_manager()
            cache.set("test_key", "test_value", ttl=10)
            value = cache.get("test_key")
            assert value == "test_value", "Cache should return stored value"
            cache.delete("test_key")

        async def test_config_loading():
            """Test configuration loading."""
            from cirkelline.deployment import get_config_manager
            config = get_config_manager()
            assert config.environment is not None, "Environment should be set"

        async def test_health_check():
            """Test health checker."""
            from cirkelline.deployment import get_health_checker
            health = get_health_checker()
            result = await health.liveness()
            assert result["status"] == "healthy", "Liveness should be healthy"

        self.register_test("imports", test_imports, suite_name="system")
        self.register_test("security_validation", test_security_validation, suite_name="system")
        self.register_test("cache_operations", test_cache_operations, suite_name="system")
        self.register_test("config_loading", test_config_loading, suite_name="system")
        self.register_test("health_check", test_health_check, suite_name="system")

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
        """Get test runner statistics."""
        return {
            "registered_suites": len(self._suites),
            "total_tests": sum(len(s.tests) for s in self._suites.values()),
            "last_run_results": len(self._results),
            "suites": list(self._suites.keys()),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def run_tests(
    tags: Optional[List[str]] = None,
    include_system: bool = True,
) -> Dict[str, Any]:
    """Run all registered tests."""
    runner = get_test_runner()

    if include_system:
        runner.register_system_tests()

    return await runner.run_all(tags)


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_runner_instance: Optional[TestRunner] = None


def get_test_runner() -> TestRunner:
    """Get the singleton TestRunner instance."""
    global _runner_instance

    if _runner_instance is None:
        _runner_instance = TestRunner()

    return _runner_instance
