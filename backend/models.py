"""
Database models for the voting system.
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class Contestant(Base):
    """Represents a contestant in the voting system."""
    __tablename__ = "contestants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    last_name_normalized = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Contestant(id={self.id}, name={self.first_name} {self.last_name})>"


class DeviceToken(Base):
    """Represents a unique device (fingerprint) that can vote."""
    __tablename__ = "device_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(String(255), nullable=False, unique=True, index=True)
    total_votes = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint('total_votes <= 3', name='check_max_votes'),
    )

    def __repr__(self):
        return f"<DeviceToken(id={self.id}, total_votes={self.total_votes})>"


class Vote(Base):
    """Represents a single vote for a contestant by a device."""
    __tablename__ = "votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contestant_id = Column(UUID(as_uuid=True), ForeignKey("contestants.id"), nullable=False)
    device_token_id = Column(UUID(as_uuid=True), ForeignKey("device_tokens.id"), nullable=False)
    voted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint('contestant_id', 'device_token_id', name='unique_vote_per_contestant'),
    )

    def __repr__(self):
        return f"<Vote(id={self.id}, contestant={self.contestant_id}, device={self.device_token_id})>"
