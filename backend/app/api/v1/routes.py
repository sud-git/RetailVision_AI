"""REST API routes for Phase 5 backend platform."""
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional, List

from app.database import get_session
from app.services.business import (
    customer_service, tracking_service, interaction_service,
    dwell_service, alert_service, event_service, analytics_service
)
from app.schemas.models import (
    CustomerResponse, CustomerCreate, CustomerUpdate,
    TrackingSessionResponse, ShelfInteractionResponse,
    DwellTimeRecordResponse, AlertResponse, EventResponse,
    PaginationParams
)


# ==============================================================================
# ANALYTICS ROUTES
# ==============================================================================

analytics_router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@analytics_router.get("/overview")
async def get_overview(session: AsyncSession = Depends(get_session)):
    """Get analytics overview."""
    try:
        overview = await analytics_service.get_overview(session)
        return {
            'success': True,
            'data': overview
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get("/dwell-time/{zone_id}")
async def get_dwell_time_by_zone(
    zone_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get dwell time analytics for zone."""
    try:
        stats = await dwell_service.get_zone_dwell_stats(session, zone_id)
        return {
            'success': True,
            'data': stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get("/zones")
async def get_zones(session: AsyncSession = Depends(get_session)):
    """Get analytics for all zones."""
    try:
        return {
            'success': True,
            'data': {'zones': []}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@analytics_router.get("/interactions")
async def get_interactions(session: AsyncSession = Depends(get_session)):
    """Get interaction analytics."""
    try:
        sessions = await tracking_service.get_active_sessions(session)
        return {
            'success': True,
            'data': {
                'total_active_sessions': len(sessions),
                'sessions': sessions
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# EVENTS ROUTES
# ==============================================================================

events_router = APIRouter(prefix="/api/v1/events", tags=["events"])


@events_router.get("")
async def get_events(
    hours: int = Query(24, ge=1, le=720),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    session: AsyncSession = Depends(get_session)
):
    """Get recent events."""
    try:
        events = await event_service.get_recent_events(session, hours, skip, limit)
        return {
            'success': True,
            'data': events,
            'total': len(events)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@events_router.get("/recent")
async def get_recent_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    session: AsyncSession = Depends(get_session)
):
    """Get most recent events."""
    try:
        events = await event_service.get_recent_events(session, hours=1, skip=skip, limit=limit)
        return {
            'success': True,
            'data': events,
            'total': len(events)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# SYSTEM ROUTES
# ==============================================================================

system_router = APIRouter(prefix="/api/v1/system", tags=["system"])


@system_router.get("/health")
async def health_check(session: AsyncSession = Depends(get_session)):
    """Health check endpoint."""
    try:
        # Test database connection
        await session.execute("SELECT 1")
        db_status = "connected"
    except:
        db_status = "disconnected"
    
    return {
        'status': 'healthy' if db_status == 'connected' else 'degraded',
        'timestamp': datetime.utcnow().isoformat(),
        'database': db_status,
        'services': {
            'api': 'running',
            'database': db_status
        }
    }


@system_router.get("/metrics")
async def get_metrics(session: AsyncSession = Depends(get_session)):
    """Get system metrics."""
    try:
        # Get counts
        customers_count = await customer_service.customer_repo.count(session)
        sessions_count = await tracking_service.session_repo.count(session)
        interactions_count = await interaction_service.interaction_repo.count(session)
        alerts_count = await alert_service.alert_repo.count(session)
        
        return {
            'success': True,
            'data': {
                'total_customers': customers_count,
                'total_sessions': sessions_count,
                'total_interactions': interactions_count,
                'total_alerts': alerts_count,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@system_router.get("/status")
async def get_status():
    """Get service status."""
    return {
        'service_name': 'RetailVision AI Backend',
        'version': '1.0.0',
        'environment': 'production',
        'uptime_seconds': 0,
        'start_time': datetime.utcnow().isoformat(),
        'status': 'healthy'
    }


# ==============================================================================
# CUSTOMERS ROUTES
# ==============================================================================

customers_router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


@customers_router.get("")
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    session: AsyncSession = Depends(get_session)
):
    """List all customers."""
    try:
        customers = await customer_service.customer_repo.get_all(session, skip, limit)
        total = await customer_service.customer_repo.count(session)
        
        return {
            'success': True,
            'data': customers,
            'total': total,
            'skip': skip,
            'limit': limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@customers_router.get("/{customer_id}")
async def get_customer(
    customer_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get customer by ID."""
    try:
        customer = await customer_service.get_customer(session, customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return {
            'success': True,
            'data': customer
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@customers_router.post("")
async def create_customer(
    customer_in: CustomerCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create new customer."""
    try:
        customer = await customer_service.create_customer(session, customer_in)
        
        return {
            'success': True,
            'data': customer,
            'message': 'Customer created successfully'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@customers_router.put("/{customer_id}")
async def update_customer(
    customer_id: str,
    update_in: CustomerUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update customer."""
    try:
        customer = await customer_service.update_customer(session, customer_id, update_in)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        return {
            'success': True,
            'data': customer,
            'message': 'Customer updated successfully'
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# ALERTS ROUTES
# ==============================================================================

alerts_router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@alerts_router.get("")
async def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    session: AsyncSession = Depends(get_session)
):
    """List active alerts."""
    try:
        alerts = await alert_service.get_active_alerts(session, skip, limit)
        total = await alert_service.alert_repo.count(session)
        
        return {
            'success': True,
            'data': alerts,
            'total': total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@alerts_router.get("/critical")
async def get_critical_alerts(
    session: AsyncSession = Depends(get_session)
):
    """Get critical alerts."""
    try:
        alerts = await alert_service.get_critical_alerts(session)
        
        return {
            'success': True,
            'data': alerts,
            'total': len(alerts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
