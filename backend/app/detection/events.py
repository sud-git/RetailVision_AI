"""
Event System - Phase 3

Generate and publish detection/tracking events to Redis Streams.
"""

import logging
import json
from typing import Optional, List, Dict
from datetime import datetime

from .models import (
    DetectionEvent, EventType, Detection, TrackingObject,
    ZoneEvent
)
from .exceptions import EventPublishingException

logger = logging.getLogger(__name__)


class EventBuffer:
    """Buffer for collecting events before publishing"""
    
    def __init__(self, max_buffer_size: int = 1000):
        """
        Initialize event buffer
        
        Args:
            max_buffer_size: Max events before auto-flush
        """
        self.max_buffer_size = max_buffer_size
        self.events: List[DetectionEvent] = []
    
    def add_event(self, event: DetectionEvent) -> None:
        """Add event to buffer"""
        self.events.append(event)
    
    def get_events(self) -> List[DetectionEvent]:
        """Get buffered events"""
        return self.events
    
    def clear(self) -> None:
        """Clear buffer"""
        self.events = []
    
    def should_flush(self) -> bool:
        """Check if buffer should be flushed"""
        return len(self.events) >= self.max_buffer_size
    
    def flush(self) -> List[DetectionEvent]:
        """Flush and return events"""
        events = self.events.copy()
        self.clear()
        return events


class EventGenerator:
    """Generate detection and tracking events"""
    
    def __init__(self, publish_config: Dict):
        """
        Initialize event generator
        
        Args:
            publish_config: Configuration for event publishing
        """
        self.publish_config = publish_config
        self.buffer = EventBuffer()
    
    def generate_detection_event(
        self,
        detection: Detection,
        frame_index: int,
        timestamp: float
    ) -> DetectionEvent:
        """Generate detection event"""
        return DetectionEvent(
            event_type=EventType.DETECTION,
            timestamp=timestamp,
            frame_index=frame_index,
            track_id=detection.track_id,
            zone_id=None,
            detection=detection,
            metadata={"class": detection.class_name.value}
        )
    
    def generate_track_event(
        self,
        track_obj: TrackingObject,
        event_type: EventType,
        frame_index: int,
        timestamp: float
    ) -> DetectionEvent:
        """Generate tracking event"""
        return DetectionEvent(
            event_type=event_type,
            timestamp=timestamp,
            frame_index=frame_index,
            track_id=track_obj.track_id,
            zone_id=None,
            tracking_object=track_obj.to_dict(),
            metadata={"age": track_obj.age, "class": track_obj.class_name.value}
        )
    
    def generate_zone_event(
        self,
        track_id: int,
        zone_id: str,
        event_type: EventType,
        frame_index: int,
        timestamp: float
    ) -> DetectionEvent:
        """Generate zone event"""
        return DetectionEvent(
            event_type=event_type,
            timestamp=timestamp,
            frame_index=frame_index,
            track_id=track_id,
            zone_id=zone_id
        )
    
    def generate_dwell_event(
        self,
        track_id: int,
        zone_id: str,
        event_type: EventType,
        frame_index: int,
        timestamp: float,
        dwell_duration_seconds: Optional[float] = None
    ) -> DetectionEvent:
        """Generate dwell time event"""
        return DetectionEvent(
            event_type=event_type,
            timestamp=timestamp,
            frame_index=frame_index,
            track_id=track_id,
            zone_id=zone_id,
            dwell_duration_seconds=dwell_duration_seconds
        )
    
    def buffer_event(self, event: DetectionEvent) -> None:
        """Buffer an event"""
        self.buffer.add_event(event)
    
    def buffer_events(self, events: List[DetectionEvent]) -> None:
        """Buffer multiple events"""
        for event in events:
            self.buffer_event(event)
    
    def get_buffered_events(self) -> List[DetectionEvent]:
        """Get buffered events"""
        return self.buffer.get_events()
    
    def flush_buffer(self) -> List[DetectionEvent]:
        """Flush buffer and return events"""
        return self.buffer.flush()


