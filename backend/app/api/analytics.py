"""
Phase 4: Analytics API Endpoints

REST endpoints for interactions, events, and analytics.
"""

import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from ..analytics.service import get_phase4_service, Phase4Service
from ..analytics.models import (
    CustomerProfileResponse, EventResponse, AnalyticsResponse,
    AddShelfZoneRequest, ZoneMetrics, StoreMetrics
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/phase4", tags=["analytics"])


# ============================================================================
# MODELS
# ============================================================================

class InteractionEventResponse(BaseModel):
    """Interaction event"""
    event_id: str
    event_type: str
    track_id: int
    zone_id: str
    timestamp: str
    duration: float


class AnomalyEventResponse(BaseModel):
    """Anomaly event"""
    anomaly_id: str
    track_id: int
    anomaly_type: str
    confidence: float
    timestamp: str
    description: str


class DwellMetricsResponse(BaseModel):
    """Dwell metrics"""
    zone_id: str
    total_time: float
    visit_count: int
    avg_time: float
    min_time: float
    max_time: float


class CustomerSegmentResponse(BaseModel):
    """Customer segments"""
    browsers: List[int]
    comparers: List[int]
    purchasers: List[int]
    suspicious: List[int]


class MovementPatternResponse(BaseModel):
    """Movement patterns"""
    zone_transitions: dict
    total_patterns: int


class CrowdAnalysisResponse(BaseModel):
    """Crowd analysis"""
    zone_id: str
    peak_hour: int
    avg_crowd: int
    max_crowd: int


# ============================================================================
# ENDPOINTS - Interactions
# ============================================================================

@router.get("/interactions")
async def get_interactions(
    track_id: Optional[int] = Query(None),
    zone_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: Phase4Service = Depends(get_phase4_service)
) -> List[InteractionEventResponse]:
    """Get recent interactions"""

    if track_id:
        interactions = service.interaction_detector.interaction_history
        interactions = [i for i in interactions if i.track_id == track_id]
    elif zone_id:
        interactions = service.interaction_detector.interaction_history
        interactions = [i for i in interactions if i.zone_id == zone_id]
    else:
        interactions = service.interaction_detector.interaction_history

    # Return recent
    interactions = interactions[-limit:]

    return [
        InteractionEventResponse(
            event_id=i.interaction_id,
            event_type=i.interaction_type.value,
            track_id=i.track_id,
            zone_id=i.zone_id,
            timestamp=i.timestamp.isoformat(),
            duration=i.duration_seconds
        )
        for i in interactions
    ]


@router.get("/interactions/{track_id}")
async def get_track_interactions(
    track_id: int,
    service: Phase4Service = Depends(get_phase4_service)
):
    """Get interactions for a specific track"""

    profile = service.interaction_detector.get_profile(track_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Track not found")

    return {
        'track_id': track_id,
        'total_interactions': len(profile.interactions),
        'zones_visited': list(profile.total_zones_visited),
        'duration_in_store': profile.duration_in_store,
        'behavior': profile.behavior_classification.value,
        'interactions': [
            {
                'type': i.interaction_type.value,
                'zone_id': i.zone_id,
                'timestamp': i.timestamp.isoformat(),
                'duration': i.duration_seconds
            }
            for i in profile.interactions[-20:]
        ]
    }


# ============================================================================
# ENDPOINTS - Events
# ============================================================================

@router.get("/events")
async def get_events(
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: Phase4Service = Depends(get_phase4_service)
) -> List[EventResponse]:
    """Get recent events"""

    events = service.event_intelligence.event_history

    if event_type:
        events = [e for e in events if e.event_type == event_type]

    if severity:
        events = [e for e in events if e.severity.value == severity]

    events = events[-limit:]

    return [
        EventResponse(
            event_id=e.event_id,
            event_type=e.event_type,
            timestamp=e.timestamp.isoformat(),
            severity=e.severity.value,
            message=e.message
        )
        for e in events
    ]


@router.get("/anomalies")
async def get_anomalies(
    track_id: Optional[int] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: Phase4Service = Depends(get_phase4_service)
) -> List[AnomalyEventResponse]:
    """Get detected anomalies"""

    anomalies = service.event_intelligence.anomaly_history

    if track_id:
        anomalies = [a for a in anomalies if a.track_id == track_id]

    anomalies = anomalies[-limit:]

    return [
        AnomalyEventResponse(
            anomaly_id=a.anomaly_id,
            track_id=a.track_id,
            anomaly_type=a.anomaly_type,
            confidence=a.confidence,
            timestamp=a.timestamp.isoformat(),
            description=a.description
        )
        for a in anomalies
    ]


# ============================================================================
# ENDPOINTS - Analytics
# ============================================================================

@router.get("/analytics")
async def get_analytics(
    service: Phase4Service = Depends(get_phase4_service)
) -> AnalyticsResponse:
    """Get analytics snapshot"""

    analytics = service.get_analytics()

    return AnalyticsResponse(
        timestamp=datetime.now().isoformat(),
        total_customers=len(service.interaction_detector.customer_profiles),
        total_interactions=len(service.interaction_detector.interaction_history),
        zone_metrics=analytics.get('store_metrics', {}).get('zone_metrics', {}),
        anomalies=service.event_intelligence.anomaly_history[-10:]
    )


@router.get("/analytics/zones")
async def get_zone_analytics(
    service: Phase4Service = Depends(get_phase4_service)
):
    """Get zone-specific analytics"""

    zones = {}
    for zone_id in service.interaction_detector.zone_sessions.keys():
        metrics = service.metrics_engine.compute_zone_metrics(zone_id)
        if metrics:
            zones[zone_id] = metrics.dict()

    return {
        'timestamp': datetime.now().isoformat(),
        'zones': zones
    }


@router.get("/analytics/zones/{zone_id}")
async def get_zone_detail(
    zone_id: str,
    service: Phase4Service = Depends(get_phase4_service)
):
    """Get detailed analytics for a zone"""

    metrics = service.metrics_engine.compute_zone_metrics(zone_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Zone not found")

    dwell_metrics = service.dwell_analytics.get_zone_dwell_metrics(zone_id)
    heatmap = service.metrics_engine.get_interaction_heatmap(zone_id)

    return {
        'zone_id': zone_id,
        'metrics': metrics.dict(),
        'dwell_metrics': dwell_metrics,
        'heatmap': heatmap
    }


@router.get("/analytics/customers/{track_id}")
async def get_customer_analytics(
    track_id: int,
    service: Phase4Service = Depends(get_phase4_service)
):
    """Get customer-specific analytics"""

    profile = service.interaction_detector.get_profile(track_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Customer not found")

    clv = service.metrics_engine.get_customer_lifetime_value(track_id)
    journey = service.metrics_engine.get_customer_journey(track_id)

    return {
        'customer_profile': profile.to_dict(),
        'customer_lifetime_value': clv,
        'journey': journey
    }


@router.get("/analytics/segments")
async def get_customer_segments(
    service: Phase4Service = Depends(get_phase4_service)
) -> CustomerSegmentResponse:
    """Get customer segmentation"""

    segments = service.metrics_engine.get_customer_segments()

    return CustomerSegmentResponse(
        browsers=segments.get('browsers', []),
        comparers=segments.get('comparers', []),
        purchasers=segments.get('purchasers', []),
        suspicious=segments.get('suspicious', [])
    )


@router.get("/analytics/patterns")
async def get_movement_patterns(
    service: Phase4Service = Depends(get_phase4_service)
) -> MovementPatternResponse:
    """Get customer movement patterns"""

    patterns = service.metrics_engine.get_movement_patterns()

    return MovementPatternResponse(
        zone_transitions=patterns.get('zone_transitions', {}),
        total_patterns=patterns.get('total_patterns', 0)
    )


@router.get("/analytics/crowd")
async def get_crowd_analysis(
    service: Phase4Service = Depends(get_phase4_service)
):
    """Get crowd density analysis"""

    crowd_data = service.metrics_engine.get_crowd_analysis()

    return {
        'timestamp': datetime.now().isoformat(),
        'crowd_analysis': crowd_data
    }


@router.get("/analytics/summary")
async def get_analytics_summary(
    service: Phase4Service = Depends(get_phase4_service)
):
    """Get store summary analytics"""

    store_metrics = service.metrics_engine.compute_store_metrics()
    dwell_summary = service.dwell_analytics.get_store_summary()

    return {
        'timestamp': datetime.now().isoformat(),
        'store_metrics': store_metrics.dict(),
        'dwell_summary': dwell_summary,
        'statistics': service.get_statistics()
    }


# ============================================================================
# ENDPOINTS - Dwell Analytics
# ============================================================================

@router.get("/dwell/zones/{zone_id}")
async def get_zone_dwell_metrics(
    zone_id: str,
    service: Phase4Service = Depends(get_phase4_service)
) -> DwellMetricsResponse:
    """Get dwell metrics for a zone"""

    metrics = service.dwell_analytics.get_zone_dwell_metrics(zone_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Zone not found")

    return DwellMetricsResponse(**metrics)


@router.get("/dwell/customers/{track_id}")
async def get_customer_dwell_metrics(
    track_id: int,
    service: Phase4Service = Depends(get_phase4_service)
):
    """Get dwell metrics for a customer"""

    metrics = service.dwell_analytics.get_customer_dwell_metrics(track_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Customer not found")

    return metrics


@router.get("/dwell/top-zones")
async def get_top_dwell_zones(
    limit: int = Query(10, ge=1, le=50),
    service: Phase4Service = Depends(get_phase4_service)
):
    """Get top zones by dwell time"""

    top_zones = service.dwell_analytics.get_top_zones_by_dwell(top_n=limit)

    return {
        'top_zones': [
            {'zone': z, 'avg_dwell_time': t}
            for z, t in top_zones
        ]
    }


# ============================================================================
# ENDPOINTS - Statistics
# ============================================================================

@router.get("/statistics")
async def get_statistics(
    service: Phase4Service = Depends(get_phase4_service)
):
    """Get service statistics"""
    return service.get_statistics()


@router.get("/health")
async def health_check(
    service: Phase4Service = Depends(get_phase4_service)
):
    """Health check"""
    stats = service.get_statistics()
    return {
        'status': 'healthy',
        'active_customers': stats['active_customers'],
        'redis_connected': stats['redis_connected']
    }


# ============================================================================
# ENDPOINTS - Management
# ============================================================================

@router.post("/reset")
async def reset_analytics(
    service: Phase4Service = Depends(get_phase4_service)
):
    """Reset all analytics"""
    service.reset()
    return {'status': 'reset_complete'}


@router.get("/export")
async def export_metrics(
    service: Phase4Service = Depends(get_phase4_service)
):
    """Export all metrics"""
    return service.metrics_engine.export_metrics_snapshot()
