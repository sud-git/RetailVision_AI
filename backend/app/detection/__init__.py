"""
Detection Module - Phase 3

Real-time customer detection and tracking system.
"""

# Models
from .models import (
    ObjectClass, EventType, ZoneType, TrackingStatus,
    BoundingBox, Detection, DetectionFrame,
    TrackingObject, Zone, ZoneEvent, DwellSession,
    DetectionEvent,
    YOLOv11Config, ByteTrackConfig, DetectionConfig
)

# Detector
from .detector import YOLOv11Detector, DetectorPool

# Zones
from .zones import ZoneManager, DwellTimeTracker, InteractionDetector

# Events
from .events import EventBuffer, EventGenerator, EventPublisher, EventSummarizer

# Overlay
from .overlay import OverlayRenderer

# Service
from .service import (
    DetectionService,
    get_detection_service,
    initialize_detection_service,
    shutdown_detection_service
)

# Exceptions
from .exceptions import (
    DetectionException,
    ModelException,
    ModelNotLoadedException,
    ModelInferenceException,
    TrackingException,
    TrackingInitializationException,
    ZoneException,
    InvalidZoneException,
    DwellTrackingException,
    ConfigurationException,
    GPUException,
    GPUNotAvailableException,
    EventPublishingException
)

__all__ = [
    # Models
    "ObjectClass", "EventType", "ZoneType", "TrackingStatus",
    "BoundingBox", "Detection", "DetectionFrame",
    "TrackingObject", "Zone", "ZoneEvent", "DwellSession",
    "DetectionEvent",
    "YOLOv11Config", "ByteTrackConfig", "DetectionConfig",
    
    # Detector
    "YOLOv11Detector", "DetectorPool",
    
    # Zones
    "ZoneManager", "DwellTimeTracker", "InteractionDetector",
    
    # Events
    "EventBuffer", "EventGenerator", "EventPublisher", "EventSummarizer",
    
    # Overlay
    "OverlayRenderer",
    
    # Service
    "DetectionService",
    "get_detection_service",
    "initialize_detection_service",
    "shutdown_detection_service",
    
    # Exceptions
    "DetectionException",
    "ModelException",
    "ModelNotLoadedException",
    "ModelInferenceException",
    "TrackingException",
    "TrackingInitializationException",
    "ZoneException",
    "InvalidZoneException",
    "DwellTrackingException",
    "ConfigurationException",
    "GPUException",
    "GPUNotAvailableException",
    "EventPublishingException"
]
