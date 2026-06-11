"""
Detection System Data Models - Phase 3

Data structures for real-time customer detection and tracking.
Includes detection results, tracking information, zone definitions, and events.
"""

from typing import Optional, List, Tuple, Dict, Any
from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json

import numpy as np
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# ENUMS
# ============================================================================

class ObjectClass(str, Enum):
    """Object detection classes from YOLOv11"""
    PERSON = "person"
    BACKPACK = "backpack"
    HANDBAG = "handbag"
    SUITCASE = "suitcase"


class EventType(str, Enum):
    """Detection and tracking event types"""
    DETECTION = "detection"
    TRACK_START = "track_start"
    TRACK_END = "track_end"
    ZONE_ENTER = "zone_enter"
    ZONE_EXIT = "zone_exit"
    DWELL_START = "dwell_start"
    DWELL_END = "dwell_end"
    DWELL_UPDATE = "dwell_update"
    INTERACTION = "interaction"
    ANOMALY = "anomaly"


class ZoneType(str, Enum):
    """Zone classification types"""
    SHELF = "shelf"
    CHECKOUT = "checkout"
    ENTRANCE = "entrance"
    RESTRICTED = "restricted"
    AISLE = "aisle"


class TrackingStatus(str, Enum):
    """Tracking state for objects"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOST = "lost"
    CONFIRMED = "confirmed"


# ============================================================================
# DETECTION DATA STRUCTURES
# ============================================================================

@dataclass
class BoundingBox:
    """Bounding box coordinates and dimensions"""
    x1: float
    y1: float
    x2: float
    y2: float
    
    @property
    def width(self) -> float:
        """Width of bounding box"""
        return self.x2 - self.x1
    
    @property
    def height(self) -> float:
        """Height of bounding box"""
        return self.y2 - self.y1
    
    @property
    def area(self) -> float:
        """Area of bounding box"""
        return self.width * self.height
    
    @property
    def center(self) -> Tuple[float, float]:
        """Center point of bounding box"""
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {"x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2}


@dataclass
class Detection:
    """Single object detection result"""
    track_id: Optional[int]  # None if untracked
    bbox: BoundingBox
    class_name: ObjectClass
    confidence: float  # 0-1
    frame_index: int
    timestamp: float  # Unix timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "track_id": self.track_id,
            "bbox": self.bbox.to_dict(),
            "class_name": self.class_name.value,
            "confidence": self.confidence,
            "frame_index": self.frame_index,
            "timestamp": self.timestamp
        }


@dataclass
class DetectionFrame:
    """All detections in a single frame"""
    frame_index: int
    timestamp: float
    detections: List[Detection]
    frame_shape: Tuple[int, int, int]  # (height, width, channels)
    
    def filter_by_confidence(self, min_confidence: float) -> "DetectionFrame":
        """Filter detections by confidence threshold"""
        filtered = [d for d in self.detections if d.confidence >= min_confidence]
        return DetectionFrame(
            frame_index=self.frame_index,
            timestamp=self.timestamp,
            detections=filtered,
            frame_shape=self.frame_shape
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "frame_index": self.frame_index,
            "timestamp": self.timestamp,
            "detections": [d.to_dict() for d in self.detections],
            "detection_count": len(self.detections),
            "frame_shape": self.frame_shape
        }


# ============================================================================
# TRACKING DATA STRUCTURES
# ============================================================================

@dataclass
class TrackingObject:
    """Tracked object across multiple frames"""
    track_id: int
    class_name: ObjectClass
    status: TrackingStatus = TrackingStatus.ACTIVE
    
    # History
    frame_history: List[int] = field(default_factory=list)
    bbox_history: List[BoundingBox] = field(default_factory=list)
    confidence_history: List[float] = field(default_factory=list)
    timestamp_history: List[float] = field(default_factory=list)
    
    # Statistics
    first_seen_frame: int = 0
    last_seen_frame: int = 0
    first_seen_timestamp: float = 0.0
    last_seen_timestamp: float = 0.0
    total_frames: int = 0
    
    # Current state
    current_bbox: Optional[BoundingBox] = None
    current_confidence: float = 0.0
    current_zone: Optional[str] = None
    
    def add_detection(
        self,
        bbox: BoundingBox,
        confidence: float,
        frame_index: int,
        timestamp: float
    ) -> None:
        """Add detection to history"""
        self.frame_history.append(frame_index)
        self.bbox_history.append(bbox)
        self.confidence_history.append(confidence)
        self.timestamp_history.append(timestamp)
        
        self.current_bbox = bbox
        self.current_confidence = confidence
        self.last_seen_frame = frame_index
        self.last_seen_timestamp = timestamp
        self.total_frames = len(self.frame_history)
        
        if self.total_frames == 1:
            self.first_seen_frame = frame_index
            self.first_seen_timestamp = timestamp
    
    @property
    def age(self) -> int:
        """Number of frames since first detection"""
        return self.total_frames
    
    @property
    def duration_seconds(self) -> float:
        """Duration in seconds since first detection"""
        if self.total_frames < 2:
            return 0.0
        return self.last_seen_timestamp - self.first_seen_timestamp
    
    @property
    def avg_confidence(self) -> float:
        """Average confidence across all detections"""
        if not self.confidence_history:
            return 0.0
        return sum(self.confidence_history) / len(self.confidence_history)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "track_id": self.track_id,
            "class_name": self.class_name.value,
            "status": self.status.value,
            "age": self.age,
            "duration_seconds": self.duration_seconds,
            "avg_confidence": self.avg_confidence,
            "current_zone": self.current_zone,
            "current_bbox": self.current_bbox.to_dict() if self.current_bbox else None
        }


# ============================================================================
# ZONE DATA STRUCTURES
# ============================================================================

@dataclass
class Zone:
    """Detection zone (shelf, checkout, etc.)"""
    zone_id: str
    zone_type: ZoneType
    name: str
    
    # Polygon coordinates (x, y pairs)
    polygon: List[Tuple[float, float]]
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def min_x(self) -> float:
        """Minimum x coordinate"""
        return min(p[0] for p in self.polygon)
    
    @property
    def max_x(self) -> float:
        """Maximum x coordinate"""
        return max(p[0] for p in self.polygon)
    
    @property
    def min_y(self) -> float:
        """Minimum y coordinate"""
        return min(p[1] for p in self.polygon)
    
    @property
    def max_y(self) -> float:
        """Maximum y coordinate"""
        return max(p[1] for p in self.polygon)
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is inside zone using ray casting"""
        # Simple ray casting algorithm
        n = len(self.polygon)
        inside = False
        
        x1, y1 = self.polygon[0]
        for i in range(1, n + 1):
            x2, y2 = self.polygon[i % n]
            if y > min(y1, y2):
                if y <= max(y1, y2):
                    if x <= max(x1, x2):
                        if y1 != y2:
                            xinters = (y - y1) * (x2 - x1) / (y2 - y1) + x1
                        if x1 == x2 or x <= xinters:
                            inside = not inside
            x1, y1 = x2, y2
        
        return inside
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "zone_id": self.zone_id,
            "zone_type": self.zone_type.value,
            "name": self.name,
            "polygon": self.polygon,
            "metadata": self.metadata
        }


