"""
Phase 4: Redis Event Publisher

Publishes retail events and anomalies to Redis Streams.
"""

import logging
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)

# Try to import redis
try:
    import redis.asyncio as aioredis
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis-asyncio not available, event publishing disabled")


class RedisEventPublisher:
    """Publishes retail events to Redis Streams"""

    # Stream names
    STREAMS = {
        'interaction': 'retail:interactions',
        'anomaly': 'retail:anomalies',
        'crowd': 'retail:crowd_events',
        'engagement': 'retail:engagement',
        'analytics': 'retail:analytics_metrics'
    }

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize publisher"""
        self.redis_url = redis_url
        self.redis: Optional[Redis] = None
        self.buffer = deque(maxlen=1000)
        self.connected = False
        logger.info(f"RedisEventPublisher initialized with {redis_url}")

    async def connect(self) -> bool:
        """Connect to Redis"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available")
            return False

        try:
            self.redis = await aioredis.from_url(self.redis_url)
            await self.redis.ping()
            self.connected = True
            logger.info("Connected to Redis")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            self.connected = False
            logger.info("Disconnected from Redis")

    async def publish_interaction(
        self,
        track_id: int,
        zone_id: str,
        interaction_type: str,
        timestamp: datetime,
        duration: float,
        confidence: float,
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """Publish interaction event"""
        
        payload = {
            'track_id': track_id,
            'zone_id': zone_id,
            'interaction_type': interaction_type,
            'timestamp': timestamp.isoformat(),
            'duration': duration,
            'confidence': confidence,
            **(metadata or {})
        }

        return await self._publish(self.STREAMS['interaction'], payload)

    async def publish_anomaly(
        self,
        track_id: int,
        anomaly_type: str,
        confidence: float,
        timestamp: datetime,
        zone_id: Optional[str] = None,
        description: str = "",
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """Publish anomaly event"""
        
        payload = {
            'track_id': track_id,
            'anomaly_type': anomaly_type,
            'confidence': confidence,
            'timestamp': timestamp.isoformat(),
            'zone_id': zone_id,
            'description': description,
            **(metadata or {})
        }

        return await self._publish(self.STREAMS['anomaly'], payload)

    async def publish_crowd_event(
        self,
        zone_id: str,
        customer_count: int,
        density_level: str,
        timestamp: datetime
    ) -> Optional[str]:
        """Publish crowd detection event"""
        
        payload = {
            'zone_id': zone_id,
            'customer_count': customer_count,
            'density_level': density_level,
            'timestamp': timestamp.isoformat()
        }

        return await self._publish(self.STREAMS['crowd'], payload)

    async def publish_engagement_metric(
        self,
        track_id: int,
        zone_id: str,
        engagement_score: float,
        interaction_count: int,
        dwell_time: float,
        behavior_type: str,
        timestamp: datetime
    ) -> Optional[str]:
        """Publish engagement metric"""
        
        payload = {
            'track_id': track_id,
            'zone_id': zone_id,
            'engagement_score': engagement_score,
            'interaction_count': interaction_count,
            'dwell_time': dwell_time,
            'behavior_type': behavior_type,
            'timestamp': timestamp.isoformat()
        }

        return await self._publish(self.STREAMS['engagement'], payload)

    async def publish_analytics_metrics(
        self,
        zone_metrics: Dict[str, Any],
        store_metrics: Dict[str, Any],
        timestamp: datetime
    ) -> Optional[str]:
        """Publish aggregated analytics metrics"""
        
        payload = {
            'zone_metrics': json.dumps(zone_metrics),
            'store_metrics': json.dumps(store_metrics),
            'timestamp': timestamp.isoformat()
        }

        return await self._publish(self.STREAMS['analytics'], payload)

    async def publish_batch(self, events: List[Dict[str, Any]], stream_name: str) -> int:
        """Publish batch of events"""
        
        if not self.connected or not self.redis:
            logger.warning("Redis not connected, buffering events")
            self.buffer.extend(events)
            return 0

        published = 0
        for event in events:
            try:
                event_id = await self.redis.xadd(
                    self.STREAMS.get(stream_name, stream_name),
                    event,
                    approximate=False
                )
                published += 1
                logger.debug(f"Published event: {event_id}")
            except Exception as e:
                logger.error(f"Failed to publish event: {e}")
                self.buffer.append(event)

        return published

    async def _publish(self, stream: str, payload: Dict[str, Any]) -> Optional[str]:
        """Internal publish method"""
        
        if not self.connected or not self.redis:
            logger.warning(f"Redis not connected, buffering event to {stream}")
            self.buffer.append({'stream': stream, 'payload': payload})
            return None

        try:
            # Convert values to strings for Redis
            data = {
                str(k): str(v) if not isinstance(v, str) else v
                for k, v in payload.items()
            }
            
            event_id = await self.redis.xadd(stream, data)
            logger.debug(f"Published to {stream}: {event_id}")
            return event_id

        except Exception as e:
            logger.error(f"Failed to publish to {stream}: {e}")
            self.buffer.append({'stream': stream, 'payload': payload})
            return None

    async def flush_buffer(self) -> int:
        """Flush buffered events"""
        
        if not self.buffer or not self.connected:
            return 0

        flushed = 0
        while self.buffer:
            item = self.buffer.popleft()
            
            try:
                if 'stream' in item and 'payload' in item:
                    await self._publish(item['stream'], item['payload'])
                    flushed += 1
            except Exception as e:
                logger.error(f"Failed to flush buffered event: {e}")

        logger.info(f"Flushed {flushed} buffered events")
        return flushed

    async def get_stream_length(self, stream_name: str) -> int:
        """Get stream length"""
        
        if not self.connected or not self.redis:
            return 0

        try:
            stream = self.STREAMS.get(stream_name, stream_name)
            length = await self.redis.xlen(stream)
            return length
        except Exception as e:
            logger.error(f"Failed to get stream length: {e}")
            return 0

    async def get_recent_events(self, stream_name: str, count: int = 10) -> List[Dict]:
        """Get recent events from stream"""
        
        if not self.connected or not self.redis:
            return []

        try:
            stream = self.STREAMS.get(stream_name, stream_name)
            events = await self.redis.xrevrange(stream, count=count)
            
            return [
                {
                    'id': event_id.decode() if isinstance(event_id, bytes) else event_id,
                    'data': {
                        k.decode() if isinstance(k, bytes) else k: 
                        v.decode() if isinstance(v, bytes) else v
                        for k, v in data.items()
                    }
                }
                for event_id, data in events
            ]

        except Exception as e:
            logger.error(f"Failed to get recent events: {e}")
            return []

    async def trim_stream(self, stream_name: str, max_len: int = 10000):
        """Trim stream to max length"""
        
        if not self.connected or not self.redis:
            return

        try:
            stream = self.STREAMS.get(stream_name, stream_name)
            await self.redis.xtrim(stream, maxlen=max_len, approximate=False)
            logger.debug(f"Trimmed stream {stream} to {max_len} entries")
        except Exception as e:
            logger.error(f"Failed to trim stream: {e}")

    def get_buffer_stats(self) -> Dict:
        """Get buffer statistics"""
        return {
            'buffer_size': len(self.buffer),
            'connected': self.connected,
            'redis_url': self.redis_url
        }

    async def health_check(self) -> bool:
        """Check Redis connection health"""
        
        if not self.redis:
            return False

        try:
            await self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
