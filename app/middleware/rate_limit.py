"""
Rate limiting middleware with Redis support
"""
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
from app.services.cache_service import cache_service
import logging
import time

logger = logging.getLogger(__name__)

# Try to import Redis for distributed rate limiting
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with Redis support for distributed systems"""
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limit_per_minute = settings.rate_limit_per_minute
        self.rate_limit_per_hour = settings.rate_limit_per_hour
        self.use_redis = settings.redis_enabled and REDIS_AVAILABLE and cache_service.enabled
        self.redis_client = cache_service.client if self.use_redis else None
        
        # Always initialize in-memory fallback (even when Redis is enabled, in case it fails)
        from collections import defaultdict
        self.requests = defaultdict(list)
        
        if self.use_redis:
            logger.info("Rate limiting using Redis for distributed support (with in-memory fallback)")
        else:
            logger.info("Rate limiting using in-memory storage")
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        # Skip rate limiting for health check and root endpoints
        if request.url.path in ["/", "/api/ai/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get client identifier (IP address or API key)
        client_id = self._get_client_id(request)
        
        # Check rate limits
        if await self._is_rate_limited(client_id):
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {self.rate_limit_per_minute} requests per minute and {self.rate_limit_per_hour} requests per hour. Please try again later."
            )
        
        # Record request
        await self._record_request(client_id)
        
        # Process request
        response = await call_next(request)
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get API key from header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key[:16]}"  # Use first 16 chars for privacy
        
        # Fallback to IP address
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"
    
    async def _is_rate_limited(self, client_id: str) -> bool:
        """Check if client has exceeded rate limits"""
        if self.use_redis and self.redis_client:
            return await self._is_rate_limited_redis(client_id)
        else:
            return self._is_rate_limited_memory(client_id)
    
    async def _is_rate_limited_redis(self, client_id: str) -> bool:
        """Check rate limits using Redis"""
        try:
            now = int(time.time())
            minute_key = f"ratelimit:{client_id}:minute"
            hour_key = f"ratelimit:{client_id}:hour"
            
            # Check per-minute limit
            minute_count = await self.redis_client.get(minute_key)
            if minute_count and int(minute_count) >= self.rate_limit_per_minute:
                return True
            
            # Check per-hour limit
            hour_count = await self.redis_client.get(hour_key)
            if hour_count and int(hour_count) >= self.rate_limit_per_hour:
                return True
            
            return False
        except Exception as e:
            logger.warning(f"Redis rate limit check failed: {str(e)}. Falling back to memory.")
            return self._is_rate_limited_memory(client_id)
    
    def _is_rate_limited_memory(self, client_id: str) -> bool:
        """Check rate limits using in-memory storage"""
        now = datetime.utcnow()
        requests = self.requests[client_id]
        
        # Remove old requests (older than 1 hour)
        requests[:] = [req_time for req_time in requests if now - req_time < timedelta(hours=1)]
        
        # Check per-minute limit
        recent_minute = [req_time for req_time in requests if now - req_time < timedelta(minutes=1)]
        if len(recent_minute) >= self.rate_limit_per_minute:
            return True
        
        # Check per-hour limit
        if len(requests) >= self.rate_limit_per_hour:
            return True
        
        return False
    
    async def _record_request(self, client_id: str):
        """Record a request for rate limiting"""
        if self.use_redis and self.redis_client:
            await self._record_request_redis(client_id)
        else:
            self._record_request_memory(client_id)
    
    async def _record_request_redis(self, client_id: str):
        """Record request using Redis"""
        try:
            now = int(time.time())
            minute_key = f"ratelimit:{client_id}:minute"
            hour_key = f"ratelimit:{client_id}:hour"
            
            # Increment counters with TTL
            pipe = self.redis_client.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)  # 1 minute TTL
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)  # 1 hour TTL
            await pipe.execute()
        except Exception as e:
            logger.warning(f"Redis rate limit record failed: {str(e)}. Falling back to memory.")
            self._record_request_memory(client_id)
    
    def _record_request_memory(self, client_id: str):
        """Record request using in-memory storage"""
        self.requests[client_id].append(datetime.utcnow())
