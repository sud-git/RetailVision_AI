"""
Phase 8: AI-Powered Anomaly Detection Engine
Advanced retail anomaly detection with multiple detector types

Detectors:
- LoiteringDetector: Customers staying beyond configurable thresholds
- CrowdDetector: Zone occupancy and overcrowding detection
- SuspiciousBehaviorDetector: Unusual movement and interaction patterns
- AbandonedObjectDetector: Stationary objects and left-behind items
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import math
import numpy as np
from abc import ABC, abstractmethod

# ==================== ENUMS ====================

class AnomalyType(str, Enum):
    """Types of detected anomalies"""
    LOITERING = "loitering"
    CROWD = "crowd"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    ABANDONED_OBJECT = "abandoned_object"
    UNUSUAL_PATH = "unusual_path"
    RAPID_ZONE_SWITCH = "rapid_zone_switch"
    RESTRICTED_AREA_ACCESS = "restricted_area_access"


class AnomalySeverity(str, Enum):
    """Anomaly severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyStatus(str, Enum):
    """Anomaly lifecycle states"""
    DETECTED = "detected"
    ONGOING = "ongoing"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


# ==================== DATA CLASSES ====================

@dataclass
class CustomerSnapshot:
    """Snapshot of customer state at a point in time"""
    customer_id: str
    timestamp: datetime
    zone_id: int
    x: float
    y: float
    dwell_time: int = 0  # milliseconds in current zone
    interaction_count: int = 0
    total_interactions: int = 0
    zones_visited: List[int] = field(default_factory=list)
    speed: float = 0.0
    direction: float = 0.0  # radians
    is_stationary: bool = False


@dataclass
class Anomaly:
    """Detected anomaly record"""
    id: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    customer_id: Optional[str]
    zone_id: int
    title: str
    description: str
    confidence_score: float  # 0.0-1.0
    details: Dict = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    status: AnomalyStatus = AnomalyStatus.DETECTED


@dataclass
class ZoneProfile:
    """Dynamic zone characteristics for anomaly detection"""
    zone_id: int
    normal_occupancy: int = 5  # Expected visitors
    max_occupancy: int = 20     # Threshold for overcrowding
    normal_dwell_time: int = 60  # Seconds
    max_dwell_time: int = 300   # Loitering threshold
    interaction_threshold: int = 3  # For suspicious behavior
    zone_type: str = "general"  # high_value, checkout, entrance, restricted
    is_restricted: bool = False


# ==================== ABSTRACT BASE DETECTOR ====================

class AnomalyDetector(ABC):
    """Base class for anomaly detectors"""
    
    def __init__(self):
        self.detected_anomalies: Dict[str, Anomaly] = {}
        self.history: deque = deque(maxlen=1000)
    
    @abstractmethod
    async def detect(self, data: Dict) -> List[Anomaly]:
        """Detect anomalies from input data"""
        pass
    
    def record_anomaly(self, anomaly: Anomaly) -> None:
        """Record detected anomaly"""
        self.detected_anomalies[anomaly.id] = anomaly
        self.history.append(anomaly)
    
    def resolve_anomaly(self, anomaly_id: str) -> None:
        """Mark anomaly as resolved"""
        if anomaly_id in self.detected_anomalies:
            anomaly = self.detected_anomalies[anomaly_id]
            anomaly.status = AnomalyStatus.RESOLVED
            anomaly.resolved_at = datetime.utcnow()


# ==================== LOITERING DETECTOR ====================

