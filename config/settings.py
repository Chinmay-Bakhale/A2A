"""
Configuration module
Loads environment variables and application settings
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Leave Policy Assistant"
    VERSION: str = "1.0.0"
    PORT: int = 8080
    LOG_LEVEL: str = "INFO"
    
    # LLM Configuration
    LITELLM_MODEL: str = "gemini/gemini-pro"
    GOOGLE_API_KEY: Optional[str] = None
    
    # Snowflake Configuration
    SNOWFLAKE_ACCOUNT: Optional[str] = None
    SNOWFLAKE_USER: Optional[str] = None
    SNOWFLAKE_PASSWORD: Optional[str] = None
    SNOWFLAKE_WAREHOUSE: Optional[str] = None
    SNOWFLAKE_DATABASE: Optional[str] = None
    SNOWFLAKE_SCHEMA: Optional[str] = None
    
    # Google Cloud
    GCP_PROJECT_ID: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # Circuit Breaker Settings
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_TIMEOUT: int = 60
    
    # Session Settings
    SESSION_TIMEOUT_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
