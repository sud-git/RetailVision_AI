"""
Zone Management Engine - Phase 3

Zone detection and tracking for shelf interactions and area monitoring.
"""

import logging
from typing import List, Optional, Dict, Tuple, Set
from collections import defaultdict
import json

from .models import (
    Zone, ZoneType, ZoneEvent, EventType, TrackingObject,
    Detection, DwellSession
)
from .exceptions import InvalidZoneException

logger = logging.getLogger(__name__)


class ZoneManager:
    """Manages detection zones and zone-based events"""
    
    def __init__(self):
        """Initialize zone manager"""
        self.zones: Dict[str, Zone] = {}
        self.track_in_zones: Dict[int, Set[str]] = defaultdict(set)
    
    def add_zone(self, zone: Zone) -> None:
        """
        Add a zone
        
        Args:
            zone: Zone object
            
        Raises:
            InvalidZoneException: Invalid zone
        """
        if not zone.zone_id:
            raise InvalidZoneException("Zone ID required")
        
        if len(zone.polygon) < 3:
            raise InvalidZoneException("Zone polygon must have at least 3 points")
        
        self.zones[zone.zone_id] = zone
        logger.info(f"Added zone: {zone.zone_id} ({zone.name})")
    
    def add_zones_from_config(self, zones_config: List[Dict]) -> None:
        """
        Add zones from configuration
        
        Args:
            zones_config: List of zone dictionaries
        """
        for zone_dict in zones_config:
            try:
                zone_type = ZoneType(zone_dict.get("type", "shelf"))
                polygon = zone_dict.get("polygon", [])
                
                zone = Zone(
                    zone_id=zone_dict.get("id", ""),
                    zone_type=zone_type,
                    name=zone_dict.get("name", ""),
                    polygon=polygon,
                    metadata=zone_dict.get("metadata", {})
                )
                self.add_zone(zone)
            except Exception as e:
                logger.warning(f"Failed to add zone: {e}")
    
    def get_zone(self, zone_id: str) -> Optional[Zone]:
        """Get zone by ID"""
        return self.zones.get(zone_id)
    
    def get_all_zones(self) -> List[Zone]:
        """Get all zones"""
        return list(self.zones.values())
    
    def check_point_in_zones(self, x: float, y: float) -> List[str]:
        """
        Find all zones containing a point
        
        Args:
            x, y: Point coordinates
            
        Returns:
            List of zone IDs containing the point
        """
        zones_containing = []
        for zone_id, zone in self.zones.items():
            if zone.contains_point(x, y):
                zones_containing.append(zone_id)
        return zones_containing
    
    def check_bbox_in_zones(self, x1: float, y1: float, x2: float, y2: float) -> Dict[str, float]:
        """
        Check zone overlap with bounding box
        
        Args:
            x1, y1, x2, y2: Bounding box coordinates
            
        Returns:
            Dict mapping zone_id to overlap percentage
        """
        bbox_area = (x2 - x1) * (y2 - y1)
        if bbox_area == 0:
            return {}
        
        overlaps = {}
        
        for zone_id, zone in self.zones.items():
            # Check if bbox overlaps with zone bounds
            overlap_x1 = max(x1, zone.min_x)
            overlap_y1 = max(y1, zone.min_y)
            overlap_x2 = min(x2, zone.max_x)
            overlap_y2 = min(y2, zone.max_y)
            
            if overlap_x2 > overlap_x1 and overlap_y2 > overlap_y1:
                overlap_area = (overlap_x2 - overlap_x1) * (overlap_y2 - overlap_y1)
                overlap_pct = overlap_area / bbox_area
                overlaps[zone_id] = overlap_pct
        
        return overlaps
    
    def update_track_zones(
        self,
        track_id: int,
        detected_zones: Set[str]
    ) -> List[ZoneEvent]:
        """
        Update zone occupancy for track and generate events
        
        Args:
            track_id: Tracking object ID
            detected_zones: Set of zone IDs containing track
            
        Returns:
            List of zone entry/exit events
        """
        events = []
        
        previous_zones = self.track_in_zones.get(track_id, set())
        current_zones = detected_zones
        
        # Check for zone entries
        for zone_id in current_zones - previous_zones:
            events.append((zone_id, EventType.ZONE_ENTER))
        
        # Check for zone exits
        for zone_id in previous_zones - current_zones:
            events.append((zone_id, EventType.ZONE_EXIT))
        
        # Update tracking
        self.track_in_zones[track_id] = current_zones
        
        return events
    
    def get_zones_for_track(self, track_id: int) -> Set[str]:
        """Get zones currently containing track"""
        return self.track_in_zones.get(track_id, set())


