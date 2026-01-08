#!/usr/bin/env python3
"""
FASE 5: Complete HCV Test Suite Runner
======================================

Kører alle Human-Centric Validation tests for FASE 5
og genererer en samlet rapport.

Brug:
    python cirkelline/headquarters/learning_rooms/hcv_fase5/run_all_hcv_tests.py

Output:
    - Individuelle test-resultater
    - Samlet HCV status
    - Evalueringsguide til manuel gennemgang
"""

import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def print_banner():
    """Print the main banner."""
    print("\n" + "=" * 80)
    print("  " + "=" * 76)
    print("  ||" + " " * 72 + "||")
    print("  ||" + "  CIRKELLINE FASE 5: HUMAN-CENTRIC VALIDATION SUITE".center(72) + "||")
    print("  ||" + "  Zero-Oversight-Drift Protocol".center(72) + "||")
    print("  ||" + " " * 72 + "||")
    print("  " + "=" * 76)
    print("=" * 80)
    print(f"\n  Timestamp: {datetime.utcnow().isoformat()}Z")
    print(f"  Læringsrum: cirkelline/headquarters/learning_rooms/hcv_fase5/")
    print("=" * 80)


async def run_hcv_5_1():
    """Run HCV-5.1: Scanner Test"""
    print("\n\n" + "=" * 80)
    print("  CHECKPOINT: HCV-5.1 - Web3 Scanner Intuitivitet")
    print("=" * 80)

    try:
        from cirkelline.headquarters.learning_rooms.hcv_fase5.hcv_5_1_scanner_test import run_all_tests
        return await run_all_tests()
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


async def run_hcv_5_2():
    """Run HCV-5.2: Analysis Test"""
    print("\n\n" + "=" * 80)
    print("  CHECKPOINT: HCV-5.2 - Analysis Output Kvalitet")
    print("=" * 80)

    try:
        from cirkelline.headquarters.learning_rooms.hcv_fase5.hcv_5_2_analysis_test import run_all_tests
        return await run_all_tests()
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


async def run_hcv_5_3():
    """Run HCV-5.3: Governance Test"""
    print("\n\n" + "=" * 80)
    print("  CHECKPOINT: HCV-5.3 - Governance Insights")
    print("=" * 80)

    try:
        from cirkelline.headquarters.learning_rooms.hcv_fase5.hcv_5_3_governance_test import run_all_tests
        return await run_all_tests()
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


async def run_hcv_5_4():
    """Run HCV-5.4: Social Test"""
    print("\n\n" + "=" * 80)
    print("  CHECKPOINT: HCV-5.4 - Social Integration UX")
    print("=" * 80)

    try:
        from cirkelline.headquarters.learning_rooms.hcv_fase5.hcv_5_4_social_test import run_all_tests
        return await run_all_tests()
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


async def run_hcv_5_5():
    """Run HCV-5.5: LLM Fallback Test"""
    print("\n\n" + "=" * 80)
    print("  CHECKPOINT: HCV-5.5 - Local LLM Fallback")
    print("=" * 80)

    try:
        from cirkelline.headquarters.learning_rooms.hcv_fase5.hcv_5_5_llm_test import run_all_tests
        return await run_all_tests()
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def print_final_report(results: dict):
    """Print final HCV report."""
    print("\n\n" + "=" * 80)
    print("  " + "=" * 76)
    print("  ||" + " " * 72 + "||")
    print("  ||" + "  FASE 5 HCV SAMLET RAPPORT".center(72) + "||")
    print("  ||" + " " * 72 + "||")
    print("  " + "=" * 76)
    print("=" * 80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\n  CHECKPOINT STATUS:")
    print("  " + "-" * 76)

    for checkpoint, status in results.items():
        icon = "✓" if status else "✗"
        status_text = "READY FOR REVIEW" if status else "NEEDS ATTENTION"
        print(f"  {icon} {checkpoint}: {status_text}")

    print("  " + "-" * 76)
    print(f"\n  TOTAL: {passed}/{total} checkpoints ready")
    print(f"  TECHNICAL STATUS: {'ALL TESTS PASSED' if passed == total else 'SOME TESTS NEED ATTENTION'}")

    print("\n" + "=" * 80)
    print("  NÆSTE SKRIDT: MANUEL HCV EVALUERING")
    print("=" * 80)
    print("""
  For at fuldføre HCV og opnå 100% FASE 5 compliance:

  1. Gennemgå hver checkpoint manuelt:
     - Kør de individuelle test-scripts
     - Evaluer output for intuitivitet og brugervenlighed
     - Notér feedback og forbedringsforslag

  2. Opdater hcv_status.json med godkendelser:
     - Sæt checkpoint status til "PASS"
     - Tilføj validated_by og validated_at
     - Inkluder feedback

  3. Kør roadmap_validator.py igen:
     python scripts/roadmap_validator.py --phase 5

  4. Bekræft 100% PASS før FASE 6 initiering

  EVALUERINGSGUIDE:
  -----------------
  [ ] HCV-5.1: Er scanner-output let at forstå?
  [ ] HCV-5.2: Er analyse-rapporter actionable?
  [ ] HCV-5.3: Er governance-insights strategisk værdifulde?
  [ ] HCV-5.4: Er OAuth-flow intuitivt?
  [ ] HCV-5.5: Er offline-oplevelsen acceptabel?
""")
    print("=" * 80)


async def main():
    """Main entry point."""
    print_banner()

    results = {
        "HCV-5.1 Scanner": await run_hcv_5_1(),
        "HCV-5.2 Analysis": await run_hcv_5_2(),
        "HCV-5.3 Governance": await run_hcv_5_3(),
        "HCV-5.4 Social": await run_hcv_5_4(),
        "HCV-5.5 LLM Fallback": await run_hcv_5_5(),
    }

    print_final_report(results)

    # Return success if all passed
    return all(results.values())


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