class LoiteringDetector(AnomalyDetector):
    """Detect customers loitering in zones beyond thresholds"""
    
    def __init__(self):
        super().__init__()
        self.customer_zone_entries: Dict[str, Dict] = {}  # {customer_id: {zone_id: entry_time}}
        self.zone_profiles: Dict[int, ZoneProfile] = {}
        self.loitering_alerts: Set[str] = set()
    
    def register_zone_profile(self, profile: ZoneProfile) -> None:
        """Register zone-specific loitering threshold"""
        self.zone_profiles[profile.zone_id] = profile
    
    async def detect(self, data: Dict) -> List[Anomaly]:
        """
        Detect loitering behavior
        
        Input: {
            'customers': [{'customer_id', 'zone_id', 'timestamp', 'dwell_time'}, ...],
            'zone_profiles': {zone_id: ZoneProfile, ...}
        }
        """
        anomalies = []
        customers = data.get('customers', [])
        current_time = datetime.utcnow()
        
        for customer in customers:
            customer_id = customer['customer_id']
            zone_id = customer['zone_id']
            dwell_time = customer.get('dwell_time', 0)
            
            # Get zone threshold
            profile = self.zone_profiles.get(
                zone_id,
                ZoneProfile(zone_id=zone_id)
            )
            
            # Check if customer exceeded dwell threshold
            if dwell_time > profile.max_dwell_time * 1000:  # Convert to milliseconds
                anomaly_id = f"loiter_{customer_id}_{zone_id}"
                
                if anomaly_id not in self.loitering_alerts:
                    # NEW loitering detection
                    severity = self._calculate_severity(dwell_time, profile.max_dwell_time)
                    confidence = self._calculate_confidence(dwell_time, profile)
                    
                    anomaly = Anomaly(
                        id=anomaly_id,
                        anomaly_type=AnomalyType.LOITERING,
                        severity=severity,
                        customer_id=customer_id,
                        zone_id=zone_id,
                        title=f"Loitering: Customer {customer_id} in Zone {zone_id}",
                        description=f"Customer has been in zone {zone_id} for {dwell_time/1000:.0f}s (threshold: {profile.max_dwell_time}s)",
                        confidence_score=confidence,
                        details={
                            'dwell_time_ms': dwell_time,
                            'threshold_ms': profile.max_dwell_time * 1000,
                            'zone_type': profile.zone_type
                        }
                    )
                    anomalies.append(anomaly)
                    self.record_anomaly(anomaly)
                    self.loitering_alerts.add(anomaly_id)
                else:
                    # UPDATE ongoing loitering
                    existing = self.detected_anomalies.get(anomaly_id)
                    if existing and existing.status != AnomalyStatus.RESOLVED:
                        existing.status = AnomalyStatus.ONGOING
                        existing.updated_at = current_time
                        existing.details['current_dwell_time_ms'] = dwell_time
            else:
                # Customer left zone or under threshold
                anomaly_id = f"loiter_{customer_id}_{zone_id}"
                if anomaly_id in self.loitering_alerts:
                    self.resolve_anomaly(anomaly_id)
                    self.loitering_alerts.discard(anomaly_id)
        
        return anomalies
    
    def _calculate_severity(self, dwell_time: int, threshold: int) -> AnomalySeverity:
        """Calculate severity based on dwell time excess"""
        ratio = dwell_time / (threshold * 1000)
        
        if ratio > 3.0:
            return AnomalySeverity.CRITICAL
        elif ratio > 2.0:
            return AnomalySeverity.HIGH
        elif ratio > 1.5:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def _calculate_confidence(self, dwell_time: int, profile: ZoneProfile) -> float:
        """Calculate detection confidence"""
        # Higher confidence if well above threshold
        ratio = dwell_time / (profile.max_dwell_time * 1000)
        confidence = min(0.95, 0.5 + (ratio * 0.15))  # 0.5-0.95
        return confidence


# ==================== CROWD DETECTOR ====================

