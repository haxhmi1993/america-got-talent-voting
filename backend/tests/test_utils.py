"""
Unit tests for utility functions.
"""
import pytest
from utils.security import (
    hash_fingerprint,
    normalize_last_name,
    validate_last_name,
    generate_nonce,
    mask_ip
)


def test_hash_fingerprint():
    """Test fingerprint hashing."""
    fingerprint = "test-fingerprint-123"
    hashed = hash_fingerprint(fingerprint)
    
    # Should return a hex string
    assert isinstance(hashed, str)
    assert len(hashed) == 64  # SHA-256 produces 64 hex chars
    
    # Same input should produce same hash
    assert hash_fingerprint(fingerprint) == hashed
    
    # Different input should produce different hash
    assert hash_fingerprint("different") != hashed


def test_normalize_last_name():
    """Test last name normalization."""
    assert normalize_last_name("Smith") == "smith"
    assert normalize_last_name("  JONES  ") == "jones"
    assert normalize_last_name("O'Brien") == "o'brien"
    assert normalize_last_name("Van Der Berg") == "van der berg"


def test_validate_last_name():
    """Test last name validation."""
    # Valid names
    valid, msg = validate_last_name("Smith")
    assert valid is True
    assert msg is None
    
    valid, msg = validate_last_name("O'Brien")
    assert valid is True
    
    valid, msg = validate_last_name("Van Der Berg")
    assert valid is True
    
    # Invalid names
    valid, msg = validate_last_name("")
    assert valid is False
    assert "required" in msg.lower()
    
    valid, msg = validate_last_name("   ")
    assert valid is False
    
    valid, msg = validate_last_name("Smith123")
    assert valid is False
    assert "invalid" in msg.lower()
    
    valid, msg = validate_last_name("a" * 256)
    assert valid is False
    assert "too long" in msg.lower()


def test_generate_nonce():
    """Test nonce generation."""
    fingerprint = "test-fp"
    timestamp = "2025-11-04T12:00:00Z"
    
    nonce = generate_nonce(fingerprint, timestamp)
    assert isinstance(nonce, str)
    assert len(nonce) == 64  # SHA-256 hash
    
    # Same inputs should produce same nonce
    assert generate_nonce(fingerprint, timestamp) == nonce
    
    # Different inputs should produce different nonce
    assert generate_nonce(fingerprint, "2025-11-04T12:00:01Z") != nonce


def test_mask_ip():
    """Test IP masking."""
    # IPv4
    assert mask_ip("192.168.1.100") == "192.168.xxx.xxx"
    assert mask_ip("10.0.0.1") == "10.0.xxx.xxx"
    
    # IPv6
    assert mask_ip("2001:0db8:85a3:0000:0000:8a2e:0370:7334").startswith("2001:0db8:")
    
    # Invalid IP
    assert mask_ip("invalid") == "xxx.xxx.xxx.xxx"
