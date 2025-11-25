"""
FastAPI dependencies for authentication and shared resources.
"""

from fastapi import Header, HTTPException
from typing import Optional

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


async def verify_admin_password(
    x_admin_password: Optional[str] = Header(None, alias="X-Admin-Password")
) -> str:
    """
    Verify admin password from X-Admin-Password header.
    Used for mutating operations (create, delete, etc.)

    Args:
        x_admin_password: Admin password from header

    Returns:
        The verified admin password

    Raises:
        HTTPException: If admin password is missing or invalid
    """
    settings = get_settings()

    # If no admin password is configured, allow access (dev mode)
    if not settings.admin_password:
        return ""

    if not x_admin_password:
        raise HTTPException(
            status_code=401,
            detail="Admin password required for this operation. Provide X-Admin-Password header."
        )

    if x_admin_password != settings.admin_password:
        raise HTTPException(
            status_code=403,
            detail="Invalid admin password"
        )

    return x_admin_password
