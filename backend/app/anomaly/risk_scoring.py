"""
Phase 8: Risk Scoring Engine
Calculate risk scores for customers, zones, and alerts with confidence levels

Risk Factors:
- Anomaly type and severity
- Customer behavior history
- Zone characteristics
- Time-based patterns
- Interaction frequency
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import statistics

# ==================== RISK ENUMS ====================

class RiskLevel(str, Enum):
    """Risk level classification"""
    LOW = "low"  # 0.0-0.3
    MEDIUM = "medium"  # 0.3-0.6
    HIGH = "high"  # 0.6-0.8
    CRITICAL = "critical"  # 0.8-1.0


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


# ==================== RISK DATA CLASSES ====================

@dataclass
class RiskFactors:
    """Components of risk calculation"""
    anomaly_factor: float = 0.0  # 0.0-1.0
    behavior_history_factor: float = 0.0  # 0.0-1.0
    zone_risk_factor: float = 0.0  # 0.0-1.0
    frequency_factor: float = 0.0  # 0.0-1.0
    time_factor: float = 0.0  # 0.0-1.0


@dataclass
class RiskScore:
    """Risk assessment result"""
    entity_id: str  # customer_id or zone_id
    entity_type: str  # "customer" or "zone"
    risk_score: float  # 0.0-1.0
    risk_level: RiskLevel
    alert_severity: AlertSeverity
    confidence: float  # 0.0-1.0
    risk_factors: RiskFactors
    active_anomaly_count: int
    recent_incidents: int
    timestamp: datetime


# ==================== CUSTOMER RISK CALCULATOR ====================

class CustomerRiskCalculator:
    """Calculate risk scores for individual customers"""
    
    def __init__(self):
        self.customer_history: Dict[str, Dict] = {}  # {customer_id: {anomalies: [], timestamps: []}}
        self.anomaly_weights = {
            'loitering': 0.3,
            'suspicious_behavior': 0.5,
            'rapid_zone_switch': 0.4,
            'restricted_area_access': 0.8,
            'abandoned_object': 0.1  # Not directly customer risk
        }
    
    def record_anomaly(self, customer_id: str, anomaly_type: str, severity: str) -> None:
        """Record anomaly for customer"""
        if customer_id not in self.customer_history:
            self.customer_history[customer_id] = {
                'anomalies': [],
                'timestamps': [],
                'severities': []
            }
        
        self.customer_history[customer_id]['anomalies'].append(anomaly_type)
        self.customer_history[customer_id]['timestamps'].append(datetime.utcnow())
        self.customer_history[customer_id]['severities'].append(severity)
    
    def calculate_customer_risk(
        self,
        customer_id: str,
        active_anomalies: int,
        anomaly_types: List[str],
        current_zone_type: str
    ) -> RiskScore:
        """
        Calculate customer risk score
        
        Factors:
        1. Anomaly severity (40%)
        2. Behavior history (30%)
        3. Anomaly frequency (20%)
        4. Time-based patterns (10%)
        """
        
        # Factor 1: Current anomaly severity
        if not anomaly_types:
            anomaly_factor = 0.0
        else:
            max_weight = max(
                [self.anomaly_weights.get(at, 0.3) for at in anomaly_types]
            )
            anomaly_factor = min(1.0, max_weight)
        
        # Factor 2: Behavior history
        history = self.customer_history.get(customer_id, {})
        anomaly_count = len(history.get('anomalies', []))
        history_factor = min(1.0, anomaly_count / 10)  # Normalize by 10 incidents
        
        # Factor 3: Frequency (anomalies in last hour)
        recent_anomalies = 0
        if customer_id in self.customer_history:
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            for ts in self.customer_history[customer_id]['timestamps']:
                if ts > one_hour_ago:
                    recent_anomalies += 1
        
        frequency_factor = min(1.0, recent_anomalies / 5)
        
        # Factor 4: Time-based patterns
        time_factor = 0.0
        if recent_anomalies > 3:  # Multiple anomalies recently
            time_factor = 0.5
        
        # Factor 5: Zone risk
        zone_risk_weights = {
            'restricted': 0.8,
            'high_value': 0.4,
            'checkout': 0.2,
            'general': 0.1
        }
        zone_factor = zone_risk_weights.get(current_zone_type, 0.1)
        
        # Calculate composite risk
        risk_factors = RiskFactors(
            anomaly_factor=anomaly_factor,
            behavior_history_factor=history_factor,
            frequency_factor=frequency_factor,
            time_factor=time_factor,
            zone_risk_factor=zone_factor
        )
        
        # Weighted composite score
        risk_score = (
            0.40 * anomaly_factor +
            0.30 * history_factor +
            0.20 * frequency_factor +
            0.10 * time_factor
        )
        
        # Add zone risk modifier
        risk_score = min(1.0, risk_score * (1.0 + zone_factor * 0.3))
        
        # Determine risk level and alert severity
        risk_level, alert_severity = self._classify_risk(risk_score, active_anomalies)
        
        # Calculate confidence
        confidence = min(0.95, 0.5 + (active_anomalies * 0.15) + (history_factor * 0.15))
        
        return RiskScore(
            entity_id=customer_id,
            entity_type="customer",
            risk_score=risk_score,
            risk_level=risk_level,
            alert_severity=alert_severity,
            confidence=confidence,
            risk_factors=risk_factors,
            active_anomaly_count=active_anomalies,
            recent_incidents=recent_anomalies,
            timestamp=datetime.utcnow()
        )
    
    def _classify_risk(self, score: float, anomaly_count: int) -> Tuple[RiskLevel, AlertSeverity]:
        """Classify risk level and alert severity"""
        
        # Risk level classification
        if score >= 0.8:
            risk_level = RiskLevel.CRITICAL
        elif score >= 0.6:
            risk_level = RiskLevel.HIGH
        elif score >= 0.3:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        # Alert severity mapping
        if anomaly_count == 0:
            alert_severity = AlertSeverity.INFO
        elif risk_level == RiskLevel.CRITICAL or anomaly_count > 2:
            alert_severity = AlertSeverity.CRITICAL
        elif risk_level == RiskLevel.HIGH:
            alert_severity = AlertSeverity.HIGH
        else:
            alert_severity = AlertSeverity.WARNING
        
        return risk_level, alert_severity


# ==================== ZONE RISK CALCULATOR ====================

class ZoneRiskCalculator:
    """Calculate risk scores for retail zones"""
    
    def __init__(self):
        self.zone_metrics: Dict[int, Dict] = {}  # {zone_id: {anomalies: [], occupancy: []}}
        self.zone_profiles = {}
    
    def register_zone_profile(self, zone_id: int, profile_data: Dict) -> None:
        """Register zone baseline for comparison"""
        self.zone_profiles[zone_id] = profile_data
    
    def record_zone_event(
        self,
        zone_id: int,
        occupancy: int,
        anomaly_count: int,
        interaction_rate: float
    ) -> None:
        """Record zone event for risk calculation"""
        if zone_id not in self.zone_metrics:
            self.zone_metrics[zone_id] = {
                'occupancy_history': [],
                'anomaly_history': [],
                'interaction_history': [],
                'timestamps': []
            }
        
        self.zone_metrics[zone_id]['occupancy_history'].append(occupancy)
        self.zone_metrics[zone_id]['anomaly_history'].append(anomaly_count)
        self.zone_metrics[zone_id]['interaction_history'].append(interaction_rate)
        self.zone_metrics[zone_id]['timestamps'].append(datetime.utcnow())
    
    def calculate_zone_risk(self, zone_id: int) -> RiskScore:
        """
        Calculate zone risk score
        
        Factors:
        1. Current occupancy vs threshold (35%)
        2. Anomaly density (35%)
        3. Interaction rate (20%)
        4. Trend (10%)
        """
        
        if zone_id not in self.zone_metrics:
            return RiskScore(
                entity_id=str(zone_id),
                entity_type="zone",
                risk_score=0.0,
                risk_level=RiskLevel.LOW,
                alert_severity=AlertSeverity.INFO,
                confidence=0.0,
                risk_factors=RiskFactors(),
                active_anomaly_count=0,
                recent_incidents=0,
                timestamp=datetime.utcnow()
            )
        
        metrics = self.zone_metrics[zone_id]
        
        # Factor 1: Occupancy risk
        if metrics['occupancy_history']:
            current_occupancy = metrics['occupancy_history'][-1]
            profile = self.zone_profiles.get(zone_id, {'max_occupancy': 20})
            occupancy_factor = min(1.0, current_occupancy / profile.get('max_occupancy', 20))
        else:
            occupancy_factor = 0.0
        
        # Factor 2: Anomaly density
        if metrics['anomaly_history']:
            # Count anomalies in last 10 minutes
            ten_min_ago = datetime.utcnow() - timedelta(minutes=10)
            recent_anomalies = sum(
                1 for i, ts in enumerate(metrics['timestamps'])
                if ts > ten_min_ago and metrics['anomaly_history'][i] > 0
            )
            anomaly_factor = min(1.0, recent_anomalies / 5)
        else:
            anomaly_factor = 0.0
        
        # Factor 3: Interaction rate anomaly
        if metrics['interaction_history']:
            interaction_rates = metrics['interaction_history'][-20:]  # Last 20 samples
            if interaction_rates:
                avg_rate = statistics.mean(interaction_rates)
                current_rate = interaction_rates[-1]
                if avg_rate > 0:
                    interaction_factor = min(1.0, current_rate / (avg_rate * 2))
                else:
                    interaction_factor = 0.0
            else:
                interaction_factor = 0.0
        else:
            interaction_factor = 0.0
        
        # Factor 4: Trend analysis (increasing anomalies?)
        trend_factor = 0.0
        if len(metrics['anomaly_history']) >= 5:
            recent = metrics['anomaly_history'][-5:]
            if sum(recent) > sum(metrics['anomaly_history'][-10:-5]):
                trend_factor = 0.3
        
        # Composite score
        risk_score = (
            0.35 * occupancy_factor +
            0.35 * anomaly_factor +
            0.20 * interaction_factor +
            0.10 * trend_factor
        )
        
        # Get active anomaly count
        active_anomalies = metrics['anomaly_history'][-1] if metrics['anomaly_history'] else 0
        
        # Classify
        risk_level = RiskLevel.LOW
        if risk_score >= 0.8:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 0.3:
            risk_level = RiskLevel.MEDIUM
        
        # Alert severity
        if active_anomalies == 0:
            alert_severity = AlertSeverity.INFO
        elif risk_level == RiskLevel.CRITICAL:
            alert_severity = AlertSeverity.CRITICAL
        elif risk_level == RiskLevel.HIGH:
            alert_severity = AlertSeverity.HIGH
        else:
            alert_severity = AlertSeverity.WARNING
        
        confidence = min(0.95, 0.5 + (len(metrics['anomaly_history']) * 0.01))
        
        return RiskScore(
            entity_id=str(zone_id),
            entity_type="zone",
            risk_score=risk_score,
            risk_level=risk_level,
            alert_severity=alert_severity,
            confidence=confidence,
            risk_factors=RiskFactors(
                anomaly_factor=anomaly_factor,
                zone_risk_factor=occupancy_factor,
                frequency_factor=interaction_factor,
                time_factor=trend_factor
            ),
            active_anomaly_count=active_anomalies,
            recent_incidents=int(sum(1 for x in metrics['anomaly_history'][-10:] if x > 0)),
            timestamp=datetime.utcnow()
        )


# ==================== ALERT PRIORITY ENGINE ====================

class AlertPriorityEngine:
    """Determine alert priority and routing"""
    
    def __init__(self):
        self.severity_to_channels = {
            AlertSeverity.INFO: ['dashboard'],
            AlertSeverity.WARNING: ['dashboard', 'websocket'],
            AlertSeverity.HIGH: ['dashboard', 'websocket', 'notification'],
            AlertSeverity.CRITICAL: ['dashboard', 'websocket', 'notification', 'sms']
        }
    
    def calculate_alert_priority(
        self,
        risk_score: float,
        anomaly_type: str,
        confidence: float,
        active_incidents: int
    ) -> Tuple[int, AlertSeverity, List[str]]:
        """
        Calculate alert priority (1-100)
        
        Factors:
        - Risk score weight: 40%
        - Anomaly type: 30%
        - Confidence: 20%
        - Incident count: 10%
        """
        
        # Base priority from risk score
        priority = int(risk_score * 40)
        
        # Add anomaly type penalty
        anomaly_weights = {
            'restricted_area_access': 30,
            'suspicious_behavior': 25,
            'crowd': 20,
            'loitering': 15,
            'rapid_zone_switch': 10,
            'abandoned_object': 5
        }
        priority += anomaly_weights.get(anomaly_type, 10)
        
        # Confidence boost
        priority += int(confidence * 20)
        
        # Multiple incidents escalation
        priority += min(10, active_incidents * 2)
        
        priority = min(100, priority)
        
        # Determine severity from priority
        if priority >= 80:
            severity = AlertSeverity.CRITICAL
        elif priority >= 60:
            severity = AlertSeverity.HIGH
        elif priority >= 40:
            severity = AlertSeverity.WARNING
        else:
            severity = AlertSeverity.INFO
        
        # Get notification channels
        channels = self.severity_to_channels.get(severity, ['dashboard'])
        
        return priority, severity, channels


# ==================== RISK SCORING FACADE ====================

class RiskScoringEngine:
    """Master risk scoring engine"""
    
    def __init__(self):
        self.customer_calculator = CustomerRiskCalculator()
        self.zone_calculator = ZoneRiskCalculator()
        self.priority_engine = AlertPriorityEngine()
        
        self.customer_risk_cache: Dict[str, RiskScore] = {}
        self.zone_risk_cache: Dict[int, RiskScore] = {}
    
    def calculate_risk(
        self,
        entity_id: str,
        entity_type: str,
        **kwargs
    ) -> RiskScore:
        """Calculate risk for entity (customer or zone)"""
        
        if entity_type == "customer":
            risk = self.customer_calculator.calculate_customer_risk(
                entity_id,
                kwargs.get('active_anomalies', 0),
                kwargs.get('anomaly_types', []),
                kwargs.get('zone_type', 'general')
            )
            self.customer_risk_cache[entity_id] = risk
        
        elif entity_type == "zone":
            zone_id = int(entity_id)
            risk = self.zone_calculator.calculate_zone_risk(zone_id)
            self.zone_risk_cache[zone_id] = risk
        
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        return risk
    
    def get_alert_priority(
        self,
        risk_score: float,
        anomaly_type: str,
        confidence: float,
        active_incidents: int = 1
    ) -> Tuple[int, AlertSeverity, List[str]]:
        """Get alert priority and severity"""
        return self.priority_engine.calculate_alert_priority(
            risk_score,
            anomaly_type,
            confidence,
            active_incidents
        )
