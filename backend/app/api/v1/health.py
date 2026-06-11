"""
Health check and system status API endpoints.
Provides endpoints for monitoring system health and diagnostics.
"""

from fastapi import APIRouter, Response
from typing import Dict, Any

from app.services.health import get_health, get_full_diagnostics

router = APIRouter(prefix="/api/v1", tags=["system"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Quick health check endpoint.
    Returns 200 if critical services (DB, Redis, Backend) are healthy.
    
    Returns:
        - overall_healthy: Boolean indicating if all critical services are up
        - database: PostgreSQL status
        - redis: Redis status
        - backend_api: Backend API status
    """
    status = await get_health()
    return status


@router.get("/health/live")
async def liveness_probe() -> Dict[str, str]:
    """
    Liveness probe for Kubernetes/Docker.
    Simple check that backend is running.
    """
    return {"status": "alive", "message": "Backend is running"}


@router.get("/health/ready")
async def readiness_probe() -> Dict[str, Any]:
    """
    Readiness probe for Kubernetes/Docker.
    Checks if all required services are ready to handle requests.
    """
    status = await get_health()
    
    if status["overall_healthy"]:
        return {"status": "ready", "message": "All services ready"}
    else:
        return Response(
            status_code=503,
            content={"status": "not_ready", "message": "Some services are not ready"},
            media_type="application/json"
        )


@router.get("/diagnostics")
async def get_diagnostics() -> Dict[str, Any]:
    """
    Detailed system diagnostics.
    Includes full status, configuration info, and check history.
    
    Use this for troubleshooting deployment issues.
    """
    return await get_full_diagnostics()


@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """
    Current system status summary.
    """
    status = await get_health()
    return {
        "timestamp": status["timestamp"],
        "overall_healthy": status["overall_healthy"],
        "uptime_seconds": status["uptime_seconds"],
        "services": status["services"]
    }


@router.get("/ping")
async def ping() -> Dict[str, str]:
    """
    Simple ping endpoint to verify backend is responding.
    """
    return {"message": "pong"}


# Export router
__all__ = ["router"]
