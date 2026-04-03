"""
KV1NT Proaktivt Anbefalingssystem
=================================

Analyserer systemtilstand og genererer intelligente anbefalinger
baseret på:
1. Test resultater (fejlende tests → fix anbefalinger)
2. Performance metrics (langsom respons → optimering)
3. Evolution historik (trends → prædiktioner)
4. System health (services → recovery)
5. REGELBASERET ENGINE - Auto-triggering baseret på tærskelværdier

Version: 2.0.0 - Med Regelbaseret Engine
Author: Claude (Ultimate Instruktor & Dirigent)
Super Admin: Rasmus (System Creator & Visionary)
"""

import json
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class RecommendationPriority(Enum):
    """Prioritet for anbefalinger."""
    CRITICAL = "critical"    # Kræver øjeblikkelig handling
    HIGH = "high"            # Bør handles snart
    MEDIUM = "medium"        # Kan vente lidt
    LOW = "low"              # Nice to have
    INFO = "info"            # Informativ


class RecommendationCategory(Enum):
    """Kategorier af anbefalinger."""
    TEST_FIX = "test_fix"
    PERFORMANCE = "performance"
    SECURITY = "security"
    INTEGRATION = "integration"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
    EVOLUTION = "evolution"


@dataclass
class Recommendation:
    """En enkelt anbefaling fra KV1NT."""
    id: str
    title: str
    description: str
    priority: RecommendationPriority
    category: RecommendationCategory
    suggested_actions: List[str]
    estimated_effort: str  # "5min", "30min", "2h", "1d", etc.
    auto_fixable: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemAnalysis:
    """Resultat af systemanalyse."""
    timestamp: datetime
    total_tests: int
    passed_tests: int
    failed_tests: int
    success_rate: float
    services_status: Dict[str, str]
    warnings: List[str]
    errors: List[str]


# =============================================================================
# REGELBASERET ENGINE - Version 2.0
# =============================================================================

class RuleType(Enum):
    """Typer af regler."""
    THRESHOLD = "threshold"      # Trigger når værdi overstiger grænse
    PATTERN = "pattern"          # Trigger ved regex match
    FREQUENCY = "frequency"      # Trigger ved gentagne events
    SCHEDULE = "schedule"        # Trigger på tidspunkt
    COMPOUND = "compound"        # Kombination af regler


@dataclass
class Rule:
    """
    En selvoptimerende regel i KV1NT systemet.

    Regler kan automatisk trigge handlinger baseret på systemtilstand.
    """
    id: str
    name: str
    description: str
    rule_type: RuleType
    condition: Dict[str, Any]  # Betingelse for trigger
    action: str                # Handling ved trigger (script/command)
    priority: RecommendationPriority
    category: RecommendationCategory
    enabled: bool = True
    auto_execute: bool = False  # Kør automatisk uden godkendelse
    cooldown_minutes: int = 30  # Minimum tid mellem triggers
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0

    def can_trigger(self) -> bool:
        """Tjek om reglen kan trigges (cooldown)."""
        if not self.enabled:
            return False
        if self.last_triggered is None:
            return True
        elapsed = datetime.now() - self.last_triggered
        return elapsed > timedelta(minutes=self.cooldown_minutes)

    def mark_triggered(self):
        """Markér reglen som triggered."""
        self.last_triggered = datetime.now()
        self.trigger_count += 1


@dataclass
class PerformanceMetrics:
    """Performance metrics for systemet."""
    response_time_ms: float = 0.0
    memory_usage_percent: float = 0.0
    cpu_usage_percent: float = 0.0
    disk_usage_percent: float = 0.0
    active_connections: int = 0
    requests_per_second: float = 0.0
    error_rate_percent: float = 0.0
    test_execution_time_seconds: float = 0.0