class CrowdDetector(AnomalyDetector):
    """Detect overcrowded zones and congestion"""
    
    def __init__(self):
        super().__init__()
        self.zone_occupancy: Dict[int, deque] = defaultdict(lambda: deque(maxlen=60))  # 60 second history
        self.zone_profiles: Dict[int, ZoneProfile] = {}
        self.crowd_alerts: Set[int] = set()
    
    def register_zone_profile(self, profile: ZoneProfile) -> None:
        """Register zone occupancy threshold"""
        self.zone_profiles[profile.zone_id] = profile
    
    async def detect(self, data: Dict) -> List[Anomaly]:
        """
        Detect crowd/overcrowding
        
        Input: {
            'zone_occupancies': {zone_id: current_visitor_count, ...}
        }
        """
        anomalies = []
        zone_occupancies = data.get('zone_occupancies', {})
        
        for zone_id, occupancy in zone_occupancies.items():
            # Get zone threshold
            profile = self.zone_profiles.get(
                zone_id,
                ZoneProfile(zone_id=zone_id, max_occupancy=20)
            )
            
            # Record occupancy
            self.zone_occupancy[zone_id].append(occupancy)
            
            # Check if overcrowded
            if occupancy > profile.max_occupancy:
                if zone_id not in self.crowd_alerts:
                    # NEW crowd detection
                    severity = self._calculate_severity(occupancy, profile)
                    confidence = self._calculate_confidence(occupancy, profile)
                    
                    anomaly = Anomaly(
                        id=f"crowd_{zone_id}",
                        anomaly_type=AnomalyType.CROWD,
                        severity=severity,
                        customer_id=None,
                        zone_id=zone_id,
                        title=f"Crowd Alert: Zone {zone_id}",
                        description=f"Zone {zone_id} has {occupancy} visitors (threshold: {profile.max_occupancy})",
                        confidence_score=confidence,
                        details={
                            'current_occupancy': occupancy,
                            'max_threshold': profile.max_occupancy,
                            'normal_occupancy': profile.normal_occupancy
                        }
                    )
                    anomalies.append(anomaly)
                    self.record_anomaly(anomaly)
                    self.crowd_alerts.add(zone_id)
                else:
                    # UPDATE ongoing crowd alert
                    existing = self.detected_anomalies.get(f"crowd_{zone_id}")
                    if existing:
                        existing.status = AnomalyStatus.ONGOING
                        existing.updated_at = datetime.utcnow()
                        existing.details['current_occupancy'] = occupancy
            else:
                # Zone no longer overcrowded
                if zone_id in self.crowd_alerts:
                    self.resolve_anomaly(f"crowd_{zone_id}")
                    self.crowd_alerts.discard(zone_id)
        
        return anomalies
    
    def _calculate_severity(self, occupancy: int, profile: ZoneProfile) -> AnomalySeverity:
        """Calculate severity based on occupancy"""
        ratio = occupancy / profile.max_occupancy
        
        if ratio > 2.0:
            return AnomalySeverity.CRITICAL
        elif ratio > 1.5:
            return AnomalySeverity.HIGH
        elif ratio > 1.2:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def _calculate_confidence(self, occupancy: int, profile: ZoneProfile) -> float:
        """Calculate detection confidence"""
        ratio = occupancy / profile.max_occupancy
        confidence = min(0.98, 0.6 + (ratio * 0.2))  # 0.6-0.98
        return confidence


# ==================== SUSPICIOUS BEHAVIOR DETECTOR ====================

class SuspiciousBehaviorDetector(AnomalyDetector):
    """Detect suspicious customer behaviors"""
    
    def __init__(self):
        super().__init__()
        self.customer_profiles: Dict[str, Dict] = {}  # {customer_id: behavior_data}
        self.interaction_threshold = 5
        self.rapid_switch_threshold = 3  # zones in N seconds
        self.restricted_zones = set()
    
    def set_restricted_zones(self, zone_ids: List[int]) -> None:
        """Register restricted access zones"""
        self.restricted_zones = set(zone_ids)
    
    async def detect(self, data: Dict) -> List[Anomaly]:
        """
        Detect suspicious behaviors:
        - Repeated shelf interactions
        - Rapid zone switching
        - Unusual movement patterns
        - Restricted area access
        
        Input: {
            'customers': [CustomerSnapshot, ...],
            'interaction_history': {customer_id: [(zone_id, interaction_count, timestamp), ...], ...}
        }
        """
        anomalies = []
        customers = data.get('customers', [])
        interaction_history = data.get('interaction_history', {})
        
        for customer in customers:
            customer_id = customer.get('customer_id')
            if not customer_id:
                continue
            
            zone_id = customer.get('zone_id')
            interaction_count = customer.get('interaction_count', 0)
            zones_visited = customer.get('zones_visited', [])
            
            # Check 1: Excessive interactions (shelf-diving)
            if interaction_count > self.interaction_threshold:
                severity = self._calculate_interaction_severity(interaction_count)
                confidence = min(0.95, 0.5 + (interaction_count * 0.1))
                
                anomaly = Anomaly(
                    id=f"suspect_interact_{customer_id}",
                    anomaly_type=AnomalyType.SUSPICIOUS_BEHAVIOR,
                    severity=severity,
                    customer_id=customer_id,
                    zone_id=zone_id,
                    title=f"Suspicious Behavior: Excessive Interactions",
                    description=f"Customer {customer_id} has {interaction_count} interactions (threshold: {self.interaction_threshold})",
                    confidence_score=confidence,
                    details={'interaction_count': interaction_count, 'behavior_type': 'excessive_interactions'}
                )
                anomalies.append(anomaly)
                self.record_anomaly(anomaly)
            
            # Check 2: Rapid zone switching
            if len(zones_visited) > self.rapid_switch_threshold:
                severity = AnomalySeverity.MEDIUM
                confidence = 0.75
                
                anomaly = Anomaly(
                    id=f"suspect_rapid_{customer_id}",
                    anomaly_type=AnomalyType.RAPID_ZONE_SWITCH,
                    severity=severity,
                    customer_id=customer_id,
                    zone_id=zone_id,
                    title=f"Suspicious Behavior: Rapid Zone Switching",
                    description=f"Customer {customer_id} switched through {len(zones_visited)} zones rapidly",
                    confidence_score=confidence,
                    details={'zones_count': len(zones_visited), 'zone_sequence': zones_visited[-3:]}
                )
                anomalies.append(anomaly)
                self.record_anomaly(anomaly)
            
            # Check 3: Restricted area access
            if zone_id in self.restricted_zones:
                severity = AnomalySeverity.HIGH
                confidence = 0.95
                
                anomaly = Anomaly(
                    id=f"suspect_restricted_{customer_id}_{zone_id}",
                    anomaly_type=AnomalyType.RESTRICTED_AREA_ACCESS,
                    severity=severity,
                    customer_id=customer_id,
                    zone_id=zone_id,
                    title=f"Unauthorized Access: Restricted Zone",
                    description=f"Customer {customer_id} accessed restricted zone {zone_id}",
                    confidence_score=confidence,
                    details={'restricted_zone_id': zone_id}
                )
                anomalies.append(anomaly)
                self.record_anomaly(anomaly)
        
        return anomalies
    
    def _calculate_interaction_severity(self, interaction_count: int) -> AnomalySeverity:
        """Calculate severity based on interaction count"""
        if interaction_count > 15:
            return AnomalySeverity.CRITICAL
        elif interaction_count > 10:
            return AnomalySeverity.HIGH
        elif interaction_count > 7:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW


