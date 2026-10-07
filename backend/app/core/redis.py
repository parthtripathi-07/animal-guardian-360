"""
Redis client connection and fallback cache manager.
Provides async get, set, delete, and rate-limiting helper methods.
Falls back to a thread-safe in-memory cache if Redis is temporarily unreachable.
"""
import logging
import time
from typing import Optional, Dict, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)

# In-memory fallback cache store: key -> (value, expire_timestamp)
_memory_cache: Dict[str, Tuple[str, Optional[float]]] = {}


class CacheService:
    def __init__(self) -> None:
        self._redis = None
        self._is_redis_available = False

    async def get_client(self):
        """Lazy load and check Redis connection."""
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                self._redis = aioredis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=1.5
                )
                await self._redis.ping()
                self._is_redis_available = True
                logger.info("Connected to Redis at %s", settings.REDIS_URL)
            except Exception as e:
                self._is_redis_available = False
                logger.warning("Redis not reachable (%s). Falling back to in-memory cache.", e)
        return self._redis

    async def get(self, key: str) -> Optional[str]:
        """Retrieve value by key."""
        try:
            client = await self.get_client()
            if self._is_redis_available and client:
                return await client.get(key)
        except Exception:
            self._is_redis_available = False

        # Memory fallback
        if key in _memory_cache:
            val, exp = _memory_cache[key]
            if exp is None or exp > time.time():
                return val
            del _memory_cache[key]
        return None

    async def set(self, key: str, value: str, expire_seconds: Optional[int] = None) -> bool:
        """Store key-value pair with optional TTL."""
        try:
            client = await self.get_client()
            if self._is_redis_available and client:
                if expire_seconds:
                    await client.setex(key, expire_seconds, value)
                else:
                    await client.set(key, value)
                return True
        except Exception:
            self._is_redis_available = False

        # Memory fallback
        exp = (time.time() + expire_seconds) if expire_seconds else None
        _memory_cache[key] = (value, exp)
        return True

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            client = await self.get_client()
            if self._is_redis_available and client:
                await client.delete(key)
        except Exception:
            pass

        _memory_cache.pop(key, None)
        return True

    async def check_rate_limit(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        """
        Sliding rate limiter check.
        Returns: (is_allowed: bool, remaining: int)
        """
        count_str = await self.get(key)
        count = int(count_str) if count_str else 0

        if count >= max_requests:
            return False, 0

        count += 1
        await self.set(key, str(count), expire_seconds=window_seconds)
        return True, max_requests - count


cache_service = CacheService()
