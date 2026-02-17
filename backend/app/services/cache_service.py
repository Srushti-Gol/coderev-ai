import redis.asyncio as aioredis
import json
import logging
from typing import Optional, Any
from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def get_client(self) -> aioredis.Redis:
        if not self._redis:
            self._redis = await aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._redis

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            client = await self.get_client()
            value = await client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL in seconds."""
        try:
            client = await self.get_client()
            await client.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            client = await self.get_client()
            await client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete failed for key {key}: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            client = await self.get_client()
            keys = await client.keys(pattern)
            if keys:
                return await client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache invalidate pattern failed for {pattern}: {e}")
            return 0

    async def close(self):
        if self._redis:
            await self._redis.close()


cache_service = CacheService()
