"""
Phase 4: Interaction Detection Engine

Detects customer-shelf interactions and engagement patterns.
"""

import logging
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import uuid

from ..analytics.models import (
    CustomerInteraction, InteractionType, ShelfZone, CustomerProfile,
    CustomerBehavior, InteractionConfig, ZoneDwellSession
)

logger = logging.getLogger(__name__)


class InteractionDetector:
    """Detects and tracks customer-shelf interactions"""

    def __init__(self, config: InteractionConfig):
        """Initialize detector"""
        self.config = config
        self.active_interactions: Dict[str, CustomerInteraction] = {}
        self.customer_profiles: Dict[int, CustomerProfile] = {}
        self.zone_sessions: Dict[str, Dict[int, ZoneDwellSession]] = {}  # zone_id -> {track_id -> session}
        self.interaction_history: List[CustomerInteraction] = []

    def detect_interactions(
        self,
        track_id: int,
        current_zones: Set[str],
        previous_zones: Set[str],
        bbox_center: tuple,
        frame_index: int,
        timestamp: datetime
    ) -> List[CustomerInteraction]:
        """
        Detect interactions between customer and zones
        
        Args:
            track_id: Customer track ID
            current_zones: Zones customer is currently in
            previous_zones: Zones from previous frame
            bbox_center: Bounding box center (x, y)
            frame_index: Current frame index
            timestamp: Current timestamp
            
        Returns:
            List of detected interactions
        """
        interactions = []

        # Track entry/exit events
        entered_zones = current_zones - previous_zones
        exited_zones = previous_zones - current_zones

        for zone_id in entered_zones:
            # Zone entry event
            interaction = CustomerInteraction(
                interaction_id=str(uuid.uuid4()),
                track_id=track_id,
                zone_id=zone_id,
                interaction_type=InteractionType.ZONE_ENTRY,
                timestamp=timestamp,
                duration_seconds=0.0,
                intensity=0.5,
                position=bbox_center,
                frame_index=frame_index
            )
            interactions.append(interaction)

            # Start dwell session
            self._start_dwell_session(track_id, zone_id, frame_index, timestamp)

            logger.debug(f"Track {track_id} entered zone {zone_id}")

        for zone_id in exited_zones:
            # Zone exit event
            interaction = CustomerInteraction(
                interaction_id=str(uuid.uuid4()),
                track_id=track_id,
                zone_id=zone_id,
                interaction_type=InteractionType.ZONE_EXIT,
                timestamp=timestamp,
                duration_seconds=0.0,
                intensity=0.2,
                position=bbox_center,
                frame_index=frame_index
            )
            interactions.append(interaction)

            # End dwell session
            self._end_dwell_session(track_id, zone_id, frame_index, timestamp)

            logger.debug(f"Track {track_id} exited zone {zone_id}")

        # Detect prolonged engagement
        for zone_id in current_zones:
            session = self._get_dwell_session(track_id, zone_id)
            if session:
                duration = (timestamp - session.entry_time).total_seconds()

                # Check for engagement types
                if duration > self.config.min_comparing_duration:
                    interaction = CustomerInteraction(
                        interaction_id=str(uuid.uuid4()),
                        track_id=track_id,
                        zone_id=zone_id,
                        interaction_type=InteractionType.COMPARE,
                        timestamp=timestamp,
                        duration_seconds=duration,
                        intensity=0.8,
                        position=bbox_center,
                        frame_index=frame_index,
                        confidence=0.9
                    )
                    interactions.append(interaction)

                elif duration > self.config.min_engagement_duration:
                    interaction = CustomerInteraction(
                        interaction_id=str(uuid.uuid4()),
                        track_id=track_id,
                        zone_id=zone_id,
                        interaction_type=InteractionType.ENGAGEMENT,
                        timestamp=timestamp,
                        duration_seconds=duration,
                        intensity=0.7,
                        position=bbox_center,
                        frame_index=frame_index
                    )
                    interactions.append(interaction)

        return interactions

    def update_customer_profile(
        self,
        track_id: int,
        interactions: List[CustomerInteraction],
        timestamp: datetime
    ) -> Optional[CustomerProfile]:
        """Update customer profile with new interactions"""

        # Create profile if needed
        if track_id not in self.customer_profiles:
            self.customer_profiles[track_id] = CustomerProfile(
                track_id=track_id,
                first_seen=timestamp,
                last_seen=timestamp
            )

        profile = self.customer_profiles[track_id]
        profile.last_seen = timestamp

        # Add interactions
        for interaction in interactions:
            profile.add_interaction(interaction)
            self.interaction_history.append(interaction)

            # Update dwell sessions
            if interaction.zone_id in self.zone_sessions:
                sessions = self.zone_sessions[interaction.zone_id]
                if track_id in sessions:
                    session = sessions[track_id]
                    session.interaction_count += 1
                    session.intensity_sum += interaction.intensity

        # Classify behavior
        profile.behavior_classification = self._classify_behavior(profile)

        # Detect anomalies
        profile.anomaly_flags = self._detect_anomalies(profile)

        return profile

    def _start_dwell_session(
        self,
        track_id: int,
        zone_id: str,
        frame_index: int,
        timestamp: datetime
    ):
        """Start a dwell session"""
        if zone_id not in self.zone_sessions:
            self.zone_sessions[zone_id] = {}

        session = ZoneDwellSession(
            session_id=str(uuid.uuid4()),
            track_id=track_id,
            zone_id=zone_id,
            entry_time=timestamp,
            entry_frame=frame_index
        )

        self.zone_sessions[zone_id][track_id] = session

    def _end_dwell_session(
        self,
        track_id: int,
        zone_id: str,
        frame_index: int,
        timestamp: datetime
    ):
        """End a dwell session"""
        if zone_id in self.zone_sessions and track_id in self.zone_sessions[zone_id]:
            session = self.zone_sessions[zone_id][track_id]
            session.exit_time = timestamp
            session.exit_frame = frame_index

    def _get_dwell_session(
        self,
        track_id: int,
        zone_id: str
    ) -> Optional[ZoneDwellSession]:
        """Get active dwell session"""
        if zone_id in self.zone_sessions and track_id in self.zone_sessions[zone_id]:
            session = self.zone_sessions[zone_id][track_id]
            if session.exit_time is None:
                return session
        return None

    def _classify_behavior(self, profile: CustomerProfile) -> CustomerBehavior:
        """Classify customer behavior"""
        if len(profile.interactions) == 0:
            return CustomerBehavior.BROWSING

        # Analyze interaction patterns
        avg_duration = profile.total_dwell_time / len(profile.total_zones_visited)
        interaction_intensity = sum(i.intensity for i in profile.interactions[-10:]) / min(10, len(profile.interactions))

        if avg_duration > self.config.min_comparing_duration:
            return CustomerBehavior.COMPARING

        if interaction_intensity > 0.8:
            return CustomerBehavior.PURCHASING

        if len(profile.anomaly_flags) > 0:
            return CustomerBehavior.SUSPICIOUS

        return CustomerBehavior.BROWSING

    def _detect_anomalies(self, profile: CustomerProfile) -> List[str]:
        """Detect anomalous behavior"""
        anomalies = []

        # Loitering detection
        if profile.duration_in_store > 600 and len(profile.total_zones_visited) < 3:
            anomalies.append("extended_loitering")

        # Suspicious pattern
        if len(profile.interactions) > 20 and profile.total_dwell_time < 60:
            anomalies.append("suspicious_browsing_pattern")

        # Repeated zone visits
        zone_visit_counts = {}
        for interaction in profile.interactions:
            zone_visit_counts[interaction.zone_id] = zone_visit_counts.get(interaction.zone_id, 0) + 1

        for zone_id, count in zone_visit_counts.items():
            if count > 10:
                anomalies.append(f"excessive_zone_visits_{zone_id}")

        return anomalies

    def get_profile(self, track_id: int) -> Optional[CustomerProfile]:
        """Get customer profile"""
        return self.customer_profiles.get(track_id)

    def get_zone_sessions(self, zone_id: str) -> Dict[int, ZoneDwellSession]:
        """Get all sessions in a zone"""
        return self.zone_sessions.get(zone_id, {})

    def get_active_sessions(self) -> Dict[str, Dict[int, ZoneDwellSession]]:
        """Get all active dwell sessions"""
        active = {}
        for zone_id, sessions in self.zone_sessions.items():
            active_in_zone = {
                track_id: session
                for track_id, session in sessions.items()
                if session.exit_time is None
            }
            if active_in_zone:
                active[zone_id] = active_in_zone
        return active

    def cleanup_inactive_sessions(self, timestamp: datetime, timeout_seconds: float = 60):
        """Remove inactive sessions"""
        for zone_id, sessions in list(self.zone_sessions.items()):
            for track_id, session in list(sessions.items()):
                if session.exit_time:
                    age = (timestamp - session.exit_time).total_seconds()
                    if age > timeout_seconds:
                        del sessions[track_id]
            
            if not sessions:
                del self.zone_sessions[zone_id]

    def cleanup_old_profiles(self, timestamp: datetime, timeout_seconds: float = 300):
        """Remove old customer profiles"""
        to_remove = []
        for track_id, profile in self.customer_profiles.items():
            age = (timestamp - profile.last_seen).total_seconds()
            if age > timeout_seconds:
                to_remove.append(track_id)

        for track_id in to_remove:
            del self.customer_profiles[track_id]

    def get_statistics(self) -> Dict:
        """Get statistics"""
        return {
            'total_customers': len(self.customer_profiles),
            'active_interactions': len(self.active_interactions),
            'total_interactions_recorded': len(self.interaction_history),
            'active_sessions': sum(
                len([s for s in sessions.values() if s.exit_time is None])
                for sessions in self.zone_sessions.values()
            ),
            'anomalies_detected': sum(
                len(p.anomaly_flags)
                for p in self.customer_profiles.values()
            )
        }
