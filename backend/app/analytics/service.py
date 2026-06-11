"""
Phase 4: Analytics & Event Orchestration Service

Coordinates interaction detection, dwell analytics, event intelligence, and metrics.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass

from ..interactions import InteractionDetector
from .dwell_analytics import DwellAnalytics
from .metrics_engine import AnalyticsMetricsEngine
from .models import AnalyticsConfig
from ..events import RetailEventIntelligence, RedisEventPublisher
from ..detection.models import TrackingObject

logger = logging.getLogger(__name__)


@dataclass
class Phase4Config:
    """Phase 4 Configuration"""
    config: AnalyticsConfig
    redis_url: str = "redis://localhost:6379"
    enable_redis: bool = True


class Phase4Service:
    """Main service orchestrating Phase 4 analytics"""

    def __init__(self, config: Phase4Config):
        """Initialize Phase 4 service"""
        self.config = config
        
        # Initialize components
        self.interaction_detector = InteractionDetector(config.config.interaction)
        self.dwell_analytics = DwellAnalytics(config.config.dwell_analytics)
        self.event_intelligence = RetailEventIntelligence(config.config.event_publishing)
        self.metrics_engine = AnalyticsMetricsEngine(self.interaction_detector, self.dwell_analytics)
        
        # Initialize Redis publisher
        self.redis_publisher: Optional[RedisEventPublisher] = None
        if config.enable_redis:
            self.redis_publisher = RedisEventPublisher(config.redis_url)
        
        # Statistics
        self.statistics = {
            'frames_processed': 0,
            'detections_processed': 0,
            'interactions_detected': 0,
            'events_published': 0,
            'anomalies_detected': 0
        }
        
        logger.info("Phase 4 Service initialized")

    async def initialize(self):
        """Initialize service"""
        if self.redis_publisher:
            await self.redis_publisher.connect()
        logger.info("Phase 4 Service initialized")

    async def shutdown(self):
        """Shutdown service"""
        if self.redis_publisher:
            await self.redis_publisher.disconnect()
        logger.info("Phase 4 Service shutdown")

    async def process_frame(
        self,
        frame_index: int,
        timestamp: datetime,
        active_tracks: Dict[int, Set[str]],  # track_id -> set of zone_ids
        track_bboxes: Dict[int, tuple]  # track_id -> (x, y) center
    ) -> Dict:
        """
        Process a frame with Phase 4 analytics
        
        Args:
            frame_index: Current frame number
            timestamp: Frame timestamp
            active_tracks: Active tracks and their zones
            track_bboxes: Track bounding box centers
            
        Returns:
            Processing results
        """
        
        self.statistics['frames_processed'] += 1
        
        # Track previous zones
        previous_zones = self._get_previous_zones(active_tracks.keys())
        
        # Process each track
        for track_id, current_zones in active_tracks.items():
            bbox_center = track_bboxes.get(track_id, (0, 0))
            prev_zones = previous_zones.get(track_id, set())
            
            # Detect interactions
            interactions = self.interaction_detector.detect_interactions(
                track_id=track_id,
                current_zones=current_zones,
                previous_zones=prev_zones,
                bbox_center=bbox_center,
                frame_index=frame_index,
                timestamp=timestamp
            )
            
            self.statistics['interactions_detected'] += len(interactions)
            
            # Update customer profile
            profile = self.interaction_detector.update_customer_profile(
                track_id=track_id,
                interactions=interactions,
                timestamp=timestamp
            )
            
            # Process interactions for events
            if interactions:
                await self._process_interactions(
                    track_id, interactions, frame_index, timestamp
                )
            
            # Check for anomalies
            if profile:
                await self._check_anomalies(profile, frame_index, timestamp)
        
        # Check for crowd events
        await self._check_crowd_events(active_tracks, frame_index, timestamp)
        
        # Cleanup inactive sessions
        self.interaction_detector.cleanup_inactive_sessions(timestamp)
        self.interaction_detector.cleanup_old_profiles(timestamp)
        
        # Flush events to Redis if needed
        if self.event_intelligence.should_flush_events():
            await self._publish_events()
        
        return {
            'frame_index': frame_index,
            'interactions_detected': len(interactions),
            'events_buffered': len(self.event_intelligence.event_buffer),
            'anomalies_buffered': len(self.event_intelligence.anomaly_buffer)
        }

    async def _process_interactions(
        self,
        track_id: int,
        interactions: List,
        frame_index: int,
        timestamp: datetime
    ):
        """Process interactions and generate events"""
        
        for interaction in interactions:
            # Publish interaction event
            await self.redis_publisher.publish_interaction(
                track_id=track_id,
                zone_id=interaction.zone_id,
                interaction_type=interaction.interaction_type.value,
                timestamp=timestamp,
                duration=interaction.duration_seconds,
                confidence=interaction.confidence
            ) if self.redis_publisher else None
            
            # Check for prolonged engagement
            if interaction.duration_seconds > self.config.config.interaction.min_engagement_duration:
                event = self.event_intelligence.detect_prolonged_engagement(
                    track_id=track_id,
                    zone_id=interaction.zone_id,
                    dwell_time=interaction.duration_seconds,
                    engagement_threshold=self.config.config.interaction.min_engagement_duration,
                    frame_index=frame_index,
                    timestamp=timestamp
                )
                if event:
                    self.statistics['events_published'] += 1

    async def _check_anomalies(
        self,
        profile,
        frame_index: int,
        timestamp: datetime
    ):
        """Check for anomalous behavior"""
        
        for anomaly_flag in profile.anomaly_flags:
            # Publish anomaly
            anomaly = self.event_intelligence.detect_suspicious_behavior(
                track_id=profile.track_id,
                anomaly_type=anomaly_flag,
                confidence=0.7,
                zone_id=None,
                frame_index=frame_index,
                timestamp=timestamp,
                description=f"Anomaly detected: {anomaly_flag}"
            )
            
            if self.redis_publisher:
                await self.redis_publisher.publish_anomaly(
                    track_id=profile.track_id,
                    anomaly_type=anomaly_flag,
                    confidence=0.7,
                    timestamp=timestamp,
                    description=anomaly.description
                )
            
            self.statistics['anomalies_detected'] += 1

    async def _check_crowd_events(
        self,
        active_tracks: Dict[int, Set[str]],
        frame_index: int,
        timestamp: datetime
    ):
        """Check for crowd events"""
        
        # Count customers per zone
        zone_counts = {}
        for track_id, zones in active_tracks.items():
            for zone_id in zones:
                zone_counts[zone_id] = zone_counts.get(zone_id, 0) + 1
        
        # Detect crowd events
        for zone_id, count in zone_counts.items():
            event = self.event_intelligence.detect_crowd_event(
                zone_id=zone_id,
                customer_count=count,
                frame_index=frame_index,
                timestamp=timestamp,
                crowd_threshold=self.config.config.interaction.crowd_threshold
            )
            
            if event and self.redis_publisher:
                await self.redis_publisher.publish_crowd_event(
                    zone_id=zone_id,
                    customer_count=count,
                    density_level=event.payload.get('density_level', 'unknown'),
                    timestamp=timestamp
                )

    async def _publish_events(self):
        """Publish buffered events to Redis"""
        
        if not self.redis_publisher:
            return
        
        # Flush event buffer
        events = self.event_intelligence.flush_event_buffer()
        if events:
            published = await self.redis_publisher.publish_batch(
                [e.to_dict() for e in events],
                'interaction'
            )
            self.statistics['events_published'] += published
            logger.debug(f"Published {published} events")
        
        # Flush anomalies
        anomalies = self.event_intelligence.flush_anomaly_buffer()
        if anomalies:
            published = await self.redis_publisher.publish_batch(
                [a.to_dict() for a in anomalies],
                'anomaly'
            )
            self.statistics['anomalies_detected'] += published

    def _get_previous_zones(self, current_track_ids) -> Dict[int, Set[str]]:
        """Get previous zone assignments"""
        previous = {}
        for track_id in current_track_ids:
            profile = self.interaction_detector.get_profile(track_id)
            if profile:
                previous[track_id] = profile.total_zones_visited
            else:
                previous[track_id] = set()
        return previous

    def record_dwell_session(self, track_id: int, zone_id: str, session):
        """Record completed dwell session"""
        
        self.dwell_analytics.record_dwell_session(
            track_id=track_id,
            zone_id=zone_id,
            session=session,
            timestamp=datetime.now()
        )

    def get_analytics(self) -> Dict:
        """Get analytics snapshot"""
        
        return {
            'store_metrics': self.metrics_engine.compute_store_metrics().dict(),
            'customer_segments': self.metrics_engine.get_customer_segments(),
            'top_zones': [
                {'zone': z, 'avg_dwell': t}
                for z, t in self.metrics_engine.get_top_engaged_zones(top_n=5)
            ],
            'movement_patterns': self.metrics_engine.get_movement_patterns(),
            'crowd_analysis': self.metrics_engine.get_crowd_analysis()
        }

    def get_statistics(self) -> Dict:
        """Get service statistics"""
        
        return {
            **self.statistics,
            'active_customers': len(self.interaction_detector.customer_profiles),
            'total_interactions_recorded': len(self.interaction_detector.interaction_history),
            'active_sessions': sum(
                len([s for s in sessions.values() if s.exit_time is None])
                for sessions in self.interaction_detector.zone_sessions.values()
            ),
            'event_buffer_size': len(self.event_intelligence.event_buffer),
            'anomaly_buffer_size': len(self.event_intelligence.anomaly_buffer),
            'event_history_size': len(self.event_intelligence.event_history),
            'anomaly_history_size': len(self.event_intelligence.anomaly_history),
            'redis_connected': self.redis_publisher.connected if self.redis_publisher else False
        }

    def reset(self):
        """Reset service"""
        self.interaction_detector.cleanup_old_profiles(datetime.now(), timeout_seconds=0)
        self.dwell_analytics.reset_analytics()
        self.event_intelligence.reset()
        self.metrics_engine.reset()
        self.statistics = {k: 0 for k in self.statistics.keys()}
        logger.info("Phase 4 Service reset")


# Global service instance
_phase4_service: Optional[Phase4Service] = None


async def get_phase4_service() -> Phase4Service:
    """Get or create Phase 4 service"""
    global _phase4_service
    if _phase4_service is None:
        raise RuntimeError("Phase 4 service not initialized")
    return _phase4_service


async def initialize_phase4_service(config: Phase4Config):
    """Initialize Phase 4 service"""
    global _phase4_service
    _phase4_service = Phase4Service(config)
    await _phase4_service.initialize()
    return _phase4_service


async def shutdown_phase4_service():
    """Shutdown Phase 4 service"""
    global _phase4_service
    if _phase4_service:
        await _phase4_service.shutdown()
        _phase4_service = None
