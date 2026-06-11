"""
Stream Manager - Manages stream lifecycle and health monitoring

Responsibilities:
- Stream connection and disconnection
- Health monitoring
- Auto-reconnect with exponential backoff
- Event and metrics publishing
- Frame extraction and buffering
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import math

from .models import (
    VideoSourceConfig, StreamStatus, StreamEvent, 
    StreamEventType, StreamHealth, FrameFormat
)
from .frame_extractor import FrameExtractor
from .async_queue import AsyncQueue
from .exceptions import VideoSourceException
from .gpu_optimizer import get_gpu_optimizer

logger = logging.getLogger(__name__)


class StreamManager:
    """
    Manages a single video stream lifecycle.
    
    Features:
    - Connect/disconnect management
    - Health monitoring
    - Auto-reconnect with exponential backoff
    - Frame extraction and buffering
    - Event publishing
    - Metrics tracking
    """
    
    def __init__(
        self,
        config: VideoSourceConfig,
        on_event_callback=None,
        on_metrics_callback=None
    ):
        """
        Initialize stream manager.
        
        Args:
            config: Video source configuration
            on_event_callback: Async callback for stream events
            on_metrics_callback: Async callback for metrics
        """
        self.config = config
        self.source_id = config.id
        self.on_event_callback = on_event_callback
        self.on_metrics_callback = on_metrics_callback
        
        # Components
        self.frame_extractor: Optional[FrameExtractor] = None
        self.frame_queue: Optional[AsyncQueue] = None
        
        # Status
        self.status = StreamStatus.INITIALIZING
        self.is_running = False
        self.is_paused = False
        
        # Reconnection tracking
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = config.reconnect_attempts
        self.reconnect_delay_ms = config.reconnect_delay_ms
        self.last_reconnect_time: Optional[datetime] = None
        
        # Health metrics
        self.frames_processed = 0
        self.frames_dropped = 0
        self.errors_count = 0
        self.start_time: Optional[datetime] = None
        self.last_frame_time: Optional[datetime] = None
        self.last_error_time: Optional[datetime] = None
        self.last_error_message = ""
        
        # Tasks
        self.processing_task: Optional[asyncio.Task] = None
        self.health_check_task: Optional[asyncio.Task] = None
        
        # GPU
        self.gpu_optimizer = get_gpu_optimizer()
    
    async def start(self) -> bool:
        """
        Start stream processing.
        
        Returns:
            True if started successfully
        """
        try:
            if self.is_running:
                logger.warning(f"[{self.source_id}] Already running")
                return False
            
            logger.info(f"[{self.source_id}] Starting stream manager...")
            self.status = StreamStatus.INITIALIZING
            self.start_time = datetime.utcnow()
            self.is_running = True
            
            # Create components
            self.frame_extractor = FrameExtractor(self.config)
            self.frame_queue = AsyncQueue(
                max_capacity=self.config.buffer_capacity,
                enable_dedup=self.config.enable_frame_dedup,
                enable_keyframe_priority=self.config.enable_keyframe_priority,
                source_id=self.source_id
            )
            
            # Start processing task
            self.processing_task = asyncio.create_task(
                self._process_stream(),
                name=f"stream_process_{self.source_id}"
            )
            
            # Start health check task
            self.health_check_task = asyncio.create_task(
                self._health_check_loop(),
                name=f"health_check_{self.source_id}"
            )
            
            logger.info(f"[{self.source_id}] Stream manager started")
            return True
            
        except Exception as e:
            logger.error(f"[{self.source_id}] Error starting stream: {e}")
            self.status = StreamStatus.ERROR
            self.is_running = False
            return False
    
    async def stop(self) -> None:
        """Stop stream processing"""
        if not self.is_running:
            return
        
        logger.info(f"[{self.source_id}] Stopping stream manager...")
        self.is_running = False
        self.status = StreamStatus.STOPPED
        
        # Cancel tasks
        if self.processing_task and not self.processing_task.done():
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        if self.health_check_task and not self.health_check_task.done():
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        # Disconnect
        if self.frame_extractor:
            self.frame_extractor.disconnect()
        
        # Clear queue
        if self.frame_queue:
            await self.frame_queue.clear()
        
        logger.info(f"[{self.source_id}] Stream manager stopped")
    
    async def pause(self) -> None:
        """Pause stream processing"""
        self.is_paused = True
        self.status = StreamStatus.PAUSED
        await self._publish_event(
            StreamEventType.DISCONNECTED,
            "Stream paused"
        )
        logger.info(f"[{self.source_id}] Stream paused")
    
    async def resume(self) -> None:
        """Resume stream processing"""
        self.is_paused = False
        self.status = StreamStatus.RUNNING
        await self._publish_event(
            StreamEventType.CONNECTED,
            "Stream resumed"
        )
        logger.info(f"[{self.source_id}] Stream resumed")
    
    async def _process_stream(self) -> None:
        """Main stream processing loop"""
        try:
            while self.is_running:
                try:
                    # Pause handling
                    if self.is_paused:
                        await asyncio.sleep(0.1)
                        continue
                    
                    # Connect if needed
                    if not self.frame_extractor.is_open:
                        success = await self.frame_extractor.connect()
                        if success:
                            self.status = StreamStatus.RUNNING
                            self.reconnect_attempts = 0
                            await self._publish_event(
                                StreamEventType.RECONNECTION_SUCCESS,
                                "Connected to stream"
                            )
                        else:
                            await self._handle_reconnect()
                            continue
                    
                    # Extract frame
                    result = await self.frame_extractor.extract_frame()
                    
                    if result is None:
                        # Frame extraction failed
                        self.errors_count += 1
                        self.last_error_time = datetime.utcnow()
                        await self._handle_reconnect()
                        continue
                    
                    frame_data, metadata = result
                    
                    # Add to queue
                    added = await self.frame_queue.put(frame_data, metadata)
                    
                    if added:
                        self.frames_processed += 1
                        self.last_frame_time = datetime.utcnow()
                    else:
                        self.frames_dropped += 1
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"[{self.source_id}] Error in processing loop: {e}")
                    self.errors_count += 1
                    self.last_error_time = datetime.utcnow()
                    self.last_error_message = str(e)
                    await self._handle_reconnect()
                    
        except asyncio.CancelledError:
            pass
        finally:
            if self.frame_extractor:
                self.frame_extractor.disconnect()
    
    async def _health_check_loop(self) -> None:
        """Periodic health check loop"""
        try:
            while self.is_running:
                try:
                    await asyncio.sleep(self.config.health_check_interval_seconds)
                    await self._perform_health_check()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"[{self.source_id}] Error in health check: {e}")
        except asyncio.CancelledError:
            pass
    
    async def _perform_health_check(self) -> None:
        """Perform health check and publish metrics"""
        try:
            uptime = 0
            if self.start_time:
                uptime = (datetime.utcnow() - self.start_time).total_seconds()
            
            # Calculate FPS
            current_fps = 0
            if uptime > 0:
                current_fps = self.frames_processed / uptime
            
            # Get buffer size
            buffer_size = await self.frame_queue.size() if self.frame_queue else 0
            
            # Get queue stats
            queue_stats = await self.frame_queue.get_stats() if self.frame_queue else {}
            
            # Create health snapshot
            health = StreamHealth(
                source_id=self.source_id,
                status=self.status,
                frames_processed=self.frames_processed,
                frames_dropped=self.frames_dropped,
                errors_count=self.errors_count,
                reconnect_attempts=self.reconnect_attempts,
                current_fps=current_fps,
                buffer_occupancy=buffer_size,
                latency_ms=0,  # Would be calculated from frame metadata
                uptime_seconds=uptime,
                last_frame_time=self.last_frame_time,
                last_error_time=self.last_error_time,
                last_error_message=self.last_error_message,
                gpu_used=self.gpu_optimizer.is_gpu_available(),
            )
            
            # Publish metrics
            if self.on_metrics_callback:
                await self.on_metrics_callback(health)
                
        except Exception as e:
            logger.error(f"[{self.source_id}] Error in health check: {e}")
    
    async def _handle_reconnect(self) -> None:
        """Handle reconnection with exponential backoff"""
        if not self.is_running:
            return
        
        self.status = StreamStatus.DISCONNECTED
        
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.status = StreamStatus.ERROR
            await self._publish_event(
                StreamEventType.ERROR,
                f"Max reconnect attempts ({self.max_reconnect_attempts}) reached"
            )
            logger.error(
                f"[{self.source_id}] Max reconnect attempts reached, "
                f"stream halted"
            )
            self.is_running = False
            return
        
        # Calculate backoff delay
        delay_ms = min(
            self.reconnect_delay_ms * (
                self.config.reconnect_backoff_factor ** self.reconnect_attempts
            ),
            300000  # Max 5 minutes
        )
        
        self.reconnect_attempts += 1
        self.last_reconnect_time = datetime.utcnow()
        
        await self._publish_event(
            StreamEventType.RECONNECTION_ATTEMPT,
            f"Reconnecting (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts}) "
            f"after {delay_ms/1000:.1f}s"
        )
        
        logger.info(
            f"[{self.source_id}] Reconnection attempt {self.reconnect_attempts}/{self.max_reconnect_attempts} "
            f"in {delay_ms/1000:.1f}s"
        )
        
        # Wait before reconnect
        await asyncio.sleep(delay_ms / 1000)
        
        # Force disconnect and reconnect
        if self.frame_extractor:
            self.frame_extractor.disconnect()
    
    async def get_frame(self, timeout_seconds: Optional[float] = None):
        """
        Get next frame from queue (blocking).
        
        Args:
            timeout_seconds: Max seconds to wait for frame
            
        Returns:
            (frame_data, metadata) or None
        """
        if not self.frame_queue:
            return None
        
        try:
            if timeout_seconds:
                return await asyncio.wait_for(
                    self.frame_queue.get(),
                    timeout=timeout_seconds
                )
            else:
                return await self.frame_queue.get()
        except asyncio.TimeoutError:
            return None
    
    async def _publish_event(
        self,
        event_type: StreamEventType,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Publish stream event"""
        try:
            event = StreamEvent(
                source_id=self.source_id,
                event_type=event_type,
                message=message,
                details=details or {}
            )
            
            if self.on_event_callback:
                await self.on_event_callback(event)
                
        except Exception as e:
            logger.error(f"[{self.source_id}] Error publishing event: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current stream status"""
        return {
            'source_id': self.source_id,
            'status': self.status.value,
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'frames_processed': self.frames_processed,
            'frames_dropped': self.frames_dropped,
            'errors_count': self.errors_count,
            'reconnect_attempts': self.reconnect_attempts,
            'uptime_seconds': (
                (datetime.utcnow() - self.start_time).total_seconds()
                if self.start_time else 0
            ),
        }
    
    def __repr__(self) -> str:
        return f"StreamManager({self.source_id}, {self.status.value})"
