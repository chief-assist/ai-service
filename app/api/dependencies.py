"""
Shared dependencies for API routes
"""
from fastapi import Header, HTTPException
from app.config import settings


async def get_api_key(x_api_key: str = Header(None)):
    """
    Dependency to extract API key from header
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    return x_api_key
