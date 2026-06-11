"""
Phase 8: Anomaly Detection Service Layer

Service layer orchestrating:
- Anomaly detection
- Risk scoring
- Alert generation
- Alert management
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func
import uuid

from app.anomaly.detection import (
    AnomalyDetectionEngine, LoiteringDetector, CrowdDetector,
    SuspiciousBehaviorDetector, AbandonedObjectDetector,
    Anomaly as AnomalyData, AnomalyType, AnomalySeverity, AnomalyStatus,
    ZoneProfile
)
from app.anomaly.risk_scoring import (
    RiskScoringEngine, CustomerRiskCalculator, ZoneRiskCalculator,
    AlertPriorityEngine, RiskScore, AlertSeverity, RiskLevel
)
from app.models.anomaly import (
    Anomaly, Alert, ZoneRiskProfile, AlertAcknowledgment,
    AnomalyHistory, RiskScoreHistory, AlertStatistics
)


# ==================== ANOMALY SERVICE ====================

class AnomalyDetectionService:
    """Service for managing anomaly detection"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.detection_engine = AnomalyDetectionEngine()
        self.risk_engine = RiskScoringEngine()
    
    async def initialize_zone_profiles(self) -> None:
        """Load zone risk profiles from database"""
        try:
            query = select(ZoneRiskProfile)
            result = await self.session.execute(query)
            profiles = result.scalars().all()
            
            for profile in profiles:
                zone_profile = ZoneProfile(
                    zone_id=profile.zone_id,
                    normal_occupancy=profile.normal_occupancy,
                    max_occupancy=profile.max_occupancy,
                    normal_dwell_time=profile.loitering_threshold,
                    max_dwell_time=profile.loitering_threshold,
                    zone_type=profile.zone_type,
                    is_restricted=profile.is_restricted
                )
                self.detection_engine.register_zone_profiles({profile.zone_id: zone_profile})
        except Exception as e:
            print(f"Error initializing zone profiles: {e}")
    
    async def detect_anomalies(self, data: Dict) -> List[Anomaly]:
        """
        Run anomaly detection on input data
        
        Input: {
            'customers': [...],
            'zone_occupancies': {...},
            'interaction_history': {...},
            'objects': [...]
        }
        """
        detected = await self.detection_engine.detect_all(data)
        
        # Persist anomalies to database
        for anomaly in detected:
            db_anomaly = Anomaly(
                id=anomaly.id,
                anomaly_type=anomaly.anomaly_type.value,
                severity=anomaly.severity.value,
                status=anomaly.status.value,
                customer_id=anomaly.customer_id,
                zone_id=anomaly.zone_id,
                title=anomaly.title,
                description=anomaly.description,
                confidence_score=anomaly.confidence_score,
                details=anomaly.details,
                detected_at=anomaly.detected_at
            )
            self.session.add(db_anomaly)
        
        await self.session.commit()
        return detected
    
    async def get_active_anomalies(self, zone_id: Optional[int] = None) -> List[Dict]:
        """Get currently active anomalies"""
        query = select(Anomaly).where(
            Anomaly.status.in_([AnomalyStatus.DETECTED.value, AnomalyStatus.ONGOING.value])
        )
        
        if zone_id:
            query = query.where(Anomaly.zone_id == zone_id)
        
        result = await self.session.execute(query)
        anomalies = result.scalars().all()
        
        return [
            {
                'id': a.id,
                'type': a.anomaly_type,
                'severity': a.severity,
                'customer_id': a.customer_id,
                'zone_id': a.zone_id,
                'title': a.title,
                'description': a.description,
                'confidence': a.confidence_score,
                'detected_at': a.detected_at.isoformat()
            }
            for a in anomalies
        ]
    
    async def get_anomaly_history(
        self,
        start_date: datetime,
        end_date: datetime,
        anomaly_type: Optional[str] = None,
        zone_id: Optional[int] = None
    ) -> List[Dict]:
        """Get anomaly history for analysis"""
        query = select(Anomaly).where(
            and_(
                Anomaly.detected_at >= start_date,
                Anomaly.detected_at <= end_date
            )
        )
        
        if anomaly_type:
            query = query.where(Anomaly.anomaly_type == anomaly_type)
        
        if zone_id:
            query = query.where(Anomaly.zone_id == zone_id)
        
        result = await self.session.execute(query)
        anomalies = result.scalars().all()
        
        return [
            {
                'id': a.id,
                'type': a.anomaly_type,
                'severity': a.severity,
                'customer_id': a.customer_id,
                'zone_id': a.zone_id,
                'title': a.title,
                'duration': (a.resolved_at or datetime.utcnow() - a.detected_at).total_seconds(),
                'detected_at': a.detected_at.isoformat(),
                'resolved_at': a.resolved_at.isoformat() if a.resolved_at else None
            }
            for a in anomalies
        ]
    
    async def resolve_anomaly(self, anomaly_id: str) -> bool:
        """Mark anomaly as resolved"""
        query = select(Anomaly).where(Anomaly.id == anomaly_id)
        result = await self.session.execute(query)
        anomaly = result.scalar_one_or_none()
        
        if anomaly:
            anomaly.status = AnomalyStatus.RESOLVED.value
            anomaly.resolved_at = datetime.utcnow()
            await self.session.commit()
            return True
        return False