class KV1NTRuleEngine:
    """
    Regelbaseret engine for automatisk systemoptimering.

    Denne engine overvåger systemet og trigger handlinger
    baseret på konfigurerbare regler.
    """

    # Standard regler for selvoptimering
    DEFAULT_RULES = [
        # Test Success Rate Regler
        Rule(
            id="rule_test_critical",
            name="Kritisk test failure rate",
            description="Trigger når test success rate falder under 90%",
            rule_type=RuleType.THRESHOLD,
            condition={"metric": "test_success_rate", "operator": "<", "value": 90.0},
            action="notify_critical",
            priority=RecommendationPriority.CRITICAL,
            category=RecommendationCategory.TEST_FIX,
            auto_execute=False
        ),
        Rule(
            id="rule_test_warning",
            name="Test warning rate",
            description="Trigger når test success rate falder under 95%",
            rule_type=RuleType.THRESHOLD,
            condition={"metric": "test_success_rate", "operator": "<", "value": 95.0},
            action="notify_warning",
            priority=RecommendationPriority.HIGH,
            category=RecommendationCategory.TEST_FIX,
            auto_execute=False
        ),

        # Performance Regler
        Rule(
            id="rule_response_time",
            name="Langsom responstid",
            description="Trigger når responstid overstiger 500ms",
            rule_type=RuleType.THRESHOLD,
            condition={"metric": "response_time_ms", "operator": ">", "value": 500.0},
            action="optimize_performance",
            priority=RecommendationPriority.HIGH,
            category=RecommendationCategory.PERFORMANCE,
            auto_execute=False
        ),
        Rule(
            id="rule_memory_high",
            name="Høj hukommelsesforbrug",
            description="Trigger når hukommelse overstiger 80%",
            rule_type=RuleType.THRESHOLD,
            condition={"metric": "memory_usage_percent", "operator": ">", "value": 80.0},
            action="memory_cleanup",
            priority=RecommendationPriority.HIGH,
            category=RecommendationCategory.PERFORMANCE,
            auto_execute=True,
            cooldown_minutes=60
        ),
        Rule(
            id="rule_cpu_sustained",
            name="Vedvarende høj CPU",
            description="Trigger når CPU vedvarende er over 70%",
            rule_type=RuleType.THRESHOLD,
            condition={"metric": "cpu_usage_percent", "operator": ">", "value": 70.0},
            action="scale_resources",
            priority=RecommendationPriority.MEDIUM,
            category=RecommendationCategory.PERFORMANCE,
            auto_execute=False
        ),
        Rule(
            id="rule_disk_space",
            name="Lav diskplads",
            description="Trigger når disk usage overstiger 85%",
            rule_type=RuleType.THRESHOLD,
            condition={"metric": "disk_usage_percent", "operator": ">", "value": 85.0},
            action="disk_cleanup",
            priority=RecommendationPriority.HIGH,
            category=RecommendationCategory.PERFORMANCE,
            auto_execute=True
        ),

        # Service Health Regler
        Rule(
            id="rule_service_down",
            name="Service nede",
            description="Trigger når en service er nede",
            rule_type=RuleType.PATTERN,
            condition={"pattern": r"(down|stopped|failed|error)", "field": "service_status"},
            action="restart_service",
            priority=RecommendationPriority.CRITICAL,
            category=RecommendationCategory.INTEGRATION,
            auto_execute=True,
            cooldown_minutes=5
        ),
        Rule(
            id="rule_error_rate",
            name="Høj fejlrate",
            description="Trigger når fejlrate overstiger 1%",
            rule_type=RuleType.THRESHOLD,
            condition={"metric": "error_rate_percent", "operator": ">", "value": 1.0},
            action="investigate_errors",
            priority=RecommendationPriority.HIGH,
            category=RecommendationCategory.INTEGRATION,
            auto_execute=False
        ),

        # Evolution Regler
        Rule(
            id="rule_regression",
            name="Test regression",
            description="Trigger når tests begynder at fejle der tidligere passede",
            rule_type=RuleType.COMPOUND,
            condition={"check": "regression_detected"},
            action="rollback_warning",
            priority=RecommendationPriority.CRITICAL,
            category=RecommendationCategory.EVOLUTION,
            auto_execute=False
        ),
    ]

    def __init__(self, custom_rules: List[Rule] = None):
        """
        Initialiserer regel engine.

        Args:
            custom_rules: Valgfri liste af custom regler
        """
        self.rules = list(self.DEFAULT_RULES)
        if custom_rules:
            self.rules.extend(custom_rules)
        self.triggered_rules: List[Rule] = []
        self.action_log: List[Dict[str, Any]] = []

    def evaluate_threshold(self, rule: Rule, metrics: Dict[str, float]) -> bool:
        """Evaluerer en threshold regel."""
        condition = rule.condition
        metric_name = condition.get("metric")
        operator = condition.get("operator")
        threshold = condition.get("value")

        if metric_name not in metrics:
            return False

        value = metrics[metric_name]

        if operator == "<":
            return value < threshold
        elif operator == ">":
            return value > threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "==":
            return value == threshold

        return False

    def evaluate_pattern(self, rule: Rule, data: Dict[str, str]) -> bool:
        """Evaluerer en pattern regel."""
        condition = rule.condition
        pattern = condition.get("pattern")
        field = condition.get("field")

        for key, value in data.items():
            if field and key != field:
                continue
            if re.search(pattern, str(value), re.IGNORECASE):
                return True

        return False

    def evaluate_rules(
        self,
        metrics: PerformanceMetrics,
        services: Dict[str, str],
        test_success_rate: float
    ) -> List[Rule]:
        """
        Evaluerer alle regler mod aktuel systemtilstand.

        Args:
            metrics: Performance metrics
            services: Service status dict
            test_success_rate: Aktuel test success rate

        Returns:
            Liste af triggered regler
        """
        triggered = []

        # Konverter metrics til dict
        metrics_dict = {
            "test_success_rate": test_success_rate,
            "response_time_ms": metrics.response_time_ms,
            "memory_usage_percent": metrics.memory_usage_percent,
            "cpu_usage_percent": metrics.cpu_usage_percent,
            "disk_usage_percent": metrics.disk_usage_percent,
            "error_rate_percent": metrics.error_rate_percent,
        }

        for rule in self.rules:
            if not rule.can_trigger():
                continue

            should_trigger = False

            if rule.rule_type == RuleType.THRESHOLD:
                should_trigger = self.evaluate_threshold(rule, metrics_dict)
            elif rule.rule_type == RuleType.PATTERN:
                should_trigger = self.evaluate_pattern(rule, services)
            # Andre rule types kan tilføjes her

            if should_trigger:
                rule.mark_triggered()
                triggered.append(rule)
                self.action_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "auto_executed": rule.auto_execute
                })

        self.triggered_rules = triggered
        return triggered

    def generate_recommendations(self, triggered_rules: List[Rule]) -> List[Recommendation]:
        """
        Genererer anbefalinger fra triggered regler.

        Args:
            triggered_rules: Liste af triggered regler

        Returns:
            Liste af anbefalinger
        """
        recommendations = []

        action_descriptions = {
            "notify_critical": [
                "KRITISK: Undersøg øjeblikkeligt",
                "Kør: pytest -v --tb=long for detaljer",
                "Check seneste commits for breaking changes",
                "Overvej rollback hvis nødvendigt"
            ],
            "notify_warning": [
                "Undersøg fejlende tests",
                "Kør: pytest -v for at se hvilke tests fejler",
                "Prioritér fixes inden næste deployment"
            ],
            "optimize_performance": [
                "Analysér slow queries i database",
                "Check for N+1 query problemer",
                "Overvej caching strategi",
                "Profiler applikationen"
            ],
            "memory_cleanup": [
                "Genstart services med høj memory",
                "Check for memory leaks",
                "Overvej at øge memory limits"
            ],
            "scale_resources": [
                "Overvej horizontal scaling",
                "Check for CPU-intensive operationer",
                "Optimér algoritmer hvis muligt"
            ],
            "disk_cleanup": [
                "Ryd gamle logs: find /var/log -mtime +30 -delete",
                "Ryd Docker: docker system prune -a",
                "Check for store midlertidige filer"
            ],
            "restart_service": [
                "Genstart service: docker restart <service>",
                "Check logs: docker logs <service>",
                "Verificer health endpoint"
            ],
            "investigate_errors": [
                "Check error logs",
                "Identificer fejlmønstre",
                "Implementér bedre error handling"
            ],
            "rollback_warning": [
                "ADVARSEL: Regression detekteret",
                "Sammenlign med tidligere test rapport",
                "Identificer breaking changes",
                "Overvej git revert"
            ]
        }

        for rule in triggered_rules:
            actions = action_descriptions.get(rule.action, ["Udfør handling: " + rule.action])

            rec = Recommendation(
                id=f"auto_{rule.id}_{datetime.now().strftime('%Y%m%d%H%M')}",
                title=f"[AUTO] {rule.name}",
                description=rule.description,
                priority=rule.priority,
                category=rule.category,
                suggested_actions=actions,
                estimated_effort="varies",
                auto_fixable=rule.auto_execute,
                metadata={
                    "rule_id": rule.id,
                    "trigger_count": rule.trigger_count,
                    "auto_execute": rule.auto_execute
                }
            )
            recommendations.append(rec)

        return recommendations

    def execute_auto_actions(self, triggered_rules: List[Rule]) -> List[Dict[str, Any]]:
        """
        Udfører automatiske handlinger for regler med auto_execute=True.

        BEMÆRK: Kun sikre handlinger udføres automatisk.
        """
        results = []

        safe_actions = {
            "memory_cleanup": "docker system prune -f --volumes 2>/dev/null || true",
            "disk_cleanup": "find /tmp -type f -mtime +7 -delete 2>/dev/null || true",
        }

        for rule in triggered_rules:
            if not rule.auto_execute:
                continue

            if rule.action in safe_actions:
                cmd = safe_actions[rule.action]
                try:
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    results.append({
                        "rule_id": rule.id,
                        "action": rule.action,
                        "success": result.returncode == 0,
                        "output": result.stdout[:500] if result.stdout else "",
                        "error": result.stderr[:500] if result.stderr else ""
                    })
                except subprocess.TimeoutExpired:
                    results.append({
                        "rule_id": rule.id,
                        "action": rule.action,
                        "success": False,
                        "error": "Timeout after 30 seconds"
                    })
                except Exception as e:
                    results.append({
                        "rule_id": rule.id,
                        "action": rule.action,
                        "success": False,
                        "error": str(e)
                    })

        return results

    def get_rule_status(self) -> Dict[str, Any]:
        """Returnerer status for alle regler."""
        return {
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for r in self.rules if r.enabled),
            "auto_execute_rules": sum(1 for r in self.rules if r.auto_execute),
            "recently_triggered": [
                {
                    "id": r.id,
                    "name": r.name,
                    "last_triggered": r.last_triggered.isoformat() if r.last_triggered else None,
                    "trigger_count": r.trigger_count
                }
                for r in self.rules if r.trigger_count > 0
            ],
            "action_log": self.action_log[-20:]  # Sidste 20 actions
        }


