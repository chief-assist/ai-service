"""
Configuration settings for the AI service
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Service Configuration
    service_name: str = "chefassist-ai"
    version: str = "1.0.0"
    port: int = 8000
    environment: str = "development"
    
    # Google Gemini AI
    google_api_key: str = ""
    google_generative_ai_api_key: str = ""
    
    # API Security
    api_key: str = ""
    
    # CORS - Can be set as comma-separated string in .env
    allowed_origins: str = "http://localhost:5000,http://localhost:9002"
    
    # Redis (optional, for caching)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_enabled: bool = False
    
    # Gemini Model Configuration
    gemini_model: str = "gemini-2.0-flash"
    gemini_timeout: int = 120  # Timeout in seconds for Gemini API calls
    gemini_max_retries: int = 3  # Maximum number of retry attempts
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000
    
    # HTTP Client Configuration
    http_timeout: int = 120  # Timeout for HTTP requests (image downloads, etc.)
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse allowed_origins from comma-separated string to list"""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