# ==================== ALERT SERVICE ====================

class AlertService:
    """Service for managing alerts"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.priority_engine = AlertPriorityEngine()
    
    async def create_alert_from_anomaly(
        self,
        anomaly: Anomaly,
        risk_score: float,
        confidence: float,
        active_incidents: int = 1
    ) -> Alert:
        """Create alert from detected anomaly"""
        
        # Calculate priority
        priority, severity, channels = self.priority_engine.calculate_alert_priority(
            risk_score,
            anomaly.anomaly_type,
            confidence,
            active_incidents
        )
        
        # Create alert
        alert = Alert(
            id=str(uuid.uuid4()),
            anomaly_id=anomaly.id,
            alert_type=severity.value,
            alert_source="anomaly_detection",
            title=f"Alert: {anomaly.title}",
            description=anomaly.description,
            customer_id=anomaly.customer_id,
            zone_id=anomaly.zone_id,
            priority=priority,
            risk_score=risk_score,
            confidence=confidence,
            notification_channels=channels,
            status="active"
        )
        
        self.session.add(alert)
        await self.session.commit()
        
        return alert
    
    async def get_active_alerts(
        self,
        zone_id: Optional[int] = None,
        alert_type: Optional[str] = None
    ) -> List[Dict]:
        """Get active alerts"""
        query = select(Alert).where(Alert.status == "active")
        
        if zone_id:
            query = query.where(Alert.zone_id == zone_id)
        
        if alert_type:
            query = query.where(Alert.alert_type == alert_type)
        
        query = query.order_by(desc(Alert.priority))
        
        result = await self.session.execute(query)
        alerts = result.scalars().all()
        
        return [
            {
                'id': a.id,
                'anomaly_id': a.anomaly_id,
                'type': a.alert_type,
                'priority': a.priority,
                'risk_score': a.risk_score,
                'confidence': a.confidence,
                'title': a.title,
                'description': a.description,
                'customer_id': a.customer_id,
                'zone_id': a.zone_id,
                'channels': a.notification_channels,
                'created_at': a.created_at.isoformat()
            }
            for a in alerts
        ]
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge alert"""
        query = select(Alert).where(Alert.id == alert_id)
        result = await self.session.execute(query)
        alert = result.scalar_one_or_none()
        
        if alert:
            alert.status = "acknowledged"
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.utcnow()
            
            # Record acknowledgment
            ack = AlertAcknowledgment(
                id=str(uuid.uuid4()),
                alert_id=alert_id,
                acknowledged_by=acknowledged_by
            )
            self.session.add(ack)
            await self.session.commit()
            return True
        
        return False
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve alert"""
        query = select(Alert).where(Alert.id == alert_id)
        result = await self.session.execute(query)
        alert = result.scalar_one_or_none()
        
        if alert:
            alert.status = "resolved"
            alert.resolved_at = datetime.utcnow()
            await self.session.commit()
            return True
        
        return False
    
    async def get_alert_history(
        self,
        start_date: datetime,
        end_date: datetime,
        zone_id: Optional[int] = None,
        alert_type: Optional[str] = None
    ) -> List[Dict]:
        """Get alert history"""
        query = select(Alert).where(
            and_(
                Alert.created_at >= start_date,
                Alert.created_at <= end_date
            )
        )
        
        if zone_id:
            query = query.where(Alert.zone_id == zone_id)
        
        if alert_type:
            query = query.where(Alert.alert_type == alert_type)
        
        query = query.order_by(desc(Alert.created_at))
        
        result = await self.session.execute(query)
        alerts = result.scalars().all()
        
        return [
            {
                'id': a.id,
                'type': a.alert_type,
                'priority': a.priority,
                'title': a.title,
                'status': a.status,
                'zone_id': a.zone_id,
                'customer_id': a.customer_id,
                'created_at': a.created_at.isoformat(),
                'acknowledged_at': a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                'resolved_at': a.resolved_at.isoformat() if a.resolved_at else None
            }
            for a in alerts
        ]
    
    async def get_alert_statistics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Get alert statistics for period"""
        query = select(Alert).where(
            and_(
                Alert.created_at >= start_date,
                Alert.created_at <= end_date
            )
        )
        
        result = await self.session.execute(query)
        alerts = result.scalars().all()
        
        stats = {
            'total': len(alerts),
            'by_type': {},
            'by_priority': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
            'acknowledged': 0,
            'resolved': 0
        }
        
        for alert in alerts:
            # By type
            stats['by_type'][alert.alert_type] = stats['by_type'].get(alert.alert_type, 0) + 1
            
            # By priority
            if alert.priority >= 80:
                stats['by_priority']['critical'] += 1
            elif alert.priority >= 60:
                stats['by_priority']['high'] += 1
            elif alert.priority >= 40:
                stats['by_priority']['medium'] += 1
            else:
                stats['by_priority']['low'] += 1
            
            # Status
            if alert.status == 'acknowledged':
                stats['acknowledged'] += 1
            elif alert.status == 'resolved':
                stats['resolved'] += 1
        
        return stats


