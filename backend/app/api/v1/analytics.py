"""
Phase 7: Advanced Analytics API Endpoints

Comprehensive analytics endpoints for:
- Customer movement heatmaps
- Customer journey analytics
- Zone engagement metrics
- Business insights
- Analytics reports
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from app.database import get_session
from app.schemas.analytics import (
    SuccessResponse, ErrorResponse
)
from app.services.analytics import (
    HeatmapService, JourneyService, ZoneEngagementService,
    InsightsService, AnalyticsReportService
)
from app.security.middleware import validate_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


class HeatmapResponse:
    """Heatmap response schema"""
    pass


class JourneyResponse:
    """Journey response schema"""
    pass


class EngagementResponse:
    """Engagement response schema"""
    pass


# ==================== HEATMAP ENDPOINTS ====================

@router.get("/heatmaps/latest")
async def get_latest_heatmap(
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> SuccessResponse:
    """Get the latest generated heatmap"""
    try:
        service = HeatmapService(session)
        heatmap = await service.get_latest_heatmap()
        
        if not heatmap:
            return SuccessResponse(
                success=True,
                data={"message": "No heatmap available"},
                timestamp=datetime.utcnow()
            )
        
        return SuccessResponse(
            success=True,
            data=heatmap,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return ErrorResponse(
            success=False,
            error=str(e),
            code="HEATMAP_ERROR"
        )


@router.get("/heatmaps/hourly")
async def get_hourly_heatmap(
    date: datetime = Query(...),
    hour: int = Query(..., ge=0, le=23),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> SuccessResponse:
    """Get heatmap for specific hour"""
    try:
        service = HeatmapService(session)
        heatmap = await service.get_heatmap_by_hour(date, hour)
        
        return SuccessResponse(
            success=True,
            data=heatmap,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return ErrorResponse(
            success=False,
            error=str(e),
            code="HEATMAP_ERROR"
        )


@router.get("/heatmaps/daily")
async def get_daily_heatmap(
    date: datetime = Query(...),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> SuccessResponse:
    """Get full-day heatmap"""
    try:
        service = HeatmapService(session)
        start = datetime(date.year, date.month, date.day)
        end = start + timedelta(days=1)
        
        heatmap = await service.generate_historical_heatmap(start, end)
        
        return SuccessResponse(
            success=True,
            data=heatmap,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return ErrorResponse(
            success=False,
            error=str(e),
            code="HEATMAP_ERROR"
        )


@router.post("/heatmaps/generate")
async def generate_heatmap(
    heatmap_type: str = Query(..., description="real_time, hourly, daily, weekly"),
    date: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> SuccessResponse:
    """Generate new heatmap"""
    try:
        from app.models.customer import DwellTimeRecord
        from sqlalchemy import select
        
        service = HeatmapService(session)
        
        if heatmap_type == "real_time":
            # Get recent dwell records
            stmt = select(DwellTimeRecord).where(
                DwellTimeRecord.created_at >= datetime.utcnow() - timedelta(minutes=5)
            )
            result = await session.execute(stmt)
            records = result.scalars().all()
            
            heatmap = await service.generate_realtime_heatmap([
                {
                    "center_x": r.center_x,
                    "center_y": r.center_y,
                    "intensity": 1.0
                }
                for r in records if r.center_x and r.center_y
            ])
        else:
            # Generate historical
            start_date = date or datetime.utcnow()
            end_date = start_date + timedelta(days=1)
            heatmap = await service.generate_historical_heatmap(start_date, end_date)
        
        await session.commit()
        
        return SuccessResponse(
            success=True,
            data=heatmap,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        await session.rollback()
        return ErrorResponse(
            success=False,
            error=str(e),
            code="HEATMAP_GENERATION_ERROR"
        )


# ==================== JOURNEY ENDPOINTS ====================

@router.get("/journeys/summary")
async def get_journey_summary(
    customer_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> SuccessResponse:
    """Get journey summary for customer"""
    try:
        service = JourneyService(session)
        summary = await service.get_journey_summary(customer_id)
        
        return SuccessResponse(
            success=True,
            data=summary,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return ErrorResponse(
            success=False,
            error=str(e),
            code="JOURNEY_ERROR"
        )


@router.get("/journeys/analytics")
async def get_journey_analytics(
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> SuccessResponse:
    """Get overall journey analytics"""
    try:
        service = JourneyService(session)
        analytics = await service.analyze_sessions()
        
        await session.commit()
        
        return SuccessResponse(
            success=True,
            data=analytics,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        await session.rollback()
        return ErrorResponse(
            success=False,
            error=str(e),
            code="JOURNEY_ANALYTICS_ERROR"
        )


@router.get("/journeys/routes")
async def get_common_routes(
    limit: int = Query(5, ge=1, le=20),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> SuccessResponse:
    """Get most common customer routes"""
    try:
        from app.models.analytics import RouteAnalytics
        from sqlalchemy import select
        
        stmt = select(RouteAnalytics).order_by(
            RouteAnalytics.frequency.desc()
        ).limit(limit)
        result = await session.execute(stmt)
        routes = result.scalars().all()
        
        return SuccessResponse(
            success=True,
            data={
                "routes": [
                    {
                        "sequence": r.zone_sequence,
                        "frequency": r.frequency,
                        "avg_duration": r.avg_duration,
                        "conversion_rate": r.conversion_rate
                    }
                    for r in routes
                ]
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return ErrorResponse(
            success=False,
            error=str(e),
            code="ROUTES_ERROR"
        )


# ==================== ZONE ENGAGEMENT ENDPOINTS ====================

@router.get("/zones/engagement")
async def get_zone_engagement(
    date: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> SuccessResponse:
    """Get zone engagement metrics"""
    try:
        service = ZoneEngagementService(session)
        target_date = date or datetime.utcnow()
        
        metrics = await service.calculate_zone_metrics(target_date)
        await session.commit()
        
        return SuccessResponse(
            success=True,
            data={
                "date": target_date.isoformat(),
                "zones": [
                    {
                        "zone_id": zone_id,
                        **metrics
                    }
                    for zone_id, metrics in metrics.items()
                ]
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        await session.rollback()
        return ErrorResponse(
            success=False,
            error=str(e),
            code="ZONE_ENGAGEMENT_ERROR"
        )


@router.get("/zones/top")
async def get_top_zones(
    limit: int = Query(5, ge=1, le=20),
    date: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> SuccessResponse:
    """Get top performing zones"""
    try:
        from app.models.analytics import ZoneEngagement
        from sqlalchemy import select
        
        target_date = date or datetime.utcnow().date()
        
        stmt = select(ZoneEngagement).where(
            ZoneEngagement.analytics_date >= target_date,
            ZoneEngagement.analytics_date < target_date + timedelta(days=1)
        ).order_by(ZoneEngagement.engagement_score.desc()).limit(limit)
        
        result = await session.execute(stmt)
        zones = result.scalars().all()
        
        return SuccessResponse(
            success=True,
            data={
                "top_zones": [
                    {
                        "zone_id": z.zone_id,
                        "engagement_score": z.engagement_score,
                        "visitor_count": z.visitor_count,
                        "conversion_rate": z.conversion_rate,
                        "performance_rating": z.performance_rating
                    }
                    for z in zones
                ]
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return ErrorResponse(
            success=False,
            error=str(e),
            code="TOP_ZONES_ERROR"
        )


@router.get("/zones/underperforming")
async def get_underperforming_zones(
    limit: int = Query(5, ge=1, le=20),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> SuccessResponse:
    """Get underperforming zones needing attention"""
    try:
        from app.models.analytics import ZoneEngagement
        from sqlalchemy import select
        
        today = datetime.utcnow().date()
        
        stmt = select(ZoneEngagement).where(
            and_(
                ZoneEngagement.analytics_date >= today,
                ZoneEngagement.analytics_date < today + timedelta(days=1)
            )
        ).order_by(ZoneEngagement.engagement_score.asc()).limit(limit)
        
        result = await session.execute(stmt)
        zones = result.scalars().all()
        
        return SuccessResponse(
            success=True,
            data={
                "underperforming_zones": [
                    {
                        "zone_id": z.zone_id,
                        "engagement_score": z.engagement_score,
                        "visitor_count": z.visitor_count,
                        "conversion_rate": z.conversion_rate,
                        "recommendations": [
                            "Reposition products for better visibility",
                            "Add promotional signage",
                            "Increase staff presence",
                            "Review pricing strategy"
                        ]
                    }
                    for z in zones
                ]
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return ErrorResponse(
            success=False,
            error=str(e),
            code="UNDERPERFORMING_ZONES_ERROR"
        )


# ==================== ENGAGEMENT ENDPOINTS ====================

@router.get("/engagement/overall")
async def get_overall_engagement(
    date: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> SuccessResponse:
    """Get overall engagement metrics"""
    try:
        from app.models.analytics import EngagementMetrics
        from sqlalchemy import select
        
        target_date = date or datetime.utcnow().date()
        
        stmt = select(EngagementMetrics).where(
            and_(
                EngagementMetrics.date >= target_date,
                EngagementMetrics.date < target_date + timedelta(days=1)
            )
        ).limit(1)
        
        result = await session.execute(stmt)
        metric = result.scalar_one_or_none()
        
        if not metric:
            return SuccessResponse(
                success=True,
                data={"message": "No engagement metrics available"},
                timestamp=datetime.utcnow()
            )
        
        return SuccessResponse(
            success=True,
            data={
                "date": metric.date.isoformat(),
                "total_customers": metric.total_customers,
                "total_interactions": metric.total_interactions,
                "avg_engagement_score": metric.avg_engagement_score,
                "conversion_rate": metric.overall_conversion_rate,
                "engagement_distribution": {
                    "high": metric.high_engagement_count,
                    "medium": metric.medium_engagement_count,
                    "low": metric.low_engagement_count
                }
            },
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return ErrorResponse(
            success=False,
            error=str(e),
            code="ENGAGEMENT_ERROR"
        )


# ==================== INSIGHTS ENDPOINTS ====================

@router.get("/insights")
async def get_business_insights(
    limit: int = Query(5, ge=1, le=20),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> SuccessResponse:
    """Get recent business insights"""
    try:
        service = InsightsService(session)
        insights = await service.get_top_insights(limit)
        
        return SuccessResponse(
            success=True,
            data={"insights": insights},
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return ErrorResponse(
            success=False,
            error=str(e),
            code="INSIGHTS_ERROR"
        )


@router.post("/insights/generate")
async def generate_daily_insights(
    date: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> SuccessResponse:
    """Generate insights for specific date"""
    try:
        service = InsightsService(session)
        target_date = date or datetime.utcnow()
        
        insights = await service.generate_daily_insights(target_date)
        await session.commit()
        
        return SuccessResponse(
            success=True,
            data=insights,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        await session.rollback()
        return ErrorResponse(
            success=False,
            error=str(e),
            code="INSIGHTS_GENERATION_ERROR"
        )


# ==================== REPORT ENDPOINTS ====================

@router.post("/reports/generate")
async def generate_analytics_report(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    report_type: str = Query("comprehensive", regex="^(comprehensive|daily|weekly)$"),
    session: AsyncSession = Depends(get_session),
    api_key: str = Depends(validate_api_key)
) -> SuccessResponse:
    """Generate comprehensive analytics report"""
    try:
        heatmap_service = HeatmapService(session)
        journey_service = JourneyService(session)
        insights_service = InsightsService(session)
        
        # Generate all components
        heatmap = await heatmap_service.generate_historical_heatmap(start_date, end_date)
        journeys = await journey_service.analyze_sessions()
        insights = await insights_service.get_top_insights(limit=10)
        
        report = {
            "period": f"{start_date.date()} to {end_date.date()}",
            "report_type": report_type,
            "generated_at": datetime.utcnow().isoformat(),
            "sections": {
                "heatmap": heatmap,
                "journeys": journeys,
                "insights": insights
            },
            "summary": {
                "total_data_points": len(insights),
                "key_finding": "Comprehensive analytics report generated successfully"
            }
        }
        
        return SuccessResponse(
            success=True,
            data=report,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        return ErrorResponse(
            success=False,
            error=str(e),
            code="REPORT_GENERATION_ERROR"
        )
