"""
Health check endpoint.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: Literal["healthy", "unhealthy"]
    service: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status of the service
    """
    return HealthResponse(
        status="healthy",
        service="agt-voting-system",
        version="1.0.0"
    )