@dataclass
class ZoneEvent:
    """Event related to zone interaction"""
    event_type: EventType
    track_id: int
    zone_id: str
    timestamp: float
    frame_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_type": self.event_type.value,
            "track_id": self.track_id,
            "zone_id": self.zone_id,
            "timestamp": self.timestamp,
            "frame_index": self.frame_index,
            "metadata": self.metadata
        }


# ============================================================================
# DWELL TIME TRACKING
# ============================================================================

@dataclass
class DwellSession:
    """Track dwell time in a zone"""
    track_id: int
    zone_id: str
    start_frame: int
    start_timestamp: float
    
    end_frame: Optional[int] = None
    end_timestamp: Optional[float] = None
    
    @property
    def is_active(self) -> bool:
        """Check if session is still active"""
        return self.end_frame is None
    
    @property
    def duration_seconds(self) -> float:
        """Duration in seconds"""
        end_ts = self.end_timestamp or datetime.now().timestamp()
        return end_ts - self.start_timestamp
    
    def end_session(self, frame_index: int, timestamp: float) -> None:
        """Mark session as ended"""
        self.end_frame = frame_index
        self.end_timestamp = timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "track_id": self.track_id,
            "zone_id": self.zone_id,
            "duration_seconds": self.duration_seconds,
            "is_active": self.is_active
        }


# ============================================================================
# EVENT STRUCTURES
# ============================================================================

@dataclass
class DetectionEvent:
    """Detection and tracking event for publishing"""
    event_type: EventType
    timestamp: float
    frame_index: int
    track_id: Optional[int]
    zone_id: Optional[str]
    
    detection: Optional[Detection] = None
    tracking_object: Optional[Dict[str, Any]] = None
    dwell_duration_seconds: Optional[float] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON"""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "frame_index": self.frame_index,
            "track_id": self.track_id,
            "zone_id": self.zone_id,
            "detection": self.detection.to_dict() if self.detection else None,
            "tracking_object": self.tracking_object,
            "dwell_duration_seconds": self.dwell_duration_seconds,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


# ============================================================================
# CONFIGURATION MODELS (Pydantic)
# ============================================================================

class YOLOv11Config(BaseModel):
    """YOLOv11 detector configuration"""
    model_size: str = Field(default="n", description="Model size: n, s, m, l, x")
    confidence_threshold: float = Field(default=0.5, ge=0, le=1)
    iou_threshold: float = Field(default=0.45, ge=0, le=1)
    max_detections: int = Field(default=300)
    use_gpu: bool = Field(default=True)
    gpu_device_id: int = Field(default=0)
    
    model_config = ConfigDict(extra="forbid")


class ByteTrackConfig(BaseModel):
    """ByteTrack tracking configuration"""
    track_thresh: float = Field(default=0.5, ge=0, le=1)
    track_buffer: int = Field(default=30)
    match_thresh: float = Field(default=0.8, ge=0, le=1)
    min_box_area: float = Field(default=10.0)
    
    model_config = ConfigDict(extra="forbid")


class DetectionConfig(BaseModel):
    """Complete detection system configuration"""
    yolo_config: YOLOv11Config = Field(default_factory=YOLOv11Config)
    bytetrack_config: ByteTrackConfig = Field(default_factory=ByteTrackConfig)
    
    # Zone configuration
    zones: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Dwell tracking
    dwell_threshold_seconds: float = Field(default=2.0)
    dwell_check_interval_seconds: float = Field(default=1.0)
    
    # Event settings
    publish_all_detections: bool = Field(default=True)
    publish_zone_events: bool = Field(default=True)
    publish_dwell_events: bool = Field(default=True)
    
    # Performance
    max_concurrent_frames: int = Field(default=10)
    gpu_memory_fraction: float = Field(default=0.5, ge=0, le=1)
    
    # Logging
    log_level: str = Field(default="INFO")
    
    model_config = ConfigDict(extra="forbid")
