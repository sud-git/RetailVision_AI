"""
Overlay Renderer - Phase 3

Render detections, tracking IDs, zones, and metadata on video frames.
"""

import logging
from typing import List, Tuple, Optional
import cv2
import numpy as np

from .models import (
    Detection, DetectionFrame, TrackingObject, Zone, BoundingBox
)

logger = logging.getLogger(__name__)


class OverlayRenderer:
    """Render visualizations on video frames"""
    
    # Colors (BGR)
    COLOR_PERSON = (0, 255, 0)  # Green
    COLOR_TRACKED = (255, 0, 0)  # Blue
    COLOR_LOST = (0, 0, 255)  # Red
    COLOR_ZONE = (200, 200, 0)  # Cyan
    COLOR_TEXT = (255, 255, 255)  # White
    COLOR_ID = (0, 255, 255)  # Yellow
    
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    FONT_SCALE = 0.6
    THICKNESS = 2
    
    def __init__(self, enable_zones: bool = True, enable_ids: bool = True):
        """
        Initialize overlay renderer
        
        Args:
            enable_zones: Draw zones
            enable_ids: Draw track IDs
        """
        self.enable_zones = enable_zones
        self.enable_ids = enable_ids
    
    def render_frame(
        self,
        frame: np.ndarray,
        detections: DetectionFrame,
        tracked_objects: Optional[List[TrackingObject]] = None,
        zones: Optional[List[Zone]] = None
    ) -> np.ndarray:
        """
        Render all visualizations on frame
        
        Args:
            frame: Input frame (HxWx3, BGR)
            detections: Detection frame
            tracked_objects: List of tracking objects
            zones: List of zones
            
        Returns:
            Rendered frame
        """
        output = frame.copy()
        
        # Draw zones first (background)
        if self.enable_zones and zones:
            output = self._draw_zones(output, zones)
        
        # Draw tracked objects
        if tracked_objects:
            output = self._draw_tracked_objects(output, tracked_objects)
        else:
            # Draw untracked detections
            output = self._draw_detections(output, detections.detections)
        
        # Draw frame info
        output = self._draw_frame_info(output, detections)
        
        return output
    
    def _draw_detections(
        self,
        frame: np.ndarray,
        detections: List[Detection]
    ) -> np.ndarray:
        """Draw untracked detections"""
        for det in detections:
            bbox = det.bbox
            
            # Draw bbox
            cv2.rectangle(
                frame,
                (int(bbox.x1), int(bbox.y1)),
                (int(bbox.x2), int(bbox.y2)),
                self.COLOR_PERSON,
                self.THICKNESS
            )
            
            # Draw label
            label = f"{det.class_name.value} {det.confidence:.2f}"
            text_size = cv2.getTextSize(label, self.FONT, self.FONT_SCALE, self.THICKNESS)[0]
            
            cv2.rectangle(
                frame,
                (int(bbox.x1), int(bbox.y1 - text_size[1] - 4)),
                (int(bbox.x1 + text_size[0]), int(bbox.y1)),
                self.COLOR_PERSON,
                -1
            )
            
            cv2.putText(
                frame,
                label,
                (int(bbox.x1), int(bbox.y1 - 2)),
                self.FONT,
                self.FONT_SCALE,
                self.COLOR_TEXT,
                self.THICKNESS
            )
        
        return frame
    
    def _draw_tracked_objects(
        self,
        frame: np.ndarray,
        tracked_objects: List[TrackingObject]
    ) -> np.ndarray:
        """Draw tracked objects with IDs"""
        for obj in tracked_objects:
            if obj.current_bbox is None:
                continue
            
            bbox = obj.current_bbox
            
            # Determine color based on status
            if obj.status.value == "active":
                color = self.COLOR_TRACKED
            elif obj.status.value == "lost":
                color = self.COLOR_LOST
            else:
                color = self.COLOR_PERSON
            
            # Draw bbox
            cv2.rectangle(
                frame,
                (int(bbox.x1), int(bbox.y1)),
                (int(bbox.x2), int(bbox.y2)),
                color,
                self.THICKNESS
            )
            
            # Draw track ID
            if self.enable_ids:
                track_label = f"ID {obj.track_id}"
                
                # Track ID background
                id_size = cv2.getTextSize(track_label, self.FONT, self.FONT_SCALE, self.THICKNESS)[0]
                cv2.rectangle(
                    frame,
                    (int(bbox.x1), int(bbox.y1 - id_size[1] - 4)),
                    (int(bbox.x1 + id_size[0]), int(bbox.y1)),
                    self.COLOR_ID,
                    -1
                )
                
                cv2.putText(
                    frame,
                    track_label,
                    (int(bbox.x1), int(bbox.y1 - 2)),
                    self.FONT,
                    self.FONT_SCALE,
                    (0, 0, 0),  # Black text
                    self.THICKNESS
                )
            
            # Draw center point
            center = bbox.center
            cv2.circle(frame, (int(center[0]), int(center[1])), 3, self.COLOR_ID, -1)
            
            # Draw age
            age_label = f"Age: {obj.age}"
            text_y = int(bbox.y2 + 20)
            cv2.putText(
                frame,
                age_label,
                (int(bbox.x1), text_y),
                self.FONT,
                0.5,
                self.COLOR_TEXT,
                1
            )
        
        return frame
    
    def _draw_zones(self, frame: np.ndarray, zones: List[Zone]) -> np.ndarray:
        """Draw zone polygons"""
        for zone in zones:
            polygon = np.array(zone.polygon, dtype=np.int32)
            
            # Draw filled polygon with transparency
            overlay = frame.copy()
            cv2.fillPoly(overlay, [polygon], self.COLOR_ZONE)
            frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
            
            # Draw zone outline
            cv2.polylines(frame, [polygon], True, self.COLOR_ZONE, 2)
            
            # Draw zone label
            min_x = int(np.min(polygon[:, 0]))
            max_y = int(np.max(polygon[:, 1]))
            
            cv2.putText(
                frame,
                zone.name,
                (min_x + 5, max_y - 5),
                self.FONT,
                0.6,
                self.COLOR_TEXT,
                1
            )
        
        return frame
    
    def _draw_frame_info(
        self,
        frame: np.ndarray,
        detections: DetectionFrame
    ) -> np.ndarray:
        """Draw frame information"""
        h, w = frame.shape[:2]
        
        # Detection count
        info_text = f"Frame: {detections.frame_index} | Detections: {len(detections.detections)}"
        
        cv2.putText(
            frame,
            info_text,
            (10, 30),
            self.FONT,
            0.7,
            self.COLOR_TEXT,
            1
        )
        
        return frame
    
    def render_trajectory(
        self,
        frame: np.ndarray,
        tracking_object: TrackingObject,
        max_history: int = 30
    ) -> np.ndarray:
        """
        Draw trajectory line for a tracking object
        
        Args:
            frame: Frame to render on
            tracking_object: Object with history
            max_history: Max history points to draw
            
        Returns:
            Frame with trajectory
        """
        if len(tracking_object.bbox_history) < 2:
            return frame
        
        # Get recent history
        history = tracking_object.bbox_history[-max_history:]
        
        # Draw lines between points
        for i in range(len(history) - 1):
            p1 = history[i].center
            p2 = history[i + 1].center
            
            # Fade color based on age
            alpha = i / len(history)
            color = (
                int(self.COLOR_TRACKED[0] * alpha),
                int(self.COLOR_TRACKED[1] * alpha),
                int(self.COLOR_TRACKED[2] * alpha)
            )
            
            cv2.line(
                frame,
                (int(p1[0]), int(p1[1])),
                (int(p2[0]), int(p2[1])),
                color,
                1
            )
        
        return frame
    
    def render_heatmap(
        self,
        frame_shape: Tuple[int, int, 3],
        tracking_objects: List[TrackingObject],
        decay: float = 0.95
    ) -> np.ndarray:
        """
        Render activity heatmap
        
        Args:
            frame_shape: Shape of output (H, W, 3)
            tracking_objects: List of tracking objects
            decay: Decay factor for history
            
        Returns:
            Heatmap image
        """
        h, w = frame_shape[:2]
        heatmap = np.zeros((h, w), dtype=np.float32)
        
        # Accumulate detections
        for obj in tracking_objects:
            for bbox in obj.bbox_history:
                center = bbox.center
                cv2.circle(
                    heatmap,
                    (int(center[0]), int(center[1])),
                    20,
                    1,
                    -1
                )
        
        # Normalize
        if heatmap.max() > 0:
            heatmap = (heatmap / heatmap.max() * 255).astype(np.uint8)
        
        # Apply colormap
        heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
        
        return heatmap_color
    
    @staticmethod
    def draw_stats(
        frame: np.ndarray,
        stats: dict,
        position: Tuple[int, int] = (10, 60)
    ) -> np.ndarray:
        """
        Draw statistics on frame
        
        Args:
            frame: Frame to draw on
            stats: Statistics dictionary
            position: Top-left position for text
            
        Returns:
            Frame with stats
        """
        x, y = position
        line_height = 25
        
        for i, (key, value) in enumerate(stats.items()):
            text = f"{key}: {value}"
            cv2.putText(
                frame,
                text,
                (x, y + i * line_height),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                1
            )
        
        return frame
