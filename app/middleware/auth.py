"""
API key authentication middleware
"""
from fastapi import Header, HTTPException, Depends
from app.config import settings
import logging

logger = logging.getLogger(__name__)


async def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")) -> str:
    """
    Verify API key from request header
    
    Args:
        x_api_key: API key from X-API-Key header
    
    Returns:
        API key if valid
    
    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not settings.api_key:
        # If no API key is configured, allow all requests (development mode)
        logger.warning("API key not configured - allowing all requests")
        return "dev-mode"
    
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Please provide X-API-Key header."
        )
    
    if x_api_key != settings.api_key:
        logger.warning(f"Invalid API key attempt from {x_api_key[:10]}...")
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    
    return x_api_key
