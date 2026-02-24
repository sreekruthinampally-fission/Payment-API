from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Database configuration
    database_url: str = "postgresql+psycopg2://payment_user:StrongPass123@localhost:5432/payment_db"
    
    # Order processing configuration
    enable_strict_idempotency_check: bool = False
    transaction_settlement_window: float = 0.0
    enable_graceful_degradation: bool = False
    
    # Wallet operation configuration
    wallet_operation_lock_timeout: int = 0
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
