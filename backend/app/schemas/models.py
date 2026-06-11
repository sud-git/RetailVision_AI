"""Request/Response schemas using Pydantic."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


# ==============================================================================
# CUSTOMER SCHEMAS
# ==============================================================================

class CustomerBase(BaseModel):
    """Base customer schema."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    external_id: Optional[str] = None


class CustomerCreate(CustomerBase):
    """Create customer."""
    pass


class CustomerUpdate(BaseModel):
    """Update customer."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_flagged: Optional[bool] = None
    flag_reason: Optional[str] = None


class CustomerResponse(CustomerBase):
    """Customer response."""
    id: UUID
    customer_tier: str
    lifetime_visits: int
    lifetime_purchase_value: float
    is_active: bool
    is_flagged: bool
    flag_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==============================================================================
# TRACKING SESSION SCHEMAS
# ==============================================================================

class TrackingSessionBase(BaseModel):
    """Base tracking session."""
    customer_id: UUID


class TrackingSessionCreate(TrackingSessionBase):
    """Create tracking session."""
    pass


class TrackingSessionUpdate(BaseModel):
    """Update tracking session."""
    exit_time: Optional[datetime] = None
    is_completed: Optional[bool] = None
    session_status: Optional[str] = None
    engagement_level: Optional[str] = None


class TrackingSessionResponse(TrackingSessionBase):
    """Tracking session response."""
    id: UUID
    entry_time: datetime
    exit_time: Optional[datetime]
    total_duration_seconds: Optional[int]
    zones_visited: int
    total_interactions: int
    total_dwell_time_seconds: int
    engagement_level: str
    is_completed: bool
    has_anomalies: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==============================================================================
# SHELF INTERACTION SCHEMAS
# ==============================================================================

class ShelfInteractionBase(BaseModel):
    """Base shelf interaction."""
    customer_id: UUID
    tracking_session_id: UUID
    interaction_type: str
    zone_id: str
    zone_name: str


class ShelfInteractionCreate(ShelfInteractionBase):
    """Create shelf interaction."""
    engagement_level: Optional[str] = "browsing"


class ShelfInteractionUpdate(BaseModel):
    """Update shelf interaction."""
    engagement_level: Optional[str] = None
    end_time: Optional[datetime] = None
    items_examined: Optional[int] = None


class ShelfInteractionResponse(ShelfInteractionBase):
    """Shelf interaction response."""
    id: UUID
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[int]
    engagement_level: str
    is_prolonged: bool
    items_examined: int
    confidence_score: float
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==============================================================================
# DWELL TIME SCHEMAS
# ==============================================================================

class DwellTimeRecordBase(BaseModel):
    """Base dwell time record."""
    customer_id: UUID
    tracking_session_id: UUID
    zone_id: str
    zone_name: str


class DwellTimeRecordCreate(DwellTimeRecordBase):
    """Create dwell time record."""
    dwell_time_seconds: int
    engagement_intensity: str = "moderate"


class DwellTimeRecordResponse(DwellTimeRecordBase):
    """Dwell time response."""
    id: UUID
    dwell_time_seconds: int
    first_visit: datetime
    last_visit: datetime
    visit_count: int
    engagement_intensity: str
    interaction_count: int
    revisit_frequency: Optional[str]
    avg_interaction_per_visit: float
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==============================================================================
# ALERT SCHEMAS
# ==============================================================================

class AlertBase(BaseModel):
    """Base alert."""
    alert_type: str
    alert_severity: str = "medium"
    alert_title: str
    alert_description: str


class AlertCreate(AlertBase):
    """Create alert."""
    customer_id: Optional[UUID] = None
    zone_id: Optional[str] = None
    related_session_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AlertUpdate(BaseModel):
    """Update alert."""
    is_acknowledged: Optional[bool] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


class AlertResponse(AlertBase):
    """Alert response."""
    id: UUID
    customer_id: Optional[UUID]
    zone_id: Optional[str]
    related_session_id: Optional[UUID]
    is_active: bool
    is_acknowledged: bool
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==============================================================================
# EVENT SCHEMAS
# ==============================================================================

class EventBase(BaseModel):
    """Base event."""
    event_type: str
    event_category: str
    event_data: Dict[str, Any]


class EventCreate(EventBase):
    """Create event."""
    customer_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    zone_id: Optional[str] = None
    event_severity: str = "info"


class EventResponse(EventBase):
    """Event response."""
    id: UUID
    customer_id: Optional[UUID]
    session_id: Optional[UUID]
    zone_id: Optional[str]
    event_severity: str
    is_processed: bool
    processing_status: str
    created_at: datetime
    timestamp: datetime
    
    class Config:
        from_attributes = True


# ==============================================================================
# ANALYTICS SNAPSHOT SCHEMAS
# ==============================================================================

class AnalyticsSnapshotBase(BaseModel):
    """Base analytics snapshot."""
    snapshot_period: str
    period_start: datetime
    period_end: datetime


class AnalyticsSnapshotCreate(AnalyticsSnapshotBase):
    """Create snapshot."""
    total_customers: int = 0
    total_interactions: int = 0
    avg_dwell_time_seconds: float = 0.0
    zone_metrics: Dict[str, Any] = Field(default_factory=dict)
    engagement_breakdown: Dict[str, Any] = Field(default_factory=dict)


class AnalyticsSnapshotResponse(AnalyticsSnapshotBase):
    """Analytics snapshot response."""
    id: UUID
    total_customers: int
    total_interactions: int
    avg_dwell_time_seconds: float
    zone_metrics: Dict[str, Any]
    engagement_breakdown: Dict[str, Any]
    customer_segments: Dict[str, Any]
    anomaly_count: int
    peak_hour: Optional[str]
    peak_hour_customer_count: int
    data_quality_score: float
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==============================================================================
# ANALYTICS API SCHEMAS
# ==============================================================================

class AnalyticsOverviewResponse(BaseModel):
    """Analytics overview response."""
    total_customers_today: int
    active_customers: int
    total_interactions: int
    avg_dwell_time_seconds: float
    top_zones: List[Dict[str, Any]]
    engagement_breakdown: Dict[str, int]
    anomalies_detected: int
    timestamp: datetime


class DwellTimeAnalyticsResponse(BaseModel):
    """Dwell time analytics response."""
    zone_id: str
    zone_name: str
    total_visitors: int
    avg_dwell_time_seconds: float
    peak_hour: str
    peak_hour_count: int
    engagement_levels: Dict[str, int]
    timestamp: datetime


class ZoneAnalyticsResponse(BaseModel):
    """Zone analytics response."""
    zone_id: str
    zone_name: str
    customer_count: int
    interaction_count: int
    avg_interaction_duration: float
    engagement_level: str
    popularity_rank: int
    trend: str  # up, down, stable
    timestamp: datetime


class InteractionAnalyticsResponse(BaseModel):
    """Interaction analytics response."""
    total_interactions: int
    breakdown_by_type: Dict[str, int]
    breakdown_by_engagement: Dict[str, int]
    avg_duration_seconds: float
    peak_hour: str
    top_zones: List[Dict[str, Any]]
    anomalies: int
    timestamp: datetime


# ==============================================================================
# HEALTH CHECK SCHEMAS
# ==============================================================================

class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str  # healthy, degraded, unhealthy
    timestamp: datetime
    database: str  # connected, disconnected
    redis: str  # connected, disconnected
    services: Dict[str, str]


class MetricsResponse(BaseModel):
    """Metrics response."""
    total_customers: int
    total_sessions: int
    total_interactions: int
    total_alerts: int
    requests_per_minute: float
    average_response_time_ms: float
    error_rate: float
    uptime_seconds: float


class StatusResponse(BaseModel):
    """Status response."""
    service_name: str
    version: str
    environment: str
    uptime_seconds: float
    start_time: datetime
    processed_events: int
    failed_events: int
    queue_depth: int


# ==============================================================================
# PAGINATION SCHEMAS
# ==============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters."""
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=1000)
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    total: int
    skip: int
    limit: int
    data: List[Any]


# ==============================================================================
# ERROR RESPONSE SCHEMAS
# ==============================================================================

class ErrorResponse(BaseModel):
    """Error response."""
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
    request_id: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    error_code: str = "VALIDATION_ERROR"
    error_message: str = "Validation failed"
    errors: List[Dict[str, Any]]
    timestamp: datetime
