from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Database Configuration
    database_url: str = "postgresql://postgres:manus12345@34.68.101.254:5432/backend_v1"
    database_echo: bool = False
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # CORS Configuration
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080"
    ]
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    
    # Scraping Configuration
    scraping_delay: float = 1.0
    max_concurrent_scrapers: int = 5
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    request_timeout: int = 30
    max_retries: int = 3
    
    # Celery Configuration
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # Search Configuration
    default_search_timeout: int = 30
    max_search_results: int = 100
    default_search_results: int = 50
    
    # Rate Limiting
    rate_limit_search: str = "10/minute"
    rate_limit_results: str = "60/minute"
    max_websocket_connections: int = 5
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()

