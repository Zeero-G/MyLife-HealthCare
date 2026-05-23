import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PORT: int = 8005
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://mylife.vercel.app"]

    class Config:
        env_file = ".env"


settings = Settings()
