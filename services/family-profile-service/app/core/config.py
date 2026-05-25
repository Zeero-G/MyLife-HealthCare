import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PORT: int = 8003
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me")
    JWT_ALGORITHM: str = "HS256"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://mylife.vercel.app"]
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
