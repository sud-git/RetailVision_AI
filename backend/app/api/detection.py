"""
Detection API Routes - Phase 3

REST API endpoints for detection and tracking system.
"""

import logging
from typing import Optional, List, Dict

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.detection import (
    get_detection_service, DetectionConfig,
    ObjectClass, EventType, ZoneType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/detection", tags=["detection"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class AddZoneRequest(BaseModel):
    """Add zone request"""
    zone_id: str
    zone_type: str  # "shelf", "checkout", etc.
    name: str
    polygon: List[List[float]]
    metadata: Optional[Dict] = None


class DetectionStatsResponse(BaseModel):
    """Detection statistics"""
    frames_processed: int
    total_detections: int
    active_tracks: int
    events_published: int


class TrackingStatsResponse(BaseModel):
    """Tracking statistics"""
    total_tracks: int
    active_tracks: int
    lost_tracks: int
    max_track_id: int


class ServiceStatusResponse(BaseModel):
    """Service status response"""
    running: bool
    frames_processed: int
    active_tracks: int
    zones: int
    statistics: Dict


# ============================================================================
# ROUTES
# ============================================================================

@router.get("/status", response_model=ServiceStatusResponse)
async def get_detection_status():
    """Get detection service status"""
    service = await get_detection_service()
    
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    stats = service.get_statistics()
    
    return ServiceStatusResponse(
        running=service.is_running,
        frames_processed=stats["frames_processed"],
        active_tracks=stats["active_tracks"],
        zones=stats["zones_count"],
        statistics=stats
    )


@router.get("/statistics")
async def get_detection_statistics():
    """Get detailed detection statistics"""
    service = await get_detection_service()
    
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return service.get_statistics()


@router.get("/zones")
async def list_zones():
    """List all detection zones"""
    service = await get_detection_service()
    
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    zones = service.zone_manager.get_all_zones()
    
    return {
        "zones": [z.to_dict() for z in zones],
        "count": len(zones)
    }


@router.post("/zones", status_code=201)
async def add_zone(request: AddZoneRequest):
    """Add a detection zone"""
    service = await get_detection_service()
    
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        from app.detection import Zone, ZoneType
        
        zone = Zone(
            zone_id=request.zone_id,
            zone_type=ZoneType(request.zone_type),
            name=request.name,
            polygon=request.polygon,
            metadata=request.metadata or {}
        )
        
        service.zone_manager.add_zone(zone)
        
        return {
            "status": "created",
            "zone_id": zone.zone_id,
            "name": zone.name
        }
    
    except Exception as e:
        logger.error(f"Error adding zone: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/zones/{zone_id}")
async def get_zone(zone_id: str):
    """Get specific zone"""
    service = await get_detection_service()
    
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    zone = service.zone_manager.get_zone(zone_id)
    
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    return zone.to_dict()


@router.delete("/zones/{zone_id}")
async def delete_zone(zone_id: str):
    """Delete detection zone"""
    service = await get_detection_service()
    
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    if zone_id not in service.zone_manager.zones:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    del service.zone_manager.zones[zone_id]
    
    return {"status": "deleted", "zone_id": zone_id}


@router.get("/tracks")
async def list_active_tracks():
    """List active tracking objects"""
    service = await get_detection_service()
    
    if not service or not service.tracker:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    tracks = service.tracker.get_active_tracks()
    
    return {
        "tracks": [t.to_dict() for t in tracks],
        "count": len(tracks)
    }


@router.get("/tracks/{track_id}")
async def get_track(track_id: int):
    """Get specific tracking object"""
    service = await get_detection_service()
    
    if not service or not service.tracker:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    track = service.tracker.get_track(track_id)
    
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    return track.to_dict()


@router.get("/metrics")
async def get_detection_metrics():
    """Get detection metrics"""
    service = await get_detection_service()
    
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    stats = service.get_statistics()
    
    return {
        "timestamp": str(__import__('datetime').datetime.now()),
        "metrics": stats
    }


@router.get("/dwell-sessions")
async def get_dwell_sessions():
    """Get active dwell sessions"""
    service = await get_detection_service()
    
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    sessions = service.dwell_tracker.get_active_sessions()
    
    return {
        "sessions": [s.to_dict() for s in sessions],
        "count": len(sessions)
    }


@router.get("/interaction-history/{track_id}")
async def get_interaction_history(track_id: int):
    """Get interaction history for a track"""
    service = await get_detection_service()
    
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    history = service.interaction_detector.get_interaction_history(track_id)
    
    return {
        "track_id": track_id,
        "interactions": history,
        "count": len(history)
    }


@router.post("/reset-statistics")
async def reset_statistics():
    """Reset detection statistics"""
    service = await get_detection_service()
    
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    service.stats = {
        "frames_processed": 0,
        "total_detections": 0,
        "active_tracks": 0,
        "events_published": 0
    }
    
    return {"status": "reset"}


@router.post("/cleanup-dwell")
async def cleanup_dwell_sessions():
    """Cleanup inactive dwell sessions"""
    service = await get_detection_service()
    
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    import time
    service.dwell_tracker.cleanup_inactive(time.time(), timeout_seconds=60)
    
    return {"status": "cleanup_complete"}


# ============================================================================
# HEALTH CHECKS
# ============================================================================

@router.get("/health")
async def detection_health():
    """Detection service health check"""
    service = await get_detection_service()
    
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return {
        "status": "healthy" if service.is_running else "unhealthy",
        "running": service.is_running
    }


@router.get("/ready")
async def detection_ready():
    """Detection service readiness check"""
    service = await get_detection_service()
    
    if not service or not service.is_running:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return {"ready": True}
