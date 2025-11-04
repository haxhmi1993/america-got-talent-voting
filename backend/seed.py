"""
Seed database with sample contestants for testing.
"""
import asyncio
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from models import Contestant, Base
from config import settings
from utils.security import normalize_last_name


async def seed_contestants():
    """Seed database with sample contestants."""
    engine = create_async_engine(settings.database_url, echo=True)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Sample contestants (AGT-themed)
    contestants_data = [
        ("John", "Smith"),
        ("Sarah", "Johnson"),
        ("Michael", "Williams"),
        ("Emily", "Brown"),
        ("David", "Jones"),
        ("Jessica", "Garcia"),
        ("Christopher", "Martinez"),
        ("Ashley", "Rodriguez"),
        ("Matthew", "Wilson"),
        ("Amanda", "Anderson"),
    ]
    
    async with async_session() as session:
        added_count = 0
        skipped_count = 0
        
        for first_name, last_name in contestants_data:
            # Check if contestant already exists
            normalized = normalize_last_name(last_name)
            stmt = select(Contestant).where(
                Contestant.first_name == first_name,
                Contestant.last_name_normalized == normalized
            )
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"⏭️  Skipping {first_name} {last_name} (already exists)")
                skipped_count += 1
            else:
                contestant = Contestant(
                    id=uuid.uuid4(),
                    first_name=first_name,
                    last_name=last_name,
                    last_name_normalized=normalized
                )
                session.add(contestant)
                added_count += 1
        
        if added_count > 0:
            await session.commit()
            print(f"✅ Seeded {added_count} new contestants")
        
        if skipped_count > 0:
            print(f"ℹ️  Skipped {skipped_count} existing contestants")
        
        if added_count == 0 and skipped_count == 0:
            print("ℹ️  No contestants to seed")
    
    await engine.dispose()


if __name__ == "__main__":
    print("🌱 Seeding database with sample contestants...")
    asyncio.run(seed_contestants())