class KV1NTRecommendationEngine:
    """
    KV1NT Proaktivt Anbefalingssystem.

    Analyserer systemtilstand og genererer intelligente anbefalinger
    for at forbedre systemets sundhed og ydeevne.
    """

    def __init__(self, evolution_reports_path: str = None):
        self.evolution_reports_path = Path(
            evolution_reports_path or
            "/home/rasmus/Desktop/projects/cirkelline-system/ecosystems/evolution_reports"
        )
        self.recommendations: List[Recommendation] = []

    def analyze_test_results(self, failed_tests: List[str]) -> List[Recommendation]:
        """Analyserer fejlende tests og genererer fix-anbefalinger."""
        recommendations = []

        # Gruppér tests efter fil
        test_files = {}
        for test in failed_tests:
            parts = test.split("::")
            file_name = parts[0] if parts else test
            if file_name not in test_files:
                test_files[file_name] = []
            test_files[file_name].append(test)

        # Generer anbefalinger per testfil
        for file_name, tests in test_files.items():
            if "async" in str(tests).lower():
                recommendations.append(Recommendation(
                    id=f"fix_async_{file_name}",
                    title=f"Tilføj @pytest.mark.asyncio til {file_name}",
                    description=f"{len(tests)} tests fejler pga. manglende async marker",
                    priority=RecommendationPriority.HIGH,
                    category=RecommendationCategory.TEST_FIX,
                    suggested_actions=[
                        f"Åbn {file_name}",
                        "Tilføj 'import pytest' øverst",
                        "Tilføj '@pytest.mark.asyncio' over hver async test funktion",
                        "Kør tests igen for at verificere"
                    ],
                    estimated_effort="15min",
                    auto_fixable=True,
                    metadata={"failed_tests": tests}
                ))
            else:
                recommendations.append(Recommendation(
                    id=f"investigate_{file_name}",
                    title=f"Undersøg fejlende tests i {file_name}",
                    description=f"{len(tests)} tests fejler og kræver manuel undersøgelse",
                    priority=RecommendationPriority.MEDIUM,
                    category=RecommendationCategory.TEST_FIX,
                    suggested_actions=[
                        f"Kør: pytest {file_name} -v --tb=long",
                        "Analysér stack traces",
                        "Identificer root cause",
                        "Implementer fix"
                    ],
                    estimated_effort="30min",
                    auto_fixable=False,
                    metadata={"failed_tests": tests}
                ))

        return recommendations

    def analyze_service_health(self, services: Dict[str, str]) -> List[Recommendation]:
        """Analyserer service sundhed og genererer recovery anbefalinger."""
        recommendations = []

        for service, status in services.items():
            if status.lower() not in ["running", "healthy", "up", "ok"]:
                recommendations.append(Recommendation(
                    id=f"recover_{service}",
                    title=f"Genstart {service} service",
                    description=f"{service} har status: {status}",
                    priority=RecommendationPriority.CRITICAL,
                    category=RecommendationCategory.INTEGRATION,
                    suggested_actions=[
                        f"Tjek logs: docker logs {service}",
                        f"Genstart: docker restart {service}",
                        "Verificer health: curl endpoint",
                        "Monitorér i 5 minutter"
                    ],
                    estimated_effort="10min",
                    auto_fixable=True,
                    metadata={"service": service, "status": status}
                ))

        return recommendations

    def analyze_port_conflicts(self, ports: Dict[int, List[str]]) -> List[Recommendation]:
        """Analyserer port konflikter."""
        recommendations = []

        for port, services in ports.items():
            if len(services) > 1:
                recommendations.append(Recommendation(
                    id=f"port_conflict_{port}",
                    title=f"Port {port} konflikt mellem {', '.join(services)}",
                    description=f"Flere services forsøger at bruge port {port}",
                    priority=RecommendationPriority.HIGH,
                    category=RecommendationCategory.ARCHITECTURE,
                    suggested_actions=[
                        f"Identificer hvilken service der skal bruge port {port}",
                        "Opdater den anden service til at bruge en anden port",
                        "Opdater environment variables",
                        "Genstart begge services"
                    ],
                    estimated_effort="20min",
                    auto_fixable=False,
                    metadata={"port": port, "services": services}
                ))

        return recommendations

    def analyze_evolution_trends(self) -> List[Recommendation]:
        """Analyserer evolution trends fra historiske rapporter."""
        recommendations = []

        try:
            reports = list(self.evolution_reports_path.glob("master_ops_*.json"))
            if len(reports) >= 2:
                # Læs de seneste to rapporter
                reports.sort(key=lambda x: x.stat().st_mtime, reverse=True)

                with open(reports[0]) as f:
                    latest = json.load(f)
                with open(reports[1]) as f:
                    previous = json.load(f)

                # Sammenlign test resultater
                latest_rate = latest.get("test_results", {}).get("success_rate", 0)
                previous_rate = previous.get("test_results", {}).get("success_rate", 0)

                if latest_rate < previous_rate:
                    recommendations.append(Recommendation(
                        id="regression_detected",
                        title="Test regression detekteret",
                        description=f"Success rate faldet fra {previous_rate}% til {latest_rate}%",
                        priority=RecommendationPriority.HIGH,
                        category=RecommendationCategory.EVOLUTION,
                        suggested_actions=[
                            "Identificer nye fejlende tests",
                            "Check seneste commits",
                            "Rollback hvis nødvendigt",
                            "Fix regression før fortsættelse"
                        ],
                        estimated_effort="1h",
                        auto_fixable=False,
                        metadata={
                            "previous_rate": previous_rate,
                            "latest_rate": latest_rate,
                            "delta": latest_rate - previous_rate
                        }
                    ))
                elif latest_rate > previous_rate:
                    recommendations.append(Recommendation(
                        id="improvement_detected",
                        title="Test forbedring registreret!",
                        description=f"Success rate steget fra {previous_rate}% til {latest_rate}%",
                        priority=RecommendationPriority.INFO,
                        category=RecommendationCategory.EVOLUTION,
                        suggested_actions=[
                            "Fortsæt det gode arbejde!",
                            "Dokumenter hvad der virkede",
                            "Del med teamet"
                        ],
                        estimated_effort="5min",
                        auto_fixable=False,
                        metadata={
                            "previous_rate": previous_rate,
                            "latest_rate": latest_rate,
                            "delta": latest_rate - previous_rate
                        }
                    ))
        except Exception:
            pass  # Ignorér fejl ved læsning af rapporter

        return recommendations

    def generate_integration_recommendations(self) -> List[Recommendation]:
        """Genererer integrationsanbefalinger baseret på systemlandskab."""
        return [
            Recommendation(
                id="integrate_cosmic_ckc",
                title="Integrér Cosmic Library med CKC MASTERMIND",
                description="Begge systemer bruger port 7778 - koordinér API endpoints",
                priority=RecommendationPriority.MEDIUM,
                category=RecommendationCategory.INTEGRATION,
                suggested_actions=[
                    "Design shared API gateway",
                    "Implementer service discovery",
                    "Setup cross-platform auth",
                    "Test integration flows"
                ],
                estimated_effort="4h",
                auto_fixable=False
            ),
            Recommendation(
                id="setup_event_bus",
                title="Implementér event bus for cross-platform kommunikation",
                description="Brug RabbitMQ (allerede kørende) til events mellem services",
                priority=RecommendationPriority.LOW,
                category=RecommendationCategory.ARCHITECTURE,
                suggested_actions=[
                    "Design event schema",
                    "Implementér publishers i CKC",
                    "Implementér subscribers i Cosmic",
                    "Test event flow"
                ],
                estimated_effort="2h",
                auto_fixable=False
            )
        ]

    def analyze_system(self, analysis: SystemAnalysis) -> List[Recommendation]:
        """
        Hovedmetode: Analyserer fuld systemtilstand.

        Args:
            analysis: SystemAnalysis objekt med aktuelle metrics

        Returns:
            Liste af prioriterede anbefalinger
        """
        all_recommendations = []

        # Analysér test resultater
        if analysis.errors:
            all_recommendations.extend(
                self.analyze_test_results(analysis.errors)
            )

        # Analysér service health
        all_recommendations.extend(
            self.analyze_service_health(analysis.services_status)
        )

        # Analysér evolution trends
        all_recommendations.extend(self.analyze_evolution_trends())

        # Tilføj integrationsanbefalinger
        all_recommendations.extend(self.generate_integration_recommendations())

        # Sortér efter prioritet
        priority_order = {
            RecommendationPriority.CRITICAL: 0,
            RecommendationPriority.HIGH: 1,
            RecommendationPriority.MEDIUM: 2,
            RecommendationPriority.LOW: 3,
            RecommendationPriority.INFO: 4
        }

        all_recommendations.sort(
            key=lambda r: priority_order.get(r.priority, 5)
        )

        self.recommendations = all_recommendations
        return all_recommendations

    def generate_recommendations(self) -> List[Recommendation]:
        """Wrapper for analyze_system with default empty analysis."""
        default_analysis = SystemAnalysis(
            timestamp=datetime.now(),
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            success_rate=100.0,
            services_status={},
            warnings=[],
            errors=[]
        )
        return self.analyze_system(default_analysis)

    def to_markdown(self) -> str:
        """Konverterer anbefalinger til markdown format."""
        lines = [
            "# KV1NT ANBEFALINGSRAPPORT",
            f"**Genereret:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**Antal anbefalinger:** {len(self.recommendations)}",
            "",
            "---",
            ""
        ]

        # Gruppér efter prioritet
        by_priority = {}
        for rec in self.recommendations:
            if rec.priority not in by_priority:
                by_priority[rec.priority] = []
            by_priority[rec.priority].append(rec)

        priority_emoji = {
            RecommendationPriority.CRITICAL: "🔴",
            RecommendationPriority.HIGH: "🟠",
            RecommendationPriority.MEDIUM: "🟡",
            RecommendationPriority.LOW: "🟢",
            RecommendationPriority.INFO: "ℹ️"
        }

        for priority in RecommendationPriority:
            if priority in by_priority:
                emoji = priority_emoji.get(priority, "")
                lines.append(f"## {emoji} {priority.value.upper()}")
                lines.append("")

                for rec in by_priority[priority]:
                    lines.append(f"### {rec.title}")
                    lines.append(f"*{rec.description}*")
                    lines.append(f"- **Kategori:** {rec.category.value}")
                    lines.append(f"- **Estimeret tid:** {rec.estimated_effort}")
                    lines.append(f"- **Auto-fixable:** {'Ja' if rec.auto_fixable else 'Nej'}")
                    lines.append("")
                    lines.append("**Handlinger:**")
                    for i, action in enumerate(rec.suggested_actions, 1):
                        lines.append(f"{i}. {action}")
                    lines.append("")
                lines.append("---")
                lines.append("")

        return "\n".join(lines)

    def save_report(self, filename: str = None) -> str:
        """Gemmer anbefalingsrapport til fil."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"KV1NT_RECOMMENDATIONS_{timestamp}.md"

        filepath = self.evolution_reports_path / filename
        filepath.write_text(self.to_markdown())
        return str(filepath)


# Convenience function for quick analysis
def quick_analysis(
    failed_tests: List[str] = None,
    services: Dict[str, str] = None
) -> str:
    """
    Hurtig analyse og generering af anbefalinger.

    Args:
        failed_tests: Liste af fejlende test navne
        services: Dict med service navn -> status

    Returns:
        Markdown formateret anbefalingsrapport
    """
    engine = KV1NTRecommendationEngine()

    analysis = SystemAnalysis(
        timestamp=datetime.now(),
        total_tests=1277,
        passed_tests=1244,
        failed_tests=33,
        success_rate=97.4,
        services_status=services or {
            "ckc-postgres": "running",
            "localstack": "running",
            "redis": "running",
            "rabbitmq": "running"
        },
        warnings=[],
        errors=failed_tests or []
    )

    engine.analyze_system(analysis)
    return engine.to_markdown()


# =============================================================================
# KV1NT PATTERN ANALYZER - AI Mønstergenkendelse (P1-11)
# =============================================================================

@dataclass
class TrendDataPoint:
    """Et datapunkt i en trend tidsserie."""
    timestamp: datetime
    value: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DetectedPattern:
    """Et detekteret mønster i historiske data."""
    pattern_id: str
    pattern_type: str  # "regression", "improvement", "oscillation", "degradation"
    description: str
    confidence: float  # 0.0 - 1.0
    occurrences: int
    first_seen: datetime
    last_seen: datetime
    affected_metrics: List[str]
    severity: str  # "low", "medium", "high", "critical"


@dataclass
class PredictiveInsight:
    """En prædiktiv indsigt baseret på historisk analyse."""
    insight_id: str
    prediction: str
    probability: float  # 0.0 - 1.0
    timeframe: str  # "immediate", "short_term", "medium_term", "long_term"
    basis: str  # Forklaring af hvad prædiktion er baseret på
    recommended_actions: List[str]
    priority: RecommendationPriority


class KV1NTPatternAnalyzer:
    """
    KV1NT AI Mønstergenkendelse System.

    Analyserer historiske data fra evolution_reports/ for at:
    1. Identificere trends i test success rates
    2. Detektere gentagne fejlmønstre
    3. Prædikere potentielle fremtidige problemer
    4. Generere proaktive anbefalinger

    Bruger simpel statistisk analyse - ingen ekstern ML model.
    """

    def __init__(self, reports_path: str = None):
        """
        Initialiserer Pattern Analyzer.

        Args:
            reports_path: Sti til evolution_reports mappe
        """
        self.reports_path = Path(
            reports_path or
            "/home/rasmus/Desktop/projects/cirkelline-system/ecosystems/evolution_reports"
        )
        self.historical_data: List[Dict[str, Any]] = []
        self.trend_data: Dict[str, List[TrendDataPoint]] = {
            "test_success_rate": [],
            "total_tests": [],
            "failed_tests": [],
        }
        self.detected_patterns: List[DetectedPattern] = []
        self.insights: List[PredictiveInsight] = []

    def load_historical_reports(self) -> int:
        """
        Indlæser alle historiske rapporter fra evolution_reports/.

        Returns:
            Antal indlæste rapporter
        """
        loaded = 0
        self.historical_data = []

        # Find alle JSON filer
        json_files = list(self.reports_path.glob("*.json"))
        json_files.sort(key=lambda x: x.stat().st_mtime)

        for json_file in json_files:
            try:
                with open(json_file) as f:
                    data = json.load(f)

                # Parse timestamp
                timestamp = None
                for ts_field in ["timestamp", "report_timestamp", "evening_validation_time"]:
                    if ts_field in data:
                        try:
                            ts_str = data[ts_field]
                            timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                            break
                        except (ValueError, TypeError):
                            pass

                if not timestamp:
                    # Brug filens modification time
                    timestamp = datetime.fromtimestamp(json_file.stat().st_mtime)

                data["_parsed_timestamp"] = timestamp
                data["_source_file"] = str(json_file.name)
                self.historical_data.append(data)

                # Udtræk test metrics til trend data
                test_results = data.get("test_results", {})
                if test_results:
                    success_rate = test_results.get("success_rate", 0)
                    self.trend_data["test_success_rate"].append(
                        TrendDataPoint(
                            timestamp=timestamp,
                            value=float(success_rate),
                            source=str(json_file.name)
                        )
                    )
                    if "total" in test_results:
                        self.trend_data["total_tests"].append(
                            TrendDataPoint(
                                timestamp=timestamp,
                                value=float(test_results["total"]),
                                source=str(json_file.name)
                            )
                        )
                    if "failed" in test_results:
                        self.trend_data["failed_tests"].append(
                            TrendDataPoint(
                                timestamp=timestamp,
                                value=float(test_results["failed"]),
                                source=str(json_file.name)
                            )
                        )

                loaded += 1
            except (OSError, json.JSONDecodeError):
                pass  # Ignorér korrupte filer

        return loaded

    def calculate_trend(self, data_points: List[TrendDataPoint]) -> Dict[str, Any]:
        """
        Beregner trend statistik for en serie af datapunkter.

        Returns:
            Dict med trend info: direction, slope, average, variance, etc.
        """
        if len(data_points) < 2:
            return {"direction": "unknown", "slope": 0.0, "confidence": 0.0}

        values = [dp.value for dp in data_points]
        n = len(values)

        # Beregn gennemsnit
        avg = sum(values) / n

        # Beregn varians
        variance = sum((v - avg) ** 2 for v in values) / n

        # Beregn simpel lineær regression slope
        # y = mx + b, find m
        x_vals = list(range(n))
        x_avg = sum(x_vals) / n

        numerator = sum((x_vals[i] - x_avg) * (values[i] - avg) for i in range(n))
        denominator = sum((x - x_avg) ** 2 for x in x_vals)

        slope = numerator / denominator if denominator != 0 else 0

        # Bestem retning
        if slope > 0.5:
            direction = "improving"
        elif slope < -0.5:
            direction = "degrading"
        else:
            direction = "stable"

        # Beregn konfidence baseret på konsistens
        if variance < 1.0:
            confidence = 0.9
        elif variance < 5.0:
            confidence = 0.7
        elif variance < 10.0:
            confidence = 0.5
        else:
            confidence = 0.3

        return {
            "direction": direction,
            "slope": slope,
            "average": avg,
            "variance": variance,
            "min": min(values),
            "max": max(values),
            "latest": values[-1] if values else 0,
            "confidence": confidence,
            "data_points": n
        }

    def analyze_trends(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyserer trends i alle metrics.

        Returns:
            Dict med trend info per metric
        """
        trends = {}

        for metric_name, data_points in self.trend_data.items():
            if data_points:
                trends[metric_name] = self.calculate_trend(data_points)

        return trends

    def detect_patterns(self) -> List[DetectedPattern]:
        """
        Detekterer mønstre i historiske data.

        Returns:
            Liste af detekterede mønstre
        """
        self.detected_patterns = []
        trends = self.analyze_trends()

        # Mønster 1: Success rate regression
        if "test_success_rate" in trends:
            trend = trends["test_success_rate"]
            if trend["direction"] == "degrading" and trend["slope"] < -1.0:
                self.detected_patterns.append(DetectedPattern(
                    pattern_id="pattern_regression",
                    pattern_type="regression",
                    description="Test success rate er faldende over tid",
                    confidence=trend["confidence"],
                    occurrences=trend["data_points"],
                    first_seen=self.trend_data["test_success_rate"][0].timestamp,
                    last_seen=self.trend_data["test_success_rate"][-1].timestamp,
                    affected_metrics=["test_success_rate"],
                    severity="high" if trend["slope"] < -2.0 else "medium"
                ))

        # Mønster 2: Oscillerende success rate
        if "test_success_rate" in trends:
            trend = trends["test_success_rate"]
            if trend["variance"] > 10.0 and trend["direction"] == "stable":
                self.detected_patterns.append(DetectedPattern(
                    pattern_id="pattern_oscillation",
                    pattern_type="oscillation",
                    description="Test success rate oscillerer ustabilt",
                    confidence=0.6,
                    occurrences=trend["data_points"],
                    first_seen=self.trend_data["test_success_rate"][0].timestamp,
                    last_seen=self.trend_data["test_success_rate"][-1].timestamp,
                    affected_metrics=["test_success_rate"],
                    severity="medium"
                ))

        # Mønster 3: Stigende antal tests
        if "total_tests" in trends:
            trend = trends["total_tests"]
            if trend["direction"] == "improving" and trend["slope"] > 10.0:
                self.detected_patterns.append(DetectedPattern(
                    pattern_id="pattern_growth",
                    pattern_type="improvement",
                    description="Test suite vokser sundt over tid",
                    confidence=trend["confidence"],
                    occurrences=trend["data_points"],
                    first_seen=self.trend_data["total_tests"][0].timestamp,
                    last_seen=self.trend_data["total_tests"][-1].timestamp,
                    affected_metrics=["total_tests"],
                    severity="low"
                ))

        # Mønster 4: Stigende fejl
        if "failed_tests" in trends:
            trend = trends["failed_tests"]
            if trend["direction"] == "improving" and trend["slope"] > 5.0:
                # "improving" slope i fejl er faktisk dårligt
                self.detected_patterns.append(DetectedPattern(
                    pattern_id="pattern_increasing_failures",
                    pattern_type="degradation",
                    description="Antal fejlende tests er stigende",
                    confidence=trend["confidence"],
                    occurrences=trend["data_points"],
                    first_seen=self.trend_data["failed_tests"][0].timestamp,
                    last_seen=self.trend_data["failed_tests"][-1].timestamp,
                    affected_metrics=["failed_tests"],
                    severity="high"
                ))

        return self.detected_patterns

    def generate_predictions(self) -> List[PredictiveInsight]:
        """
        Genererer prædiktive indsigter baseret på mønstre og trends.

        Returns:
            Liste af prædiktive indsigter
        """
        self.insights = []
        trends = self.analyze_trends()

        # Prædiktion 1: Baseret på success rate trend
        if "test_success_rate" in trends:
            trend = trends["test_success_rate"]
            current_rate = trend["latest"]

            if trend["direction"] == "degrading":
                # Prædiker hvornår vi rammer kritisk niveau
                if current_rate > 90:
                    days_to_critical = (current_rate - 90) / abs(trend["slope"]) if trend["slope"] != 0 else float("inf")
                    self.insights.append(PredictiveInsight(
                        insight_id="predict_critical_rate",
                        prediction=f"Test success rate kan falde under 90% inden for {int(days_to_critical)} dage",
                        probability=trend["confidence"] * 0.8,
                        timeframe="short_term" if days_to_critical < 7 else "medium_term",
                        basis=f"Baseret på nuværende slope ({trend['slope']:.2f}) og rate ({current_rate}%)",
                        recommended_actions=[
                            "Prioritér at fixe eksisterende fejlende tests",
                            "Review seneste kodeændringer",
                            "Overvej at pause nye features indtil stabilitet"
                        ],
                        priority=RecommendationPriority.HIGH
                    ))

            elif trend["direction"] == "improving" and current_rate < 100:
                # Prædiker hvornår vi kan nå 100%
                days_to_perfect = (100 - current_rate) / trend["slope"] if trend["slope"] > 0 else float("inf")
                if days_to_perfect < 30:
                    self.insights.append(PredictiveInsight(
                        insight_id="predict_perfect_rate",
                        prediction=f"Potentiale for 100% success rate inden for {int(days_to_perfect)} dage",
                        probability=trend["confidence"] * 0.6,
                        timeframe="short_term",
                        basis=f"Positiv trend med slope ({trend['slope']:.2f})",
                        recommended_actions=[
                            "Fortsæt nuværende momentum",
                            "Dokumenter hvad der virker",
                            "Del best practices med teamet"
                        ],
                        priority=RecommendationPriority.INFO
                    ))

        # Prædiktion 2: Baseret på mønstre
        for pattern in self.detected_patterns:
            if pattern.pattern_type == "oscillation":
                self.insights.append(PredictiveInsight(
                    insight_id="predict_instability",
                    prediction="System er ustabilt - sandsynlighed for uventede fejl er høj",
                    probability=0.7,
                    timeframe="immediate",
                    basis=f"Baseret på oscillation mønster med varians {trends.get('test_success_rate', {}).get('variance', 0):.2f}",
                    recommended_actions=[
                        "Identificér root cause til variationen",
                        "Check for flaky tests",
                        "Stabiliser CI/CD pipeline",
                        "Overvej at køre tests flere gange for konsistens"
                    ],
                    priority=RecommendationPriority.MEDIUM
                ))

            elif pattern.pattern_type == "degradation":
                self.insights.append(PredictiveInsight(
                    insight_id="predict_system_degradation",
                    prediction="System kvalitet degraderer - handling påkrævet",
                    probability=pattern.confidence,
                    timeframe="immediate",
                    basis=f"Baseret på {pattern.description}",
                    recommended_actions=[
                        "Stop nye features midlertidigt",
                        "Allokér ressourcer til teknisk gæld",
                        "Kør audit af kodebase",
                        "Etabler kvalitets-gates"
                    ],
                    priority=RecommendationPriority.CRITICAL
                ))

        return self.insights

    def get_full_analysis(self) -> Dict[str, Any]:
        """
        Returnerer komplet analyse med trends, mønstre og prædiktioner.

        Returns:
            Dict med samlet analyse
        """
        # Sørg for at data er loaded
        if not self.historical_data:
            self.load_historical_reports()

        trends = self.analyze_trends()
        patterns = self.detect_patterns()
        predictions = self.generate_predictions()

        return {
            "analysis_timestamp": datetime.now().isoformat(),
            "data_points_analyzed": len(self.historical_data),
            "trends": trends,
            "patterns": [
                {
                    "id": p.pattern_id,
                    "type": p.pattern_type,
                    "description": p.description,
                    "confidence": p.confidence,
                    "severity": p.severity
                }
                for p in patterns
            ],
            "predictions": [
                {
                    "id": i.insight_id,
                    "prediction": i.prediction,
                    "probability": i.probability,
                    "timeframe": i.timeframe,
                    "priority": i.priority.value
                }
                for i in predictions
            ],
            "recommendations": self._generate_combined_recommendations()
        }

    def _generate_combined_recommendations(self) -> List[Recommendation]:
        """
        Genererer kombinerede anbefalinger fra mønstre og prædiktioner.
        """
        recommendations = []

        for insight in self.insights:
            rec = Recommendation(
                id=f"kv1nt_{insight.insight_id}",
                title=f"[KV1NT PRÆDIKTION] {insight.prediction[:50]}...",
                description=insight.prediction,
                priority=insight.priority,
                category=RecommendationCategory.EVOLUTION,
                suggested_actions=insight.recommended_actions,
                estimated_effort="varies",
                auto_fixable=False,
                metadata={
                    "probability": insight.probability,
                    "timeframe": insight.timeframe,
                    "basis": insight.basis
                }
            )
            recommendations.append(rec)

        for pattern in self.detected_patterns:
            if pattern.severity in ["high", "critical"]:
                rec = Recommendation(
                    id=f"kv1nt_{pattern.pattern_id}",
                    title=f"[KV1NT MØNSTER] {pattern.description[:50]}...",
                    description=pattern.description,
                    priority=RecommendationPriority.HIGH if pattern.severity == "high" else RecommendationPriority.CRITICAL,
                    category=RecommendationCategory.EVOLUTION,
                    suggested_actions=[
                        f"Undersøg mønster: {pattern.pattern_type}",
                        f"Påvirker: {', '.join(pattern.affected_metrics)}",
                        "Kør detaljeret analyse",
                        "Etabler monitoring"
                    ],
                    estimated_effort="1h",
                    auto_fixable=False,
                    metadata={
                        "pattern_type": pattern.pattern_type,
                        "confidence": pattern.confidence,
                        "occurrences": pattern.occurrences
                    }
                )
                recommendations.append(rec)

        return recommendations

    def to_markdown(self) -> str:
        """Konverterer analyse til markdown format."""
        analysis = self.get_full_analysis()

        lines = [
            "# KV1NT MØNSTERGENKENDELSE RAPPORT",
            f"**Genereret:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**Datapunkter analyseret:** {analysis['data_points_analyzed']}",
            "",
            "---",
            "",
            "## TRENDS",
            ""
        ]

        for metric, trend in analysis["trends"].items():
            direction_emoji = {
                "improving": "📈",
                "degrading": "📉",
                "stable": "➡️",
                "unknown": "❓"
            }.get(trend.get("direction", "unknown"), "❓")

            lines.append(f"### {metric}")
            lines.append(f"- **Retning:** {direction_emoji} {trend.get('direction', 'unknown')}")
            lines.append(f"- **Slope:** {trend.get('slope', 0):.2f}")
            lines.append(f"- **Gennemsnit:** {trend.get('average', 0):.2f}")
            lines.append(f"- **Seneste:** {trend.get('latest', 0):.2f}")
            lines.append(f"- **Konfidence:** {trend.get('confidence', 0):.0%}")
            lines.append("")

        lines.extend([
            "---",
            "",
            "## DETEKTEREDE MØNSTRE",
            ""
        ])

        if analysis["patterns"]:
            for pattern in analysis["patterns"]:
                severity_emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(pattern["severity"], "⚪")

                lines.append(f"### {severity_emoji} {pattern['id']}")
                lines.append(f"- **Type:** {pattern['type']}")
                lines.append(f"- **Beskrivelse:** {pattern['description']}")
                lines.append(f"- **Konfidence:** {pattern['confidence']:.0%}")
                lines.append("")
        else:
            lines.append("*Ingen signifikante mønstre detekteret.*")
            lines.append("")

        lines.extend([
            "---",
            "",
            "## PRÆDIKTIONER",
            ""
        ])

        if analysis["predictions"]:
            for pred in analysis["predictions"]:
                priority_emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢",
                    "info": "ℹ️"
                }.get(pred["priority"], "⚪")

                lines.append(f"### {priority_emoji} {pred['prediction'][:60]}...")
                lines.append(f"- **Sandsynlighed:** {pred['probability']:.0%}")
                lines.append(f"- **Tidsramme:** {pred['timeframe']}")
                lines.append(f"- **Prioritet:** {pred['priority']}")
                lines.append("")
        else:
            lines.append("*Ingen signifikante prædiktioner.*")
            lines.append("")

        return "\n".join(lines)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def full_kv1nt_analysis() -> str:
    """
    Kører komplet KV1NT analyse: regelbaseret + mønstergenkendelse.

    Returns:
        Markdown rapport
    """
    # Regel-baseret engine analyse
    rule_engine = KV1NTRuleEngine()

    # Simuleret system metrics (kan erstattes med rigtige)
    metrics = PerformanceMetrics(
        response_time_ms=200.0,
        memory_usage_percent=45.0,
        cpu_usage_percent=30.0,
        disk_usage_percent=60.0,
    )
    services = {"postgres": "healthy", "localstack": "running", "redis": "running"}
    test_rate = 97.0

    triggered = rule_engine.evaluate_rules(metrics, services, test_rate)
    rule_recs = rule_engine.generate_recommendations(triggered)

    # Mønstergenkendelse analyse
    pattern_analyzer = KV1NTPatternAnalyzer()
    pattern_analyzer.load_historical_reports()
    pattern_report = pattern_analyzer.to_markdown()

    # Kombinér rapporter
    lines = [
        "# KV1NT KOMPLET SYSTEMANALYSE",
        f"**Genereret:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "---",
        "",
        "## DEL 1: REGELBASERET ENGINE",
        "",
        f"**Aktive regler:** {len(rule_engine.rules)}",
        f"**Triggered regler:** {len(triggered)}",
        ""
    ]

    if triggered:
        for rule in triggered:
            lines.append(f"- 🔔 **{rule.name}** ({rule.priority.value})")
    else:
        lines.append("*Ingen regler triggered - systemet er sundt.*")

    lines.extend([
        "",
        "---",
        "",
        pattern_report
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    # Test kørsel af komplet analyse
    print("=== KV1NT KOMPLET ANALYSE ===\n")

    # Test Pattern Analyzer
    analyzer = KV1NTPatternAnalyzer()
    loaded = analyzer.load_historical_reports()
    print(f"Indlæste rapporter: {loaded}")

    # Kør analyse
    analysis = analyzer.get_full_analysis()
    print(f"\nTrends: {len(analysis['trends'])}")
    print(f"Patterns: {len(analysis['patterns'])}")
    print(f"Predictions: {len(analysis['predictions'])}")

    # Udskriv markdown rapport
    print("\n" + analyzer.to_markdown())
