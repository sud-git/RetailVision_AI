"""
Advanced Analytics Engine for RetailVision AI

Provides:
- Customer movement heatmap generation
- Customer journey tracking and analysis
- Zone intelligence and engagement metrics
- Business insights and recommendations
- Real-time and historical analytics
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Set
import numpy as np
from collections import defaultdict
from enum import Enum


class EngagementLevel(str, Enum):
    """Engagement level classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ZoneType(str, Enum):
    """Zone classification"""
    ENTRY = "entry"
    HIGH_VALUE = "high_value"
    ENGAGEMENT = "engagement"
    CONVERSION = "conversion"
    EXIT = "exit"
    DEAD_ZONE = "dead_zone"


class HeatmapPoint:
    """Single point in heatmap"""
    def __init__(self, x: float, y: float, intensity: float, count: int):
        self.x = x
        self.y = y
        self.intensity = intensity  # 0.0 to 1.0
        self.count = count


class HeatmapGrid:
    """2D heatmap grid with spatial analysis"""
    
    def __init__(self, width: int = 1920, height: int = 1080, cell_size: int = 40):
        """
        Initialize heatmap grid
        
        Args:
            width: Frame width in pixels
            height: Frame height in pixels
            cell_size: Size of each grid cell in pixels
        """
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.cols = (width + cell_size - 1) // cell_size
        self.rows = (height + cell_size - 1) // cell_size
        self.grid = np.zeros((self.rows, self.cols), dtype=np.float32)
        self.counts = np.zeros((self.rows, self.cols), dtype=np.int32)
    
    def add_point(self, x: float, y: float, intensity: float = 1.0):
        """Add a point to the heatmap"""
        col = int(x / self.cell_size)
        row = int(y / self.cell_size)
        
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.grid[row, col] += intensity
            self.counts[row, col] += 1
    
    def add_trajectory(self, points: List[Tuple[float, float]], intensity: float = 1.0):
        """Add a trajectory (connected points) to heatmap"""
        for point in points:
            self.add_point(point[0], point[1], intensity)
    
    def get_grid_data(self) -> np.ndarray:
        """Get normalized grid (0 to 1)"""
        max_val = np.max(self.grid)
        if max_val > 0:
            return self.grid / max_val
        return self.grid
    
    def get_hotspots(self, threshold: float = 0.7) -> List[HeatmapPoint]:
        """Get hotspots above threshold"""
        normalized = self.get_grid_data()
        hotspots = []
        
        for row in range(self.rows):
            for col in range(self.cols):
                if normalized[row, col] >= threshold:
                    x = col * self.cell_size + self.cell_size / 2
                    y = row * self.cell_size + self.cell_size / 2
                    hotspots.append(HeatmapPoint(
                        x, y,
                        float(normalized[row, col]),
                        int(self.counts[row, col])
                    ))
        
        return sorted(hotspots, key=lambda p: p.intensity, reverse=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export grid as dictionary"""
        return {
            "grid": self.get_grid_data().tolist(),
            "width": self.width,
            "height": self.height,
            "cell_size": self.cell_size,
            "cols": self.cols,
            "rows": self.rows
        }


class JourneyAnalyzer:
    """Analyze customer journeys and paths"""
    
    def __init__(self, min_path_length: int = 3):
        """
        Initialize journey analyzer
        
        Args:
            min_path_length: Minimum points to consider a valid journey
        """
        self.min_path_length = min_path_length
    
    def extract_journeys(self, trajectories: List[List[Tuple[float, float]]]) -> List[Dict[str, Any]]:
        """Extract journeys from trajectories"""
        journeys = []
        
        for traj in trajectories:
            if len(traj) >= self.min_path_length:
                journey = {
                    "path": traj,
                    "length": len(traj),
                    "distance": self._calculate_distance(traj),
                    "duration_estimate": len(traj) * 0.5,  # 0.5s per frame
                    "zones_visited": self._extract_zones(traj),
                    "start_point": traj[0],
                    "end_point": traj[-1]
                }
                journeys.append(journey)
        
        return journeys
    
    def _calculate_distance(self, path: List[Tuple[float, float]]) -> float:
        """Calculate total distance traveled"""
        distance = 0.0
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            distance += ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        return distance
    
    def _extract_zones(self, path: List[Tuple[float, float]]) -> List[int]:
        """Extract zones visited in path"""
        zones = []
        for point in path:
            zone = self._point_to_zone(point)
            if zone not in zones:
                zones.append(zone)
        return zones
    
    def _point_to_zone(self, point: Tuple[float, float]) -> int:
        """Map point to zone ID (simple grid-based)"""
        x, y = point
        zone_x = int(x // 400)  # 400px per zone
        zone_y = int(y // 300)  # 300px per zone
        return zone_y * 5 + zone_x  # Assume 5 columns
    
    def cluster_journeys(self, journeys: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Cluster similar journeys"""
        clusters = defaultdict(list)
        
        for journey in journeys:
            zones = tuple(journey["zones_visited"])
            clusters[zones].append(journey)
        
        # Sort clusters by frequency
        return dict(sorted(
            clusters.items(),
            key=lambda x: len(x[1]),
            reverse=True
        ))
    
    def get_common_routes(self, journeys: List[Dict[str, Any]], top_n: int = 5) -> List[Tuple[List[int], int]]:
        """Get most common routes (zone sequences)"""
        route_counts = defaultdict(int)
        
        for journey in journeys:
            zones = tuple(journey["zones_visited"])
            route_counts[zones] += 1
        
        sorted_routes = sorted(
            route_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [(list(route), count) for route, count in sorted_routes[:top_n]]


class EngagementAnalyzer:
    """Analyze customer engagement with products/zones"""
    
    def calculate_engagement_score(self,
                                   dwell_time: float,
                                   interaction_count: int,
                                   pickup_count: int) -> float:
        """
        Calculate engagement score (0 to 1)
        
        Args:
            dwell_time: Time spent in seconds
            interaction_count: Number of interactions
            pickup_count: Number of pickups
        """
        # Weighted scoring
        dwell_score = min(dwell_time / 120.0, 1.0) * 0.4  # Max 2min
        interaction_score = min(interaction_count / 5.0, 1.0) * 0.35
        pickup_score = min(pickup_count / 2.0, 1.0) * 0.25
        
        return dwell_score + interaction_score + pickup_score
    
    def classify_engagement(self, score: float) -> EngagementLevel:
        """Classify engagement level by score"""
        if score >= 0.75:
            return EngagementLevel.VERY_HIGH
        elif score >= 0.5:
            return EngagementLevel.HIGH
        elif score >= 0.25:
            return EngagementLevel.MEDIUM
        else:
            return EngagementLevel.LOW
    
    def analyze_zone_engagement(self, zone_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze engagement metrics for a zone"""
        total_visitors = zone_data.get("visitor_count", 0)
        
        engagement_scores = []
        pickup_count = zone_data.get("pickup_count", 0)
        
        if total_visitors > 0:
            avg_dwell = zone_data.get("avg_dwell_time", 0)
            avg_interactions = zone_data.get("avg_interactions", 0)
            avg_pickups = pickup_count / total_visitors
            
            engagement_score = self.calculate_engagement_score(
                avg_dwell,
                avg_interactions,
                avg_pickups
            )
        else:
            engagement_score = 0.0
        
        return {
            "zone_id": zone_data.get("zone_id"),
            "engagement_score": engagement_score,
            "engagement_level": self.classify_engagement(engagement_score),
            "visitor_count": total_visitors,
            "conversion_rate": (pickup_count / total_visitors) if total_visitors > 0 else 0,
            "avg_dwell_time": zone_data.get("avg_dwell_time", 0),
            "attention_score": min(1.0, len(engagement_scores) / 10.0) if engagement_scores else 0
        }


class BusinessInsightsEngine:
    """Generate business intelligence insights"""
    
    def __init__(self, zone_configs: Dict[int, Dict[str, Any]]):
        """
        Initialize with zone configurations
        
        Args:
            zone_configs: Zone configuration data
        """
        self.zone_configs = zone_configs
    
    def generate_insights(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive business insights"""
        return {
            "top_performing_zones": self._get_top_zones(analytics_data),
            "underperforming_zones": self._get_bottom_zones(analytics_data),
            "peak_traffic_periods": self._identify_peak_periods(analytics_data),
            "customer_flow_patterns": self._analyze_flow(analytics_data),
            "engagement_trends": self._analyze_trends(analytics_data),
            "recommendations": self._generate_recommendations(analytics_data)
        }
    
    def _get_top_zones(self, data: Dict[str, Any], top_n: int = 5) -> List[Dict[str, Any]]:
        """Get top performing zones"""
        zones = data.get("zones", [])
        zones_sorted = sorted(
            zones,
            key=lambda z: z.get("engagement_score", 0),
            reverse=True
        )
        return zones_sorted[:top_n]
    
    def _get_bottom_zones(self, data: Dict[str, Any], bottom_n: int = 3) -> List[Dict[str, Any]]:
        """Get underperforming zones"""
        zones = data.get("zones", [])
        zones_sorted = sorted(
            zones,
            key=lambda z: z.get("engagement_score", 0)
        )
        return zones_sorted[:bottom_n]
    
    def _identify_peak_periods(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify peak traffic periods"""
        hourly_data = data.get("hourly_traffic", {})
        
        periods = [
            {"hour": h, "traffic": count}
            for h, count in hourly_data.items()
        ]
        
        return sorted(periods, key=lambda p: p["traffic"], reverse=True)[:3]
    
    def _analyze_flow(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze customer flow patterns"""
        routes = data.get("common_routes", [])
        
        return {
            "top_entry_zones": self._get_entry_zones(data),
            "top_exit_zones": self._get_exit_zones(data),
            "most_common_routes": routes[:5],
            "average_journey_length": data.get("avg_journey_length", 0)
        }
    
    def _analyze_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze engagement trends"""
        return {
            "overall_engagement": data.get("overall_engagement_score", 0),
            "engagement_distribution": data.get("engagement_distribution", {}),
            "trend_direction": self._calculate_trend(data),
            "engagement_by_hour": data.get("hourly_engagement", {})
        }
    
    def _get_entry_zones(self, data: Dict[str, Any], top_n: int = 3) -> List[Dict[str, Any]]:
        """Get zones with highest entry traffic"""
        zones = data.get("zones", [])
        return sorted(zones, key=lambda z: z.get("entry_count", 0), reverse=True)[:top_n]
    
    def _get_exit_zones(self, data: Dict[str, Any], top_n: int = 3) -> List[Dict[str, Any]]:
        """Get zones with highest exit traffic"""
        zones = data.get("zones", [])
        return sorted(zones, key=lambda z: z.get("exit_count", 0), reverse=True)[:top_n]
    
    def _calculate_trend(self, data: Dict[str, Any]) -> str:
        """Calculate trend direction"""
        current = data.get("current_engagement", 0)
        previous = data.get("previous_engagement", 0)
        
        if current > previous * 1.1:
            return "increasing"
        elif current < previous * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    def _generate_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Check underperforming zones
        bottom_zones = self._get_bottom_zones(data)
        if bottom_zones:
            zone_id = bottom_zones[0].get("zone_id")
            recommendations.append(
                f"Zone {zone_id} is underperforming. Consider repositioning products or improving visibility."
            )
        
        # Check conversion rates
        zones = data.get("zones", [])
        low_conversion = [z for z in zones if z.get("conversion_rate", 0) < 0.1]
        if low_conversion:
            recommendations.append(
                f"{len(low_conversion)} zones have low conversion rates. Review product placement and pricing."
            )
        
        # Check peak periods
        peaks = self._identify_peak_periods(data)
        if peaks:
            recommendations.append(
                f"Plan staff and inventory around peak hours: {peaks[0]['hour']}:00"
            )
        
        # Check flow patterns
        routes = data.get("common_routes", [])
        if not routes:
            recommendations.append(
                "Add wayfinding or promotional materials to guide customer flow."
            )
        
        return recommendations


class AnalyticsAggregator:
    """Aggregate analytics data from multiple sources"""
    
    @staticmethod
    def aggregate_zone_analytics(tracking_sessions: List[Dict[str, Any]],
                                 interactions: List[Dict[str, Any]],
                                 dwell_records: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """
        Aggregate analytics by zone
        
        Args:
            tracking_sessions: List of customer tracking sessions
            interactions: List of shelf interactions
            dwell_records: List of dwell time records
        
        Returns:
            Dictionary mapping zone_id to analytics
        """
        zones = defaultdict(lambda: {
            "zone_id": None,
            "visitor_count": 0,
            "total_dwell_time": 0.0,
            "avg_dwell_time": 0.0,
            "interaction_count": 0,
            "avg_interactions": 0.0,
            "pickup_count": 0,
            "putback_count": 0,
            "entry_count": 0,
            "exit_count": 0,
            "unique_customers": set()
        })
        
        # Aggregate dwell time data
        for record in dwell_records:
            zone_id = record.get("zone_id")
            zones[zone_id]["zone_id"] = zone_id
            zones[zone_id]["visitor_count"] += 1
            zones[zone_id]["total_dwell_time"] += record.get("dwell_time_seconds", 0)
            zones[zone_id]["unique_customers"].add(record.get("customer_id"))
        
        # Calculate averages
        for zone_id, data in zones.items():
            if data["visitor_count"] > 0:
                data["avg_dwell_time"] = data["total_dwell_time"] / data["visitor_count"]
        
        # Aggregate interactions
        for interaction in interactions:
            zone_id = interaction.get("zone_id")
            if zone_id in zones:
                zones[zone_id]["interaction_count"] += 1
                
                interaction_type = interaction.get("interaction_type")
                if interaction_type == "pickup":
                    zones[zone_id]["pickup_count"] += 1
                elif interaction_type == "putback":
                    zones[zone_id]["putback_count"] += 1
        
        # Convert sets to counts
        for zone_data in zones.values():
            zone_data["unique_visitor_count"] = len(zone_data["unique_customers"])
            del zone_data["unique_customers"]
        
        return dict(zones)
    
    @staticmethod
    def calculate_hourly_metrics(data_points: List[Dict[str, Any]],
                                 date: datetime) -> Dict[int, Dict[str, Any]]:
        """Calculate hourly aggregated metrics"""
        hourly = defaultdict(lambda: {
            "traffic_count": 0,
            "engagement_scores": [],
            "interactions": 0,
            "pickups": 0
        })
        
        for point in data_points:
            timestamp = point.get("timestamp")
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            if timestamp.date() == date.date():
                hour = timestamp.hour
                hourly[hour]["traffic_count"] += 1
                if "engagement_score" in point:
                    hourly[hour]["engagement_scores"].append(point["engagement_score"])
        
        # Calculate averages
        for hour_data in hourly.values():
            if hour_data["engagement_scores"]:
                hour_data["avg_engagement"] = np.mean(hour_data["engagement_scores"])
            else:
                hour_data["avg_engagement"] = 0
        
        return dict(hourly)
