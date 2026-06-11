"""
Phase 8: Anomaly Detection & Alert API Endpoints

API endpoints for:
- Anomaly detection and retrieval
- Alert management
- Risk scoring
- Statistics and reporting
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_session
from app.security.middleware import validate_api_key
from app.services.anomaly import (
    AnomalyDetectionService, AlertService, RiskManagementService
)

router = APIRouter(prefix="/api/v1/anomalies", tags=["anomalies"])

# ==================== REQUEST/RESPONSE SCHEMAS ====================

class AnomalyResponse(BaseModel):
    """Anomaly data response"""
    id: str
    type: str
    severity: str
    customer_id: Optional[str] = None
    zone_id: int
    title: str
    description: str
    confidence: float
    detected_at: str

class AlertResponse(BaseModel):
    """Alert data response"""
    id: str
    anomaly_id: Optional[str] = None
    type: str
    priority: int
    risk_score: float
    confidence: float
    title: str
    description: str
    customer_id: Optional[str] = None
    zone_id: Optional[int] = None
    channels: List[str]
    created_at: str

class RiskScoreResponse(BaseModel):
    """Risk score response"""
    entity_id: str
    entity_type: str
    risk_score: float
    risk_level: str
    alert_severity: str
    confidence: float
    active_anomalies: int
    recent_incidents: int

class AlertStatisticsResponse(BaseModel):
    """Alert statistics response"""
    total: int
    by_type: dict
    by_priority: dict
    acknowledged: int
    resolved: int

class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    data: dict = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseModel):
    """Generic error response"""
    success: bool = False
    error: str
    details: Optional[str] = None

# ==================== ANOMALY ENDPOINTS ====================

@router.get("/active")
async def get_active_anomalies(
    zone_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> dict:
    """Get currently active anomalies"""
    try:
        service = AnomalyDetectionService(session)
        anomalies = await service.get_active_anomalies(zone_id)
        
        return {
            "success": True,
            "data": {
                "count": len(anomalies),
                "anomalies": anomalies
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/history")
async def get_anomaly_history(
    start_date: str = Query(..., description="Start date YYYY-MM-DD"),
    end_date: str = Query(..., description="End date YYYY-MM-DD"),
    anomaly_type: Optional[str] = Query(None),
    zone_id: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> dict:
    """Get anomaly history for period"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        
        service = AnomalyDetectionService(session)
        anomalies = await service.get_anomaly_history(
            start, end, anomaly_type, zone_id
        )
        
        return {
            "success": True,
            "data": {
                "count": len(anomalies),
                "anomalies": anomalies
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/detect")
async def trigger_anomaly_detection(
    data: dict,
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> dict:
    """Trigger anomaly detection on input data"""
    try:
        service = AnomalyDetectionService(session)
        
        # Initialize zone profiles on first run
        await service.initialize_zone_profiles()
        
        # Run detection
        detected = await service.detect_anomalies(data)
        
        return {
            "success": True,
            "data": {
                "count": len(detected),
                "anomalies": [
                    {
                        "id": a.id,
                        "type": a.anomaly_type,
                        "severity": a.severity.value
                    }
                    for a in detected
                ]
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ==================== ALERT ENDPOINTS ====================

@router.get("/alerts/active")
async def get_active_alerts(
    zone_id: Optional[int] = Query(None),
    alert_type: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> dict:
    """Get active alerts"""
    try:
        service = AlertService(session)
        alerts = await service.get_active_alerts(zone_id, alert_type)
        
        return {
            "success": True,
            "data": {
                "count": len(alerts),
                "alerts": alerts
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/alerts/history")
async def get_alert_history(
    start_date: str = Query(...),
    end_date: str = Query(...),
    zone_id: Optional[int] = Query(None),
    alert_type: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> dict:
    """Get alert history"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        
        service = AlertService(session)
        alerts = await service.get_alert_history(start, end, zone_id, alert_type)
        
        return {
            "success": True,
            "data": {
                "count": len(alerts),
                "alerts": alerts
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    acknowledged_by: str = Query(...),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> dict:
    """Acknowledge alert"""
    try:
        service = AlertService(session)
        success = await service.acknowledge_alert(alert_id, acknowledged_by)
        
        if success:
            return {
                "success": True,
                "data": {"alert_id": alert_id, "status": "acknowledged"}
            }
        else:
            return {
                "success": False,
                "error": "Alert not found"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> dict:
    """Resolve alert"""
    try:
        service = AlertService(session)
        success = await service.resolve_alert(alert_id)
        
        if success:
            return {
                "success": True,
                "data": {"alert_id": alert_id, "status": "resolved"}
            }
        else:
            return {
                "success": False,
                "error": "Alert not found"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/alerts/statistics")
async def get_alert_statistics(
    start_date: str = Query(...),
    end_date: str = Query(...),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> dict:
    """Get alert statistics"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        
        service = AlertService(session)
        stats = await service.get_alert_statistics(start, end)
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ==================== RISK SCORING ENDPOINTS ====================

@router.get("/risk/customer/{customer_id}")
async def get_customer_risk(
    customer_id: str,
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> dict:
    """Get customer risk score"""
    try:
        service = RiskManagementService(session)
        risk = await service.calculate_customer_risk(
            customer_id,
            active_anomalies=0,
            anomaly_types=[]
        )
        
        return {
            "success": True,
            "data": risk
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/risk/zone/{zone_id}")
async def get_zone_risk(
    zone_id: int,
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> dict:
    """Get zone risk score"""
    try:
        service = RiskManagementService(session)
        risk = await service.calculate_zone_risk(zone_id)
        
        return {
            "success": True,
            "data": risk
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/risk/high-risk-customers")
async def get_high_risk_customers(
    threshold: float = Query(0.7),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> dict:
    """Get customers with high risk scores"""
    try:
        service = RiskManagementService(session)
        customers = await service.get_high_risk_customers(threshold)
        
        return {
            "success": True,
            "data": {
                "count": len(customers),
                "customers": customers
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/risk/high-risk-zones")
async def get_high_risk_zones(
    threshold: float = Query(0.7),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> dict:
    """Get zones with high risk scores"""
    try:
        service = RiskManagementService(session)
        zones = await service.get_high_risk_zones(threshold)
        
        return {
            "success": True,
            "data": {
                "count": len(zones),
                "zones": zones
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ==================== HEALTH CHECK ====================

@router.get("/health")
async def anomaly_detection_health():
    """Health check for anomaly detection system"""
    return {
        "status": "healthy",
        "service": "anomaly_detection",
        "version": "8.0.0",
        "components": {
            "loitering_detector": "active",
            "crowd_detector": "active",
            "suspicious_behavior_detector": "active",
            "abandoned_object_detector": "active",
            "risk_scoring": "active",
            "alert_system": "active"
        }
    }