class DwellTimeTracker:
    """Track dwell time in zones"""
    
    def __init__(self, threshold_seconds: float = 2.0):
        """
        Initialize dwell tracker
        
        Args:
            threshold_seconds: Minimum dwell time to report
        """
        self.threshold_seconds = threshold_seconds
        self.active_sessions: Dict[Tuple[int, str], DwellSession] = {}
        self.completed_sessions: List[DwellSession] = []
    
    def update(
        self,
        track_id: int,
        zones: Set[str],
        frame_index: int,
        timestamp: float
    ) -> List[Tuple[int, str, EventType]]:
        """
        Update dwell tracking
        
        Args:
            track_id: Tracking object ID
            zones: Set of zone IDs containing track
            frame_index: Current frame
            timestamp: Current timestamp
            
        Returns:
            List of (track_id, zone_id, event_type) tuples
        """
        events = []
        
        # Start new sessions for zones
        for zone_id in zones:
            key = (track_id, zone_id)
            if key not in self.active_sessions:
                session = DwellSession(
                    track_id=track_id,
                    zone_id=zone_id,
                    start_frame=frame_index,
                    start_timestamp=timestamp
                )
                self.active_sessions[key] = session
                events.append((track_id, zone_id, EventType.DWELL_START))
        
        # End sessions for zones exited
        for (tid, zid) in list(self.active_sessions.keys()):
            if tid == track_id and zid not in zones:
                session = self.active_sessions.pop((tid, zid))
                session.end_session(frame_index, timestamp)
                
                if session.duration_seconds >= self.threshold_seconds:
                    self.completed_sessions.append(session)
                    events.append((track_id, zid, EventType.DWELL_END))
                else:
                    events.append((track_id, zid, EventType.DWELL_END))
        
        return events
    
    def get_dwell_duration(self, track_id: int, zone_id: str) -> Optional[float]:
        """Get current dwell duration in zone"""
        session = self.active_sessions.get((track_id, zone_id))
        if session:
            return session.duration_seconds
        return None
    
    def get_active_sessions(self) -> List[DwellSession]:
        """Get all active dwell sessions"""
        return list(self.active_sessions.values())
    
    def cleanup_inactive(self, current_timestamp: float, timeout_seconds: float = 60) -> None:
        """
        Clean up inactive sessions
        
        Args:
            current_timestamp: Current timestamp
            timeout_seconds: Timeout for inactive sessions
        """
        keys_to_remove = []
        for key, session in self.active_sessions.items():
            if current_timestamp - session.start_timestamp > timeout_seconds:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            session = self.active_sessions.pop(key)
            if session.duration_seconds >= self.threshold_seconds:
                self.completed_sessions.append(session)


class InteractionDetector:
    """Detect customer-shelf interactions"""
    
    def __init__(self):
        """Initialize interaction detector"""
        self.interaction_history: Dict[int, List[Dict]] = defaultdict(list)
    
    def detect_interaction(
        self,
        track_id: int,
        zones: Set[str],
        frame_index: int,
        timestamp: float
    ) -> List[Dict]:
        """
        Detect interactions (pickup, shelf browsing, etc.)
        
        Args:
            track_id: Tracking object ID
            zones: Zones containing track
            frame_index: Frame number
            timestamp: Timestamp
            
        Returns:
            List of detected interactions
        """
        interactions = []
        
        # For now, any presence in shelf zone is an interaction
        if zones:
            interaction = {
                "type": "shelf_presence",
                "track_id": track_id,
                "zones": list(zones),
                "frame": frame_index,
                "timestamp": timestamp
            }
            self.interaction_history[track_id].append(interaction)
            interactions.append(interaction)
        
        return interactions
    
    def get_interaction_history(self, track_id: int) -> List[Dict]:
        """Get interaction history for track"""
        return self.interaction_history.get(track_id, [])
