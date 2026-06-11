"""
Detection Service Orchestrator - Phase 3

Main service coordinating detection, tracking, zones, and events.
"""

import logging
import asyncio
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import numpy as np

from app.cache import CacheManager

from .models import (
    DetectionFrame, Detection, DetectionConfig, ZoneEvent, EventType,
    TrackingObject, Zone, ZoneType
)
from .detector import YOLOv11Detector, DetectorPool
from .exceptions import DetectionException, ModelNotLoadedException
from .overlay import OverlayRenderer
from .zones import ZoneManager, DwellTimeTracker, InteractionDetector
from .events import EventGenerator, EventPublisher, EventBuffer
from ..tracking.bytetrack import TrackingEngine

logger = logging.getLogger(__name__)

# Global detection service instance
_detection_service: Optional["DetectionService"] = None


class DetectionService:
    """Main detection and tracking service"""
    
    def __init__(
        self,
        config: DetectionConfig,
        cache_manager: Optional[CacheManager] = None
    ):
        """
        Initialize detection service
        
        Args:
            config: Detection configuration
            cache_manager: Optional Redis cache manager
        """
        self.config = config
        self.cache_manager = cache_manager
        
        # Initialize components
        self.detector: Optional[YOLOv11Detector] = None
        self.tracker: Optional[TrackingEngine] = None
        self.zone_manager = ZoneManager()
        self.dwell_tracker = DwellTimeTracker(config.dwell_threshold_seconds)
        self.interaction_detector = InteractionDetector()
        self.event_generator = EventGenerator(config.dict())
        self.event_publisher: Optional[EventPublisher] = None
        self.overlay_renderer = OverlayRenderer()
        
        # Statistics
        self.stats = {
            "frames_processed": 0,
            "total_detections": 0,
            "active_tracks": 0,
            "events_published": 0
        }
        
        self.is_running = False
        self.frame_queue: asyncio.Queue = asyncio.Queue(maxsize=config.max_concurrent_frames)
    
    async def initialize(self) -> None:
        """Initialize service components"""
        logger.info("Initializing detection service...")
        
        try:
            # Load detector
            self.detector = YOLOv11Detector(self.config.yolo_config)
            logger.info("✓ Detector loaded")
            
            # Initialize tracking (need dummy frame shape)
            dummy_shape = (1080, 1920, 3)
            self.tracker = TrackingEngine(self.config.bytetrack_config, dummy_shape)
            logger.info("✓ Tracker initialized")
            
            # Initialize zones from config
            if self.config.zones:
                self.zone_manager.add_zones_from_config(self.config.zones)
                logger.info(f"✓ Added {len(self.config.zones)} zones")
            
            # Initialize event publisher
            if self.cache_manager:
                self.event_publisher = EventPublisher(self.cache_manager.redis)
                logger.info("✓ Event publisher initialized")
            
            self.is_running = True
            logger.info("✅ Detection service initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize detection service: {e}")
            self.is_running = False
            raise
    
    async def process_frame(
        self,
        frame: np.ndarray,
        frame_index: int,
        timestamp: float
    ) -> Dict:
        """
        Process single frame
        
        Args:
            frame: Input frame (HxWx3, BGR)
            frame_index: Frame number
            timestamp: Frame timestamp
            
        Returns:
            Detection results dictionary
        """
        if not self.is_running or self.detector is None or self.tracker is None:
            raise DetectionException("Service not initialized")
        
        try:
            # Run detection
            detection_frame = self.detector.detect(frame, frame_index, timestamp)
            
            # Update tracking
            tracked_detections, tracked_objects = self.tracker.update(detection_frame)
            
            # Update detection frame with tracked detections
            detection_frame.detections = tracked_detections
            
            # Process zones and dwell
            zone_events = self._process_zone_interactions(
                tracked_detections,
                frame_index,
                timestamp
            )
            
            # Generate events
            events = self._generate_events(
                detection_frame,
                tracked_objects,
                zone_events
            )
            
            # Publish events
            if self.event_publisher and self.config.publish_all_detections:
                await self.event_publisher.publish_batch(events)
                self.stats["events_published"] += len(events)
            
            # Update statistics
            self.stats["frames_processed"] += 1
            self.stats["total_detections"] += len(tracked_detections)
            self.stats["active_tracks"] = len(self.tracker.get_active_tracks())
            
            return {
                "frame_index": frame_index,
                "timestamp": timestamp,
                "detections": tracked_detections,
                "tracked_objects": tracked_objects,
                "events": events,
                "zone_events": zone_events
            }
        
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            raise
    
    def _process_zone_interactions(
        self,
        detections: List[Detection],
        frame_index: int,
        timestamp: float
    ) -> List[Dict]:
        """Process zone interactions for tracked objects"""
        zone_events = []
        
        for det in detections:
            if det.track_id is None:
                continue
            
            # Check zones for this detection
            zones = self.zone_manager.check_point_in_zones(
                det.bbox.center[0],
                det.bbox.center[1]
            )
            
            # Update zone tracking
            prev_events = self.zone_manager.update_track_zones(
                det.track_id,
                set(zones)
            )
            
            for zone_id, event_type in prev_events:
                zone_event = {
                    "event_type": event_type.value,
                    "track_id": det.track_id,
                    "zone_id": zone_id,
                    "frame": frame_index,
                    "timestamp": timestamp
                }
                zone_events.append(zone_event)
            
            # Update dwell tracking
            dwell_events = self.dwell_tracker.update(
                det.track_id,
                set(zones),
                frame_index,
                timestamp
            )
            
            for track_id, zone_id, event_type in dwell_events:
                zone_events.append({
                    "event_type": event_type.value,
                    "track_id": track_id,
                    "zone_id": zone_id,
                    "frame": frame_index,
                    "timestamp": timestamp
                })
            
            # Detect interactions
            interactions = self.interaction_detector.detect_interaction(
                det.track_id,
                set(zones),
                frame_index,
                timestamp
            )
        
        return zone_events
    
    def _generate_events(
        self,
        detection_frame: DetectionFrame,
        tracked_objects: List[TrackingObject],
        zone_events: List[Dict]
    ) -> List:
        """Generate events from detections and tracking"""
        events = []
        
        # Detection events
        if self.config.publish_all_detections:
            for det in detection_frame.detections:
                event = self.event_generator.generate_detection_event(
                    det,
                    detection_frame.frame_index,
                    detection_frame.timestamp
                )
                events.append(event)
        
        # Zone events
        if self.config.publish_zone_events and zone_events:
            for z_event in zone_events:
                event = self.event_generator.generate_zone_event(
                    z_event["track_id"],
                    z_event["zone_id"],
                    EventType(z_event["event_type"]),
                    z_event["frame"],
                    z_event["timestamp"]
                )
                events.append(event)
        
        return events
    
    def render_detections(
        self,
        frame: np.ndarray,
        detections: List[Detection],
        tracked_objects: Optional[List[TrackingObject]] = None,
        draw_zones: bool = True
    ) -> np.ndarray:
        """
        Render detections on frame
        
        Args:
            frame: Input frame
            detections: List of detections
            tracked_objects: Optional tracking objects
            draw_zones: Draw zone overlays
            
        Returns:
            Rendered frame
        """
        detection_frame = DetectionFrame(
            frame_index=0,
            timestamp=0.0,
            detections=detections,
            frame_shape=frame.shape
        )
        
        zones = self.zone_manager.get_all_zones() if draw_zones else None
        
        return self.overlay_renderer.render_frame(
            frame,
            detection_frame,
            tracked_objects,
            zones
        )
    
    async def shutdown(self) -> None:
        """Shutdown service"""
        logger.info("Shutting down detection service...")
        self.is_running = False
        logger.info("✓ Detection service shutdown complete")
    
    def get_statistics(self) -> Dict:
        """Get service statistics"""
        return {
            **self.stats,
            "tracking_stats": self.tracker.get_statistics() if self.tracker else {},
            "zones_count": len(self.zone_manager.get_all_zones()),
            "active_dwell_sessions": len(self.dwell_tracker.get_active_sessions())
        }


async def get_detection_service() -> Optional[DetectionService]:
    """Get global detection service instance"""
    return _detection_service


async def initialize_detection_service(
    config: DetectionConfig,
    cache_manager: Optional[CacheManager] = None
) -> DetectionService:
    """Initialize global detection service"""
    global _detection_service
    
    _detection_service = DetectionService(config, cache_manager)
    await _detection_service.initialize()
    return _detection_service


async def shutdown_detection_service() -> None:
    """Shutdown global detection service"""
    global _detection_service
    
    if _detection_service:
        await _detection_service.shutdown()
        _detection_service = None
