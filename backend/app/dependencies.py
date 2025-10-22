"""
FastAPI dependencies for authentication and shared resources.
"""

from fastapi import Header, HTTPException

from .config import get_settings


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """
    Verify API key from X-API-Key header.

    Args:
        x_api_key: API key from header

    Returns:
        The verified API key

    Raises:
        HTTPException: If API key is missing or invalid
    """
    settings = get_settings()

    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Provide X-API-Key header."
        )

    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )

    return x_api_key
