"""
Phase 4: Retail Event Intelligence

Extended event system for shelf interactions, anomalies, and analytics.
"""

import logging
import json
from typing import Dict, List, Optional, Set
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
import uuid
from collections import defaultdict

from ..analytics.models import (
    RetailEvent, AnomalyEvent, EventSeverity, CustomerBehavior,
    EventPublishingConfig
)

logger = logging.getLogger(__name__)


class RetailEventType(str, Enum):
    """Extended retail event types"""
    # Interaction events
    ZONE_ENTRY = "zone_entry"
    ZONE_EXIT = "zone_exit"
    SHELF_INTERACTION = "shelf_interaction"
    PROLONGED_ENGAGEMENT = "prolonged_engagement"
    
    # Anomaly events
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    LOITERING = "loitering"
    THEFT_RISK = "theft_risk"
    
    # Crowd events
    CROWD_DETECTED = "crowd_detected"
    HIGH_DENSITY = "high_density"
    
    # Analytics events
    PEAK_HOUR = "peak_hour"
    ZONE_POPULARITY = "zone_popularity"
    CUSTOMER_SEGMENT = "customer_segment"


class AnomalyType(str, Enum):
    """Anomaly classifications"""
    LOITERING = "loitering"
    SUSPICIOUS_BROWSING = "suspicious_browsing"
    RAPID_ZONE_CHANGES = "rapid_zone_changes"
    EXTENDED_ENGAGEMENT = "extended_engagement"
    PACKAGE_CONCEALMENT = "package_concealment"
    REPEATED_ZONE_VISITS = "repeated_zone_visits"


@dataclass
class CrowdEvent:
    """Crowd density event"""
    event_id: str
    timestamp: datetime
    zone_id: str
    customer_count: int
    density_level: str  # "low", "medium", "high"
    frame_index: int


@dataclass
class EngagementMetric:
    """Customer engagement metric"""
    track_id: int
    zone_id: str
    engagement_score: float  # 0-1
    interaction_count: int
    dwell_time: float
    behavior_type: str


