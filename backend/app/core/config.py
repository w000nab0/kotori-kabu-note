from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    gemini_api_key: str
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    
    # JWT
    jwt_secret: str
    refresh_token_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60  # 1時間
    refresh_token_expire_days: int = 7     # 7日間
    
    # External APIs
    yfinance_timeout: int = 30
    
    # Monitoring
    sentry_dsn: Optional[str] = None
    ga_tracking_id: Optional[str] = None
    
    # Database
    database_url: Optional[str] = None
    
    # App Configuration
    cors_origin: str = "http://localhost:3000"
    
    # API Limits (Gemini 2.0 Flash-Lite)
    daily_requests_limit: int = 170  # 85% of 200
    minute_requests_limit: int = 25  # 85% of 30
    minute_tokens_limit: int = 850000  # 85% of 1,000,000
    user_daily_limit: int = 10
    tokens_per_request: int = 650
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()