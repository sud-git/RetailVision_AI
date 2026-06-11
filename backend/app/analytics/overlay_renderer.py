"""
Phase 4: Enhanced Overlay Renderer

Visualizes interactions, dwell time, alerts, and behavior on video frames.
"""

import logging
import cv2
import numpy as np
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime

from ..analytics import InteractionType, CustomerBehavior

logger = logging.getLogger(__name__)


class Phase4OverlayRenderer:
    """Enhanced overlay rendering for Phase 4 analytics"""

    # Color definitions (BGR)
    COLORS = {
        'zone': (200, 100, 50),      # Orange
        'zone_high': (0, 165, 255),  # Orange
        'zone_entry': (0, 255, 0),   # Green
        'zone_exit': (0, 0, 255),    # Red
        'interaction': (255, 255, 0),  # Cyan
        'engagement': (255, 0, 255),   # Magenta
        'anomaly': (0, 0, 255),       # Red
        'loitering': (0, 165, 255),   # Orange
        'crowd': (0, 0, 255),         # Red
        'text_bg': (50, 50, 50),      # Dark gray
        'text_fg': (255, 255, 255),   # White
        'green': (0, 255, 0),
        'red': (0, 0, 255),
        'blue': (255, 0, 0),
        'yellow': (0, 255, 255),
        'magenta': (255, 0, 255)
    }

    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE = 0.5
    THICKNESS = 2

    def __init__(self, config=None):
        """Initialize renderer"""
        self.config = config
        logger.info("Phase 4 Overlay Renderer initialized")

    def render_frame(
        self,
        frame: np.ndarray,
        zones: Dict[str, List[Tuple[int, int]]],
        active_tracks: Dict[int, Dict],
        interactions: List[Dict],
        anomalies: List[Dict],
        dwell_sessions: Dict[str, Dict],
        crowd_events: List[Dict],
        timestamp: datetime,
        config: Optional[Dict] = None
    ) -> np.ndarray:
        """
        Render complete analytics overlay
        
        Args:
            frame: Input video frame
            zones: Zone definitions {zone_id: [(x, y), ...]}
            active_tracks: Active tracking data
            interactions: Recent interactions
            anomalies: Detected anomalies
            dwell_sessions: Dwell time sessions
            crowd_events: Crowd detection events
            timestamp: Frame timestamp
            config: Rendering configuration
            
        Returns:
            Rendered frame with overlays
        """

        # Make copy to avoid modifying original
        frame = frame.copy()
        height, width = frame.shape[:2]

        # Render zones
        if config is None or config.get('show_zones', True):
            frame = self._render_zones(frame, zones, dwell_sessions)

        # Render active tracks
        if config is None or config.get('show_tracks', True):
            frame = self._render_tracks(frame, active_tracks, dwell_sessions)

        # Render interactions
        if config is None or config.get('show_interactions', True):
            frame = self._render_interactions(frame, interactions)

        # Render anomalies
        if config is None or config.get('show_alerts', True):
            frame = self._render_anomalies(frame, anomalies)

        # Render crowd events
        if config is None or config.get('show_crowds', True):
            frame = self._render_crowd_events(frame, crowd_events)

        # Render dwell time
        if config is None or config.get('show_dwell_time', True):
            frame = self._render_dwell_times(frame, dwell_sessions)

        # Render frame info
        frame = self._render_frame_info(frame, timestamp, len(active_tracks))

        return frame

    def _render_zones(
        self,
        frame: np.ndarray,
        zones: Dict[str, List[Tuple[int, int]]],
        dwell_sessions: Dict[str, Dict]
    ) -> np.ndarray:
        """Render zone polygons"""

        for zone_id, polygon in zones.items():
            if not polygon:
                continue

            pts = np.array(polygon, np.int32)
            pts = pts.reshape((-1, 1, 2))

            # Determine color based on crowd
            session_count = len(dwell_sessions.get(zone_id, {}))
            if session_count > 3:
                color = self.COLORS['zone_high']
            else:
                color = self.COLORS['zone']

            # Draw zone with transparency
            overlay = frame.copy()
            cv2.polylines(overlay, [pts], True, color, 2)
            cv2.fillPoly(overlay, [pts], color)
            frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)

            # Draw zone label
            center = tuple(np.mean(pts, axis=0)[0].astype(int))
            cv2.putText(
                frame, zone_id, center,
                self.FONT, self.FONT_SCALE,
                self.COLORS['text_fg'],
                self.THICKNESS
            )

        return frame

    def _render_tracks(
        self,
        frame: np.ndarray,
        active_tracks: Dict[int, Dict],
        dwell_sessions: Dict[str, Dict]
    ) -> np.ndarray:
        """Render tracking information"""

        for track_id, track_data in active_tracks.items():
            if 'bbox_center' not in track_data:
                continue

            x, y = track_data['bbox_center']
            x, y = int(x), int(y)

            # Determine track color based on behavior
            behavior = track_data.get('behavior', 'browsing')
            if behavior == 'suspicious':
                color = self.COLORS['anomaly']
            elif behavior == 'purchasing':
                color = self.COLORS['magenta']
            elif behavior == 'comparing':
                color = self.COLORS['engagement']
            else:
                color = self.COLORS['green']

            # Draw track ID circle
            cv2.circle(frame, (x, y), 10, color, 2)
            cv2.putText(
                frame, f"ID:{track_id}", (x - 20, y - 15),
                self.FONT, 0.4, color, 1
            )

            # Draw trajectory if available
            if 'trajectory' in track_data:
                trajectory = track_data['trajectory']
                if len(trajectory) > 1:
                    for i in range(len(trajectory) - 1):
                        pt1 = tuple(map(int, trajectory[i]))
                        pt2 = tuple(map(int, trajectory[i + 1]))
                        cv2.line(frame, pt1, pt2, color, 1)

        return frame

    def _render_interactions(
        self,
        frame: np.ndarray,
        interactions: List[Dict]
    ) -> np.ndarray:
        """Render recent interactions"""

        for interaction in interactions[-10:]:  # Show last 10
            zone_id = interaction.get('zone_id', '')
            interaction_type = interaction.get('type', '')

            if interaction_type == 'engagement':
                y_offset = 50 + interactions.index(interaction) * 20
                cv2.putText(
                    frame, f"Engagement: {zone_id}",
                    (10, y_offset), self.FONT, 0.5,
                    self.COLORS['engagement'], 1
                )

        return frame

    def _render_anomalies(
        self,
        frame: np.ndarray,
        anomalies: List[Dict]
    ) -> np.ndarray:
        """Render anomalies and alerts"""

        for idx, anomaly in enumerate(anomalies[-5:]):  # Show last 5
            anomaly_type = anomaly.get('type', '')
            track_id = anomaly.get('track_id', '')
            confidence = anomaly.get('confidence', 0)

            y_offset = 100 + idx * 25

            # Draw alert box
            cv2.rectangle(frame, (5, y_offset - 15), (300, y_offset + 5),
                         self.COLORS['text_bg'], -1)

            text = f"⚠ {anomaly_type} (ID:{track_id}, {confidence:.0%})"
            cv2.putText(
                frame, text, (10, y_offset),
                self.FONT, 0.5, self.COLORS['anomaly'], 1
            )

        return frame

    def _render_crowd_events(
        self,
        frame: np.ndarray,
        crowd_events: List[Dict]
    ) -> np.ndarray:
        """Render crowd detection events"""

        for event in crowd_events[-3:]:
            zone_id = event.get('zone_id', '')
            count = event.get('count', 0)
            density = event.get('density', 'unknown')

            # Draw warning
            cv2.rectangle(frame, (frame.shape[1] - 250, 50), (frame.shape[1] - 10, 100),
                         self.COLORS['crowd'], -1)

            text = f"Crowd: {zone_id} ({count} customers, {density})"
            cv2.putText(
                frame, text, (frame.shape[1] - 240, 75),
                self.FONT, 0.5, self.COLORS['text_fg'], 1
            )

        return frame

    def _render_dwell_times(
        self,
        frame: np.ndarray,
        dwell_sessions: Dict[str, Dict]
    ) -> np.ndarray:
        """Render dwell time information"""

        y_offset = frame.shape[0] - 100
        cv2.putText(
            frame, "Dwell Times:",
            (10, y_offset), self.FONT, 0.6,
            self.COLORS['text_fg'], 1
        )

        for idx, (zone_id, sessions) in enumerate(list(dwell_sessions.items())[:5]):
            avg_dwell = 0
            if sessions:
                avg_dwell = sum(s.get('duration', 0) for s in sessions.values()) / len(sessions)

            y_offset += 20
            text = f"  {zone_id}: {avg_dwell:.1f}s"
            cv2.putText(
                frame, text, (10, y_offset),
                self.FONT, 0.5, self.COLORS['yellow'], 1
            )

        return frame

    def _render_frame_info(
        self,
        frame: np.ndarray,
        timestamp: datetime,
        track_count: int
    ) -> np.ndarray:
        """Render frame information"""

        # Draw background box
        cv2.rectangle(frame, (5, 5), (300, 50), self.COLORS['text_bg'], -1)

        # Draw timestamp
        time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(
            frame, f"Time: {time_str}",
            (10, 20), self.FONT, 0.5,
            self.COLORS['text_fg'], 1
        )

        # Draw track count
        cv2.putText(
            frame, f"Tracks: {track_count}",
            (10, 40), self.FONT, 0.5,
            self.COLORS['text_fg'], 1
        )

        return frame

    @staticmethod
    def draw_heatmap(
        frame: np.ndarray,
        heatmap_data: np.ndarray,
        alpha: float = 0.3
    ) -> np.ndarray:
        """Draw heatmap overlay"""

        if heatmap_data is None or heatmap_data.size == 0:
            return frame

        # Normalize heatmap
        heatmap_normalized = cv2.normalize(heatmap_data, None, 0, 255, cv2.NORM_MINMAX)
        heatmap_colored = cv2.applyColorMap(heatmap_normalized.astype(np.uint8), cv2.COLORMAP_JET)

        # Resize to frame size
        heatmap_resized = cv2.resize(heatmap_colored, (frame.shape[1], frame.shape[0]))

        # Blend with frame
        result = cv2.addWeighted(frame, 1 - alpha, heatmap_resized, alpha, 0)
        return result

    @staticmethod
    def draw_engagement_meter(
        frame: np.ndarray,
        engagement_score: float,
        position: Tuple[int, int] = (10, 70)
    ) -> np.ndarray:
        """Draw engagement meter"""

        x, y = position
        width = 150
        height = 20

        # Draw background
        cv2.rectangle(frame, (x, y), (x + width, y + height), (100, 100, 100), -1)

        # Draw filled portion
        filled_width = int(width * min(engagement_score, 1.0))
        cv2.rectangle(frame, (x, y), (x + filled_width, y + height), (0, 255, 0), -1)

        # Draw border
        cv2.rectangle(frame, (x, y), (x + width, y + height), (255, 255, 255), 2)

        # Draw percentage text
        text = f"{engagement_score * 100:.0f}%"
        cv2.putText(
            frame, text, (x + width + 5, y + 15),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1
        )

        return frame
