"""
Analytics Service - Implements business logic for analytics operations

Provides:
- Heatmap generation and management
- Journey analytics and clustering
- Zone engagement analysis
- Business insights generation
- Analytics data aggregation
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import json

from app.analytics.engine import (
    HeatmapGrid, JourneyAnalyzer, EngagementAnalyzer,
    BusinessInsightsEngine, AnalyticsAggregator
)
from app.models.analytics import (
    Heatmap, CustomerJourney, ZoneEngagement, RouteAnalytics,
    EngagementMetrics, BusinessInsight, AnalyticsSnapshot
)
from app.models.customer import (
    DwellTimeRecord, ShelfInteraction, TrackingSession
)


class HeatmapService:
    """Manage heatmap generation and retrieval"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.grid_generator = HeatmapGrid()
    
    async def generate_realtime_heatmap(self,
                                       dwell_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate real-time heatmap from current dwell records"""
        grid = HeatmapGrid()
        
        # Add points to grid
        for record in dwell_records:
            if "center_x" in record and "center_y" in record:
                intensity = record.get("intensity", 1.0)
                grid.add_point(record["center_x"], record["center_y"], intensity)
        
        # Create heatmap record
        grid_data = grid.to_dict()
        hotspots = grid.get_hotspots(threshold=0.6)
        
        heatmap = Heatmap(
            heatmap_type="real_time",
            time_period_start=datetime.utcnow(),
            time_period_end=datetime.utcnow(),
            grid_data=grid_data,
            width=grid.width,
            height=grid.height,
            cell_size=grid.cell_size,
            total_samples=len(dwell_records),
            max_intensity=float(grid.get_grid_data().max()),
            hotspot_count=len(hotspots)
        )
        
        self.session.add(heatmap)
        await self.session.flush()
        
        return {
            "heatmap_id": heatmap.id,
            "type": "real_time",
            "grid": grid_data,
            "hotspots": [
                {
                    "x": h.x,
                    "y": h.y,
                    "intensity": h.intensity,
                    "count": h.count
                }
                for h in hotspots
            ],
            "metadata": {
                "total_samples": heatmap.total_samples,
                "max_intensity": heatmap.max_intensity,
                "hotspot_count": len(hotspots)
            }
        }
    
    async def generate_historical_heatmap(self,
                                         start_date: datetime,
                                         end_date: datetime) -> Dict[str, Any]:
        """Generate heatmap from historical data"""
        # Query dwell records in date range
        stmt = select(DwellTimeRecord).where(
            and_(
                DwellTimeRecord.created_at >= start_date,
                DwellTimeRecord.created_at <= end_date
            )
        )
        result = await self.session.execute(stmt)
        records = result.scalars().all()
        
        grid = HeatmapGrid()
        
        for record in records:
            if record.center_x and record.center_y:
                grid.add_point(record.center_x, record.center_y, 1.0)
        
        grid_data = grid.to_dict()
        hotspots = grid.get_hotspots(threshold=0.5)
        
        heatmap = Heatmap(
            heatmap_type="historical",
            time_period_start=start_date,
            time_period_end=end_date,
            grid_data=grid_data,
            width=grid.width,
            height=grid.height,
            cell_size=grid.cell_size,
            total_samples=len(records),
            max_intensity=float(grid.get_grid_data().max()),
            hotspot_count=len(hotspots)
        )
        
        self.session.add(heatmap)
        await self.session.flush()
        
        return {
            "heatmap_id": heatmap.id,
            "type": "historical",
            "period": f"{start_date.date()} to {end_date.date()}",
            "grid": grid_data,
            "hotspots": [
                {
                    "x": h.x,
                    "y": h.y,
                    "intensity": h.intensity,
                    "count": h.count
                }
                for h in hotspots
            ]
        }
    
    async def get_heatmap_by_hour(self, date: datetime, hour: int) -> Dict[str, Any]:
        """Get hourly heatmap"""
        start = datetime(date.year, date.month, date.day, hour, 0, 0)
        end = start + timedelta(hours=1)
        
        return await self.generate_historical_heatmap(start, end)
    
    async def get_latest_heatmap(self) -> Optional[Dict[str, Any]]:
        """Get most recent heatmap"""
        stmt = select(Heatmap).order_by(Heatmap.created_at.desc()).limit(1)
        result = await self.session.execute(stmt)
        heatmap = result.scalar_one_or_none()
        
        if not heatmap:
            return None
        
        return {
            "heatmap_id": heatmap.id,
            "type": heatmap.heatmap_type,
            "grid": heatmap.grid_data,
            "metadata": {
                "total_samples": heatmap.total_samples,
                "max_intensity": heatmap.max_intensity,
                "generated_at": heatmap.generated_at.isoformat()
            }
        }


class JourneyService:
    """Analyze and manage customer journeys"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.analyzer = JourneyAnalyzer()
    
    async def analyze_sessions(self) -> Dict[str, Any]:
        """Analyze all tracking sessions"""
        stmt = select(TrackingSession)
        result = await self.session.execute(stmt)
        sessions = result.scalars().all()
        
        journeys = []
        trajectories = []
        
        for session in sessions:
            if session.trajectory and len(session.trajectory) >= 3:
                trajectories.append(session.trajectory)
                
                journey = {
                    "session_id": session.id,
                    "customer_id": session.customer_id,
                    "path": session.trajectory,
                    "duration": (session.end_time - session.start_time).total_seconds() if session.end_time else 0,
                    "zones_visited": self._extract_zones(session.trajectory)
                }
                journeys.append(journey)
        
        # Cluster journeys
        clustered = self.analyzer.cluster_journeys(journeys)
        common_routes = self.analyzer.get_common_routes(journeys, top_n=10)
        
        # Store top routes
        for route, frequency in common_routes:
            route_str = "->".join(map(str, route))
            route_record = RouteAnalytics(
                zone_sequence=route_str,
                sequence_length=len(route),
                frequency=frequency,
                avg_duration=0.0,
                conversion_rate=0.0
            )
            self.session.add(route_record)
        
        return {
            "total_journeys": len(journeys),
            "unique_routes": len(clustered),
            "most_common_routes": [
                {
                    "zones": route,
                    "frequency": count
                }
                for route, count in common_routes[:5]
            ],
            "avg_journey_length": sum(len(j["path"]) for j in journeys) / len(journeys) if journeys else 0
        }
    
    def _extract_zones(self, path: List[tuple]) -> List[int]:
        """Extract zones from trajectory"""
        zones = []
        for point in path:
            zone = int(point[0] // 400) * 5 + int(point[1] // 300)
            if zone not in zones:
                zones.append(zone)
        return zones
    
    async def get_journey_summary(self, customer_id: str) -> Dict[str, Any]:
        """Get journey summary for customer"""
        stmt = select(TrackingSession).where(TrackingSession.customer_id == customer_id)
        result = await self.session.execute(stmt)
        sessions = result.scalars().all()
        
        total_distance = 0.0
        total_time = 0.0
        zones_visited = set()
        
        for session in sessions:
            if session.trajectory:
                total_distance += self._calculate_distance(session.trajectory)
            if session.end_time and session.start_time:
                total_time += (session.end_time - session.start_time).total_seconds()
            
            zones_visited.update(self._extract_zones(session.trajectory or []))
        
        return {
            "customer_id": customer_id,
            "sessions": len(sessions),
            "total_distance": total_distance,
            "total_time": total_time,
            "zones_visited": len(zones_visited),
            "avg_session_duration": total_time / len(sessions) if sessions else 0
        }
    
    def _calculate_distance(self, path: List[tuple]) -> float:
        """Calculate distance for path"""
        distance = 0.0
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            distance += ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        return distance


class ZoneEngagementService:
    """Analyze zone engagement metrics"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.engagement_analyzer = EngagementAnalyzer()
    
    async def calculate_zone_metrics(self, date: datetime) -> Dict[int, Dict[str, Any]]:
        """Calculate engagement metrics for all zones on date"""
        # Query data for date
        stmt = select(DwellTimeRecord).where(
            and_(
                DwellTimeRecord.created_at >= datetime(date.year, date.month, date.day),
                DwellTimeRecord.created_at < datetime(date.year, date.month, date.day) + timedelta(days=1)
            )
        )
        result = await self.session.execute(stmt)
        dwell_records = result.scalars().all()
        
        # Get interactions for date
        stmt = select(ShelfInteraction).where(
            and_(
                ShelfInteraction.created_at >= datetime(date.year, date.month, date.day),
                ShelfInteraction.created_at < datetime(date.year, date.month, date.day) + timedelta(days=1)
            )
        )
        result = await self.session.execute(stmt)
        interactions = result.scalars().all()
        
        # Aggregate by zone
        zone_data = {}
        for record in dwell_records:
            zone_id = record.zone_id
            if zone_id not in zone_data:
                zone_data[zone_id] = {
                    "zone_id": zone_id,
                    "dwell_times": [],
                    "visitors": set(),
                    "interactions": 0,
                    "pickups": 0,
                    "putbacks": 0
                }
            
            zone_data[zone_id]["dwell_times"].append(record.dwell_time_seconds)
            zone_data[zone_id]["visitors"].add(record.customer_id)
        
        # Add interaction data
        for interaction in interactions:
            zone_id = interaction.zone_id
            if zone_id not in zone_data:
                zone_data[zone_id] = {
                    "zone_id": zone_id,
                    "dwell_times": [],
                    "visitors": set(),
                    "interactions": 0,
                    "pickups": 0,
                    "putbacks": 0
                }
            
            zone_data[zone_id]["interactions"] += 1
            if interaction.interaction_type == "pickup":
                zone_data[zone_id]["pickups"] += 1
            elif interaction.interaction_type == "putback":
                zone_data[zone_id]["putbacks"] += 1
        
        # Calculate metrics
        zone_metrics = {}
        for zone_id, data in zone_data.items():
            avg_dwell = sum(data["dwell_times"]) / len(data["dwell_times"]) if data["dwell_times"] else 0
            visitor_count = len(data["visitors"])
            
            engagement = self.engagement_analyzer.analyze_zone_engagement({
                "zone_id": zone_id,
                "visitor_count": visitor_count,
                "avg_dwell_time": avg_dwell,
                "avg_interactions": data["interactions"] / visitor_count if visitor_count > 0 else 0,
                "pickup_count": data["pickups"]
            })
            
            zone_engagement = ZoneEngagement(
                zone_id=zone_id,
                analytics_date=date,
                time_bucket="daily",
                visitor_count=visitor_count,
                unique_visitor_count=visitor_count,
                total_dwell_time=sum(data["dwell_times"]),
                avg_dwell_time=avg_dwell,
                interaction_count=data["interactions"],
                avg_interactions=data["interactions"] / visitor_count if visitor_count > 0 else 0,
                pickup_count=data["pickups"],
                putback_count=data["putbacks"],
                conversion_rate=data["pickups"] / visitor_count if visitor_count > 0 else 0,
                engagement_score=engagement["engagement_score"],
                attention_score=engagement["attention_score"],
                performance_rating=self._rate_performance(engagement["engagement_score"])
            )
            
            self.session.add(zone_engagement)
            zone_metrics[zone_id] = engagement
        
        return zone_metrics
    
    def _rate_performance(self, score: float) -> str:
        """Rate zone performance"""
        if score >= 0.75:
            return "excellent"
        elif score >= 0.5:
            return "good"
        elif score >= 0.25:
            return "average"
        else:
            return "poor"


class InsightsService:
    """Generate business insights"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.insights_engine = BusinessInsightsEngine({})
    
    async def generate_daily_insights(self, date: datetime) -> Dict[str, Any]:
        """Generate daily insights"""
        # Get zone engagement data
        stmt = select(ZoneEngagement).where(ZoneEngagement.analytics_date == date)
        result = await self.session.execute(stmt)
        zones = result.scalars().all()
        
        # Convert to dict
        zone_data = [
            {
                "zone_id": z.zone_id,
                "engagement_score": z.engagement_score,
                "visitor_count": z.visitor_count,
                "conversion_rate": z.conversion_rate,
                "avg_dwell_time": z.avg_dwell_time
            }
            for z in zones
        ]
        
        analytics_data = {
            "zones": zone_data,
            "hourly_traffic": {},
            "common_routes": [],
            "overall_engagement_score": sum(z["engagement_score"] for z in zone_data) / len(zone_data) if zone_data else 0,
            "avg_journey_length": 0
        }
        
        insights = self.insights_engine.generate_insights(analytics_data)
        
        # Store top insights
        for insight_type, data in insights.items():
            if isinstance(data, list) and data:
                insight_record = BusinessInsight(
                    insight_type=insight_type,
                    category="analytics",
                    title=f"{insight_type.replace('_', ' ').title()}",
                    description=str(data[:1]),
                    details=data,
                    period_start=date,
                    period_end=date + timedelta(days=1),
                    severity="medium",
                    confidence_score=0.85
                )
                self.session.add(insight_record)
        
        return insights
    
    async def get_top_insights(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top recent insights"""
        stmt = select(BusinessInsight).order_by(BusinessInsight.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        insights = result.scalars().all()
        
        return [
            {
                "insight_id": i.id,
                "title": i.title,
                "description": i.description,
                "severity": i.severity,
                "confidence_score": i.confidence_score
            }
            for i in insights
        ]


class AnalyticsReportService:
    """Generate comprehensive analytics reports"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def generate_report(self,
                            report_type: str,
                            start_date: datetime,
                            end_date: datetime) -> Dict[str, Any]:
        """Generate comprehensive report"""
        # Get zone engagement
        stmt = select(ZoneEngagement).where(
            and_(
                ZoneEngagement.analytics_date >= start_date,
                ZoneEngagement.analytics_date <= end_date
            )
        )
        result = await self.session.execute(stmt)
        zones = result.scalars().all()
        
        # Get insights
        stmt = select(BusinessInsight).where(
            and_(
                BusinessInsight.period_start >= start_date,
                BusinessInsight.period_end <= end_date
            )
        ).limit(10)
        result = await self.session.execute(stmt)
        insights = result.scalars().all()
        
        # Calculate metrics
        total_customers = sum(z.visitor_count for z in zones) if zones else 0
        total_pickups = sum(z.pickup_count for z in zones) if zones else 0
        total_interactions = sum(z.interaction_count for z in zones) if zones else 0
        avg_engagement = sum(z.engagement_score for z in zones) / len(zones) if zones else 0
        
        top_zones = sorted(
            zones,
            key=lambda z: z.engagement_score,
            reverse=True
        )[:5]
        
        report = {
            "report_id": str(datetime.utcnow().timestamp()),
            "report_type": report_type,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_customers": total_customers,
            "total_interactions": total_interactions,
            "overall_conversion_rate": total_pickups / total_customers if total_customers > 0 else 0,
            "overall_engagement_score": avg_engagement,
            "top_zones": [
                {
                    "zone_id": z.zone_id,
                    "engagement_score": z.engagement_score,
                    "visitor_count": z.visitor_count,
                    "performance_rating": z.performance_rating
                }
                for z in top_zones
            ],
            "key_insights": [
                {
                    "title": i.title,
                    "description": i.description,
                    "severity": i.severity
                }
                for i in insights[:3]
            ],
            "recommendations": [
                "Optimize underperforming zones with better product placement",
                "Allocate more staff during peak hours",
                "Implement promotional strategies for high-value zones",
                "Review pricing for conversion optimization"
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Store report as snapshot
        snapshot = AnalyticsSnapshot(
            snapshot_date=datetime.utcnow(),
            period_type=report_type,
            top_zones=[z.to_dict() for z in top_zones],
            top_insights=[i.to_dict() for i in insights[:3]],
            key_recommendations=report["recommendations"],
            summary_text=f"Analytics Report for {start_date.date()} to {end_date.date()}"
        )
        self.session.add(snapshot)
        
        return report
    
    async def list_reports(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """List generated reports"""
        stmt = select(AnalyticsSnapshot).order_by(
            AnalyticsSnapshot.created_at.desc()
        ).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        snapshots = result.scalars().all()
        
        return [
            {
                "id": s.id,
                "date": s.snapshot_date.isoformat(),
                "period_type": s.period_type,
                "summary": s.summary_text
            }
            for s in snapshots
        ]
    
    async def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get specific report"""
        stmt = select(AnalyticsSnapshot).where(AnalyticsSnapshot.id == report_id)
        result = await self.session.execute(stmt)
        snapshot = result.scalar()
        
        if not snapshot:
            return None
        
        return {
            "id": snapshot.id,
            "date": snapshot.snapshot_date.isoformat(),
            "period_type": snapshot.period_type,
            "summary": snapshot.summary_text,
            "top_zones": snapshot.top_zones,
            "insights": snapshot.top_insights,
            "recommendations": snapshot.key_recommendations
        }

        return [
            {
                "id": i.id,
                "type": i.insight_type,
                "title": i.title,
                "description": i.description,
                "severity": i.severity,
                "created_at": i.created_at.isoformat()
            }
            for i in insights
        ]
