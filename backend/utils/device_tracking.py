"""
Enhanced device tracking combining multiple signals.
"""
import hashlib
from typing import Optional
from fastapi import Request
from config import settings


def extract_device_signals(request: Request) -> dict:
    """
    Extract multiple device signals for cross-browser tracking.
    
    Combines:
    - IP address
    - User-Agent
    - Accept-Language
    - Screen resolution (from client)
    - Platform
    """
    signals = {
        "ip": get_client_ip(request),
        "user_agent": request.headers.get("user-agent", ""),
        "accept_language": request.headers.get("accept-language", ""),
        "accept_encoding": request.headers.get("accept-encoding", ""),
    }
    return signals


def generate_composite_device_id(
    fingerprint: str,
    ip_address: str,
    user_agent: str,
) -> str:
    """
    Generate a composite device ID that works across browsers.
    
    This uses IP + User-Agent patterns to identify the same physical device
    even when using different browsers.
    
    Args:
        fingerprint: Client-provided fingerprint
        ip_address: Client IP address
        user_agent: Browser user agent string
    
    Returns:
        Composite device ID hash
    """
    # Extract stable parts of user agent (OS, not browser)
    ua_lower = user_agent.lower()
    
    # Identify OS/platform (order matters - check mobile first)
    if "iphone" in ua_lower or "ipad" in ua_lower or "ipod" in ua_lower:
        platform = "ios"
    elif "android" in ua_lower:
        platform = "android"
    elif "mac os" in ua_lower or "macintosh" in ua_lower:
        platform = "macos"
    elif "windows" in ua_lower:
        platform = "windows"
    elif "linux" in ua_lower:
        platform = "linux"
    else:
        platform = "unknown"
    
    # For cross-browser tracking on SAME device, use only IP + platform
    # This makes Chrome and Safari on same Mac share vote limits
    composite = f"{ip_address}:{platform}"
    
    # Hash the composite
    salted = f"{composite}{settings.fingerprint_salt}"
    return hashlib.sha256(salted.encode()).hexdigest()


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
        return forwarded_for.split(",")[0].strip()
    
    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fall back to direct connection IP
    return request.client.host if request.client else "unknown"


def should_use_composite_tracking() -> bool:
    """
    Check if composite device tracking is enabled.
    
    Returns:
        True if composite tracking should be used
    """
    return getattr(settings, 'use_composite_device_tracking', True)
