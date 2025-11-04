"""
Configuration management using pydantic-settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql+asyncpg://voting_user:voting_pass@postgres:5432/voting_db"
    
    # Redis
    redis_url: Optional[str] = None
    
    # Security
    fingerprint_salt: str = "default-salt-change-in-production"
    
    # Rate limiting
    ip_rate_limit: int = 5  # requests per minute
    ip_rate_window: int = 60  # seconds
    
    # Nonce
    nonce_ttl: int = 300  # 5 minutes in seconds
    
    # Escalation
    enable_escalation: bool = False
    
    # Device Tracking
    use_composite_device_tracking: bool = True  # Cross-browser tracking
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
