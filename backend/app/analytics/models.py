"""
Phase 4: Analytics Data Models & Configurations

Data structures for shelf interactions, events, and retail analytics.
"""

from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
import json
from pydantic import BaseModel, Field


# ============================================================================
# ENUMS
# ============================================================================

class InteractionType(str, Enum):
    """Customer interaction types"""
    ZONE_ENTRY = "zone_entry"
    ZONE_EXIT = "zone_exit"
    SHELF_TOUCH = "shelf_touch"
    PICKUP = "pickup"
    PUTBACK = "putback"
    BROWSE = "browse"
    COMPARE = "compare"
    ENGAGEMENT = "engagement"


class EventSeverity(str, Enum):
    """Event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    CRITICAL = "critical"


class CustomerBehavior(str, Enum):
    """Customer behavior classifications"""
    BROWSING = "browsing"
    COMPARING = "comparing"
    PURCHASING = "purchasing"
    SUSPICIOUS = "suspicious"
    STUCK = "stuck"


class ShelfSection(str, Enum):
    """Shelf sections/zones"""
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"
    ENDCAP = "endcap"
    COOLER = "cooler"


# ============================================================================
# DATACLASSES - Interactions
# ============================================================================

@dataclass
class ShelfZone:
    """Configurable shelf zone"""
    zone_id: str
    name: str
    store_section: str
    shelf_level: ShelfSection
    polygon: List[Tuple[float, float]]  # [x, y] coordinates
    category: str  # e.g., "dairy", "produce"
    product_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'zone_id': self.zone_id,
            'name': self.name,
            'store_section': self.store_section,
            'shelf_level': self.shelf_level.value,
            'polygon': self.polygon,
            'category': self.category,
            'product_count': self.product_count,
            'metadata': self.metadata
        }


@dataclass
class CustomerInteraction:
    """Single customer-shelf interaction event"""
    interaction_id: str
    track_id: int
    zone_id: str
    interaction_type: InteractionType
    timestamp: datetime
    duration_seconds: float
    intensity: float  # 0-1 scale, how engaged
    position: Tuple[float, float]  # (x, y) on frame
    frame_index: int
    confidence: float = 0.9
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'interaction_id': self.interaction_id,
            'track_id': self.track_id,
            'zone_id': self.zone_id,
            'interaction_type': self.interaction_type.value,
            'timestamp': self.timestamp.isoformat(),
            'duration_seconds': self.duration_seconds,
            'intensity': self.intensity,
            'position': self.position,
            'frame_index': self.frame_index,
            'confidence': self.confidence,
            'metadata': self.metadata
        }

    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps(self.to_dict())


@dataclass
class ZoneDwellSession:
    """Customer dwell session in a zone"""
    session_id: str
    track_id: int
    zone_id: str
    entry_time: datetime
    exit_time: Optional[datetime] = None
    entry_frame: int = 0
    exit_frame: Optional[int] = None
    interaction_count: int = 0
    intensity_sum: float = 0.0
    visits: int = 1

    @property
    def duration_seconds(self) -> float:
        """Calculate session duration"""
        end_time = self.exit_time or datetime.now()
        return (end_time - self.entry_time).total_seconds()

    @property
    def avg_intensity(self) -> float:
        """Average interaction intensity"""
        if self.interaction_count == 0:
            return 0.0
        return self.intensity_sum / self.interaction_count

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'session_id': self.session_id,
            'track_id': self.track_id,
            'zone_id': self.zone_id,
            'entry_time': self.entry_time.isoformat(),
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'duration_seconds': self.duration_seconds,
            'interaction_count': self.interaction_count,
            'avg_intensity': self.avg_intensity,
            'visits': self.visits
        }


@dataclass
class CustomerProfile:
    """Real-time customer profile"""
    track_id: int
    first_seen: datetime
    last_seen: datetime
    total_zones_visited: Set[str] = field(default_factory=set)
    interactions: List[CustomerInteraction] = field(default_factory=list)
    dwell_sessions: Dict[str, ZoneDwellSession] = field(default_factory=dict)
    total_dwell_time: float = 0.0
    behavior_classification: CustomerBehavior = CustomerBehavior.BROWSING
    anomaly_flags: List[str] = field(default_factory=list)

    @property
    def duration_in_store(self) -> float:
        """Total time in store"""
        return (self.last_seen - self.first_seen).total_seconds()

    def add_interaction(self, interaction: CustomerInteraction):
        """Add interaction to profile"""
        self.interactions.append(interaction)
        self.total_zones_visited.add(interaction.zone_id)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'track_id': self.track_id,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'duration_in_store': self.duration_in_store,
            'total_zones_visited': list(self.total_zones_visited),
            'interaction_count': len(self.interactions),
            'total_dwell_time': self.total_dwell_time,
            'behavior': self.behavior_classification.value,
            'anomalies': self.anomaly_flags
        }


# ============================================================================
# DATACLASSES - Events
# ============================================================================

@dataclass
class RetailEvent:
    """Retail event (interaction, alert, metric)"""
    event_id: str
    event_type: str
    timestamp: datetime
    track_id: Optional[int] = None
    zone_id: Optional[str] = None
    severity: EventSeverity = EventSeverity.INFO
    message: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    frame_index: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat(),
            'track_id': self.track_id,
            'zone_id': self.zone_id,
            'severity': self.severity.value,
            'message': self.message,
            'payload': self.payload,
            'frame_index': self.frame_index
        }

    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps(self.to_dict())


@dataclass
class AnomalyEvent:
    """Anomalous behavior detection"""
    anomaly_id: str
    track_id: int
    anomaly_type: str  # "loitering", "suspicious", "theft_risk"
    confidence: float
    timestamp: datetime
    zone_id: Optional[str] = None
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'anomaly_id': self.anomaly_id,
            'track_id': self.track_id,
            'anomaly_type': self.anomaly_type,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'zone_id': self.zone_id,
            'description': self.description,
            'metadata': self.metadata
        }


# ============================================================================
# PYDANTIC MODELS - Configurations
# ============================================================================

class ShelfZoneConfig(BaseModel):
    """Configuration for shelf zones"""
    zone_id: str
    name: str
    store_section: str
    shelf_level: str
    polygon: List[List[float]]
    category: str
    product_count: int = 0
    metadata: Dict[str, Any] = {}


class InteractionConfig(BaseModel):
    """Configuration for interaction detection"""
    min_engagement_duration: float = 2.0  # seconds
    max_quick_browse_duration: float = 5.0
    min_comparing_duration: float = 10.0
    pickup_distance_threshold: float = 50  # pixels
    putback_confidence_threshold: float = 0.7
    suspicious_behavior_threshold: float = 0.8
    crowd_threshold: int = 5  # min customers in zone


class DwellAnalyticsConfig(BaseModel):
    """Configuration for dwell time analytics"""
    min_dwell_time: float = 1.0  # seconds
    max_session_gap: float = 5.0  # seconds before ending session
    aggregate_intervals: List[int] = [60, 300, 3600]  # second intervals
    track_history_size: int = 1000  # max interactions per track


class EventPublishingConfig(BaseModel):
    """Configuration for event publishing"""
    publish_interactions: bool = True
    publish_anomalies: bool = True
    publish_analytics: bool = True
    batch_events: bool = True
    batch_size: int = 50
    batch_timeout_ms: int = 1000
    retry_count: int = 3
    retry_delay_ms: int = 100


class OverlayConfig(BaseModel):
    """Configuration for visualization overlay"""
    show_zones: bool = True
    show_interactions: bool = True
    show_dwell_time: bool = True
    show_alerts: bool = True
    show_behavior: bool = True
    zone_opacity: float = 0.3
    interaction_radius: int = 10
    text_scale: float = 0.6


class AnalyticsConfig(BaseModel):
    """Main analytics configuration"""
    shelf_zones: List[ShelfZoneConfig] = []
    interaction: InteractionConfig = InteractionConfig()
    dwell_analytics: DwellAnalyticsConfig = DwellAnalyticsConfig()
    event_publishing: EventPublishingConfig = EventPublishingConfig()
    overlay: OverlayConfig = OverlayConfig()
    anomaly_detection_enabled: bool = True
    crowd_detection_enabled: bool = True
    heatmap_enabled: bool = True
    log_level: str = "INFO"


# ============================================================================
# PYDANTIC MODELS - Analytics Metrics
# ============================================================================

class ZoneMetrics(BaseModel):
    """Metrics for a shelf zone"""
    zone_id: str
    name: str
    total_visits: int = 0
    total_interactions: int = 0
    average_dwell_time: float = 0.0
    max_dwell_time: float = 0.0
    min_dwell_time: float = 0.0
    unique_customers: int = 0
    engagement_rate: float = 0.0
    peak_hours: List[int] = []
    interaction_heatmap: Dict[str, int] = {}


class StoreMetrics(BaseModel):
    """Overall store metrics"""
    total_customers: int = 0
    average_store_time: float = 0.0
    popular_zones: List[str] = []
    total_interactions: int = 0
    anomaly_count: int = 0
    crowd_events: int = 0
    peak_hours: List[int] = []
    zone_metrics: Dict[str, ZoneMetrics] = {}


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class AddShelfZoneRequest(BaseModel):
    """Request to add a shelf zone"""
    zone_id: str
    name: str
    store_section: str
    shelf_level: str
    polygon: List[List[float]]
    category: str


class CustomerProfileResponse(BaseModel):
    """Customer profile response"""
    track_id: int
    duration_in_store: float
    zones_visited: List[str]
    interaction_count: int
    total_dwell_time: float
    behavior: str
    anomalies: List[str]


class EventResponse(BaseModel):
    """Event response"""
    event_id: str
    event_type: str
    timestamp: str
    severity: str
    message: str


class AnalyticsResponse(BaseModel):
    """Analytics response"""
    timestamp: str
    total_customers: int
    total_interactions: int
    zone_metrics: Dict[str, Dict]
    anomalies: List[Dict]
