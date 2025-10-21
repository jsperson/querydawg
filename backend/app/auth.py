"""
Authentication utilities for API key validation
"""
import os
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader


API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key() -> str:
    """Get the configured API key from environment"""
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError("API_KEY environment variable not set")
    return api_key


async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    """
    Verify the API key from the X-API-Key header

    Args:
        api_key: API key from request header

    Raises:
        HTTPException: If API key is missing or invalid

    Returns:
        The validated API key
    """
    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include X-API-Key header in your request."
        )

    expected_key = get_api_key()
    if api_key != expected_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )

    return api_key
