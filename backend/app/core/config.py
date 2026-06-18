"""
Application configuration module.
Loads settings from environment variables or a local .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core API Configurations
    APP_NAME: str = "AI Customer Retention Platform API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api"

    # Security & Authentication
    JWT_SECRET: str = "super-secret-key-change-in-production-1234567890"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database Persistence
    DATABASE_URL: str = "sqlite:///./customer_retention.db"

    # Machine Learning Model Paths
    MODEL_PATH: str = "ml/artifacts/model.pkl"
    PIPELINE_PATH: str = "ml/artifacts/pipeline.pkl"


settings = Settings()
