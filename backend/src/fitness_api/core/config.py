from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql://localhost/fitness_dashboard"
    
    # For future environments, you can override these using environment variables
    class Config:
        env_file = ".env"