# ==================== ABANDONED OBJECT DETECTOR ====================

class AbandonedObjectDetector(AnomalyDetector):
    """Detect abandoned or left-behind objects"""
    
    def __init__(self, stationary_threshold: int = 30):  # seconds
        super().__init__()
        self.stationary_threshold = stationary_threshold  # object must be stationary for N seconds
        self.tracked_objects: Dict[str, Dict] = {}  # {object_id: {first_seen, last_position, ...}}
    
    async def detect(self, data: Dict) -> List[Anomaly]:
        """
        Detect abandoned objects
        
        Input: {
            'objects': [{'object_id', 'zone_id', 'x', 'y', 'timestamp'}, ...]
        }
        """
        anomalies = []
        objects = data.get('objects', [])
        current_time = datetime.utcnow()
        
        for obj in objects:
            obj_id = obj.get('object_id')
            zone_id = obj.get('zone_id')
            x, y = obj.get('x', 0), obj.get('y', 0)
            timestamp = obj.get('timestamp', current_time)
            
            if obj_id not in self.tracked_objects:
                # First sighting of object
                self.tracked_objects[obj_id] = {
                    'first_seen': timestamp,
                    'last_position': (x, y),
                    'zone_id': zone_id,
                    'stationary_since': timestamp
                }
            else:
                # Check if object has moved
                last_pos = self.tracked_objects[obj_id]['last_position']
                distance = math.sqrt((x - last_pos[0])**2 + (y - last_pos[1])**2)
                
                if distance < 10:  # Less than 10 pixels movement = stationary
                    stationary_time = (timestamp - self.tracked_objects[obj_id]['stationary_since']).total_seconds()
                    
                    if stationary_time > self.stationary_threshold:
                        # Object has been stationary long enough = abandoned
                        anomaly = Anomaly(
                            id=f"abandoned_{obj_id}",
                            anomaly_type=AnomalyType.ABANDONED_OBJECT,
                            severity=AnomalySeverity.HIGH,
                            customer_id=None,
                            zone_id=zone_id,
                            title=f"Abandoned Object Alert",
                            description=f"Object {obj_id} abandoned in zone {zone_id} for {stationary_time:.0f}s",
                            confidence_score=0.9,
                            details={
                                'object_id': obj_id,
                                'stationary_duration': stationary_time,
                                'position': {'x': x, 'y': y},
                                'zone_id': zone_id
                            }
                        )
                        anomalies.append(anomaly)
                        self.record_anomaly(anomaly)
                else:
                    # Object moved, reset tracking
                    self.tracked_objects[obj_id]['last_position'] = (x, y)
                    self.tracked_objects[obj_id]['stationary_since'] = timestamp
        
        return anomalies
    
    def remove_object(self, obj_id: str) -> None:
        """Remove object from tracking (picked up)"""
        if obj_id in self.tracked_objects:
            del self.tracked_objects[obj_id]
            self.resolve_anomaly(f"abandoned_{obj_id}")


