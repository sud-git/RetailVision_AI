"""
Phase 8: Anomaly Detection & Alert Response Schemas

Pydantic models for API request/response validation
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ==================== ANOMALY SCHEMAS ====================

class HotspotPoint(BaseModel):
    """Hotspot location"""
    x: float
    y: float
    intensity: float


class AnomalyDetailsResponse(BaseModel):
    """Detailed anomaly response"""
    id: str
    anomaly_type: str
    severity: str
    status: str
    customer_id: Optional[str] = None
    zone_id: int
    title: str
    description: str
    confidence_score: float
    details: Dict[str, Any] = {}
    detected_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None


class AnomalyListResponse(BaseModel):
    """List of anomalies"""
    id: str
    anomaly_type: str
    severity: str
    customer_id: Optional[str] = None
    zone_id: int
    title: str
    confidence_score: float
    detected_at: datetime


class AnomalyStatisticsResponse(BaseModel):
    """Anomaly statistics"""
    total_detected: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    by_status: Dict[str, int]
    average_confidence: float
    resolution_rate: float  # percentage resolved


# ==================== ALERT SCHEMAS ====================

class AlertDetailsResponse(BaseModel):
    """Detailed alert response"""
    id: str
    anomaly_id: Optional[str] = None
    alert_type: str
    alert_source: str
    priority: int
    risk_score: float
    confidence: float
    title: str
    description: str
    customer_id: Optional[str] = None
    zone_id: Optional[int] = None
    notification_channels: List[str]
    status: str
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AlertListResponse(BaseModel):
    """List of alerts"""
    id: str
    alert_type: str
    priority: int
    risk_score: float
    title: str
    status: str
    zone_id: Optional[int] = None
    created_at: datetime


class AlertCreateRequest(BaseModel):
    """Create alert request"""
    anomaly_id: Optional[str] = None
    alert_type: str
    title: str
    description: str
    customer_id: Optional[str] = None
    zone_id: Optional[int] = None
    priority: int


class AcknowledgeAlertRequest(BaseModel):
    """Acknowledge alert request"""
    acknowledged_by: str
    notes: Optional[str] = None


class AlertStatisticsResponse(BaseModel):
    """Alert statistics"""
    total_alerts: int
    active_count: int
    acknowledged_count: int
    resolved_count: int
    by_type: Dict[str, int]
    by_priority: Dict[str, int]
    avg_response_time: float  # seconds


# ==================== RISK SCORE SCHEMAS ====================

class RiskFactorsResponse(BaseModel):
    """Risk calculation factors"""
    anomaly_factor: float
    behavior_history_factor: float
    zone_risk_factor: float
    frequency_factor: float
    time_factor: float


class RiskScoreResponse(BaseModel):
    """Risk score response"""
    entity_id: str
    entity_type: str
    risk_score: float
    risk_level: str  # low, medium, high, critical
    alert_severity: str  # info, warning, high, critical
    confidence: float
    risk_factors: RiskFactorsResponse
    active_anomaly_count: int
    recent_incidents: int
    timestamp: datetime


class CustomerRiskResponse(BaseModel):
    """Customer risk response"""
    customer_id: str
    risk_score: float
    risk_level: str
    alert_severity: str
    confidence: float
    active_anomalies: int
    recent_incidents: int
    anomaly_types: List[str] = []


class ZoneRiskResponse(BaseModel):
    """Zone risk response"""
    zone_id: int
    risk_score: float
    risk_level: str
    alert_severity: str
    confidence: float
    active_anomalies: int
    occupancy_factor: Optional[float] = None
    anomaly_density: Optional[float] = None


# ==================== ZONE PROFILE SCHEMAS ====================

class ZoneRiskProfileResponse(BaseModel):
    """Zone risk profile"""
    id: str
    zone_id: int
    zone_type: str
    is_restricted: bool
    max_occupancy: int
    normal_occupancy: int
    loitering_threshold: int
    interaction_threshold: int
    anomalies_enabled: bool


# ==================== DETECTION DATA SCHEMAS ====================

class CustomerSnapshotRequest(BaseModel):
    """Customer data for anomaly detection"""
    customer_id: str
    zone_id: int
    x: float
    y: float
    dwell_time: int  # milliseconds
    interaction_count: int
    zones_visited: List[int] = []


class ZoneOccupancyRequest(BaseModel):
    """Zone occupancy for crowd detection"""
    zone_id: int
    occupancy: int


class AnomalyDetectionRequest(BaseModel):
    """Request for anomaly detection"""
    customers: List[CustomerSnapshotRequest] = []
    zone_occupancies: Dict[int, int] = {}
    interaction_history: Dict[str, List[Dict[str, Any]]] = {}
    objects: List[Dict[str, Any]] = []


# ==================== RESPONSE WRAPPERS ====================

class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    data: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Generic error response"""
    success: bool = False
    error: str
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel):
    """Paginated list response"""
    success: bool = True
    data: List[Dict[str, Any]] = []
    total: int
    page: int
    page_size: int
    total_pages: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ==================== ALERT ACKNOWLEDGMENT SCHEMAS ====================

class AlertAcknowledgmentResponse(BaseModel):
    """Alert acknowledgment record"""
    id: str
    alert_id: str
    acknowledged_by: str
    acknowledgment_time: datetime
    action_taken: Optional[str] = None
    notes: Optional[str] = None
    is_resolved: bool


# ==================== ANOMALY HISTORY SCHEMAS ====================

class AnomalyHistoryResponse(BaseModel):
    """Anomaly history entry"""
    id: str
    anomaly_id: str
    snapshot_number: int
    status_at_time: str
    severity_at_time: str
    duration_seconds: int
    recorded_at: datetime


# ==================== BATCH OPERATION SCHEMAS ====================

class BatchAcknowledgeRequest(BaseModel):
    """Acknowledge multiple alerts"""
    alert_ids: List[str]
    acknowledged_by: str
    notes: Optional[str] = None


class BatchResolveRequest(BaseModel):
    """Resolve multiple alerts"""
    alert_ids: List[str]
    resolution_notes: Optional[str] = None


# ==================== REPORT SCHEMAS ====================

class AnomalyReportResponse(BaseModel):
    """Anomaly report"""
    report_date: datetime
    period: str  # daily, weekly, monthly
    total_anomalies: int
    resolved_count: int
    active_count: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    by_zone: Dict[int, int]
    average_severity: str
    critical_zones: List[int]
    key_insights: List[str]


class AlertReportResponse(BaseModel):
    """Alert report"""
    report_date: datetime
    period: str
    total_alerts: int
    acknowledged_count: int
    resolved_count: int
    response_rate: float
    average_response_time: float
    by_severity: Dict[str, int]
    by_zone: Dict[int, int]
    critical_incidents: List[str]


# ==================== DASHBOARD SCHEMAS ====================

class DashboardSummaryResponse(BaseModel):
    """Dashboard summary"""
    total_active_alerts: int
    total_active_anomalies: int
    critical_alerts: int
    high_risk_zones: int
    high_risk_customers: int
    alerts_by_severity: Dict[str, int]
    anomalies_by_type: Dict[str, int]
    top_anomaly_zones: List[Dict[str, Any]]
    recent_alerts: List[AlertListResponse]
    recent_anomalies: List[AnomalyListResponse]
