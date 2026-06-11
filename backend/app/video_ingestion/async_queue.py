"""
Async Queue - Intelligent frame buffer with deduplication and capacity management

Implements a smart queue for video frames with:
- Capacity management (drops old frames if full)
- Frame deduplication (skip identical frames)
- Keyframe prioritization
- Thread-safe async operations
"""

import asyncio
from collections import deque
from typing import Optional, Tuple
import hashlib
import numpy as np
from datetime import datetime
import logging

from .models import FrameMetadata

logger = logging.getLogger(__name__)


class AsyncQueue:
    """
    Intelligent async queue for video frames with smart buffering strategies.
    
    Features:
    - Max capacity enforcement
    - Automatic old frame dropping when full
    - Frame deduplication detection
    - Keyframe prioritization
    - Thread-safe async operations
    """
    
    def __init__(
        self,
        max_capacity: int = 1000,
        enable_dedup: bool = True,
        enable_keyframe_priority: bool = True,
        source_id: str = "unknown"
    ):
        """
        Initialize async queue.
        
        Args:
            max_capacity: Maximum frames in queue
            enable_dedup: Enable frame deduplication
            enable_keyframe_priority: Prioritize keyframes
            source_id: Source identifier for logging
        """
        self.max_capacity = max_capacity
        self.enable_dedup = enable_dedup
        self.enable_keyframe_priority = enable_keyframe_priority
        self.source_id = source_id
        
        # Main queue stores (frame_data, metadata, hash)
        self.queue: deque = deque(maxlen=max_capacity)
        
        # Tracking
        self.frames_added = 0
        self.frames_removed = 0
        self.frames_dropped_dedup = 0
        self.frames_dropped_overflow = 0
        self.last_hash: Optional[str] = None
        
        # Synchronization
        self._lock = asyncio.Lock()
        self._not_empty = asyncio.Condition(self._lock)
    
    async def put(
        self,
        frame_data: Optional[np.ndarray],
        metadata: FrameMetadata
    ) -> bool:
        """
        Add frame to queue (async).
        
        Args:
            frame_data: Frame numpy array (or None for metadata-only)
            metadata: Frame metadata
            
        Returns:
            True if frame was added, False if dropped
        """
        async with self._lock:
            # Compute hash if dedup enabled
            frame_hash = None
            if self.enable_dedup and frame_data is not None:
                frame_hash = self._compute_hash(frame_data)
                
                # Check for duplicate
                if frame_hash == self.last_hash:
                    self.frames_dropped_dedup += 1
                    logger.debug(
                        f"[{self.source_id}] Duplicate frame detected, dropping"
                    )
                    return False
            
            # If queue is full, drop oldest non-keyframe
            if len(self.queue) >= self.max_capacity:
                if self.enable_keyframe_priority:
                    # Try to drop oldest non-keyframe
                    dropped = False
                    for i in range(len(self.queue)):
                        queued_frame, queued_meta, _ = self.queue[i]
                        if not queued_meta.is_keyframe:
                            # Remove this frame
                            self.queue[i] = None  # Mark for removal
                            dropped = True
                            break
                    
                    if dropped:
                        self.queue = deque(
                            [f for f in self.queue if f is not None],
                            maxlen=self.max_capacity
                        )
                    else:
                        # All frames are keyframes, drop oldest
                        self.queue.popleft()
                        self.frames_dropped_overflow += 1
                        logger.warning(
                            f"[{self.source_id}] Buffer overflow, dropped keyframe"
                        )
                else:
                    # Simple FIFO drop
                    self.queue.popleft()
                    self.frames_dropped_overflow += 1
                    logger.debug(
                        f"[{self.source_id}] Buffer full, dropped oldest frame"
                    )
            
            # Add frame to queue
            self.queue.append((frame_data, metadata, frame_hash))
            self.frames_added += 1
            self.last_hash = frame_hash
            
            # Notify waiters
            self._not_empty.notify()
            
            return True
    
    async def get(self) -> Tuple[Optional[np.ndarray], FrameMetadata]:
        """
        Get next frame from queue (async, blocks if empty).
        
        Returns:
            Tuple of (frame_data, metadata)
        """
        async with self._not_empty:
            # Wait until queue has data
            while len(self.queue) == 0:
                await self._not_empty.wait()
            
            # Get frame
            frame_data, metadata, _ = self.queue.popleft()
            self.frames_removed += 1
            
            # Update queue age
            now = datetime.utcnow()
            queue_age_ms = (now - metadata.timestamp.replace(
                tzinfo=None) if hasattr(metadata.timestamp, 'replace')
                else (now.timestamp() - metadata.timestamp) * 1000)
            metadata.queue_age_ms = queue_age_ms
            
            return frame_data, metadata
    
    async def get_nowait(self) -> Optional[Tuple[Optional[np.ndarray], FrameMetadata]]:
        """
        Get next frame without blocking (returns None if empty).
        
        Returns:
            Tuple of (frame_data, metadata) or None if queue empty
        """
        async with self._lock:
            if len(self.queue) == 0:
                return None
            
            frame_data, metadata, _ = self.queue.popleft()
            self.frames_removed += 1
            return frame_data, metadata
    
    async def size(self) -> int:
        """Get current queue size"""
        async with self._lock:
            return len(self.queue)
    
    async def clear(self) -> None:
        """Clear all frames from queue"""
        async with self._lock:
            self.queue.clear()
            logger.info(f"[{self.source_id}] Queue cleared")
    
    async def get_stats(self) -> dict:
        """Get queue statistics"""
        async with self._lock:
            return {
                "current_size": len(self.queue),
                "max_capacity": self.max_capacity,
                "occupancy_percent": (len(self.queue) / self.max_capacity) * 100,
                "frames_added_total": self.frames_added,
                "frames_removed_total": self.frames_removed,
                "frames_dropped_dedup": self.frames_dropped_dedup,
                "frames_dropped_overflow": self.frames_dropped_overflow,
                "total_dropped": self.frames_dropped_dedup + self.frames_dropped_overflow,
            }
    
    @staticmethod
    def _compute_hash(frame_data: np.ndarray, sample_size: int = 10000) -> str:
        """
        Compute hash of frame for deduplication.
        
        Uses sampling for large frames to keep computation fast.
        
        Args:
            frame_data: Frame array
            sample_size: Number of bytes to sample
            
        Returns:
            MD5 hex digest
        """
        try:
            # Sample frame if large
            if frame_data.size > sample_size:
                sample = frame_data.flat[::frame_data.size // sample_size]
                data = sample.tobytes()
            else:
                data = frame_data.tobytes()
            
            return hashlib.md5(data).hexdigest()
        except Exception as e:
            logger.warning(f"Error computing frame hash: {e}")
            return ""
    
    def __len__(self) -> int:
        """Get queue length (non-async)"""
        return len(self.queue)
    
    def __repr__(self) -> str:
        return (
            f"AsyncQueue("
            f"size={len(self.queue)}/{self.max_capacity}, "
            f"added={self.frames_added}, "
            f"removed={self.frames_removed}, "
            f"dropped={self.frames_dropped_dedup + self.frames_dropped_overflow}"
            f")"
        )
