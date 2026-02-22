"""
Redis cache service for AI service responses
"""
import json
import hashlib
import logging
from typing import Optional, Any
from app.config import settings

logger = logging.getLogger(__name__)

# Try to import Redis, but make it optional
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available. Caching will be disabled.")


class CacheService:
    """Service for caching AI responses using Redis"""
    
    def __init__(self):
        """Initialize cache service"""
        self.enabled = settings.redis_enabled and REDIS_AVAILABLE
        self.client = None
        
        if self.enabled:
            try:
                self.client = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    password=settings.redis_password if settings.redis_password else None,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                logger.info(f"Redis cache initialized: {settings.redis_host}:{settings.redis_port}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}. Caching disabled.")
                self.enabled = False
                self.client = None
        else:
            logger.info("Redis caching is disabled")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self.enabled or not self.client:
            return None
        
        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set value in cache with TTL
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            await self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        if not self.enabled or not self.client:
            return False
        
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.warning(f"Cache exists error for key {key}: {str(e)}")
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            try:
                await self.client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {str(e)}")
    
    @staticmethod
    def generate_key(prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from prefix and arguments
        
        Args:
            prefix: Key prefix (e.g., 'ingredients', 'recipes')
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key
            
        Returns:
            Generated cache key
        """
        # Create a deterministic key from arguments
        key_parts = [prefix]
        
        # Add positional args
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            elif isinstance(arg, list):
                # Sort list for consistent keys
                key_parts.append(','.join(sorted(str(x) for x in arg)))
            else:
                # Hash complex objects
                key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])
        
        # Add keyword args (sorted for consistency)
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            for k, v in sorted_kwargs:
                if isinstance(v, (str, int, float, bool)):
                    key_parts.append(f"{k}:{v}")
                elif isinstance(v, list):
                    key_parts.append(f"{k}:{','.join(sorted(str(x) for x in v))}")
                else:
                    key_parts.append(f"{k}:{hashlib.md5(str(v).encode()).hexdigest()[:8]}")
        
        # Join and hash if too long
        key = ':'.join(key_parts)
        if len(key) > 250:  # Redis key length limit
            key = f"{prefix}:{hashlib.md5(key.encode()).hexdigest()}"
        
        return key


# Global cache service instance
cache_service = CacheService()
