"""
Phase 4: Analytics Metrics Engine

Aggregates and computes retail metrics from detection and interaction data.
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

from ..analytics.models import ZoneMetrics, StoreMetrics
from .detector import InteractionDetector
from .dwell_analytics import DwellAnalytics

logger = logging.getLogger(__name__)


class AnalyticsMetricsEngine:
    """Computes aggregated retail metrics"""

    def __init__(self, interaction_detector: InteractionDetector, dwell_analytics: DwellAnalytics):
        """Initialize metrics engine"""
        self.interaction_detector = interaction_detector
        self.dwell_analytics = dwell_analytics
        self.metrics_history: List[Dict] = []
        self.zone_popularity: Dict[str, int] = defaultdict(int)
        self.customer_segments: Dict[str, List[int]] = defaultdict(list)

    def compute_zone_metrics(self, zone_id: str) -> Optional[ZoneMetrics]:
        """Compute metrics for a zone"""
        
        dwell_metrics = self.dwell_analytics.get_zone_dwell_metrics(zone_id)
        if not dwell_metrics:
            return None

        # Get unique customers in zone
        unique_customers = set()
        for profile in self.interaction_detector.customer_profiles.values():
            if zone_id in profile.total_zones_visited:
                unique_customers.add(profile.track_id)

        # Count interactions in zone
        total_interactions = sum(
            1 for interaction in self.interaction_detector.interaction_history
            if interaction.zone_id == zone_id
        )

        # Calculate engagement rate
        engagement_rate = self.dwell_analytics.get_engagement_rate(zone_id)

        # Get peak hours
        peak_hours_dict = self.dwell_analytics.get_peak_hours(zone_id)
        peak_hours = sorted(peak_hours_dict.keys(), key=lambda h: peak_hours_dict[h], reverse=True)[:3]

        metrics = ZoneMetrics(
            zone_id=zone_id,
            name=zone_id,
            total_visits=dwell_metrics['visit_count'],
            total_interactions=total_interactions,
            average_dwell_time=dwell_metrics['avg_time'],
            max_dwell_time=dwell_metrics['max_time'],
            min_dwell_time=dwell_metrics['min_time'],
            unique_customers=len(unique_customers),
            engagement_rate=engagement_rate,
            peak_hours=peak_hours
        )

        return metrics

    def compute_store_metrics(self) -> StoreMetrics:
        """Compute overall store metrics"""
        
        # Total customers
        total_customers = len(self.interaction_detector.customer_profiles)

        # Average store time
        store_times = []
        for profile in self.interaction_detector.customer_profiles.values():
            store_times.append(profile.duration_in_store)

        avg_store_time = statistics.mean(store_times) if store_times else 0

        # Popular zones
        all_zones = set()
        zone_visit_counts = defaultdict(int)
        
        for profile in self.interaction_detector.customer_profiles.values():
            for zone_id in profile.total_zones_visited:
                all_zones.add(zone_id)
                zone_visit_counts[zone_id] += 1

        popular_zones = [
            zone_id for zone_id, _ in sorted(
                zone_visit_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        ]

        # Total interactions
        total_interactions = len(self.interaction_detector.interaction_history)

        # Anomaly count
        anomaly_count = sum(
            len(p.anomaly_flags)
            for p in self.interaction_detector.customer_profiles.values()
        )

        # Peak hours
        all_peak_hours = defaultdict(int)
        for zone_id in all_zones:
            zone_peaks = self.dwell_analytics.get_peak_hours(zone_id)
            for hour, count in zone_peaks.items():
                all_peak_hours[hour] += count

        peak_hours = [
            hour for hour, _ in sorted(
                all_peak_hours.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        ]

        # Compute metrics for each zone
        zone_metrics = {}
        for zone_id in all_zones:
            zone_m = self.compute_zone_metrics(zone_id)
            if zone_m:
                zone_metrics[zone_id] = zone_m.dict()

        metrics = StoreMetrics(
            total_customers=total_customers,
            average_store_time=avg_store_time,
            popular_zones=popular_zones,
            total_interactions=total_interactions,
            anomaly_count=anomaly_count,
            peak_hours=peak_hours,
            zone_metrics=zone_metrics
        )

        return metrics

    def get_top_engaged_zones(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """Get zones with highest average dwell time"""
        return self.dwell_analytics.get_top_zones_by_dwell(top_n)

    def get_customer_segments(self) -> Dict[str, List[int]]:
        """Segment customers by behavior"""
        
        segments = {
            'browsers': [],
            'comparers': [],
            'purchasers': [],
            'suspicious': []
        }

        for track_id, profile in self.interaction_detector.customer_profiles.items():
            behavior = profile.behavior_classification.value
            
            if behavior == 'suspicious':
                segments['suspicious'].append(track_id)
            elif behavior == 'purchasing':
                segments['purchasers'].append(track_id)
            elif behavior == 'comparing':
                segments['comparers'].append(track_id)
            else:
                segments['browsers'].append(track_id)

        return segments

    def get_interaction_heatmap(self, zone_id: str) -> Dict[str, int]:
        """Get interaction heatmap for zone"""
        
        heatmap = defaultdict(int)
        
        for interaction in self.interaction_detector.interaction_history:
            if interaction.zone_id == zone_id:
                hour = interaction.timestamp.hour
                heatmap[f"hour_{hour}"] += 1

        return dict(heatmap)

    def get_customer_lifetime_value(self, track_id: int) -> Dict:
        """Estimate customer value metrics"""
        
        profile = self.interaction_detector.customer_profiles.get(track_id)
        if not profile:
            return {}

        # Calculate purchase likelihood based on engagement
        engagement_interactions = sum(
            1 for i in profile.interactions
            if i.interaction_type.value in ['engagement', 'compare', 'pickup']
        )

        purchase_likelihood = min(engagement_interactions / 5, 1.0)

        # Calculate store value (time spent)
        store_value_score = profile.duration_in_store / 300  # Normalized to 5 min baseline

        return {
            'track_id': track_id,
            'zones_visited': len(profile.total_zones_visited),
            'total_interactions': len(profile.interactions),
            'total_dwell_time': profile.total_dwell_time,
            'purchase_likelihood': purchase_likelihood,
            'store_value_score': store_value_score,
            'anomaly_count': len(profile.anomaly_flags)
        }

    def get_movement_patterns(self) -> Dict:
        """Analyze customer movement patterns"""
        
        zone_transitions = defaultdict(lambda: defaultdict(int))
        
        # Analyze transitions between zones
        for profile in self.interaction_detector.customer_profiles.values():
            zone_sequence = []
            
            for interaction in sorted(profile.interactions, key=lambda x: x.timestamp):
                if interaction.zone_id not in zone_sequence:
                    zone_sequence.append(interaction.zone_id)
            
            # Count transitions
            for i in range(len(zone_sequence) - 1):
                from_zone = zone_sequence[i]
                to_zone = zone_sequence[i + 1]
                zone_transitions[from_zone][to_zone] += 1

        # Convert to dictionary format
        transitions_dict = {
            zone: dict(dests)
            for zone, dests in zone_transitions.items()
        }

        return {
            'zone_transitions': transitions_dict,
            'total_patterns': len(zone_transitions)
        }

    def get_crowd_analysis(self) -> Dict:
        """Analyze crowd density patterns"""
        
        zone_crowd_levels = defaultdict(list)
        
        # Group sessions by hour
        for zone_id, sessions in self.interaction_detector.zone_sessions.items():
            for track_id, session in sessions.items():
                hour = session.entry_time.hour
                zone_crowd_levels[zone_id].append(hour)

        # Compute statistics
        crowd_stats = {}
        for zone_id, hours in zone_crowd_levels.items():
            if hours:
                crowd_stats[zone_id] = {
                    'peak_hour': max(set(hours), key=hours.count),
                    'avg_crowd': len(hours),
                    'max_crowd': hours.count(max(set(hours), key=hours.count))
                }

        return crowd_stats

    def export_metrics_snapshot(self) -> Dict:
        """Export current metrics snapshot"""
        
        store_metrics = self.compute_store_metrics()
        
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'store_metrics': store_metrics.dict(),
            'customer_segments': self.get_customer_segments(),
            'movement_patterns': self.get_movement_patterns(),
            'crowd_analysis': self.get_crowd_analysis(),
            'top_zones': [
                {'zone': z, 'avg_dwell': t}
                for z, t in self.get_top_engaged_zones(top_n=5)
            ]
        }

        self.metrics_history.append(snapshot)
        logger.debug(f"Exported metrics snapshot")

        return snapshot

    def get_metrics_history(self, hours: int = 1) -> List[Dict]:
        """Get metrics history"""
        
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            m for m in self.metrics_history
            if datetime.fromisoformat(m['timestamp']) > cutoff
        ]

    def reset(self):
        """Reset metrics"""
        self.metrics_history.clear()
        self.zone_popularity.clear()
        self.customer_segments.clear()
        logger.info("Analytics metrics reset")
