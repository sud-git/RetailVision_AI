"""
Redis cache and connection management.
Provides connection pooling and common cache operations.
"""

from typing import Optional, Any
import json

import redis
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import RedisError

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

# Global Redis client
_redis_client: Optional[Redis] = None


async def init_redis() -> Redis:
    """Initialize Redis connection."""
    global _redis_client

    try:
        logger.info("Connecting to Redis", url=settings.redis_connection_string)

        # Create connection pool
        pool = ConnectionPool.from_url(
            settings.redis_connection_string,
            decode_responses=True,
            max_connections=50
        )

        _redis_client = Redis(connection_pool=pool)

        # Test connection
        await _redis_client.ping()
        logger.info("Redis connection established")

        return _redis_client

    except RedisError as e:
        logger.error("Failed to connect to Redis", error=str(e))
        raise


def get_redis() -> Optional[Redis]:
    """Get Redis client instance."""
    return _redis_client


async def close_redis():
    """Close Redis connection."""
    global _redis_client

    if _redis_client is not None:
        await _redis_client.close()
        logger.info("Redis connection closed")
        _redis_client = None


class CacheManager:
    """High-level cache operations."""

    def __init__(self, redis_client: Optional[Redis] = None):
        self.redis = redis_client or _redis_client

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        serialize: bool = True
    ) -> bool:
        """Set cache value."""
        try:
            if serialize:
                value = json.dumps(value)

            if ttl:
                await self.redis.setex(key, ttl, value)
            else:
                await self.redis.set(key, value)
            return True

        except RedisError as e:
            logger.error("Cache set failed", key=key, error=str(e))
            return False

    async def get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """Get cache value."""
        try:
            value = await self.redis.get(key)
            if value and deserialize:
                return json.loads(value)
            return value

        except RedisError as e:
            logger.error("Cache get failed", key=key, error=str(e))
            return None

    async def delete(self, key: str) -> bool:
        """Delete cache key."""
        try:
            await self.redis.delete(key)
            return True

        except RedisError as e:
            logger.error("Cache delete failed", key=key, error=str(e))
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            return await self.redis.exists(key) > 0

        except RedisError as e:
            logger.error("Cache exists check failed", key=key, error=str(e))
            return False

    async def increment(self, key: str, increment: int = 1) -> int:
        """Increment counter."""
        try:
            return await self.redis.incrby(key, increment)

        except RedisError as e:
            logger.error("Cache increment failed", key=key, error=str(e))
            return 0

    async def push_to_stream(
        self,
        stream_key: str,
        data: dict,
        max_length: Optional[int] = None
    ) -> Optional[str]:
        """Push event to Redis stream."""
        try:
            message_id = await self.redis.xadd(
                stream_key,
                data,
                maxlen=max_length,
                approximate=True
            )
            return message_id

        except RedisError as e:
            logger.error("Stream push failed", stream=stream_key, error=str(e))
            return None


async def get_cache_manager() -> CacheManager:
    """FastAPI dependency for cache manager."""
    return CacheManager()
