"""
Unit tests for cache abstraction.
"""
import pytest
from services.cache import InMemoryCache


@pytest.mark.asyncio
async def test_in_memory_cache_set_get():
    """Test basic set and get operations."""
    cache = InMemoryCache()
    
    await cache.set("key1", "value1")
    result = await cache.get("key1")
    assert result == "value1"
    
    # Non-existent key
    result = await cache.get("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_in_memory_cache_ttl():
    """Test TTL expiration."""
    cache = InMemoryCache()
    
    await cache.set("key1", "value1", ttl=1)
    result = await cache.get("key1")
    assert result == "value1"
    
    # Wait for expiration
    import asyncio
    await asyncio.sleep(1.1)
    
    result = await cache.get("key1")
    assert result is None


@pytest.mark.asyncio
async def test_in_memory_cache_setnx():
    """Test SETNX operation."""
    cache = InMemoryCache()
    
    # First set should succeed
    result = await cache.setnx("key1", "value1")
    assert result is True
    
    # Second set should fail (key exists)
    result = await cache.setnx("key1", "value2")
    assert result is False
    
    # Value should still be the first one
    value = await cache.get("key1")
    assert value == "value1"


@pytest.mark.asyncio
async def test_in_memory_cache_incr():
    """Test increment operation."""
    cache = InMemoryCache()
    
    # First increment creates key with value 1
    result = await cache.incr("counter")
    assert result == 1
    
    # Subsequent increments
    result = await cache.incr("counter")
    assert result == 2
    
    result = await cache.incr("counter")
    assert result == 3


@pytest.mark.asyncio
async def test_in_memory_cache_delete():
    """Test delete operation."""
    cache = InMemoryCache()
    
    await cache.set("key1", "value1")
    assert await cache.get("key1") == "value1"
    
    await cache.delete("key1")
    assert await cache.get("key1") is None