# ==================== ANOMALY DETECTION ENGINE ====================

class AnomalyDetectionEngine:
    """Master anomaly detection engine coordinating all detectors"""
    
    def __init__(self):
        self.loitering_detector = LoiteringDetector()
        self.crowd_detector = CrowdDetector()
        self.suspicious_detector = SuspiciousBehaviorDetector()
        self.abandoned_detector = AbandonedObjectDetector()
        
        self.all_anomalies: Dict[str, Anomaly] = {}
        self.active_anomalies: List[str] = []
    
    def register_zone_profiles(self, profiles: Dict[int, ZoneProfile]) -> None:
        """Register zone profiles for all detectors"""
        for profile in profiles.values():
            self.loitering_detector.register_zone_profile(profile)
            self.crowd_detector.register_zone_profile(profile)
    
    def set_restricted_zones(self, zone_ids: List[int]) -> None:
        """Set restricted access zones"""
        self.suspicious_detector.set_restricted_zones(zone_ids)
    
    async def detect_all(self, data: Dict) -> List[Anomaly]:
        """
        Run all anomaly detectors
        
        Input:
        {
            'customers': [...],
            'zone_occupancies': {...},
            'interaction_history': {...},
            'objects': [...]
        }
        """
        all_detected = []
        
        # Run all detectors in parallel logic
        loitering = await self.loitering_detector.detect({
            'customers': data.get('customers', []),
            'zone_profiles': self.loitering_detector.zone_profiles
        })
        
        crowd = await self.crowd_detector.detect({
            'zone_occupancies': data.get('zone_occupancies', {})
        })
        
        suspicious = await self.suspicious_detector.detect({
            'customers': data.get('customers', []),
            'interaction_history': data.get('interaction_history', {})
        })
        
        abandoned = await self.abandoned_detector.detect({
            'objects': data.get('objects', [])
        })
        
        all_detected.extend(loitering)
        all_detected.extend(crowd)
        all_detected.extend(suspicious)
        all_detected.extend(abandoned)
        
        # Update master anomaly store
        for anomaly in all_detected:
            self.all_anomalies[anomaly.id] = anomaly
            if anomaly.id not in self.active_anomalies:
                self.active_anomalies.append(anomaly.id)
        
        return all_detected
    
    def get_active_anomalies(self) -> List[Anomaly]:
        """Get currently active anomalies"""
        return [
            self.all_anomalies[aid] 
            for aid in self.active_anomalies 
            if aid in self.all_anomalies and self.all_anomalies[aid].status != AnomalyStatus.RESOLVED
        ]
    
    def get_anomalies_by_type(self, anomaly_type: AnomalyType) -> List[Anomaly]:
        """Get anomalies of specific type"""
        return [a for a in self.all_anomalies.values() if a.anomaly_type == anomaly_type]
    
    def get_zone_anomalies(self, zone_id: int) -> List[Anomaly]:
        """Get anomalies in specific zone"""
        return [a for a in self.all_anomalies.values() if a.zone_id == zone_id]
    
    def get_customer_anomalies(self, customer_id: str) -> List[Anomaly]:
        """Get anomalies for specific customer"""
        return [a for a in self.all_anomalies.values() if a.customer_id == customer_id]
    
    def acknowledge_anomaly(self, anomaly_id: str) -> bool:
        """Mark anomaly as acknowledged"""
        if anomaly_id in self.all_anomalies:
            anomaly = self.all_anomalies[anomaly_id]
            anomaly.status = AnomalyStatus.ACKNOWLEDGED
            return True
        return False
    
    def resolve_anomaly(self, anomaly_id: str) -> bool:
        """Resolve anomaly"""
        if anomaly_id in self.all_anomalies:
            self.all_anomalies[anomaly_id].status = AnomalyStatus.RESOLVED
            self.all_anomalies[anomaly_id].resolved_at = datetime.utcnow()
            if anomaly_id in self.active_anomalies:
                self.active_anomalies.remove(anomaly_id)
            return True
        return False
