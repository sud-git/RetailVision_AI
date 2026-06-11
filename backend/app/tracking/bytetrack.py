"""
ByteTrack Integration - Phase 3

Multi-object tracking using ByteTrack algorithm.
Maintains persistent object IDs across frames.
"""

import logging
from typing import List, Optional, Dict, Tuple
import numpy as np
from collections import defaultdict

from .models import (
    Detection, DetectionFrame, TrackingObject, TrackingStatus,
    BoundingBox, ByteTrackConfig
)
from .exceptions import TrackingInitializationException

logger = logging.getLogger(__name__)

try:
    from boxmot import BYTETracker
    BOXMOT_AVAILABLE = True
except ImportError:
    BOXMOT_AVAILABLE = False


class ByteTrackWrapper:
    """Wrapper for ByteTrack multi-object tracking"""
    
    def __init__(self, config: ByteTrackConfig, frame_shape: Tuple[int, int, 3]):
        """
        Initialize ByteTrack tracker
        
        Args:
            config: ByteTrackConfig
            frame_shape: Input frame shape (H, W, 3)
            
        Raises:
            TrackingInitializationException: If initialization fails
        """
        if not BOXMOT_AVAILABLE:
            logger.warning("boxmot not available, using fallback tracker")
            self.tracker = None
            self.use_fallback = True
        else:
            try:
                self.tracker = BYTETracker(
                    track_thresh=config.track_thresh,
                    track_buffer=config.track_buffer,
                    match_thresh=config.match_thresh,
                    frame_rate=30,
                    device="cuda:0" if self._gpu_available() else "cpu"
                )
                self.use_fallback = False
                logger.info("ByteTrack initialized successfully")
            except Exception as e:
                logger.warning(f"ByteTrack init failed: {e}, using fallback")
                self.tracker = None
                self.use_fallback = True
        
        self.config = config
        self.frame_shape = frame_shape
        self.last_track_id = 0
    
    @staticmethod
    def _gpu_available() -> bool:
        """Check if GPU is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False
    
    def update(
        self,
        detections: DetectionFrame
    ) -> List[Detection]:
        """
        Update tracker with detections
        
        Args:
            detections: DetectionFrame with new detections
            
        Returns:
            List of Detection objects with assigned track IDs
        """
        if self.use_fallback or self.tracker is None:
            return self._update_fallback(detections)
        
        try:
            # Convert detections to tracker format
            dets = self._prepare_detections(detections)
            
            if len(dets) > 0:
                # Update tracker
                tracks = self.tracker.update(dets)
                
                # Assign IDs to detections
                return self._assign_track_ids(detections, tracks)
            else:
                return detections.detections
        
        except Exception as e:
            logger.error(f"Tracking error: {e}")
            return self._update_fallback(detections)
    
    def _prepare_detections(self, detections: DetectionFrame) -> np.ndarray:
        """
        Convert DetectionFrame to tracker format
        
        Format: [[x1, y1, x2, y2, conf, class_id], ...]
        """
        if not detections.detections:
            return np.empty((0, 6), dtype=np.float32)
        
        dets_array = []
        for det in detections.detections:
            dets_array.append([
                det.bbox.x1,
                det.bbox.y1,
                det.bbox.x2,
                det.bbox.y2,
                det.confidence,
                0  # class_id (0 for person)
            ])
        
        return np.array(dets_array, dtype=np.float32)
    
    def _assign_track_ids(
        self,
        detections: DetectionFrame,
        tracks: np.ndarray
    ) -> List[Detection]:
        """Assign ByteTrack IDs to detections"""
        result = []
        
        for track in tracks:
            x1, y1, x2, y2, track_id, conf = track[:6]
            
            # Find corresponding detection
            matching_det = None
            min_iou = float('inf')
            
            for det in detections.detections:
                iou = self._bbox_iou(
                    (det.bbox.x1, det.bbox.y1, det.bbox.x2, det.bbox.y2),
                    (x1, y1, x2, y2)
                )
                if iou > 0.5 and iou < min_iou:
                    min_iou = iou
                    matching_det = det
            
            if matching_det:
                matching_det.track_id = int(track_id)
                result.append(matching_det)
        
        return result
    
    @staticmethod
    def _bbox_iou(bbox1: Tuple, bbox2: Tuple) -> float:
        """Calculate IoU between two bounding boxes"""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        inter_x1 = max(x1_1, x1_2)
        inter_y1 = max(y1_1, y1_2)
        inter_x2 = min(x2_1, x2_2)
        inter_y2 = min(y2_1, y2_2)
        
        if inter_x2 < inter_x1 or inter_y2 < inter_y1:
            return 0.0
        
        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union_area = area1 + area2 - inter_area
        
        return inter_area / union_area if union_area > 0 else 0.0
    
    def _update_fallback(
        self,
        detections: DetectionFrame
    ) -> List[Detection]:
        """Fallback tracker when ByteTrack unavailable"""
        # Simple ID assignment based on bbox proximity
        result = []
        for det in detections.detections:
            if det.track_id is None:
                self.last_track_id += 1
                det.track_id = self.last_track_id
            result.append(det)
        return result


class TrackingEngine:
    """Main tracking engine managing tracked objects"""
    
    def __init__(self, config: ByteTrackConfig, frame_shape: Tuple[int, int, 3]):
        """
        Initialize tracking engine
        
        Args:
            config: ByteTrackConfig
            frame_shape: Frame shape (H, W, 3)
        """
        self.config = config
        self.frame_shape = frame_shape
        self.tracker = ByteTrackWrapper(config, frame_shape)
        
        # Tracking object registry
        self.tracks: Dict[int, TrackingObject] = {}
        self.confirmed_tracks: Dict[int, TrackingObject] = {}
        self.lost_tracks: Dict[int, TrackingObject] = {}
        
        # Statistics
        self.max_track_id = 0
    
    def update(
        self,
        detections: DetectionFrame
    ) -> Tuple[List[Detection], List[TrackingObject]]:
        """
        Update tracker with detections
        
        Args:
            detections: DetectionFrame with new detections
            
        Returns:
            Tuple of (updated_detections, tracked_objects)
        """
        # Get tracked detections from ByteTrack
        tracked_detections = self.tracker.update(detections)
        tracked_objects = []
        
        # Update tracking objects
        for det in tracked_detections:
            if det.track_id is not None:
                track_id = det.track_id
                
                if track_id not in self.tracks:
                    # New track
                    obj = TrackingObject(
                        track_id=track_id,
                        class_name=det.class_name,
                        status=TrackingStatus.CONFIRMED
                    )
                    self.tracks[track_id] = obj
                    self.confirmed_tracks[track_id] = obj
                    self.max_track_id = max(self.max_track_id, track_id)
                else:
                    obj = self.tracks[track_id]
                    if obj.status == TrackingStatus.LOST:
                        obj.status = TrackingStatus.ACTIVE
                
                # Add detection to tracking object
                obj.add_detection(
                    det.bbox,
                    det.confidence,
                    det.frame_index,
                    det.timestamp
                )
                tracked_objects.append(obj)
        
        # Mark lost tracks
        self._update_lost_tracks(tracked_detections)
        
        return tracked_detections, tracked_objects
    
    def _update_lost_tracks(self, tracked_detections: List[Detection]) -> None:
        """Mark tracks not updated as lost"""
        tracked_ids = {d.track_id for d in tracked_detections if d.track_id is not None}
        
        for track_id, obj in self.confirmed_tracks.items():
            if track_id not in tracked_ids:
                if obj.status == TrackingStatus.ACTIVE:
                    obj.status = TrackingStatus.LOST
                    if track_id in self.confirmed_tracks:
                        del self.confirmed_tracks[track_id]
                        self.lost_tracks[track_id] = obj
    
    def get_active_tracks(self) -> List[TrackingObject]:
        """Get all active tracking objects"""
        return [obj for obj in self.tracks.values() if obj.status == TrackingStatus.ACTIVE]
    
    def get_track(self, track_id: int) -> Optional[TrackingObject]:
        """Get specific tracking object"""
        return self.tracks.get(track_id)
    
    def get_statistics(self) -> Dict:
        """Get tracking statistics"""
        return {
            "total_tracks": len(self.tracks),
            "active_tracks": len(self.confirmed_tracks),
            "lost_tracks": len(self.lost_tracks),
            "max_track_id": self.max_track_id
        }
