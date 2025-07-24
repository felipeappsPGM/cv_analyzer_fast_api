# =============================================
# app/config/settings.py
# =============================================
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str
    database_url_sync: str
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # App
    app_name: str = "FastAPI Users App"
    debug: bool = False
    version: str = "0.1.0"
    
    class Config:
        env_file = ".env"

settings = Settings()