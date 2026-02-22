"""
Rate limiting middleware
"""
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.requests = defaultdict(list)
        self.rate_limit_per_minute = settings.rate_limit_per_minute
        self.rate_limit_per_hour = settings.rate_limit_per_hour
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        # Get client identifier (IP address or API key)
        client_id = self._get_client_id(request)
        
        # Check rate limits
        if self._is_rate_limited(client_id):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Record request
        self._record_request(client_id)
        
        # Process request
        response = await call_next(request)
        return response
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get API key from header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"
        
        # Fallback to IP address
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"
    
    def _is_rate_limited(self, client_id: str) -> bool:
        """Check if client has exceeded rate limits"""
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
    
    def _record_request(self, client_id: str):
        """Record a request for rate limiting"""
        self.requests[client_id].append(datetime.utcnow())
