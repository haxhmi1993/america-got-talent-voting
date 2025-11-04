"""
Cache abstraction layer with Redis and in-memory fallback.
"""
import asyncio
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class InMemoryCache:
    """In-memory cache implementation as fallback."""
    
    def __init__(self):
        self.store: Dict[str, tuple[Any, Optional[float]]] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            if key in self.store:
                value, expiry = self.store[key]
                if expiry is None or expiry > time.time():
                    return value
                else:
                    del self.store[key]
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with optional TTL."""
        async with self._lock:
            expiry = time.time() + ttl if ttl else None
            self.store[key] = (value, expiry)
    
    async def setnx(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set if not exists. Returns True if set, False if key exists."""
        async with self._lock:
            if key in self.store:
                val, expiry = self.store[key]
                if expiry is None or expiry > time.time():
                    return False
                else:
                    del self.store[key]
            
            expiry = time.time() + ttl if ttl else None
            self.store[key] = (value, expiry)
            return True
    
    async def incr(self, key: str) -> int:
        """Increment value by 1."""
        async with self._lock:
            if key in self.store:
                value, expiry = self.store[key]
                if expiry is None or expiry > time.time():
                    new_value = int(value) + 1
                    self.store[key] = (new_value, expiry)
                    return new_value
            
            self.store[key] = (1, None)
            return 1
    
    async def delete(self, key: str):
        """Delete key from cache."""
        async with self._lock:
            if key in self.store:
                del self.store[key]
    
    async def cleanup_expired(self):
        """Remove expired entries."""
        async with self._lock:
            now = time.time()
            expired = [k for k, (_, exp) in self.store.items() if exp and exp <= now]
            for k in expired:
                del self.store[k]


class RedisCache:
    """Redis-based cache implementation."""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client = None
    
    async def initialize(self):
        """Initialize Redis connection."""
        try:
            import redis.asyncio as aioredis
            self.client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def close(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        return await self.client.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in Redis with optional TTL."""
        if ttl:
            await self.client.setex(key, ttl, str(value))
        else:
            await self.client.set(key, str(value))
    
    async def setnx(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set if not exists. Returns True if set, False if key exists."""
        result = await self.client.setnx(key, str(value))
        if result and ttl:
            await self.client.expire(key, ttl)
        return bool(result)
    
    async def incr(self, key: str) -> int:
        """Increment value by 1."""
        return await self.client.incr(key)
    
    async def delete(self, key: str):
        """Delete key from Redis."""
        await self.client.delete(key)
    
    async def eval_lua(self, script: str, keys: list, args: list) -> Any:
        """Execute Lua script."""
        return await self.client.eval(script, len(keys), *keys, *args)


class Cache:
    """Cache abstraction that uses Redis or falls back to in-memory."""
    
    def __init__(self):
        self.backend = None
        self.is_redis = False
    
    async def initialize(self):
        """Initialize cache backend."""
        from config import settings
        
        if settings.redis_url:
            try:
                self.backend = RedisCache(settings.redis_url)
                await self.backend.initialize()
                self.is_redis = True
                logger.info("Using Redis cache")
            except Exception as e:
                logger.warning(f"Redis unavailable, falling back to in-memory cache: {e}")
                self.backend = InMemoryCache()
                self.is_redis = False
        else:
            logger.info("Using in-memory cache")
            self.backend = InMemoryCache()
            self.is_redis = False
    
    async def close(self):
        """Close cache connection."""
        if self.is_redis and self.backend:
            await self.backend.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return await self.backend.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache."""
        await self.backend.set(key, value, ttl)
    
    async def setnx(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set if not exists."""
        return await self.backend.setnx(key, value, ttl)
    
    async def incr(self, key: str) -> int:
        """Increment value."""
        return await self.backend.incr(key)
    
    async def delete(self, key: str):
        """Delete key."""
        await self.backend.delete(key)
    
    async def eval_lua(self, script: str, keys: list, args: list) -> Any:
        """Execute Lua script (Redis only)."""
        if not self.is_redis:
            raise NotImplementedError("Lua scripts only available with Redis")
        return await self.backend.eval_lua(script, keys, args)


# Global cache instance
cache = Cache()
