"""
Rate limiting middleware and utilities.
"""
import time
from fastapi import Request, HTTPException
from typing import Optional
import logging

from services.cache import cache
from config import settings
from utils.security import mask_ip

logger = logging.getLogger(__name__)


async def check_ip_rate_limit(ip: str) -> tuple[bool, Optional[str]]:
    """
    Check if IP address has exceeded rate limit.
    
    Uses sliding window counter approach.
    
    Args:
        ip: Client IP address
    
    Returns:
        Tuple of (is_allowed, error_message)
    """
    key = f"rate_limit:ip:{ip}"
    current_time = int(time.time())
    window_key = f"{key}:{current_time // settings.ip_rate_window}"
    
    try:
        # Get current count
        count_str = await cache.get(window_key)
        count = int(count_str) if count_str else 0
        
        if count >= settings.ip_rate_limit:
            logger.warning(f"Rate limit exceeded for IP: {mask_ip(ip)}")
            return False, f"Rate limit exceeded. Max {settings.ip_rate_limit} requests per {settings.ip_rate_window} seconds."
        
        # Increment counter
        await cache.incr(window_key)
        await cache.set(window_key, count + 1, ttl=settings.ip_rate_window)
        
        return True, None
        
    except Exception as e:
        logger.error(f"Error checking rate limit: {e}")
        # Fail open - allow request if rate limiting fails
        return True, None


async def validate_nonce(nonce: str) -> tuple[bool, Optional[str]]:
    """
    Validate that nonce is unique and not expired.
    
    Args:
        nonce: Nonce string from client
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not nonce:
        return False, "Nonce is required"
    
    key = f"nonce:{nonce}"
    
    try:
        # Try to set nonce with SETNX (set if not exists)
        was_set = await cache.setnx(key, "1", ttl=settings.nonce_ttl)
        
        if not was_set:
            logger.warning(f"Nonce reuse detected: {nonce[:16]}...")
            return False, "Invalid or reused nonce"
        
        return True, None
        
    except Exception as e:
        logger.error(f"Error validating nonce: {e}")
        return False, "Error validating nonce"


def get_client_ip(request: Request) -> str:
    """
    Extract client IP from request, considering proxy headers.
    
    Args:
        request: FastAPI request object
    
    Returns:
        Client IP address
    """
    # Check X-Forwarded-For header (from proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fall back to direct connection IP
    return request.client.host if request.client else "unknown"
