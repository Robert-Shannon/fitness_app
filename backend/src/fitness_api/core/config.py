from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql://localhost/fitness_dashboard"
    
    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # OAuth2 settings for different providers
    WHOOP_CLIENT_ID: Optional[str] = None
    WHOOP_CLIENT_SECRET: Optional[str] = None
    WHOOP_REDIRECT_URI: Optional[str] = None
    
    STRAVA_CLIENT_ID: Optional[str] = None
    STRAVA_CLIENT_SECRET: Optional[str] = None
    STRAVA_REDIRECT_URI: Optional[str] = None
    
    GARMIN_CLIENT_ID: Optional[str] = None
    GARMIN_CLIENT_SECRET: Optional[str] = None
    GARMIN_REDIRECT_URI: Optional[str] = None
    
    class Config:
        env_file = ".env"
        extra = "allow" 