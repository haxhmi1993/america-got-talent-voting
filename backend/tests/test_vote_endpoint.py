"""
Integration tests for the voting endpoint.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import uuid

from main import app
from models import Base, Contestant, DeviceToken
from database import get_db
from config import settings
from utils.security import normalize_last_name

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    """Override database dependency for testing."""
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def setup_database():
    """Setup test database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed test contestant
    async with TestSessionLocal() as session:
        contestant = Contestant(
            id=uuid.uuid4(),
            first_name="John",
            last_name="Smith",
            last_name_normalized=normalize_last_name("Smith")
        )
        session.add(contestant)
        await session.commit()
    
    yield
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_vote_success(setup_database):
    """Test successful vote submission."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/vote",
            json={
                "last_name": "Smith",
                "fingerprint": "test-fingerprint-123",
                "nonce": f"test-nonce-{uuid.uuid4()}"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "recorded" in data["message"].lower()


@pytest.mark.asyncio
async def test_vote_contestant_not_found(setup_database):
    """Test voting for non-existent contestant."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/vote",
            json={
                "last_name": "NonExistent",
                "fingerprint": "test-fingerprint-456",
                "nonce": f"test-nonce-{uuid.uuid4()}"
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_vote_duplicate(setup_database):
    """Test duplicate vote prevention."""
    fingerprint = "test-fingerprint-duplicate"
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First vote
        response1 = await client.post(
            "/api/vote",
            json={
                "last_name": "Smith",
                "fingerprint": fingerprint,
                "nonce": f"test-nonce-{uuid.uuid4()}"
            }
        )
        assert response1.status_code == 200
        
        # Second vote for same contestant (should be idempotent)
        response2 = await client.post(
            "/api/vote",
            json={
                "last_name": "Smith",
                "fingerprint": fingerprint,
                "nonce": f"test-nonce-{uuid.uuid4()}"
            }
        )
        assert response2.status_code == 200
        data = response2.json()
        assert "already recorded" in data["message"].lower()


@pytest.mark.asyncio
async def test_vote_invalid_last_name(setup_database):
    """Test validation of last name."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Empty last name
        response = await client.post(
            "/api/vote",
            json={
                "last_name": "",
                "fingerprint": "test-fingerprint",
                "nonce": f"test-nonce-{uuid.uuid4()}"
            }
        )
        assert response.status_code == 422 or response.status_code == 400
        
        # Invalid characters
        response = await client.post(
            "/api/vote",
            json={
                "last_name": "Smith123",
                "fingerprint": "test-fingerprint",
                "nonce": f"test-nonce-{uuid.uuid4()}"
            }
        )
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_vote_nonce_reuse(setup_database):
    """Test nonce reuse prevention."""
    nonce = f"test-nonce-{uuid.uuid4()}"
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First request with nonce
        response1 = await client.post(
            "/api/vote",
            json={
                "last_name": "Smith",
                "fingerprint": "test-fingerprint-nonce1",
                "nonce": nonce
            }
        )
        assert response1.status_code == 200
        
        # Second request with same nonce (should fail)
        response2 = await client.post(
            "/api/vote",
            json={
                "last_name": "Smith",
                "fingerprint": "test-fingerprint-nonce2",
                "nonce": nonce
            }
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "nonce" in data["detail"].lower()
