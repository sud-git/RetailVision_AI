"""Business logic service layer."""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.services.repositories import (
    customer_repo, session_repo, interaction_repo, 
    dwell_repo, alert_repo, event_repo, snapshot_repo
)
from app.schemas.models import (
    CustomerCreate, CustomerUpdate, TrackingSessionCreate,
    ShelfInteractionCreate, DwellTimeRecordCreate, AlertCreate,
    EventCreate, AnalyticsSnapshotCreate
)


class CustomerService:
    """Customer business logic."""
    
    async def create_customer(self, session: AsyncSession, 
                             customer_in: CustomerCreate) -> Dict[str, Any]:
        """Create new customer."""
        customer = await customer_repo.create(
            session, 
            customer_in.model_dump()
        )
        await session.commit()
        await session.refresh(customer)
        return customer
    
    async def get_customer(self, session: AsyncSession, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer by ID."""
        return await customer_repo.get_by_id(session, uuid.UUID(customer_id))
    
    async def update_customer(self, session: AsyncSession, customer_id: str,
                             update_in: CustomerUpdate) -> Optional[Dict[str, Any]]:
        """Update customer."""
        customer = await customer_repo.update(
            session,
            uuid.UUID(customer_id),
            update_in.model_dump(exclude_unset=True)
        )
        if customer:
            await session.commit()
            await session.refresh(customer)
        return customer
    
    async def get_or_create(self, session: AsyncSession, external_id: str) -> Dict[str, Any]:
        """Get or create customer by external ID."""
        customer = await customer_repo.get_by_external_id(session, external_id)
        if not customer:
            customer = await customer_repo.create(
                session,
                {'external_id': external_id}
            )
            await session.commit()
        await session.refresh(customer)
        return customer


class TrackingService:
    """Tracking session business logic."""
    
    async def start_session(self, session: AsyncSession, customer_id: str) -> Dict[str, Any]:
        """Start new tracking session."""
        tracking_session = await session_repo.create(
            session,
            {'customer_id': uuid.UUID(customer_id)}
        )
        await session.commit()
        await session.refresh(tracking_session)
        return tracking_session
    
    async def end_session(self, session: AsyncSession, session_id: str) -> Optional[Dict[str, Any]]:
        """End tracking session and calculate metrics."""
        tracking_session = await session_repo.get_by_id(session, uuid.UUID(session_id))
        if not tracking_session:
            return None
        
        exit_time = datetime.utcnow()
        duration = (exit_time - tracking_session.entry_time).total_seconds()
        
        # Get interactions for aggregation
        interactions = await interaction_repo.get_by_session(session, uuid.UUID(session_id))
        
        # Calculate metrics
        zones_visited = len(set(i.zone_id for i in interactions))
        total_dwell = sum(i.duration_seconds for i in interactions if i.duration_seconds)
        
        # Determine engagement level
        engagement_level = "high" if total_dwell > 300 else "medium" if total_dwell > 60 else "low"
        
        # Check for anomalies
        anomaly_flags = []
        if total_dwell > 600:
            anomaly_flags.append("prolonged_browsing")
        if len(interactions) > 10:
            anomaly_flags.append("high_interaction_count")
        
        update_data = {
            'exit_time': exit_time,
            'total_duration_seconds': int(duration),
            'zones_visited': zones_visited,
            'total_interactions': len(interactions),
            'total_dwell_time_seconds': total_dwell,
            'engagement_level': engagement_level,
            'is_completed': True,
            'session_status': 'completed',
            'has_anomalies': len(anomaly_flags) > 0,
            'anomaly_flags': anomaly_flags
        }
        
        tracking_session = await session_repo.update(session, uuid.UUID(session_id), update_data)
        await session.commit()
        await session.refresh(tracking_session)
        return tracking_session
    
    async def get_active_sessions(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """Get all active sessions."""
        return await session_repo.get_active(session)


class InteractionService:
    """Shelf interaction business logic."""
    
    async def record_interaction(self, session: AsyncSession,
                                interaction_in: ShelfInteractionCreate) -> Dict[str, Any]:
        """Record shelf interaction."""
        interaction = await interaction_repo.create(
            session,
            interaction_in.model_dump()
        )
        await session.commit()
        await session.refresh(interaction)
        return interaction
    
    async def get_zone_interactions_today(self, session: AsyncSession, zone_id: str) -> Dict[str, Any]:
        """Get zone interaction statistics for today."""
        return await interaction_repo.get_zone_stats_today(session, zone_id)
    
    async def get_session_interactions(self, session: AsyncSession, session_id: str) -> List[Dict[str, Any]]:
        """Get all interactions in a session."""
        return await interaction_repo.get_by_session(session, uuid.UUID(session_id))


class DwellTimeService:
    """Dwell time business logic."""
    
    async def record_dwell_time(self, session: AsyncSession,
                               dwell_in: DwellTimeRecordCreate) -> Dict[str, Any]:
        """Record dwell time in zone."""
        dwell = await dwell_repo.create(
            session,
            dwell_in.model_dump()
        )
        await session.commit()
        await session.refresh(dwell)
        return dwell
    
    async def get_zone_dwell_stats(self, session: AsyncSession, zone_id: str) -> Dict[str, Any]:
        """Get dwell statistics for zone."""
        records = await dwell_repo.get_by_zone(session, zone_id)
        
        if not records:
            return {
                'zone_id': zone_id,
                'total_visitors': 0,
                'avg_dwell_time': 0.0,
                'total_dwell_time': 0
            }
        
        total_dwell = sum(r.dwell_time_seconds for r in records)
        avg_dwell = total_dwell / len(records)
        
        return {
            'zone_id': zone_id,
            'total_visitors': len(set(r.customer_id for r in records)),
            'avg_dwell_time': avg_dwell,
            'total_dwell_time': total_dwell,
            'visit_count': len(records)
        }


class AlertService:
    """Alert business logic."""
    
    async def create_alert(self, session: AsyncSession, 
                          alert_in: AlertCreate) -> Dict[str, Any]:
        """Create new alert."""
        alert = await alert_repo.create(
            session,
            alert_in.model_dump()
        )
        await session.commit()
        await session.refresh(alert)
        return alert
    
    async def get_active_alerts(self, session: AsyncSession, skip: int = 0, 
                               limit: int = 100) -> List[Dict[str, Any]]:
        """Get active alerts."""
        return await alert_repo.get_active(session, skip, limit)
    
    async def get_critical_alerts(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """Get critical alerts."""
        return await alert_repo.get_by_severity(session, "critical")
    
    async def acknowledge_alert(self, session: AsyncSession, alert_id: str,
                               acknowledged_by: str) -> Optional[Dict[str, Any]]:
        """Acknowledge alert."""
        alert = await alert_repo.update(
            session,
            uuid.UUID(alert_id),
            {
                'is_acknowledged': True,
                'acknowledged_by': acknowledged_by,
                'acknowledged_at': datetime.utcnow()
            }
        )
        if alert:
            await session.commit()
            await session.refresh(alert)
        return alert
    
    async def resolve_alert(self, session: AsyncSession, alert_id: str,
                           notes: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Resolve alert."""
        alert = await alert_repo.update(
            session,
            uuid.UUID(alert_id),
            {
                'is_active': False,
                'resolved_at': datetime.utcnow(),
                'resolution_notes': notes
            }
        )
        if alert:
            await session.commit()
            await session.refresh(alert)
        return alert


class EventService:
    """Event business logic."""
    
    async def create_event(self, session: AsyncSession,
                          event_in: EventCreate) -> Dict[str, Any]:
        """Create new event."""
        event = await event_repo.create(
            session,
            event_in.model_dump()
        )
        await session.commit()
        await session.refresh(event)
        return event
    
    async def get_recent_events(self, session: AsyncSession, hours: int = 24,
                               skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent events."""
        return await event_repo.get_recent(session, hours, skip, limit)
    
    async def mark_event_processed(self, session: AsyncSession, event_id: str,
                                  results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mark event as processed."""
        event = await event_repo.mark_processed(session, uuid.UUID(event_id), results)
        if event:
            await session.commit()
            await session.refresh(event)
        return event


class AnalyticsService:
    """Analytics business logic."""
    
    async def get_overview(self, session: AsyncSession) -> Dict[str, Any]:
        """Get analytics overview."""
        today = datetime.utcnow().date()
        
        # Get today's sessions
        sessions_today = await session_repo.get_completed_today(session)
        
        # Get today's interactions
        result = await interaction_repo.get_all(session)
        interactions_today = [i for i in result if i.start_time.date() == today]
        
        # Get top zones
        zone_stats = {}
        for interaction in interactions_today:
            zone_id = interaction.zone_id
            if zone_id not in zone_stats:
                zone_stats[zone_id] = {'count': 0, 'name': interaction.zone_name}
            zone_stats[zone_id]['count'] += 1
        
        top_zones = sorted(zone_stats.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
        
        # Get alerts today
        alerts = await alert_repo.get_active(session)
        alerts_today = [a for a in alerts if a.created_at.date() == today]
        
        return {
            'total_customers_today': len(set(s.customer_id for s in sessions_today)),
            'active_customers': len(await session_repo.get_active(session)),
            'total_interactions': len(interactions_today),
            'avg_dwell_time_seconds': sum(
                s.total_dwell_time_seconds for s in sessions_today
            ) / len(sessions_today) if sessions_today else 0,
            'top_zones': [
                {'zone_id': z[0], 'zone_name': z[1]['name'], 'interactions': z[1]['count']}
                for z in top_zones
            ],
            'engagement_breakdown': {'high': 0, 'medium': 0, 'low': 0},
            'anomalies_detected': len([a for a in alerts_today if a.is_acknowledged == False]),
            'timestamp': datetime.utcnow()
        }
    
    async def create_snapshot(self, session: AsyncSession,
                             snapshot_in: AnalyticsSnapshotCreate) -> Dict[str, Any]:
        """Create analytics snapshot."""
        snapshot = await snapshot_repo.create(
            session,
            snapshot_in.model_dump()
        )
        await session.commit()
        await session.refresh(snapshot)
        return snapshot


# Service instances
customer_service = CustomerService()
tracking_service = TrackingService()
interaction_service = InteractionService()
dwell_service = DwellTimeService()
alert_service = AlertService()
event_service = EventService()
analytics_service = AnalyticsService()
