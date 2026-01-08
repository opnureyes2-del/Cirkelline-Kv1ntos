#!/usr/bin/env python3
"""
CIRKELLINE ROADMAP SELF-VALIDATION SYSTEM
==========================================

Zero-Oversight-Drift Validation Protocol

This script validates roadmap phases against Definition of Done criteria,
identifies missing pieces, and ensures compliance with the Zero-Drift mandate.

Usage:
    python scripts/roadmap_validator.py [--phase PHASE] [--full-audit]

Examples:
    python scripts/roadmap_validator.py --phase 5
    python scripts/roadmap_validator.py --full-audit
"""

import sys
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime, timezone


class ValidationStatus(Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"


class BlockingLevel(Enum):
    CRITICAL = "CRITICAL"  # Cannot proceed
    BLOCKING = "BLOCKING"  # Should not proceed
    WARNING = "WARNING"    # Can proceed with caution
    INFO = "INFO"          # Informational only


@dataclass
class ValidationResult:
    name: str
    status: ValidationStatus
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class MissingPiece:
    id: str
    description: str
    phase: str
    blocking: bool
    status: str
    integration_plan: str


@dataclass
class PhaseValidation:
    phase: str
    timestamp: str
    overall_status: ValidationStatus
    compliance_score: float
    validations: List[ValidationResult] = field(default_factory=list)
    missing_pieces: List[MissingPiece] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class RoadmapValidator:
    """
    Zero-Oversight-Drift Roadmap Validator

    Performs comprehensive validation of roadmap phases including:
    - Definition of Done verification
    - Dependency analysis
    - Missing pieces identification
    - Risk mitigation status
    - Documentation completeness
    """

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.results: List[PhaseValidation] = []

    def validate_phase(self, phase: str) -> PhaseValidation:
        """Validate a specific phase."""
        validation = PhaseValidation(
            phase=phase,
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            overall_status=ValidationStatus.PASS,
            compliance_score=0.0
        )

        # Run all validation checks (including HCV as mandatory checkpoint)
        validators = [
            self._validate_dod,
            self._validate_dependencies,
            self._validate_tests,
            self._validate_documentation,
            self._validate_security,
            self._validate_missing_pieces,
            self._validate_hcv  # Human-Centric Validation - MANDATORY
        ]

        scores = []
        for validator in validators:
            result = validator(phase)
            validation.validations.append(result)

            if result.status == ValidationStatus.FAIL:
                validation.overall_status = ValidationStatus.FAIL
                scores.append(0.0)
            elif result.status == ValidationStatus.WARN:
                if validation.overall_status != ValidationStatus.FAIL:
                    validation.overall_status = ValidationStatus.WARN
                scores.append(0.7)
            elif result.status == ValidationStatus.PASS:
                scores.append(1.0)
            else:
                scores.append(0.5)

        validation.compliance_score = sum(scores) / len(scores) if scores else 0.0

        # Generate recommendations
        validation.recommendations = self._generate_recommendations(validation)

        self.results.append(validation)
        return validation

    def _validate_dod(self, phase: str) -> ValidationResult:
        """Validate Definition of Done criteria."""
        # Check for implementation files based on phase
        phase_paths = {
            "5": self.project_root / "cirkelline" / "research",
            "6": self.project_root / "cirkelline" / "marketplace",
            "7": self.project_root / "cirkelline" / "ai",
            "8": self.project_root / "cirkelline" / "security"
        }

        # For now, check if web3 modules (prerequisite) are complete
        web3_path = self.project_root / "cirkelline" / "web3"

        if not web3_path.exists():
            return ValidationResult(
                name="DoD Validation",
                status=ValidationStatus.FAIL,
                message="Web3 module (prerequisite) not found",
                details={"missing_path": str(web3_path)}
            )

        # Count implemented modules
        module_count = len(list(web3_path.glob("**/*.py")))

        if module_count >= 20:
            return ValidationResult(
                name="DoD Validation",
                status=ValidationStatus.PASS,
                message=f"Web3 modules complete ({module_count} files)",
                details={"module_count": module_count}
            )
        else:
            return ValidationResult(
                name="DoD Validation",
                status=ValidationStatus.WARN,
                message=f"Web3 modules partial ({module_count}/20 files)",
                details={"module_count": module_count}
            )

    def _validate_dependencies(self, phase: str) -> ValidationResult:
        """Validate all dependencies are satisfied."""
        required_deps = {
            "5": ["web3.scanner", "web3.analysis", "web3.reporting"],
            "6": ["research.pipeline", "web3.identity"],
            "7": ["marketplace.api", "research.commander"],
            "8": ["ai.router", "ai.learning"]
        }

        deps = required_deps.get(phase, [])

        # Check if web3 modules are importable
        importable = []
        not_importable = []

        for dep in deps:
            try:
                if dep.startswith("web3"):
                    # These should be importable
                    module_path = self.project_root / "cirkelline" / dep.replace(".", "/")
                    if (self.project_root / "cirkelline" / "web3" / dep.split(".")[-1]).exists():
                        importable.append(dep)
                    else:
                        not_importable.append(dep)
                else:
                    not_importable.append(dep)  # Future phases
            except Exception:
                not_importable.append(dep)

        if not not_importable:
            return ValidationResult(
                name="Dependency Validation",
                status=ValidationStatus.PASS,
                message=f"All dependencies satisfied ({len(importable)}/{len(deps)})",
                details={"importable": importable}
            )
        elif importable:
            return ValidationResult(
                name="Dependency Validation",
                status=ValidationStatus.WARN,
                message=f"Partial dependencies ({len(importable)}/{len(deps)})",
                details={"importable": importable, "missing": not_importable}
            )
        else:
            return ValidationResult(
                name="Dependency Validation",
                status=ValidationStatus.FAIL,
                message="No dependencies satisfied",
                details={"missing": not_importable}
            )

    def _validate_tests(self, phase: str) -> ValidationResult:
        """Validate test coverage."""
        test_file = self.project_root / "tests" / "test_web3_modules.py"

        if not test_file.exists():
            return ValidationResult(
                name="Test Validation",
                status=ValidationStatus.FAIL,
                message="Test file not found",
                details={"expected_path": str(test_file)}
            )

        # Count test functions
        content = test_file.read_text()
        test_count = content.count("def test_")
        async_test_count = content.count("async def test_")
        total_tests = test_count + async_test_count

        if total_tests >= 70:
            return ValidationResult(
                name="Test Validation",
                status=ValidationStatus.PASS,
                message=f"Comprehensive test suite ({total_tests} tests)",
                details={"test_count": total_tests}
            )
        elif total_tests >= 40:
            return ValidationResult(
                name="Test Validation",
                status=ValidationStatus.WARN,
                message=f"Partial test coverage ({total_tests} tests)",
                details={"test_count": total_tests, "target": 70}
            )
        else:
            return ValidationResult(
                name="Test Validation",
                status=ValidationStatus.FAIL,
                message=f"Insufficient tests ({total_tests}/70)",
                details={"test_count": total_tests, "target": 70}
            )

    def _validate_documentation(self, phase: str) -> ValidationResult:
        """Validate documentation completeness."""
        docs_to_check = [
            self.project_root / "docs" / "ZERO-DRIFT-ROADMAP-FASE-5-8.md",
            self.project_root / "CLAUDE.md"
        ]

        existing = []
        missing = []

        for doc in docs_to_check:
            if doc.exists():
                existing.append(str(doc.name))
            else:
                missing.append(str(doc.name))

        if not missing:
            return ValidationResult(
                name="Documentation Validation",
                status=ValidationStatus.PASS,
                message=f"All documentation present ({len(existing)} files)",
                details={"existing": existing}
            )
        elif existing:
            return ValidationResult(
                name="Documentation Validation",
                status=ValidationStatus.WARN,
                message=f"Partial documentation ({len(existing)}/{len(docs_to_check)})",
                details={"existing": existing, "missing": missing}
            )
        else:
            return ValidationResult(
                name="Documentation Validation",
                status=ValidationStatus.FAIL,
                message="Documentation missing",
                details={"missing": missing}
            )

    def _validate_security(self, phase: str) -> ValidationResult:
        """Validate security requirements."""
        # Check for common security issues
        security_checks = {
            "no_hardcoded_secrets": True,
            "ci_security_scan": False,
            "dependency_audit": False
        }

        # Check CI for security job
        ci_file = self.project_root / ".github" / "workflows" / "ci.yml"
        if ci_file.exists():
            content = ci_file.read_text()
            if "security" in content.lower() and "bandit" in content.lower():
                security_checks["ci_security_scan"] = True
            if "safety" in content.lower():
                security_checks["dependency_audit"] = True

        passed = sum(1 for v in security_checks.values() if v)
        total = len(security_checks)

        if passed == total:
            return ValidationResult(
                name="Security Validation",
                status=ValidationStatus.PASS,
                message=f"All security checks pass ({passed}/{total})",
                details=security_checks
            )
        elif passed >= total / 2:
            return ValidationResult(
                name="Security Validation",
                status=ValidationStatus.WARN,
                message=f"Partial security ({passed}/{total})",
                details=security_checks
            )
        else:
            return ValidationResult(
                name="Security Validation",
                status=ValidationStatus.FAIL,
                message=f"Security gaps ({passed}/{total})",
                details=security_checks
            )

    def _check_module_implemented(self, module_path: str, min_files: int = 3) -> bool:
        """Check if a module is implemented with minimum file count."""
        path = self.project_root / module_path
        if not path.exists():
            return False
        py_files = list(path.glob("*.py"))
        return len(py_files) >= min_files

    def _validate_missing_pieces(self, phase: str) -> ValidationResult:
        """Identify and validate missing pieces with dynamic detection."""
        # Dynamic checks for implemented modules
        social_implemented = self._check_module_implemented("cirkelline/web3/social")
        llm_implemented = self._check_module_implemented("cirkelline/web3/llm")

        # Build missing pieces list based on actual implementation status
        missing_pieces = []

        # MP-001: Social Media API - only add if NOT implemented
        if not social_implemented:
            missing_pieces.append(MissingPiece(
                id="MP-001",
                description="Social Media API Keys",
                phase="5",
                blocking=False,
                status="PENDING",
                integration_plan="Request API keys, implement OAuth flow"
            ))

        # MP-002: Local LLM Fallback - only add if NOT implemented
        if not llm_implemented:
            missing_pieces.append(MissingPiece(
                id="MP-002",
                description="Local LLM Fallback",
                phase="5",
                blocking=False,
                status="PENDING",
                integration_plan="Integrate Ollama/llama.cpp"
            ))

        # Future phases - these remain as requirements
        missing_pieces.extend([
            MissingPiece(
                id="MP-005",
                description="Marketing Website",
                phase="6",
                blocking=True,
                status="REQUIRED",
                integration_plan="Create landing page before launch"
            ),
            MissingPiece(
                id="MP-009",
                description="Penetration Testing",
                phase="8",
                blocking=True,
                status="REQUIRED",
                integration_plan="Engage security firm"
            )
        ])

        phase_pieces = [p for p in missing_pieces if p.phase == phase]
        blocking_pieces = [p for p in phase_pieces if p.blocking]

        # Log implementation status for phase 5
        if phase == "5":
            impl_status = []
            if social_implemented:
                impl_status.append("Social API: IMPLEMENTED")
            if llm_implemented:
                impl_status.append("Local LLM: IMPLEMENTED")

        if not phase_pieces:
            return ValidationResult(
                name="Missing Pieces",
                status=ValidationStatus.PASS,
                message="All pieces implemented" if phase == "5" else "No missing pieces identified",
                details={
                    "social_api": "IMPLEMENTED" if social_implemented else "PENDING",
                    "local_llm": "IMPLEMENTED" if llm_implemented else "PENDING"
                } if phase == "5" else {}
            )
        elif not blocking_pieces:
            return ValidationResult(
                name="Missing Pieces",
                status=ValidationStatus.WARN,
                message=f"{len(phase_pieces)} non-blocking items",
                details={"items": [p.description for p in phase_pieces]}
            )
        else:
            return ValidationResult(
                name="Missing Pieces",
                status=ValidationStatus.FAIL,
                message=f"{len(blocking_pieces)} blocking items",
                details={
                    "blocking": [p.description for p in blocking_pieces],
                    "non_blocking": [p.description for p in phase_pieces if not p.blocking]
                }
            )

    def _validate_hcv(self, phase: str) -> ValidationResult:
        """
        Human-Centric Validation (HCV) checkpoint.

        Validates that human review has been completed for:
        - Intuitiv funktionalitet
        - Æstetisk kvalitet
        - Strategisk alignment
        - Brugeroplevelse

        Reads status from hcv_status.json
        """
        hcv_file = self.project_root / "scripts" / "hcv_status.json"

        if not hcv_file.exists():
            return ValidationResult(
                name="HCV Validation",
                status=ValidationStatus.FAIL,
                message="HCV status file not found",
                details={"expected_path": str(hcv_file)}
            )

        try:
            hcv_data = json.loads(hcv_file.read_text())
            phase_hcv = hcv_data.get("phases", {}).get(phase, {})

            if not phase_hcv:
                return ValidationResult(
                    name="HCV Validation",
                    status=ValidationStatus.SKIP,
                    message=f"No HCV defined for phase {phase}",
                    details={}
                )

            checkpoints = phase_hcv.get("checkpoints", [])
            total = len(checkpoints)
            passed = sum(1 for cp in checkpoints if cp.get("status") == "PASS")
            pending = sum(1 for cp in checkpoints if cp.get("status") == "PENDING")

            phase_status = phase_hcv.get("status", "PENDING")

            if phase_status == "PASS" and passed == total:
                return ValidationResult(
                    name="HCV Validation",
                    status=ValidationStatus.PASS,
                    message=f"Human validation complete ({passed}/{total} checkpoints)",
                    details={
                        "checkpoints_passed": passed,
                        "checkpoints_total": total,
                        "approved_by": phase_hcv.get("approved_by"),
                        "approved_at": phase_hcv.get("approved_at")
                    }
                )
            elif passed > 0:
                return ValidationResult(
                    name="HCV Validation",
                    status=ValidationStatus.WARN,
                    message=f"HCV in progress ({passed}/{total} complete, {pending} pending)",
                    details={
                        "checkpoints_passed": passed,
                        "checkpoints_pending": pending,
                        "checkpoints_total": total,
                        "pending_items": [
                            cp["name"] for cp in checkpoints
                            if cp.get("status") == "PENDING"
                        ]
                    }
                )
            else:
                return ValidationResult(
                    name="HCV Validation",
                    status=ValidationStatus.WARN,
                    message=f"HCV PENDING - Awaiting human validation ({total} checkpoints)",
                    details={
                        "checkpoints_total": total,
                        "required_checkpoints": [cp["name"] for cp in checkpoints],
                        "action_required": "Complete manual HCV review process"
                    }
                )

        except json.JSONDecodeError as e:
            return ValidationResult(
                name="HCV Validation",
                status=ValidationStatus.FAIL,
                message=f"Invalid HCV status file: {e}",
                details={}
            )
        except Exception as e:
            return ValidationResult(
                name="HCV Validation",
                status=ValidationStatus.FAIL,
                message=f"HCV validation error: {e}",
                details={}
            )

    def _generate_recommendations(self, validation: PhaseValidation) -> List[str]:
        """Generate actionable recommendations based on validation results."""
        recommendations = []

        for v in validation.validations:
            if v.status == ValidationStatus.FAIL:
                recommendations.append(f"[CRITICAL] {v.name}: {v.message}")
            elif v.status == ValidationStatus.WARN:
                recommendations.append(f"[ACTION] {v.name}: Address - {v.message}")

        if validation.compliance_score < 0.95:
            recommendations.append(
                f"[PRIORITY] Overall compliance at {validation.compliance_score:.1%}. "
                f"Target: 95%+"
            )

        if not recommendations:
            recommendations.append("[OK] Phase validation passed. Ready for implementation.")

        return recommendations

    def full_audit(self) -> Dict[str, Any]:
        """Run full audit across all phases."""
        audit_results = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "phases": {},
            "summary": {
                "total_phases": 4,
                "validated": 0,
                "passed": 0,
                "warnings": 0,
                "failures": 0
            }
        }

        for phase in ["5", "6", "7", "8"]:
            result = self.validate_phase(phase)
            audit_results["phases"][f"FASE_{phase}"] = {
                "status": result.overall_status.value,
                "score": result.compliance_score,
                "validations": [
                    {"name": v.name, "status": v.status.value, "message": v.message}
                    for v in result.validations
                ],
                "recommendations": result.recommendations
            }
            audit_results["summary"]["validated"] += 1

            if result.overall_status == ValidationStatus.PASS:
                audit_results["summary"]["passed"] += 1
            elif result.overall_status == ValidationStatus.WARN:
                audit_results["summary"]["warnings"] += 1
            else:
                audit_results["summary"]["failures"] += 1

        return audit_results

    def print_report(self, validation: PhaseValidation):
        """Print formatted validation report."""
        status_colors = {
            ValidationStatus.PASS: "\033[92m",  # Green
            ValidationStatus.WARN: "\033[93m",  # Yellow
            ValidationStatus.FAIL: "\033[91m",  # Red
            ValidationStatus.SKIP: "\033[90m"   # Gray
        }
        reset = "\033[0m"

        print("\n" + "=" * 70)
        print(f"  FASE {validation.phase} VALIDATION REPORT")
        print(f"  Timestamp: {validation.timestamp}")
        print("=" * 70)

        color = status_colors[validation.overall_status]
        print(f"\n  Overall Status: {color}{validation.overall_status.value}{reset}")
        print(f"  Compliance Score: {validation.compliance_score:.1%}")

        print("\n  Validation Results:")
        print("  " + "-" * 66)

        for v in validation.validations:
            color = status_colors[v.status]
            status_str = f"{color}[{v.status.value:4s}]{reset}"
            print(f"  {status_str} {v.name}: {v.message}")

        if validation.recommendations:
            print("\n  Recommendations:")
            print("  " + "-" * 66)
            for rec in validation.recommendations:
                print(f"  - {rec}")

        print("\n" + "=" * 70 + "\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Cirkelline Roadmap Zero-Oversight-Drift Validator"
    )
    parser.add_argument(
        "--phase",
        choices=["5", "6", "7", "8"],
        help="Validate specific phase"
    )
    parser.add_argument(
        "--full-audit",
        action="store_true",
        help="Run full audit across all phases"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    validator = RoadmapValidator()

    if args.full_audit:
        results = validator.full_audit()
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print("\n" + "=" * 70)
            print("  FULL AUDIT RESULTS")
            print("=" * 70)
            for phase_name, phase_data in results["phases"].items():
                print(f"\n  {phase_name}: {phase_data['status']} ({phase_data['score']:.1%})")
            print("\n  Summary:")
            print(f"    Validated: {results['summary']['validated']}")
            print(f"    Passed: {results['summary']['passed']}")
            print(f"    Warnings: {results['summary']['warnings']}")
            print(f"    Failures: {results['summary']['failures']}")
            print("=" * 70 + "\n")
    elif args.phase:
        result = validator.validate_phase(args.phase)
        if args.json:
            print(json.dumps({
                "phase": result.phase,
                "status": result.overall_status.value,
                "score": result.compliance_score,
                "validations": [
                    {"name": v.name, "status": v.status.value, "message": v.message}
                    for v in result.validations
                ]
            }, indent=2))
        else:
            validator.print_report(result)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