class EventPublisher:
    """Publish events to Redis Streams"""
    
    def __init__(self, redis_client):
        """
        Initialize event publisher
        
        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
        self.stream_keys = {
            EventType.DETECTION: "detection:events",
            EventType.TRACK_START: "tracking:events",
            EventType.TRACK_END: "tracking:events",
            EventType.ZONE_ENTER: "zone:events",
            EventType.ZONE_EXIT: "zone:events",
            EventType.DWELL_START: "dwell:events",
            EventType.DWELL_END: "dwell:events",
            EventType.DWELL_UPDATE: "dwell:events",
            EventType.INTERACTION: "interaction:events",
            EventType.ANOMALY: "anomaly:events"
        }
    
    async def publish_event(self, event: DetectionEvent) -> Optional[str]:
        """
        Publish single event to Redis
        
        Args:
            event: Detection event
            
        Returns:
            Stream ID if successful
        """
        try:
            stream_key = self.stream_keys.get(event.event_type, "detection:events")
            
            # Prepare event data
            event_data = {
                "event_type": event.event_type.value,
                "timestamp": event.timestamp,
                "frame_index": event.frame_index,
                "track_id": str(event.track_id) if event.track_id else "",
                "zone_id": event.zone_id or "",
                "data": json.dumps(event.to_dict())
            }
            
            # Publish to stream
            event_id = await self.redis.xadd(stream_key, event_data)
            return event_id
        
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            raise EventPublishingException(f"Publishing failed: {e}")
    
    async def publish_events(self, events: List[DetectionEvent]) -> List[Optional[str]]:
        """
        Publish multiple events to Redis
        
        Args:
            events: List of detection events
            
        Returns:
            List of stream IDs
        """
        result = []
        for event in events:
            try:
                stream_id = await self.publish_event(event)
                result.append(stream_id)
            except Exception as e:
                logger.error(f"Error publishing event: {e}")
                result.append(None)
        return result
    
    async def publish_batch(self, events: List[DetectionEvent]) -> int:
        """
        Publish batch of events
        
        Args:
            events: List of events
            
        Returns:
            Number of successfully published events
        """
        published = 0
        for event in events:
            try:
                await self.publish_event(event)
                published += 1
            except Exception as e:
                logger.warning(f"Failed to publish event: {e}")
        
        return published
    
    async def publish_metrics(self, metrics: Dict) -> None:
        """
        Publish detection metrics
        
        Args:
            metrics: Metrics dictionary
        """
        try:
            metrics_data = {
                "timestamp": datetime.now().isoformat(),
                "data": json.dumps(metrics)
            }
            await self.redis.xadd("detection:metrics", metrics_data)
        except Exception as e:
            logger.error(f"Failed to publish metrics: {e}")


class EventSummarizer:
    """Summarize events for analytics"""
    
    def __init__(self):
        """Initialize event summarizer"""
        self.event_counts = {}
        self.track_summary = {}
    
    def process_events(self, events: List[DetectionEvent]) -> Dict:
        """
        Process and summarize events
        
        Args:
            events: List of events
            
        Returns:
            Summary dictionary
        """
        summary = {
            "total_events": len(events),
            "event_types": {},
            "tracks_involved": set(),
            "zones_involved": set(),
            "timestamp": datetime.now().isoformat()
        }
        
        for event in events:
            # Count event types
            event_type = event.event_type.value
            summary["event_types"][event_type] = summary["event_types"].get(event_type, 0) + 1
            
            # Track involved objects
            if event.track_id:
                summary["tracks_involved"].add(event.track_id)
            
            if event.zone_id:
                summary["zones_involved"].add(event.zone_id)
        
        # Convert sets to lists for JSON serialization
        summary["tracks_involved"] = list(summary["tracks_involved"])
        summary["zones_involved"] = list(summary["zones_involved"])
        
        return summary
