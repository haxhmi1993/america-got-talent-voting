"""
Database service layer for contestants, device tokens, and votes.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import Optional
import logging

from models import Contestant, DeviceToken, Vote

logger = logging.getLogger(__name__)


async def get_or_create_device_token(
    db: AsyncSession,
    hashed_token: str
) -> DeviceToken:
    """
    Get or create a device token by hashed fingerprint.
    
    Args:
        db: Database session
        hashed_token: SHA-256 hash of the fingerprint
    
    Returns:
        DeviceToken instance
    """
    # Try to find existing token
    result = await db.execute(
        select(DeviceToken).where(DeviceToken.token == hashed_token)
    )
    device_token = result.scalar_one_or_none()
    
    if device_token:
        return device_token
    
    # Create new device token
    device_token = DeviceToken(token=hashed_token, total_votes=0)
    db.add(device_token)
    
    try:
        await db.commit()
        await db.refresh(device_token)
        logger.info(f"Created new device token: {device_token.id}")
    except IntegrityError:
        # Race condition - another process created it
        await db.rollback()
        result = await db.execute(
            select(DeviceToken).where(DeviceToken.token == hashed_token)
        )
        device_token = result.scalar_one()
    
    return device_token


async def get_contestant_by_last_name(
    db: AsyncSession,
    last_name_normalized: str
) -> Optional[Contestant]:
    """
    Find a contestant by normalized last name.
    
    Args:
        db: Database session
        last_name_normalized: Lowercase last name
    
    Returns:
        Contestant instance or None
    """
    result = await db.execute(
        select(Contestant).where(
            Contestant.last_name_normalized == last_name_normalized
        )
    )
    return result.scalar_one_or_none()


async def record_vote_tx(
    db: AsyncSession,
    contestant_id: str,
    device_token_id: str
) -> tuple[bool, str]:
    """
    Record a vote atomically with proper transaction handling.
    
    This function:
    1. Locks the device token row
    2. Checks total votes constraint
    3. Inserts the vote
    4. Updates device token total_votes
    
    Args:
        db: Database session
        contestant_id: UUID of contestant
        device_token_id: UUID of device token
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Start transaction with FOR UPDATE lock
        result = await db.execute(
            select(DeviceToken)
            .where(DeviceToken.id == device_token_id)
            .with_for_update()
        )
        device_token = result.scalar_one_or_none()
        
        if not device_token:
            return False, "Device token not found"
        
        # Check vote limit
        if device_token.total_votes >= 3:
            return False, "Vote limit exceeded (max 3 votes)"
        
        # Create vote record
        vote = Vote(
            contestant_id=contestant_id,
            device_token_id=device_token_id
        )
        db.add(vote)
        
        # Update device token vote count
        device_token.total_votes += 1
        
        # Commit transaction
        await db.commit()
        
        logger.info(
            f"Vote recorded: contestant={contestant_id}, "
            f"device={device_token_id}, total_votes={device_token.total_votes}"
        )
        return True, "Vote recorded successfully"
        
    except IntegrityError as e:
        await db.rollback()
        error_msg = str(e.orig)
        
        if "unique_vote_per_contestant" in error_msg:
            logger.info(f"Duplicate vote attempt: contestant={contestant_id}, device={device_token_id}")
            return False, "Vote already recorded for this contestant"
        elif "check_max_votes" in error_msg:
            logger.warning(f"Vote limit check failed: device={device_token_id}")
            return False, "Vote limit exceeded (max 3 votes)"
        else:
            logger.error(f"Database integrity error: {e}")
            return False, "Database error"
    
    except Exception as e:
        await db.rollback()
        logger.error(f"Unexpected error recording vote: {e}")
        return False, "Internal server error"


async def check_existing_vote(
    db: AsyncSession,
    contestant_id: str,
    device_token_id: str
) -> bool:
    """
    Check if a vote already exists for this contestant and device.
    
    Args:
        db: Database session
        contestant_id: UUID of contestant
        device_token_id: UUID of device token
    
    Returns:
        True if vote exists, False otherwise
    """
    result = await db.execute(
        select(Vote).where(
            Vote.contestant_id == contestant_id,
            Vote.device_token_id == device_token_id
        )
    )
    return result.scalar_one_or_none() is not None


async def get_device_vote_count(
    db: AsyncSession,
    device_token_id: str
) -> int:
    """
    Get the total number of votes for a device.
    
    Args:
        db: Database session
        device_token_id: UUID of device token
    
    Returns:
        Total vote count
    """
    result = await db.execute(
        select(DeviceToken).where(DeviceToken.id == device_token_id)
    )
    device_token = result.scalar_one_or_none()
    return device_token.total_votes if device_token else 0
