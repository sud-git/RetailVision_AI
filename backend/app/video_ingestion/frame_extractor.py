"""
Frame Extractor - Async video frame extraction from various sources

Handles:
- RTSP stream extraction
- Webcam frame capture
- Local video file reading
- FPS throttling
- Error recovery
- GPU optimization
"""

import asyncio
import cv2
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from time import time

from .models import VideoSourceConfig, FrameMetadata, FrameFormat, VideoSourceType
from .exceptions import (
    FrameExtractionException,
    RTSPConnectionException,
    WebcamAccessException,
    LocalFileException
)
from .gpu_optimizer import get_gpu_optimizer

logger = logging.getLogger(__name__)


class FrameExtractor:
    """
    Async frame extractor for video sources.
    
    Features:
    - Supports RTSP, webcam, local files
    - Configurable FPS throttling
    - Error recovery with retry logic
    - GPU optimization support
    - Frame metadata generation
    """
    
    def __init__(self, config: VideoSourceConfig):
        """
        Initialize frame extractor.
        
        Args:
            config: Video source configuration
        """
        self.config = config
        self.source_id = config.id
        self.source_type = config.type
        
        # Video capture
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_open = False
        
        # FPS control
        self.target_fps = config.fps
        self.frame_interval = 1.0 / max(self.target_fps, 1)
        self.last_frame_time = time()
        
        # Frame tracking
        self.frame_index = 0
        self.frames_extracted = 0
        self.frames_skipped = 0
        self.extraction_errors = 0
        
        # Timing
        self.start_time = None
        self.last_error_time: Optional[datetime] = None
        self.last_error_message = ""
        
        # GPU
        self.gpu_optimizer = get_gpu_optimizer()
        self.use_gpu = self.gpu_optimizer.is_gpu_available()
    
    async def connect(self) -> bool:
        """
        Connect to video source (async wrapper).
        
        Returns:
            True if connection successful
        """
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, self._connect_sync)
            if result:
                self.is_open = True
                self.start_time = datetime.utcnow()
                logger.info(f"[{self.source_id}] Connected successfully")
            return result
        except Exception as e:
            self._record_error(str(e))
            raise FrameExtractionException(f"Connection failed: {e}")
    
    def _connect_sync(self) -> bool:
        """Synchronous connection (run in executor)"""
        try:
            # Build URL for RTSP with credentials
            source_url = self._build_source_url()
            
            # Create video capture
            self.cap = cv2.VideoCapture(source_url)
            
            if not self.cap.isOpened():
                raise FrameExtractionException(f"Failed to open: {self._sanitize_url(source_url)}")
            
            # Set properties based on source type
            if self.source_type == VideoSourceType.RTSP:
                # RTSP-specific properties
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer
                self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)   # Disable autofocus
                self.cap.set(cv2.CAP_PROP_AUTOEXPOSURE, 1)  # Auto exposure
            
            elif self.source_type == VideoSourceType.WEBCAM:
                # Webcam properties
                if self.config.resolution:
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.resolution[0])
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.resolution[1])
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            
            # Set timeout for reading
            self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, self.config.read_timeout_seconds * 1000)
            
            logger.debug(f"[{self.source_id}] Connection established, source: {self._sanitize_url(source_url)}")
            return True
            
        except Exception as e:
            logger.error(f"[{self.source_id}] Connection error: {e}")
            if self.cap:
                self.cap.release()
                self.cap = None
            return False
    
    def _build_source_url(self) -> str:
        """Build source URL based on type"""
        if self.source_type == VideoSourceType.RTSP:
            if self.config.username and self.config.password:
                url = (
                    f"rtsp://{self.config.username}:{self.config.password}@"
                    f"{self.config.url.replace('rtsp://', '').replace('rtsp-://', '')}"
                )
            else:
                url = self.config.url
            return url
        
        elif self.source_type == VideoSourceType.WEBCAM:
            return int(self.config.device_id or 0)
        
        elif self.source_type == VideoSourceType.LOCAL_FILE:
            return self.config.url
        
        else:
            raise ValueError(f"Unknown source type: {self.source_type}")
    
    def _sanitize_url(self, url: str) -> str:
        """Remove credentials from URL for logging"""
        if isinstance(url, int):
            return f"Device {url}"
        url_str = str(url)
        return url_str.replace(self.config.password or "", "***") if self.config.password else url_str
    
    async def extract_frame(self) -> Optional[Tuple[np.ndarray, FrameMetadata]]:
        """
        Extract next frame (async).
        
        Returns:
            Tuple of (frame_data, metadata) or None if error
        """
        if not self.is_open:
            raise FrameExtractionException(f"[{self.source_id}] Not connected")
        
        # Apply FPS throttling
        await self._throttle_fps()
        
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, self._read_frame_sync)
            
            if result is not None:
                frame, metadata = result
                self.frames_extracted += 1
                return frame, metadata
            else:
                return None
                
        except Exception as e:
            self.extraction_errors += 1
            self._record_error(str(e))
            logger.error(f"[{self.source_id}] Frame extraction error: {e}")
            return None
    
    def _read_frame_sync(self) -> Optional[Tuple[np.ndarray, FrameMetadata]]:
        """Synchronous frame reading (run in executor)"""
        if not self.cap or not self.cap.isOpened():
            return None
        
        try:
            ret, frame = self.cap.read()
            
            if not ret:
                # Handle end of file for local videos
                if self.source_type == VideoSourceType.LOCAL_FILE and self.config.loop:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()
                    if not ret:
                        return None
                else:
                    return None
            
            # Resize if needed
            if self.config.resolution:
                frame = cv2.resize(frame, tuple(self.config.resolution))
            
            # Convert format if needed
            if self.config.format == FrameFormat.RGB:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            elif self.config.format == FrameFormat.GRAY:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Create metadata
            metadata = FrameMetadata(
                source_id=self.source_id,
                frame_index=self.frame_index,
                timestamp=datetime.utcnow().timestamp(),
                width=frame.shape[1],
                height=frame.shape[0],
                format=self.config.format,
                is_keyframe=self.frame_index % 30 == 0,  # Heuristic: every 30th frame
            )
            
            self.frame_index += 1
            return frame, metadata
            
        except Exception as e:
            logger.error(f"[{self.source_id}] Error reading frame: {e}")
            return None
    
    async def _throttle_fps(self) -> None:
        """Apply FPS throttling"""
        elapsed = time() - self.last_frame_time
        sleep_time = self.frame_interval - elapsed
        
        if sleep_time > 0:
            await asyncio.sleep(sleep_time)
        else:
            self.frames_skipped += 1
        
        self.last_frame_time = time()
    
    def disconnect(self) -> None:
        """Disconnect from video source"""
        if self.cap:
            self.cap.release()
            self.cap = None
        self.is_open = False
        logger.info(f"[{self.source_id}] Disconnected")
    
    def _record_error(self, message: str) -> None:
        """Record error information"""
        self.last_error_time = datetime.utcnow()
        self.last_error_message = message
    
    def get_stats(self) -> dict:
        """Get extractor statistics"""
        uptime = 0
        if self.start_time:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        fps = self.frames_extracted / max(uptime, 1)
        
        return {
            'source_id': self.source_id,
            'is_connected': self.is_open,
            'frames_extracted': self.frames_extracted,
            'frames_skipped': self.frames_skipped,
            'extraction_errors': self.extraction_errors,
            'current_fps': fps,
            'target_fps': self.target_fps,
            'uptime_seconds': uptime,
            'last_error': self.last_error_message,
        }
    
    def __repr__(self) -> str:
        status = "OPEN" if self.is_open else "CLOSED"
        return f"FrameExtractor({self.source_id}, {status})"
