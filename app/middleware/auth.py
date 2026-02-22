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
    # Log API key configuration status
    logger.info(f"[AUTH] API key check - Configured API key: {'SET' if settings.api_key else 'NOT SET'}")
    logger.info(f"[AUTH] API key check - Received X-API-Key header: {'PRESENT' if x_api_key else 'MISSING'}")
    
    if not settings.api_key:
        # If no API key is configured, allow all requests (development mode)
        logger.warning("[AUTH] API key not configured - allowing all requests (development mode)")
        return "dev-mode"
    
    if not x_api_key:
        logger.error("[AUTH] ❌ API key missing from request headers")
        logger.error(f"[AUTH] Expected API key: {settings.api_key[:10]}...{settings.api_key[-4:] if len(settings.api_key) > 14 else ''}")
        raise HTTPException(
            status_code=401,
            detail="API key required. Please provide X-API-Key header."
        )
    
    # Log received vs expected (partial for security)
    received_preview = f"{x_api_key[:10]}...{x_api_key[-4:]}" if len(x_api_key) > 14 else x_api_key[:10] + "..."
    expected_preview = f"{settings.api_key[:10]}...{settings.api_key[-4:]}" if len(settings.api_key) > 14 else settings.api_key[:10] + "..."
    logger.info(f"[AUTH] Received API key: {received_preview}")
    logger.info(f"[AUTH] Expected API key: {expected_preview}")
    
    if x_api_key != settings.api_key:
        logger.warning(f"[AUTH] ❌ Invalid API key attempt")
        logger.warning(f"[AUTH] Received: {received_preview}")
        logger.warning(f"[AUTH] Expected: {expected_preview}")
        logger.warning(f"[AUTH] Length match: {len(x_api_key)} vs {len(settings.api_key)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    logger.info("[AUTH] ✅ API key verified successfully")
    return x_api_key
