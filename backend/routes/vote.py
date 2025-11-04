"""
Vote endpoint implementation.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
import logging
from typing import Optional

from database import get_db
from services.db import (
    get_or_create_device_token,
    get_contestant_by_last_name,
    record_vote_tx,
    check_existing_vote
)
from utils.security import hash_fingerprint, normalize_last_name, validate_last_name
from utils.rate_limiter import check_ip_rate_limit, validate_nonce, get_client_ip
from utils.device_tracking import generate_composite_device_id, should_use_composite_tracking
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class VoteRequest(BaseModel):
    """Request model for voting."""
    last_name: str = Field(..., description="Contestant's last name", min_length=1, max_length=255)
    fingerprint: str = Field(..., description="Device fingerprint", min_length=1)
    nonce: str = Field(..., description="One-time nonce for request", min_length=1)


class VoteResponse(BaseModel):
    """Response model for voting."""
    status: str = Field(..., description="Status: success, error, or challenge")
    message: str = Field(..., description="Human-readable message")
    type: Optional[str] = Field(None, description="Challenge type if status=challenge")


@router.post("/vote", response_model=VoteResponse)
async def vote(
    vote_request: VoteRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a vote for a contestant.
    
    Process:
    1. Validate input
    2. Check rate limits
    3. Validate nonce
    4. Hash fingerprint
    5. Get or create device token
    6. Find contestant
    7. Record vote atomically
    
    Returns:
        VoteResponse with status and message
    """
    client_ip = get_client_ip(request)
    
    # Log request (with masked data)
    logger.info(f"Vote request from IP: {client_ip[:10]}..., last_name: {vote_request.last_name}")
    
    # 1. Validate last name format
    is_valid, error_msg = validate_last_name(vote_request.last_name)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # 2. Check IP rate limit
    rate_ok, rate_msg = await check_ip_rate_limit(client_ip)
    if not rate_ok:
        # Check if escalation is enabled
        if settings.enable_escalation:
            logger.info(f"Escalation triggered for IP: {client_ip}")
            return VoteResponse(
                status="challenge",
                message="Too many requests. Please complete verification.",
                type="captcha"
            )
        raise HTTPException(status_code=429, detail=rate_msg)
    
    # 3. Validate nonce
    nonce_valid, nonce_msg = await validate_nonce(vote_request.nonce)
    if not nonce_valid:
        raise HTTPException(status_code=400, detail=nonce_msg)
    
    # 4. Generate device ID (composite or simple)
    if should_use_composite_tracking():
        # Use composite tracking: IP + User-Agent + Fingerprint
        # This prevents voting from different browsers on same device
        user_agent = request.headers.get("user-agent", "")
        hashed_token = generate_composite_device_id(
            vote_request.fingerprint,
            client_ip,
            user_agent
        )
        logger.info(f"Using composite device tracking for IP: {client_ip[:10]}...")
    else:
        # Use simple fingerprint-only tracking
        hashed_token = hash_fingerprint(vote_request.fingerprint)
    
    # 5. Get or create device token
    try:
        device_token = await get_or_create_device_token(db, hashed_token)
    except Exception as e:
        logger.error(f"Error getting device token: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
    # 6. Find contestant
    normalized_name = normalize_last_name(vote_request.last_name)
    contestant = await get_contestant_by_last_name(db, normalized_name)
    
    if not contestant:
        raise HTTPException(
            status_code=404,
            detail=f"Contestant with last name '{vote_request.last_name}' not found"
        )
    
    # 7. Check if vote already exists (idempotent check)
    already_voted = await check_existing_vote(db, str(contestant.id), str(device_token.id))
    if already_voted:
        logger.info(f"Vote already recorded (idempotent): contestant={contestant.id}")
        return VoteResponse(
            status="success",
            message="Vote already recorded for this contestant"
        )
    
    # 8. Record vote atomically
    success, message = await record_vote_tx(db, str(contestant.id), str(device_token.id))
    
    if success:
        logger.info(
            f"Vote successful: contestant={contestant.last_name}, "
            f"device_total={device_token.total_votes + 1}"
        )
        return VoteResponse(
            status="success",
            message=message
        )
    else:
        # Check if it's a vote limit issue
        if "limit exceeded" in message.lower():
            raise HTTPException(status_code=403, detail=message)
        elif "already recorded" in message.lower():
            # Duplicate vote (race condition handled at DB level)
            return VoteResponse(
                status="success",
                message="Vote already recorded for this contestant"
            )
        else:
            logger.error(f"Vote failed: {message}")
            raise HTTPException(status_code=500, detail=message)
