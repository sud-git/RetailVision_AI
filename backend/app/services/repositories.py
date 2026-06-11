"""Repository layer for data access."""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import select, func
from sqlalchemy import desc, and_

from app.models.customer import (
    Customer, TrackingSession, ShelfInteraction, 
    DwellTimeRecord, Alert, Event, AnalyticsSnapshot
)
from app.schemas.models import (
    CustomerCreate, CustomerUpdate, TrackingSessionCreate, ShelfInteractionCreate,
    DwellTimeRecordCreate, AlertCreate, AlertUpdate, EventCreate, AnalyticsSnapshotCreate
)


class BaseRepository:
    """Base repository with common CRUD operations."""
    
    def __init__(self, model):
        self.model = model
    
    async def create(self, session: AsyncSession, obj_in: dict) -> Any:
        """Create object."""
        db_obj = self.model(**obj_in)
        session.add(db_obj)
        await session.flush()
        return db_obj
    
    async def get_by_id(self, session: AsyncSession, id: Any) -> Optional[Any]:
        """Get by ID."""
        return await session.get(self.model, id)
    
    async def get_all(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> List[Any]:
        """Get all with pagination."""
        result = await session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def count(self, session: AsyncSession) -> int:
        """Count total."""
        result = await session.execute(select(func.count(self.model.id)))
        return result.scalar_one()
    
    async def update(self, session: AsyncSession, id: Any, obj_in: dict) -> Optional[Any]:
        """Update object."""
        db_obj = await self.get_by_id(session, id)
        if not db_obj:
            return None
        for key, value in obj_in.items():
            if value is not None:
                setattr(db_obj, key, value)
        await session.flush()
        return db_obj
    
    async def delete(self, session: AsyncSession, id: Any) -> bool:
        """Delete object."""
        db_obj = await self.get_by_id(session, id)
        if not db_obj:
            return False
        await session.delete(db_obj)
        await session.flush()
        return True


class CustomerRepository(BaseRepository):
    """Customer repository."""
    
    def __init__(self):
        super().__init__(Customer)
    
    async def get_by_external_id(self, session: AsyncSession, external_id: str) -> Optional[Customer]:
        """Get customer by external ID."""
        result = await session.execute(
            select(Customer).where(Customer.external_id == external_id)
        )
        return result.scalars().first()
    
    async def get_by_email(self, session: AsyncSession, email: str) -> Optional[Customer]:
        """Get customer by email."""
        result = await session.execute(
            select(Customer).where(Customer.email == email)
        )
        return result.scalars().first()
    
    async def get_flagged(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> List[Customer]:
        """Get flagged customers."""
        result = await session.execute(
            select(Customer)
            .where(Customer.is_flagged == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_vip_customers(self, session: AsyncSession) -> List[Customer]:
        """Get VIP customers."""
        result = await session.execute(
            select(Customer).where(Customer.customer_tier == "vip")
        )
        return result.scalars().all()


class TrackingSessionRepository(BaseRepository):
    """Tracking session repository."""
    
    def __init__(self):
        super().__init__(TrackingSession)
    
    async def get_by_customer(self, session: AsyncSession, customer_id: Any, 
                             skip: int = 0, limit: int = 100) -> List[TrackingSession]:
        """Get sessions by customer."""
        result = await session.execute(
            select(TrackingSession)
            .where(TrackingSession.customer_id == customer_id)
            .order_by(desc(TrackingSession.entry_time))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_active(self, session: AsyncSession) -> List[TrackingSession]:
        """Get active sessions."""
        result = await session.execute(
            select(TrackingSession)
            .where(TrackingSession.is_completed == False)
            .order_by(TrackingSession.entry_time)
        )
        return result.scalars().all()
    
    async def get_today_count(self, session: AsyncSession) -> int:
        """Get session count for today."""
        today = datetime.utcnow().date()
        result = await session.execute(
            select(func.count(TrackingSession.id))
            .where(func.date(TrackingSession.entry_time) == today)
        )
        return result.scalar_one()
    
    async def get_completed_today(self, session: AsyncSession) -> List[TrackingSession]:
        """Get completed sessions from today."""
        today = datetime.utcnow().date()
        result = await session.execute(
            select(TrackingSession)
            .where(
                and_(
                    func.date(TrackingSession.entry_time) == today,
                    TrackingSession.is_completed == True
                )
            )
        )
        return result.scalars().all()


class ShelfInteractionRepository(BaseRepository):
    """Shelf interaction repository."""
    
    def __init__(self):
        super().__init__(ShelfInteraction)
    
    async def get_by_session(self, session: AsyncSession, session_id: Any) -> List[ShelfInteraction]:
        """Get interactions by session."""
        result = await session.execute(
            select(ShelfInteraction)
            .where(ShelfInteraction.tracking_session_id == session_id)
            .order_by(ShelfInteraction.start_time)
        )
        return result.scalars().all()
    
    async def get_by_zone(self, session: AsyncSession, zone_id: str, 
                         skip: int = 0, limit: int = 100) -> List[ShelfInteraction]:
        """Get interactions by zone."""
        result = await session.execute(
            select(ShelfInteraction)
            .where(ShelfInteraction.zone_id == zone_id)
            .order_by(desc(ShelfInteraction.start_time))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_zone_stats_today(self, session: AsyncSession, zone_id: str) -> Dict[str, Any]:
        """Get zone statistics for today."""
        today = datetime.utcnow().date()
        result = await session.execute(
            select(
                func.count(ShelfInteraction.id).label('total'),
                func.count(func.distinct(ShelfInteraction.customer_id)).label('unique_customers'),
                func.avg(ShelfInteraction.duration_seconds).label('avg_duration')
            )
            .where(
                and_(
                    ShelfInteraction.zone_id == zone_id,
                    func.date(ShelfInteraction.start_time) == today
                )
            )
        )
        row = result.one()
        return {
            'total_interactions': row.total or 0,
            'unique_customers': row.unique_customers or 0,
            'avg_duration': float(row.avg_duration) if row.avg_duration else 0.0
        }


class DwellTimeRepository(BaseRepository):
    """Dwell time repository."""
    
    def __init__(self):
        super().__init__(DwellTimeRecord)
    
    async def get_by_session(self, session: AsyncSession, session_id: Any) -> List[DwellTimeRecord]:
        """Get dwell records by session."""
        result = await session.execute(
            select(DwellTimeRecord)
            .where(DwellTimeRecord.tracking_session_id == session_id)
        )
        return result.scalars().all()
    
    async def get_by_zone(self, session: AsyncSession, zone_id: str) -> List[DwellTimeRecord]:
        """Get dwell records by zone."""
        result = await session.execute(
            select(DwellTimeRecord).where(DwellTimeRecord.zone_id == zone_id)
        )
        return result.scalars().all()
    
    async def get_zone_avg_dwell(self, session: AsyncSession, zone_id: str) -> float:
        """Get average dwell time for zone."""
        result = await session.execute(
            select(func.avg(DwellTimeRecord.dwell_time_seconds))
            .where(DwellTimeRecord.zone_id == zone_id)
        )
        avg = result.scalar_one()
        return float(avg) if avg else 0.0


class AlertRepository(BaseRepository):
    """Alert repository."""
    
    def __init__(self):
        super().__init__(Alert)
    
    async def get_active(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> List[Alert]:
        """Get active alerts."""
        result = await session.execute(
            select(Alert)
            .where(Alert.is_active == True)
            .order_by(desc(Alert.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_severity(self, session: AsyncSession, severity: str) -> List[Alert]:
        """Get alerts by severity."""
        result = await session.execute(
            select(Alert)
            .where(
                and_(
                    Alert.alert_severity == severity,
                    Alert.is_active == True
                )
            )
            .order_by(desc(Alert.created_at))
        )
        return result.scalars().all()
    
    async def get_by_customer(self, session: AsyncSession, customer_id: Any) -> List[Alert]:
        """Get alerts by customer."""
        result = await session.execute(
            select(Alert)
            .where(Alert.customer_id == customer_id)
            .order_by(desc(Alert.created_at))
        )
        return result.scalars().all()
    
    async def get_unacknowledged(self, session: AsyncSession) -> List[Alert]:
        """Get unacknowledged alerts."""
        result = await session.execute(
            select(Alert)
            .where(
                and_(
                    Alert.is_acknowledged == False,
                    Alert.is_active == True
                )
            )
            .order_by(desc(Alert.created_at))
        )
        return result.scalars().all()


class EventRepository(BaseRepository):
    """Event repository."""
    
    def __init__(self):
        super().__init__(Event)
    
    async def get_recent(self, session: AsyncSession, hours: int = 24, 
                        skip: int = 0, limit: int = 100) -> List[Event]:
        """Get recent events."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = await session.execute(
            select(Event)
            .where(Event.created_at >= cutoff)
            .order_by(desc(Event.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_type(self, session: AsyncSession, event_type: str) -> List[Event]:
        """Get events by type."""
        result = await session.execute(
            select(Event)
            .where(Event.event_type == event_type)
            .order_by(desc(Event.created_at))
        )
        return result.scalars().all()
    
    async def get_unprocessed(self, session: AsyncSession, limit: int = 100) -> List[Event]:
        """Get unprocessed events."""
        result = await session.execute(
            select(Event)
            .where(Event.is_processed == False)
            .order_by(Event.created_at)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def mark_processed(self, session: AsyncSession, event_id: Any, 
                            results: Dict[str, Any]) -> Optional[Event]:
        """Mark event as processed."""
        return await self.update(
            session, 
            event_id,
            {
                'is_processed': True,
                'processing_status': 'processed',
                'processing_results': results
            }
        )


class AnalyticsSnapshotRepository(BaseRepository):
    """Analytics snapshot repository."""
    
    def __init__(self):
        super().__init__(AnalyticsSnapshot)
    
    async def get_latest(self, session: AsyncSession, period: str) -> Optional[AnalyticsSnapshot]:
        """Get latest snapshot by period."""
        result = await session.execute(
            select(AnalyticsSnapshot)
            .where(AnalyticsSnapshot.snapshot_period == period)
            .order_by(desc(AnalyticsSnapshot.period_end))
            .limit(1)
        )
        return result.scalars().first()
    
    async def get_hourly_trend(self, session: AsyncSession, hours: int = 24) -> List[AnalyticsSnapshot]:
        """Get hourly snapshots for trend."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = await session.execute(
            select(AnalyticsSnapshot)
            .where(
                and_(
                    AnalyticsSnapshot.snapshot_period == "hourly",
                    AnalyticsSnapshot.period_start >= cutoff
                )
            )
            .order_by(AnalyticsSnapshot.period_start)
        )
        return result.scalars().all()


# Repository instances
customer_repo = CustomerRepository()
session_repo = TrackingSessionRepository()
interaction_repo = ShelfInteractionRepository()
dwell_repo = DwellTimeRepository()
alert_repo = AlertRepository()
event_repo = EventRepository()
snapshot_repo = AnalyticsSnapshotRepository()