# ==================== RISK MANAGEMENT SERVICE ====================

class RiskManagementService:
    """Service for risk scoring and management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.risk_engine = RiskScoringEngine()
    
    async def calculate_customer_risk(
        self,
        customer_id: str,
        active_anomalies: int,
        anomaly_types: List[str],
        zone_type: str = "general"
    ) -> Dict:
        """Calculate customer risk score"""
        risk = self.risk_engine.calculate_risk(
            customer_id,
            "customer",
            active_anomalies=active_anomalies,
            anomaly_types=anomaly_types,
            zone_type=zone_type
        )
        
        # Store in history
        history = RiskScoreHistory(
            id=str(uuid.uuid4()),
            entity_id=customer_id,
            entity_type="customer",
            risk_score=risk.risk_score,
            risk_level=risk.risk_level.value,
            confidence=risk.confidence,
            anomaly_factor=risk.risk_factors.anomaly_factor,
            behavior_history_factor=risk.risk_factors.behavior_history_factor,
            zone_risk_factor=risk.risk_factors.zone_risk_factor,
            frequency_factor=risk.risk_factors.frequency_factor,
            active_anomalies=risk.active_anomaly_count,
            recent_incidents=risk.recent_incidents
        )
        self.session.add(history)
        await self.session.commit()
        
        return {
            'customer_id': customer_id,
            'risk_score': risk.risk_score,
            'risk_level': risk.risk_level.value,
            'alert_severity': risk.alert_severity.value,
            'confidence': risk.confidence,
            'active_anomalies': risk.active_anomaly_count,
            'recent_incidents': risk.recent_incidents
        }
    
    async def calculate_zone_risk(self, zone_id: int) -> Dict:
        """Calculate zone risk score"""
        risk = self.risk_engine.calculate_risk(
            str(zone_id),
            "zone"
        )
        
        # Store in history
        history = RiskScoreHistory(
            id=str(uuid.uuid4()),
            entity_id=str(zone_id),
            entity_type="zone",
            risk_score=risk.risk_score,
            risk_level=risk.risk_level.value,
            confidence=risk.confidence,
            anomaly_factor=risk.risk_factors.anomaly_factor,
            zone_risk_factor=risk.risk_factors.zone_risk_factor,
            active_anomalies=risk.active_anomaly_count
        )
        self.session.add(history)
        await self.session.commit()
        
        return {
            'zone_id': zone_id,
            'risk_score': risk.risk_score,
            'risk_level': risk.risk_level.value,
            'alert_severity': risk.alert_severity.value,
            'confidence': risk.confidence,
            'active_anomalies': risk.active_anomaly_count
        }
    
    async def get_high_risk_customers(self, threshold: float = 0.7) -> List[Dict]:
        """Get customers with high risk scores"""
        # Query recent risk scores
        query = select(RiskScoreHistory).where(
            and_(
                RiskScoreHistory.entity_type == "customer",
                RiskScoreHistory.risk_score >= threshold,
                RiskScoreHistory.recorded_at >= datetime.utcnow() - timedelta(hours=1)
            )
        ).distinct(RiskScoreHistory.entity_id).order_by(
            RiskScoreHistory.entity_id,
            desc(RiskScoreHistory.recorded_at)
        )
        
        result = await self.session.execute(query)
        records = result.scalars().all()
        
        return [
            {
                'customer_id': r.entity_id,
                'risk_score': r.risk_score,
                'risk_level': r.risk_level,
                'active_anomalies': r.active_anomalies,
                'recorded_at': r.recorded_at.isoformat()
            }
            for r in records
        ]
    
    async def get_high_risk_zones(self, threshold: float = 0.7) -> List[Dict]:
        """Get zones with high risk scores"""
        query = select(RiskScoreHistory).where(
            and_(
                RiskScoreHistory.entity_type == "zone",
                RiskScoreHistory.risk_score >= threshold,
                RiskScoreHistory.recorded_at >= datetime.utcnow() - timedelta(hours=1)
            )
        ).distinct(RiskScoreHistory.entity_id).order_by(
            RiskScoreHistory.entity_id,
            desc(RiskScoreHistory.recorded_at)
        )
        
        result = await self.session.execute(query)
        records = result.scalars().all()
        
        return [
            {
                'zone_id': int(r.entity_id),
                'risk_score': r.risk_score,
                'risk_level': r.risk_level,
                'active_anomalies': r.active_anomalies,
                'recorded_at': r.recorded_at.isoformat()
            }
            for r in records
        ]
