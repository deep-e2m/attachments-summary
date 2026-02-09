"""
Configuration settings for the WordPress Analyzer API.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    app_name: str = "WordPress Analyzer API"
    debug: bool = False

    # HTTP Client Settings
    request_timeout: int = Field(default=30, description="HTTP request timeout in seconds")
    analysis_timeout: int = Field(default=120, description="Overall analysis timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of HTTP retries")
    user_agent: str = Field(
        default="Mozilla/5.0 (compatible; WordPress-Analyzer/1.0)",
        description="User agent for HTTP requests"
    )

    # WordPress Detection Settings
    enable_plugin_detection: bool = Field(default=True, description="Enable plugin detection")
    enable_theme_detection: bool = Field(default=True, description="Enable theme detection")
    enable_version_detection: bool = Field(default=True, description="Enable WordPress version detection")

    # Rate Limiting
    rate_limit_requests: int = Field(default=10, description="Max requests per minute per IP")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
