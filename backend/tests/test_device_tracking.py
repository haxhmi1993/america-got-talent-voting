"""
Test composite device tracking across browsers.
"""
import pytest
from utils.device_tracking import generate_composite_device_id


def test_same_device_different_browsers():
    """Test that same device with different browsers gets same device ID."""
    ip = "192.168.1.100"
    
    # Chrome fingerprint
    chrome_fp = "chrome-fingerprint-abc123"
    chrome_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Safari fingerprint (different!)
    safari_fp = "safari-fingerprint-xyz789"
    safari_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
    
    # Generate device IDs
    chrome_device_id = generate_composite_device_id(chrome_fp, ip, chrome_ua)
    safari_device_id = generate_composite_device_id(safari_fp, ip, safari_ua)
    
    # Both should be THE SAME because:
    # - Same IP address
    # - Same OS (macOS)
    # Despite different browsers and fingerprints!
    assert chrome_device_id == safari_device_id, \
        "Same device with different browsers should have same device ID"


def test_different_devices_different_ids():
    """Test that different devices get different IDs."""
    # Device 1
    device1_fp = "fingerprint-1"
    device1_ip = "192.168.1.100"
    device1_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    
    # Device 2 (different IP)
    device2_fp = "fingerprint-2"
    device2_ip = "192.168.1.101"
    device2_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    
    id1 = generate_composite_device_id(device1_fp, device1_ip, device1_ua)
    id2 = generate_composite_device_id(device2_fp, device2_ip, device2_ua)
    
    assert id1 != id2, "Different devices should have different IDs"


def test_different_os_different_ids():
    """Test that different OS on same IP get different IDs."""
    ip = "192.168.1.100"
    fp = "same-fingerprint"
    
    # macOS
    macos_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    macos_id = generate_composite_device_id(fp, ip, macos_ua)
    
    # Windows
    windows_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    windows_id = generate_composite_device_id(fp, ip, windows_ua)
    
    assert macos_id != windows_id, "Different OS should have different IDs"


def test_mobile_vs_desktop():
    """Test that mobile and desktop on same network are treated as different devices."""
    ip = "192.168.1.100"
    fp = "same-fingerprint"
    
    # Desktop
    desktop_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    desktop_id = generate_composite_device_id(fp, ip, desktop_ua)
    
    # Mobile
    mobile_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"
    mobile_id = generate_composite_device_id(fp, ip, mobile_ua)
    
    # Should be different because different OS (macOS vs iOS)
    assert desktop_id != mobile_id, "Desktop and mobile should have different IDs"
