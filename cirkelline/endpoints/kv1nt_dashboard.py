"""
KV1NT Dashboard API Endpoints
=============================

Exposes KV1NT recommendations and analysis to the Commander Dashboard.

Endpoints:
    GET  /api/kv1nt/recommendations    - Get current recommendations
    GET  /api/kv1nt/analysis           - Get full system analysis
    GET  /api/kv1nt/rules/status       - Get rule engine status
    POST /api/kv1nt/rules/trigger      - Manually trigger rule evaluation
    GET  /api/kv1nt/patterns           - Get detected patterns and predictions
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel

# Add ckc-core to path for imports
CKC_CORE_PATH = Path(__file__).parent.parent.parent / "ecosystems" / "ckc-core"
if str(CKC_CORE_PATH) not in sys.path:
    sys.path.insert(0, str(CKC_CORE_PATH))

try:
    from cirkelline.ckc.kv1nt_recommendations import (
        KV1NTRuleEngine,
        KV1NTRecommendationEngine,
        KV1NTPatternAnalyzer,
        RecommendationPriority,
        RecommendationCategory,
        full_kv1nt_analysis,
    )
    KV1NT_AVAILABLE = True
except ImportError as e:
    KV1NT_AVAILABLE = False
    IMPORT_ERROR = str(e)

from cirkelline.config import logger

router = APIRouter(prefix="/api/kv1nt", tags=["KV1NT Dashboard"])


# Response Models
class RecommendationResponse(BaseModel):
    id: str
    title: str
    description: str
    priority: str
    category: str
    suggested_actions: List[str]
    estimated_effort: str
    auto_fixable: bool
    created_at: str


class RuleStatusResponse(BaseModel):
    total_rules: int
    active_rules: int
    recently_triggered: List[dict]
    next_evaluation: Optional[str]


class PatternResponse(BaseModel):
    patterns: List[dict]
    predictions: List[dict]
    trends: dict


# Singletons for engines (only used when KV1NT is available)
_rule_engine = None
_recommendation_engine = None
_pattern_analyzer = None


def get_rule_engine():
    """Get or create KV1NT Rule Engine singleton."""
    global _rule_engine
    if not KV1NT_AVAILABLE:
        return None
    if _rule_engine is None:
        _rule_engine = KV1NTRuleEngine()
    return _rule_engine


def get_recommendation_engine():
    """Get or create KV1NT Recommendation Engine singleton."""
    global _recommendation_engine
    if not KV1NT_AVAILABLE:
        return None
    if _recommendation_engine is None:
        _recommendation_engine = KV1NTRecommendationEngine()
    return _recommendation_engine


def get_pattern_analyzer():
    """Get or create KV1NT Pattern Analyzer singleton."""
    global _pattern_analyzer
    if not KV1NT_AVAILABLE:
        return None
    if _pattern_analyzer is None:
        _pattern_analyzer = KV1NTPatternAnalyzer()
    return _pattern_analyzer


@router.get("/health")
async def kv1nt_health():
    """Check KV1NT system health."""
    if not KV1NT_AVAILABLE:
        return {
            "status": "unavailable",
            "error": IMPORT_ERROR,
            "message": "KV1NT module not loaded"
        }
    return {
        "status": "healthy",
        "version": "2.0.0",
        "engines": {
            "rule_engine": "ready",
            "recommendation_engine": "ready",
            "pattern_analyzer": "ready"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/recommendations")
async def get_recommendations(
    priority: Optional[str] = Query(None, description="Filter by priority"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get current KV1NT recommendations.

    Returns actionable recommendations for system improvements.
    """
    if not KV1NT_AVAILABLE:
        raise HTTPException(status_code=503, detail="KV1NT not available")

    try:
        engine = get_recommendation_engine()
        recommendations = engine.generate_recommendations()

        # Filter by priority if specified
        if priority:
            try:
                p = RecommendationPriority(priority.lower())
                recommendations = [r for r in recommendations if r.priority == p]
            except ValueError:
                pass

        # Filter by category if specified
        if category:
            try:
                c = RecommendationCategory(category.lower())
                recommendations = [r for r in recommendations if r.category == c]
            except ValueError:
                pass

        # Apply limit
        recommendations = recommendations[:limit]

        return {
            "count": len(recommendations),
            "recommendations": [
                {
                    "id": r.id,
                    "title": r.title,
                    "description": r.description,
                    "priority": r.priority.value,
                    "category": r.category.value,
                    "suggested_actions": r.suggested_actions,
                    "estimated_effort": r.estimated_effort,
                    "auto_fixable": r.auto_fixable,
                    "created_at": r.created_at.isoformat()
                }
                for r in recommendations
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"KV1NT recommendations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis")
async def get_full_analysis():
    """
    Get full KV1NT system analysis.

    Returns comprehensive markdown report with:
    - System status
    - Recommendations
    - Patterns
    - Predictions
    """
    if not KV1NT_AVAILABLE:
        raise HTTPException(status_code=503, detail="KV1NT not available")

    try:
        analysis = full_kv1nt_analysis()
        return {
            "report": analysis,
            "format": "markdown",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"KV1NT analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/status")
async def get_rules_status():
    """
    Get KV1NT Rule Engine status.

    Shows active rules and recent triggers.
    """
    if not KV1NT_AVAILABLE:
        raise HTTPException(status_code=503, detail="KV1NT not available")

    try:
        engine = get_rule_engine()

        return {
            "total_rules": len(engine.rules),
            "rules": [
                {
                    "id": r.id,
                    "name": r.name,
                    "type": r.rule_type.value,
                    "priority": r.priority.value,
                    "last_triggered": r.last_triggered.isoformat() if r.last_triggered else None,
                    "trigger_count": r.trigger_count,
                    "enabled": r.enabled
                }
                for r in engine.rules
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"KV1NT rules status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/trigger")
async def trigger_rule_evaluation():
    """
    Manually trigger KV1NT rule evaluation.

    Evaluates all rules and returns triggered recommendations.
    """
    if not KV1NT_AVAILABLE:
        raise HTTPException(status_code=503, detail="KV1NT not available")

    try:
        engine = get_rule_engine()
        triggered = engine.evaluate_all()

        return {
            "evaluated": len(engine.rules),
            "triggered": len(triggered),
            "recommendations": [
                {
                    "rule_id": r["rule"].id,
                    "rule_name": r["rule"].name,
                    "recommendation": r["recommendation"].title
                }
                for r in triggered
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"KV1NT rule trigger error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns")
async def get_patterns():
    """
    Get detected patterns and predictions.

    Analyzes historical data for trends and anomalies.
    """
    if not KV1NT_AVAILABLE:
        raise HTTPException(status_code=503, detail="KV1NT not available")

    try:
        analyzer = get_pattern_analyzer()
        analysis = analyzer.get_full_analysis()

        return {
            "trends": analysis.get("trends", {}),
            "patterns": analysis.get("patterns", []),
            "predictions": analysis.get("predictions", []),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"KV1NT patterns error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard_data():
    """
    Get aggregated data for Commander Dashboard.

    Combines recommendations, patterns, and status in one call.
    """
    if not KV1NT_AVAILABLE:
        return {
            "status": "unavailable",
            "message": "KV1NT not loaded",
            "timestamp": datetime.utcnow().isoformat()
        }

    try:
        rec_engine = get_recommendation_engine()
        rule_engine = get_rule_engine()

        recommendations = rec_engine.generate_recommendations()

        # Count by priority
        priority_counts = {
            "critical": sum(1 for r in recommendations if r.priority == RecommendationPriority.CRITICAL),
            "high": sum(1 for r in recommendations if r.priority == RecommendationPriority.HIGH),
            "medium": sum(1 for r in recommendations if r.priority == RecommendationPriority.MEDIUM),
            "low": sum(1 for r in recommendations if r.priority == RecommendationPriority.LOW),
        }

        # Get top 5 recommendations
        top_recommendations = [
            {
                "id": r.id,
                "title": r.title,
                "priority": r.priority.value,
                "category": r.category.value,
                "auto_fixable": r.auto_fixable
            }
            for r in recommendations[:5]
        ]

        return {
            "status": "operational",
            "summary": {
                "total_recommendations": len(recommendations),
                "priority_counts": priority_counts,
                "total_rules": len(rule_engine.rules),
                "active_rules": sum(1 for r in rule_engine.rules if r.enabled)
            },
            "top_recommendations": top_recommendations,
            "last_analysis": datetime.utcnow().isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"KV1NT dashboard error: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


logger.info("KV1NT Dashboard endpoints loaded")
