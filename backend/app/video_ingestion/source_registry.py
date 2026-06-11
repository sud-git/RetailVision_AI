"""
Video Source Registry - Central catalog of video sources

Manages:
- Adding/removing sources
- Lifecycle management
- Metrics aggregation
- Thread-safe operations
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import VideoSourceConfig, StreamHealth, StreamStatus
from .stream_manager import StreamManager
from .exceptions import (
    SourceNotFoundException,
    DuplicateSourceException,
    RegistryException
)

logger = logging.getLogger(__name__)


class VideoSourceRegistry:
    """
    Central registry for managing video sources.
    
    Features:
    - Add/remove/list sources
    - Lifecycle management (start/stop/pause/resume)
    - Metrics aggregation
    - Thread-safe async operations
    """
    
    def __init__(
        self,
        on_event_callback=None,
        on_metrics_callback=None
    ):
        """
        Initialize registry.
        
        Args:
            on_event_callback: Async callback for stream events
            on_metrics_callback: Async callback for metrics
        """
        self.sources: Dict[str, StreamManager] = {}
        self.on_event_callback = on_event_callback
        self.on_metrics_callback = on_metrics_callback
        self._lock = asyncio.Lock()
    
    async def add_source(self, config: VideoSourceConfig) -> bool:
        """
        Add video source to registry.
        
        Args:
            config: Video source configuration
            
        Returns:
            True if added successfully
            
        Raises:
            DuplicateSourceException: If source already exists
        """
        async with self._lock:
            if config.id in self.sources:
                raise DuplicateSourceException(
                    f"Source '{config.id}' already exists"
                )
            
            try:
                # Create stream manager
                manager = StreamManager(
                    config,
                    on_event_callback=self.on_event_callback,
                    on_metrics_callback=self.on_metrics_callback
                )
                
                # Start stream
                success = await manager.start()
                
                if success:
                    self.sources[config.id] = manager
                    logger.info(
                        f"Added source '{config.id}' "
                        f"({config.type.value}, URL: {self._sanitize_config(config)})"
                    )
                    return True
                else:
                    logger.error(f"Failed to start source '{config.id}'")
                    return False
                    
            except Exception as e:
                logger.error(f"Error adding source '{config.id}': {e}")
                raise RegistryException(f"Failed to add source: {e}")
    
    async def remove_source(self, source_id: str) -> bool:
        """
        Remove video source from registry.
        
        Args:
            source_id: Source identifier
            
        Returns:
            True if removed
            
        Raises:
            SourceNotFoundException: If source doesn't exist
        """
        async with self._lock:
            if source_id not in self.sources:
                raise SourceNotFoundException(
                    f"Source '{source_id}' not found"
                )
            
            try:
                manager = self.sources[source_id]
                await manager.stop()
                del self.sources[source_id]
                logger.info(f"Removed source '{source_id}'")
                return True
            except Exception as e:
                logger.error(f"Error removing source '{source_id}': {e}")
                raise RegistryException(f"Failed to remove source: {e}")
    
    async def get_source(self, source_id: str) -> Optional[StreamManager]:
        """
        Get stream manager for source.
        
        Args:
            source_id: Source identifier
            
        Returns:
            StreamManager or None if not found
        """
        async with self._lock:
            return self.sources.get(source_id)
    
    async def get_all_sources(self) -> List[StreamManager]:
        """
        Get all stream managers.
        
        Returns:
            List of StreamManager instances
        """
        async with self._lock:
            return list(self.sources.values())
    
    async def pause_source(self, source_id: str) -> bool:
        """Pause source processing"""
        manager = await self.get_source(source_id)
        if not manager:
            raise SourceNotFoundException(f"Source '{source_id}' not found")
        
        await manager.pause()
        return True
    
    async def resume_source(self, source_id: str) -> bool:
        """Resume source processing"""
        manager = await self.get_source(source_id)
        if not manager:
            raise SourceNotFoundException(f"Source '{source_id}' not found")
        
        await manager.resume()
        return True
    
    async def get_source_status(self, source_id: str) -> Dict[str, Any]:
        """
        Get status of specific source.
        
        Args:
            source_id: Source identifier
            
        Returns:
            Status dictionary
        """
        manager = await self.get_source(source_id)
        if not manager:
            raise SourceNotFoundException(f"Source '{source_id}' not found")
        
        return manager.get_status()
    
    async def get_all_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all sources.
        
        Returns:
            List of status dictionaries
        """
        statuses = []
        for manager in await self.get_all_sources():
            statuses.append(manager.get_status())
        return statuses
    
    async def get_metrics_snapshot(self) -> Dict[str, Any]:
        """
        Get aggregated metrics snapshot.
        
        Returns:
            Dictionary with aggregated metrics
        """
        managers = await self.get_all_sources()
        
        total_frames = 0
        total_dropped = 0
        total_errors = 0
        total_uptime = 0
        running_count = 0
        
        source_metrics = []
        
        for manager in managers:
            status = manager.get_status()
            
            total_frames += status['frames_processed']
            total_dropped += status['frames_dropped']
            total_errors += status['errors_count']
            total_uptime += status['uptime_seconds']
            
            if status['is_running'] and not status['is_paused']:
                running_count += 1
            
            # Per-source metrics
            source_metrics.append({
                'source_id': manager.source_id,
                'status': status['status'],
                'frames_processed': status['frames_processed'],
                'frames_dropped': status['frames_dropped'],
                'errors': status['errors_count'],
                'uptime_seconds': status['uptime_seconds'],
            })
        
        # Aggregate metrics
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_sources': len(managers),
            'running_sources': running_count,
            'paused_sources': sum(1 for m in managers if m.is_paused),
            'failed_sources': sum(1 for m in managers if m.status == StreamStatus.ERROR),
            'total_frames_processed': total_frames,
            'total_frames_dropped': total_dropped,
            'total_errors': total_errors,
            'total_uptime_seconds': total_uptime,
            'average_uptime_seconds': total_uptime / max(len(managers), 1),
            'sources': source_metrics,
        }
    
    async def shutdown(self) -> None:
        """Shutdown all sources"""
        async with self._lock:
            managers_copy = list(self.sources.values())
        
        for manager in managers_copy:
            try:
                await manager.stop()
            except Exception as e:
                logger.error(f"Error stopping '{manager.source_id}': {e}")
        
        async with self._lock:
            self.sources.clear()
        
        logger.info("Registry shutdown complete")
    
    def __len__(self) -> int:
        """Get number of sources"""
        return len(self.sources)
    
    def __repr__(self) -> str:
        running = sum(1 for m in self.sources.values() if m.is_running)
        return f"Registry({len(self.sources)} sources, {running} running)"
    
    @staticmethod
    def _sanitize_config(config: VideoSourceConfig) -> str:
        """Sanitize config for logging (hide credentials)"""
        url = config.url or ""
        if config.password:
            url = url.replace(config.password, "***")
        return url[:50]  # Truncate long URLs
