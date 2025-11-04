"""
Utility functions for hashing, validation, and security.
"""
import hashlib
import re
from typing import Optional
from config import settings


def hash_fingerprint(fingerprint: str) -> str:
    """
    Hash a fingerprint with salt using SHA-256.
    
    Args:
        fingerprint: Raw fingerprint string
    
    Returns:
        Hex-encoded SHA-256 hash
    """
    salted = f"{fingerprint}{settings.fingerprint_salt}"
    return hashlib.sha256(salted.encode()).hexdigest()


def normalize_last_name(last_name: str) -> str:
    """
    Normalize last name to lowercase and trim whitespace.
    
    Args:
        last_name: Raw last name input
    
    Returns:
        Normalized last name
    """
    return last_name.strip().lower()


def validate_last_name(last_name: str) -> tuple[bool, Optional[str]]:
    """
    Validate last name format.
    
    Args:
        last_name: Last name to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not last_name or not last_name.strip():
        return False, "Last name is required"
    
    if len(last_name) > 255:
        return False, "Last name is too long (max 255 characters)"
    
    # Allow letters, spaces, hyphens, apostrophes
    if not re.match(r"^[a-zA-Z\s\-']+$", last_name):
        return False, "Last name contains invalid characters"
    
    return True, None


def generate_nonce(fingerprint: str, timestamp: str) -> str:
    """
    Generate a nonce from fingerprint and timestamp.
    
    Args:
        fingerprint: Device fingerprint
        timestamp: ISO format timestamp
    
    Returns:
        Nonce string
    """
    combined = f"{fingerprint}:{timestamp}"
    return hashlib.sha256(combined.encode()).hexdigest()


def mask_ip(ip: str) -> str:
    """
    Mask IP address for logging (keep first two octets for IPv4).
    
    Args:
        ip: IP address
    
    Returns:
        Masked IP address
    """
    if "." in ip:  # IPv4
        parts = ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.xxx.xxx"
    elif ":" in ip:  # IPv6
        parts = ip.split(":")
        if len(parts) >= 2:
            return f"{parts[0]}:{parts[1]}:xxxx"
    
    return "xxx.xxx.xxx.xxx"
