from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Lead & Voice Desk"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment & Security
    APP_ENV: str = "development"
    SECRET_KEY: str = "super_secret_jwt_signing_key_replace_in_production_32bytes"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    ENCRYPTION_KEY: str = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="  # Base64 encoded 32 bytes
    
    # Database
    DATABASE_URL: str = "sqlite:///./desk.db"  # Defaults to SQLite for local tests; PostgreSQL in docker
    POSTGRES_SERVER: Optional[str] = None
    
    # Telephony & Calling Defaults
    DEFAULT_TELEPHONY_PROVIDER: str = "mock"  # mock | sarvam_vobiz | exotel | smartflo
    SARVAM_API_KEY: str = "mock_sarvam_api_key"
    SARVAM_BASE_URL: str = "https://api.sarvam.ai"
    
    # Regulatory Compliance (TRAI / India)
    ENFORCE_CALLING_HOURS: bool = True
    CALLING_WINDOW_START_HOUR: int = 9   # 09:00 AM IST
    CALLING_WINDOW_END_HOUR: int = 21    # 09:00 PM IST
    DEFAULT_CALL_TIMEOUT_SECONDS: int = 300
    
    # Web Scraper Security
    MAX_CRAWL_PAGES: int = 20
    MAX_CRAWL_DEPTH: int = 2
    CRAWL_TIMEOUT_SECONDS: int = 10
    MAX_PAGE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5MB
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
