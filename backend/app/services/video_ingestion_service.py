"""
Video Ingestion Service - Orchestrates the entire video ingestion pipeline

Responsibilities:
- Initialize and manage VideoSourceRegistry
- Handle event publishing to Redis Streams
- Metrics aggregation and publishing
- Service lifecycle management
"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.cache import CacheManager
from app.video_ingestion import (
    VideoSourceRegistry,
    VideoSourceConfig,
    VideoIngestionConfig,
    StreamEvent,
    StreamHealth,
)

logger = logging.getLogger(__name__)


class VideoIngestionService:
    """
    Main service for video ingestion pipeline.
    
    Coordinates:
    - Video source management via registry
    - Event publishing to Redis Streams
    - Metrics aggregation and publishing
    - Lifecycle management
    """
    
    def __init__(self, cache_manager: CacheManager):
        """
        Initialize video ingestion service.
        
        Args:
            cache_manager: CacheManager for Redis operations
        """
        self.cache_manager = cache_manager
        self.registry: Optional[VideoSourceRegistry] = None
        self.is_running = False
        
        # Tasks
        self.metrics_publish_task: Optional[asyncio.Task] = None
        self.metrics_interval = 10  # seconds
    
    async def initialize(self, config: VideoIngestionConfig) -> bool:
        """
        Initialize video ingestion service.
        
        Args:
            config: Video ingestion configuration
            
        Returns:
            True if initialized successfully
        """
        try:
            logger.info("Initializing VideoIngestionService...")
            
            # Create registry with callbacks
            self.registry = VideoSourceRegistry(
                on_event_callback=self._on_stream_event,
                on_metrics_callback=self._on_stream_metrics
            )
            
            # Add all configured sources
            for source_config in config.sources:
                try:
                    success = await self.registry.add_source(source_config)
                    if success:
                        logger.info(f"Added source: {source_config.id}")
                    else:
                        logger.warning(f"Failed to add source: {source_config.id}")
                except Exception as e:
                    logger.error(f"Error adding source '{source_config.id}': {e}")
            
            self.is_running = True
            
            # Start metrics publishing task
            self.metrics_publish_task = asyncio.create_task(
                self._metrics_publish_loop()
            )
            
            logger.info(
                f"VideoIngestionService initialized with "
                f"{len(self.registry)} sources"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error initializing VideoIngestionService: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown video ingestion service"""
        logger.info("Shutting down VideoIngestionService...")
        
        self.is_running = False
        
        # Cancel metrics task
        if self.metrics_publish_task:
            self.metrics_publish_task.cancel()
            try:
                await self.metrics_publish_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown registry
        if self.registry:
            await self.registry.shutdown()
        
        logger.info("VideoIngestionService shutdown complete")
    
    async def add_source(self, config: VideoSourceConfig) -> bool:
        """
        Add video source dynamically.
        
        Args:
            config: Video source configuration
            
        Returns:
            True if added successfully
        """
        if not self.registry:
            logger.error("Registry not initialized")
            return False
        
        return await self.registry.add_source(config)
    
    async def remove_source(self, source_id: str) -> bool:
        """
        Remove video source.
        
        Args:
            source_id: Source identifier
            
        Returns:
            True if removed
        """
        if not self.registry:
            return False
        
        return await self.registry.remove_source(source_id)
    
    async def get_sources(self) -> List[Dict[str, Any]]:
        """
        Get list of all sources.
        
        Returns:
            List of source status dictionaries
        """
        if not self.registry:
            return []
        
        return await self.registry.get_all_status()
    
    async def get_source_status(self, source_id: str) -> Dict[str, Any]:
        """
        Get status of specific source.
        
        Args:
            source_id: Source identifier
            
        Returns:
            Status dictionary
        """
        if not self.registry:
            return {}
        
        return await self.registry.get_source_status(source_id)
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get aggregated metrics.
        
        Returns:
            Metrics dictionary
        """
        if not self.registry:
            return {}
        
        return await self.registry.get_metrics_snapshot()
    
    async def pause_source(self, source_id: str) -> bool:
        """Pause source processing"""
        if not self.registry:
            return False
        return await self.registry.pause_source(source_id)
    
    async def resume_source(self, source_id: str) -> bool:
        """Resume source processing"""
        if not self.registry:
            return False
        return await self.registry.resume_source(source_id)
    
    async def get_frame(self, source_id: str, timeout_seconds: float = 5.0):
        """
        Get next frame from source.
        
        Args:
            source_id: Source identifier
            timeout_seconds: Max wait time
            
        Returns:
            (frame_data, metadata) or None
        """
        if not self.registry:
            return None
        
        manager = await self.registry.get_source(source_id)
        if not manager:
            return None
        
        return await manager.get_frame(timeout_seconds)
    
    async def _on_stream_event(self, event: StreamEvent) -> None:
        """Handle stream event"""
        try:
            # Publish to Redis Stream
            event_key = f"stream_events:{event.source_id}"
            event_data = {
                "event_type": event.event_type.value,
                "message": event.message,
                "timestamp": event.timestamp.isoformat(),
                "details": json.dumps(event.details or {}),
            }
            
            await self.cache_manager.push_to_stream(event_key, event_data)
            logger.debug(f"Published event: {event_key} -> {event.event_type.value}")
            
        except Exception as e:
            logger.error(f"Error publishing stream event: {e}")
    
    async def _on_stream_metrics(self, health: StreamHealth) -> None:
        """Handle stream health metrics"""
        try:
            # Publish to Redis Stream and cache
            metrics_key = f"stream_metrics:{health.source_id}"
            metrics_data = {
                "status": health.status.value,
                "frames_processed": str(health.frames_processed),
                "frames_dropped": str(health.frames_dropped),
                "errors_count": str(health.errors_count),
                "current_fps": f"{health.current_fps:.2f}",
                "buffer_occupancy": str(health.buffer_occupancy),
                "latency_ms": f"{health.latency_ms:.2f}",
                "uptime_seconds": f"{health.uptime_seconds:.2f}",
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            # Store in cache (with TTL)
            await self.cache_manager.set(
                metrics_key,
                json.dumps(metrics_data),
                ttl=60
            )
            
            # Publish to stream
            await self.cache_manager.push_to_stream(metrics_key, metrics_data)
            
        except Exception as e:
            logger.error(f"Error publishing stream metrics: {e}")
    
    async def _metrics_publish_loop(self) -> None:
        """Periodic metrics aggregation and publishing"""
        try:
            while self.is_running:
                try:
                    await asyncio.sleep(self.metrics_interval)
                    
                    if not self.registry:
                        continue
                    
                    # Get aggregated metrics
                    metrics = await self.registry.get_metrics_snapshot()
                    
                    # Publish to Redis
                    await self.cache_manager.set(
                        "video_ingestion:metrics:aggregated",
                        json.dumps(metrics, default=str),
                        ttl=30
                    )
                    
                    logger.debug("Published aggregated metrics")
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in metrics publish loop: {e}")
                    
        except asyncio.CancelledError:
            pass
    
    def __repr__(self) -> str:
        sources_count = len(self.registry) if self.registry else 0
        return f"VideoIngestionService({sources_count} sources)"


# Global service instance
_service: Optional[VideoIngestionService] = None


async def get_video_ingestion_service(
    cache_manager: Optional[CacheManager] = None
) -> VideoIngestionService:
    """
    Get or create global VideoIngestionService instance.
    
    Args:
        cache_manager: CacheManager instance
        
    Returns:
        VideoIngestionService instance
    """
    global _service
    
    if _service is None:
        if cache_manager is None:
            from app.cache import init_redis
            await init_redis()
            from app.cache import get_cache_manager
            cache_manager = get_cache_manager()
        
        _service = VideoIngestionService(cache_manager)
    
    return _service


async def shutdown_video_ingestion_service() -> None:
    """Shutdown global service"""
    global _service
    if _service:
        await _service.shutdown()
        _service = None
