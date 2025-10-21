"""
Pydantic models for API responses
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: datetime


class DatabaseListResponse(BaseModel):
    """Database list response"""
    databases: List[str]
    count: int


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