class RetailEventIntelligence:
    """Generate and manage retail intelligence events"""

    def __init__(self, config: EventPublishingConfig):
        """Initialize event intelligence"""
        self.config = config
        self.event_buffer: List[RetailEvent] = []
        self.anomaly_buffer: List[AnomalyEvent] = []
        self.event_history: List[RetailEvent] = []
        self.anomaly_history: List[AnomalyEvent] = []
        
        # Event tracking
        self.recent_zone_entries: Dict[int, float] = {}  # track_id -> timestamp
        self.zone_interactions: Dict[str, Set[int]] = defaultdict(set)  # zone_id -> track_ids
        self.customer_zone_visits: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        logger.info("Retail Event Intelligence initialized")

    def generate_interaction_event(
        self,
        track_id: int,
        zone_id: str,
        interaction_type: str,
        confidence: float,
        duration: float,
        frame_index: int,
        timestamp: datetime,
        metadata: Optional[Dict] = None
    ) -> RetailEvent:
        """Generate interaction event"""
        
        event = RetailEvent(
            event_id=str(uuid.uuid4()),
            event_type=interaction_type,
            timestamp=timestamp,
            track_id=track_id,
            zone_id=zone_id,
            severity=EventSeverity.INFO,
            message=f"Customer {track_id} {interaction_type} in zone {zone_id}",
            payload={
                'confidence': confidence,
                'duration': duration,
                'zone_id': zone_id,
                'track_id': track_id,
                **(metadata or {})
            },
            frame_index=frame_index
        )

        self.event_buffer.append(event)
        self.event_history.append(event)

        # Track zone interactions
        if interaction_type == "zone_entry":
            self.zone_interactions[zone_id].add(track_id)
            self.recent_zone_entries[track_id] = timestamp.timestamp()
            self.customer_zone_visits[track_id][zone_id] += 1

        return event

    def detect_prolonged_engagement(
        self,
        track_id: int,
        zone_id: str,
        dwell_time: float,
        engagement_threshold: float,
        frame_index: int,
        timestamp: datetime
    ) -> Optional[RetailEvent]:
        """Detect prolonged customer engagement"""
        
        if dwell_time < engagement_threshold:
            return None

        # Calculate engagement score
        engagement_score = min(dwell_time / (engagement_threshold * 2), 1.0)

        event = RetailEvent(
            event_id=str(uuid.uuid4()),
            event_type=RetailEventType.PROLONGED_ENGAGEMENT.value,
            timestamp=timestamp,
            track_id=track_id,
            zone_id=zone_id,
            severity=EventSeverity.INFO,
            message=f"Prolonged engagement: Customer {track_id} in zone {zone_id} for {dwell_time:.1f}s",
            payload={
                'dwell_time': dwell_time,
                'engagement_score': engagement_score,
                'zone_id': zone_id
            },
            frame_index=frame_index
        )

        self.event_buffer.append(event)
        self.event_history.append(event)
        return event

    def detect_suspicious_behavior(
        self,
        track_id: int,
        anomaly_type: AnomalyType,
        confidence: float,
        zone_id: Optional[str],
        frame_index: int,
        timestamp: datetime,
        description: str = ""
    ) -> AnomalyEvent:
        """Detect suspicious behavior"""
        
        severity = EventSeverity.ALERT if confidence > 0.8 else EventSeverity.WARNING

        anomaly = AnomalyEvent(
            anomaly_id=str(uuid.uuid4()),
            track_id=track_id,
            anomaly_type=anomaly_type.value,
            confidence=confidence,
            timestamp=timestamp,
            zone_id=zone_id,
            description=description or f"Suspicious behavior detected: {anomaly_type.value}"
        )

        self.anomaly_buffer.append(anomaly)
        self.anomaly_history.append(anomaly)

        # Also create alert event
        event = RetailEvent(
            event_id=str(uuid.uuid4()),
            event_type=RetailEventType.SUSPICIOUS_BEHAVIOR.value,
            timestamp=timestamp,
            track_id=track_id,
            zone_id=zone_id,
            severity=severity,
            message=f"Alert: {description}",
            payload={
                'anomaly_id': anomaly.anomaly_id,
                'anomaly_type': anomaly_type.value,
                'confidence': confidence
            },
            frame_index=frame_index
        )

        self.event_buffer.append(event)
        self.event_history.append(event)

        logger.warning(f"Anomaly detected: track={track_id}, type={anomaly_type.value}, conf={confidence}")

        return anomaly

    def detect_crowd_event(
        self,
        zone_id: str,
        customer_count: int,
        frame_index: int,
        timestamp: datetime,
        crowd_threshold: int = 5
    ) -> Optional[RetailEvent]:
        """Detect crowd in zone"""
        
        if customer_count < crowd_threshold:
            return None

        # Determine density level
        if customer_count > crowd_threshold * 2:
            density = "high"
            severity = EventSeverity.ALERT
        elif customer_count > crowd_threshold:
            density = "medium"
            severity = EventSeverity.WARNING
        else:
            density = "low"
            severity = EventSeverity.INFO

        event = RetailEvent(
            event_id=str(uuid.uuid4()),
            event_type=RetailEventType.CROWD_DETECTED.value,
            timestamp=timestamp,
            zone_id=zone_id,
            severity=severity,
            message=f"Crowd detected in zone {zone_id}: {customer_count} customers ({density} density)",
            payload={
                'zone_id': zone_id,
                'customer_count': customer_count,
                'density_level': density
            },
            frame_index=frame_index
        )

        self.event_buffer.append(event)
        self.event_history.append(event)

        logger.info(f"Crowd event: zone={zone_id}, count={customer_count}, density={density}")

        return event

    def detect_rapid_zone_changes(
        self,
        track_id: int,
        previous_zones: Set[str],
        current_zones: Set[str],
        frame_index: int,
        timestamp: datetime,
        time_window: float = 1.0
    ) -> Optional[AnomalyEvent]:
        """Detect rapid zone changes (unusual movement patterns)"""
        
        changes = len(previous_zones.symmetric_difference(current_zones))
        
        if changes < 3:
            return None

        description = f"Rapid zone changes detected: {changes} zones"
        confidence = min(changes / 5, 1.0)

        anomaly = self.detect_suspicious_behavior(
            track_id=track_id,
            anomaly_type=AnomalyType.RAPID_ZONE_CHANGES,
            confidence=confidence,
            zone_id=None,
            frame_index=frame_index,
            timestamp=timestamp,
            description=description
        )

        return anomaly

    def detect_loitering(
        self,
        track_id: int,
        zone_id: str,
        dwell_time: float,
        loitering_threshold: float,
        frame_index: int,
        timestamp: datetime
    ) -> Optional[AnomalyEvent]:
        """Detect loitering behavior"""
        
        if dwell_time < loitering_threshold:
            return None

        confidence = min(dwell_time / (loitering_threshold * 2), 1.0)

        anomaly = self.detect_suspicious_behavior(
            track_id=track_id,
            anomaly_type=AnomalyType.LOITERING,
            confidence=confidence,
            zone_id=zone_id,
            frame_index=frame_index,
            timestamp=timestamp,
            description=f"Customer loitering in zone {zone_id} for {dwell_time:.0f}s"
        )

        return anomaly

    def buffer_event(self, event: RetailEvent):
        """Buffer an event"""
        self.event_buffer.append(event)
        self.event_history.append(event)

    def buffer_events(self, events: List[RetailEvent]):
        """Buffer multiple events"""
        for event in events:
            self.buffer_event(event)

    def should_flush_events(self) -> bool:
        """Check if should flush event buffer"""
        if not self.config.batch_events:
            return len(self.event_buffer) > 0

        return len(self.event_buffer) >= self.config.batch_size

    def flush_event_buffer(self) -> List[RetailEvent]:
        """Flush event buffer"""
        events = self.event_buffer.copy()
        self.event_buffer.clear()
        logger.debug(f"Flushed {len(events)} events")
        return events

    def flush_anomaly_buffer(self) -> List[AnomalyEvent]:
        """Flush anomaly buffer"""
        anomalies = self.anomaly_buffer.copy()
        self.anomaly_buffer.clear()
        return anomalies

    def get_zone_events(self, zone_id: str) -> List[RetailEvent]:
        """Get events for a zone"""
        return [e for e in self.event_history if e.zone_id == zone_id]

    def get_customer_events(self, track_id: int) -> List[RetailEvent]:
        """Get events for a customer"""
        return [e for e in self.event_history if e.track_id == track_id]

    def get_anomalies_for_customer(self, track_id: int) -> List[AnomalyEvent]:
        """Get anomalies for a customer"""
        return [a for a in self.anomaly_history if a.track_id == track_id]

    def get_recent_events(self, seconds: float = 60) -> List[RetailEvent]:
        """Get recent events"""
        cutoff = datetime.now().timestamp() - seconds
        return [
            e for e in self.event_history
            if e.timestamp.timestamp() > cutoff
        ]

    def get_statistics(self) -> Dict:
        """Get event statistics"""
        return {
            'total_events': len(self.event_history),
            'total_anomalies': len(self.anomaly_history),
            'buffered_events': len(self.event_buffer),
            'buffered_anomalies': len(self.anomaly_buffer),
            'event_types': self._count_event_types(),
            'anomaly_types': self._count_anomaly_types()
        }

    def _count_event_types(self) -> Dict[str, int]:
        """Count event types"""
        counts = defaultdict(int)
        for event in self.event_history:
            counts[event.event_type] += 1
        return dict(counts)

    def _count_anomaly_types(self) -> Dict[str, int]:
        """Count anomaly types"""
        counts = defaultdict(int)
        for anomaly in self.anomaly_history:
            counts[anomaly.anomaly_type] += 1
        return dict(counts)

    def reset(self):
        """Reset event system"""
        self.event_buffer.clear()
        self.anomaly_buffer.clear()
        self.event_history.clear()
        self.anomaly_history.clear()
        self.recent_zone_entries.clear()
        self.zone_interactions.clear()
        self.customer_zone_visits.clear()
        logger.info("Event intelligence reset")
