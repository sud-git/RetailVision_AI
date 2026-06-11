"""
Phase 4: Advanced Dwell Time Analytics

Tracks and aggregates dwell time metrics per customer and zone.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import statistics

from ..analytics.models import DwellAnalyticsConfig, ZoneMetrics, StoreMetrics, ZoneDwellSession

logger = logging.getLogger(__name__)


@dataclass
class DwellTimeMetrics:
    """Dwell time metrics for an entity"""
    total_time: float = 0.0
    visit_count: int = 0
    avg_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    std_dev: float = 0.0
    time_samples: List[float] = field(default_factory=list)

    def add_sample(self, duration: float):
        """Add a dwell time sample"""
        self.total_time += duration
        self.visit_count += 1
        self.time_samples.append(duration)
        
        if duration < self.min_time:
            self.min_time = duration
        if duration > self.max_time:
            self.max_time = duration

        self._update_stats()

    def _update_stats(self):
        """Update aggregated statistics"""
        if self.visit_count == 0:
            return

        self.avg_time = self.total_time / self.visit_count
        
        if len(self.time_samples) > 1:
            self.std_dev = statistics.stdev(self.time_samples)


class DwellAnalytics:
    """Advanced dwell time analytics"""

    def __init__(self, config: DwellAnalyticsConfig):
        """Initialize analytics engine"""
        self.config = config
        
        # Per-zone metrics
        self.zone_dwell_metrics: Dict[str, DwellTimeMetrics] = defaultdict(DwellTimeMetrics)
        
        # Per-customer metrics
        self.customer_dwell_metrics: Dict[int, DwellTimeMetrics] = defaultdict(DwellTimeMetrics)
        
        # Zone-specific customer metrics: {zone_id: {track_id: DwellTimeMetrics}}
        self.zone_customer_metrics: Dict[str, Dict[int, DwellTimeMetrics]] = defaultdict(
            lambda: defaultdict(DwellTimeMetrics)
        )
        
        # Time-series data for heatmaps
        self.hourly_zones: Dict[str, Dict[int, float]] = defaultdict(lambda: defaultdict(float))
        self.hourly_customers: Dict[int, Dict[int, float]] = defaultdict(lambda: defaultdict(float))
        
        # Peak hour tracking
        self.zone_peak_hours: Dict[str, List[int]] = defaultdict(list)
        self.customer_peak_hours: Dict[int, List[int]] = defaultdict(list)

    def record_dwell_session(
        self,
        track_id: int,
        zone_id: str,
        session: ZoneDwellSession,
        timestamp: datetime
    ):
        """Record a completed dwell session"""
        
        duration = session.duration_seconds
        
        # Skip very short sessions
        if duration < self.config.min_dwell_time:
            return

        # Update zone metrics
        self.zone_dwell_metrics[zone_id].add_sample(duration)
        
        # Update customer metrics
        self.customer_dwell_metrics[track_id].add_sample(duration)
        
        # Update zone-customer metrics
        self.zone_customer_metrics[zone_id][track_id].add_sample(duration)
        
        # Update hourly tracking
        hour = timestamp.hour
        self.hourly_zones[zone_id][hour] += duration
        self.hourly_customers[track_id][hour] += duration
        
        logger.debug(
            f"Recorded dwell: track={track_id}, zone={zone_id}, "
            f"duration={duration:.2f}s"
        )

    def get_zone_dwell_metrics(self, zone_id: str) -> Optional[Dict]:
        """Get dwell metrics for a zone"""
        if zone_id not in self.zone_dwell_metrics:
            return None

        metrics = self.zone_dwell_metrics[zone_id]
        return {
            'zone_id': zone_id,
            'total_time': metrics.total_time,
            'visit_count': metrics.visit_count,
            'avg_time': metrics.avg_time,
            'min_time': metrics.min_time if metrics.min_time != float('inf') else 0,
            'max_time': metrics.max_time,
            'std_dev': metrics.std_dev
        }

    def get_customer_dwell_metrics(self, track_id: int) -> Optional[Dict]:
        """Get dwell metrics for a customer"""
        if track_id not in self.customer_dwell_metrics:
            return None

        metrics = self.customer_dwell_metrics[track_id]
        return {
            'track_id': track_id,
            'total_time': metrics.total_time,
            'visit_count': metrics.visit_count,
            'avg_time': metrics.avg_time,
            'min_time': metrics.min_time if metrics.min_time != float('inf') else 0,
            'max_time': metrics.max_time,
            'std_dev': metrics.std_dev
        }

    def get_zone_customer_dwell_metrics(self, zone_id: str, track_id: int) -> Optional[Dict]:
        """Get dwell metrics for customer in specific zone"""
        if zone_id not in self.zone_customer_metrics or track_id not in self.zone_customer_metrics[zone_id]:
            return None

        metrics = self.zone_customer_metrics[zone_id][track_id]
        return {
            'zone_id': zone_id,
            'track_id': track_id,
            'total_time': metrics.total_time,
            'visit_count': metrics.visit_count,
            'avg_time': metrics.avg_time
        }

    def get_top_zones_by_dwell(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """Get top zones by average dwell time"""
        zones = [
            (zone_id, metrics.avg_time)
            for zone_id, metrics in self.zone_dwell_metrics.items()
            if metrics.visit_count > 0
        ]
        zones.sort(key=lambda x: x[1], reverse=True)
        return zones[:top_n]

    def get_peak_hours(self, zone_id: Optional[str] = None) -> Dict[int, float]:
        """Get peak hours for zone or overall"""
        if zone_id:
            hours = self.hourly_zones.get(zone_id, {})
        else:
            # Aggregate across all zones
            hours = defaultdict(float)
            for zone_hours in self.hourly_zones.values():
                for hour, duration in zone_hours.items():
                    hours[hour] += duration

        return dict(hours)

    def get_heatmap_data(self, zone_id: str) -> Dict[int, float]:
        """Get heatmap data (hourly dwell time) for zone"""
        return dict(self.hourly_zones.get(zone_id, {}))

    def get_engagement_rate(self, zone_id: str, threshold_seconds: float = 10.0) -> float:
        """Get engagement rate (% of visitors with sufficient dwell time)"""
        if zone_id not in self.zone_customer_metrics:
            return 0.0

        customers = self.zone_customer_metrics[zone_id]
        if not customers:
            return 0.0

        engaged = sum(
            1 for metrics in customers.values()
            if metrics.avg_time >= threshold_seconds
        )

        return (engaged / len(customers)) * 100

    def get_store_summary(self) -> Dict:
        """Get overall store dwell statistics"""
        if not self.zone_dwell_metrics:
            return {}

        total_dwell = sum(m.total_time for m in self.zone_dwell_metrics.values())
        total_visits = sum(m.visit_count for m in self.zone_dwell_metrics.values())
        avg_dwell = total_dwell / total_visits if total_visits > 0 else 0

        zone_rankings = self.get_top_zones_by_dwell(top_n=5)

        return {
            'total_dwell_time': total_dwell,
            'total_zone_visits': total_visits,
            'avg_zone_dwell': avg_dwell,
            'unique_zones': len(self.zone_dwell_metrics),
            'top_zones': [{'zone': z, 'avg_time': t} for z, t in zone_rankings],
            'peak_hours': self.get_peak_hours()
        }

    def get_customer_journey(self, track_id: int) -> Dict:
        """Get customer's dwell journey through zones"""
        if track_id not in self.zone_customer_metrics:
            return {}

        zones = self.zone_customer_metrics[track_id]
        journey = []

        for zone_id, metrics in zones.items():
            journey.append({
                'zone_id': zone_id,
                'visits': metrics.visit_count,
                'total_time': metrics.total_time,
                'avg_time': metrics.avg_time
            })

        journey.sort(key=lambda x: x['total_time'], reverse=True)
        return {
            'track_id': track_id,
            'zones_visited': journey,
            'total_time': self.customer_dwell_metrics[track_id].total_time
        }

    def reset_analytics(self):
        """Reset all analytics data"""
        self.zone_dwell_metrics.clear()
        self.customer_dwell_metrics.clear()
        self.zone_customer_metrics.clear()
        self.hourly_zones.clear()
        self.hourly_customers.clear()
        self.zone_peak_hours.clear()
        self.customer_peak_hours.clear()
        logger.info("Analytics reset")

    def export_metrics(self) -> Dict:
        """Export all metrics"""
        return {
            'zone_metrics': {
                zone_id: self.get_zone_dwell_metrics(zone_id)
                for zone_id in self.zone_dwell_metrics.keys()
            },
            'store_summary': self.get_store_summary(),
            'timestamp': datetime.now().isoformat()
        }
