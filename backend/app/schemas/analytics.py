"""
Analytics Response Schemas for Phase 7

Pydantic models for analytics API responses.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class HotspotPoint(BaseModel):
    """Single hotspot in heatmap"""
    x: float
    y: float
    intensity: float  # 0.0 to 1.0
    count: int


class HeatmapResponse(BaseModel):
    """Heatmap response"""
    heatmap_id: str
    heatmap_type: str  # "real_time", "hourly", "daily"
    time_period_start: datetime
    time_period_end: datetime
    grid: Dict[str, Any]
    hotspots: List[HotspotPoint]
    total_samples: int
    max_intensity: float
    hotspot_count: int
    generated_at: datetime


class JourneyPoint(BaseModel):
    """Single point in journey"""
    x: float
    y: float
    timestamp: Optional[datetime] = None


class JourneyResponse(BaseModel):
    """Customer journey response"""
    journey_id: str
    customer_id: str
    path_points: List[Dict[str, float]]
    path_length: int
    total_distance: float
    zones_visited: List[int]
    zone_sequence: str
    duration_seconds: float
    interaction_count: int
    pickup_count: int
    engagement_score: float
    journey_type: str  # "browsing", "seeking", "purchasing"


class ZoneEngagementResponse(BaseModel):
    """Zone engagement metrics"""
    zone_id: int
    visitor_count: int
    unique_visitor_count: int
    entry_count: int
    exit_count: int
    total_dwell_time: float
    avg_dwell_time: float
    interaction_count: int
    avg_interactions: float
    pickup_count: int
    putback_count: int
    conversion_rate: float
    engagement_score: float
    attention_score: float
    quality_score: float
    zone_type: str  # "entry", "high_value", "engagement", "conversion", "exit", "dead_zone"
    performance_rating: str  # "excellent", "good", "average", "poor"


class RouteResponse(BaseModel):
    """Customer route pattern"""
    zone_sequence: str  # "z1->z2->z3"
    sequence_length: int
    frequency: int
    avg_duration: float
    avg_engagement_score: float
    conversion_rate: float
    completion_rate: float


class EngagementDistribution(BaseModel):
    """Engagement level distribution"""
    very_high_count: int
    high_count: int
    medium_count: int
    low_count: int


class EngagementMetricsResponse(BaseModel):
    """Aggregated engagement metrics"""
    date: datetime
    time_bucket: str
    total_customers: int
    total_interactions: int
    avg_session_duration: float
    avg_engagement_score: float
    engagement_distribution: EngagementDistribution
    total_pickups: int
    total_putbacks: int
    overall_conversion_rate: float
    avg_zones_per_journey: float
    avg_journey_distance: float
    peak_hour: int


class BusinessInsightResponse(BaseModel):
    """Business insight"""
    insight_id: str
    insight_type: str  # "performance", "trend", "anomaly", "recommendation"
    category: str  # "zones", "flow", "engagement", "conversion"
    title: str
    description: str
    details: Dict[str, Any]
    period_start: datetime
    period_end: datetime
    severity: str  # "high", "medium", "low"
    confidence_score: float
    action_items: List[str]
    expected_impact: str
    status: str
    is_actionable: bool


class AnalyticsReportResponse(BaseModel):
    """Comprehensive analytics report"""
    report_id: str
    report_type: str  # "daily", "weekly", "comprehensive"
    period_start: datetime
    period_end: datetime
    
    # Summary statistics
    total_customers: int
    total_sessions: int
    avg_session_duration: float
    total_interactions: int
    overall_engagement_score: float
    overall_conversion_rate: float
    
    # Top performers
    top_zones: List[ZoneEngagementResponse]
    top_routes: List[RouteResponse]
    
    # Insights
    key_insights: List[BusinessInsightResponse]
    recommendations: List[str]
    
    # Trends
    hourly_breakdown: Dict[str, Any]
    daily_breakdown: Dict[str, Any]
    
    # Generated
    generated_at: datetime
    generated_by: str = "analytics-engine"


class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Generic error response"""
    success: bool = False
    error: str
    code: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel):
    """Paginated response"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
