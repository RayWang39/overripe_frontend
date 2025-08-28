"""Configuration management for the API"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    api_title: str = "IYP Query API"
    api_version: str = "1.0.0"
    api_description: str = "RESTful API for Internet Yellow Pages Graph Database Queries"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    
    # Neo4j Configuration
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt+s://iyp.christyquinn.com:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "lewagon25omgbbq")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    api_key_enabled: bool = os.getenv("API_KEY_ENABLED", "false").lower() == "true"
    api_keys: list = os.getenv("API_KEYS", "test-api-key-123").split(",")
    
    # CORS
    cors_origins: list = ["*"]  # Configure appropriately for production
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds
    
    # Caching
    cache_enabled: bool = False  # Set to True if Redis is available
    redis_url: Optional[str] = os.getenv("REDIS_URL", None)
    cache_ttl: int = 300  # seconds
    
    # Query Limits
    max_query_limit: int = 1000
    default_query_limit: int = 100
    query_timeout: int = 30  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()