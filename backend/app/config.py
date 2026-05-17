from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@duct-tape.local"
    FRONTEND_URL: str = "http://localhost:5173"
    DEBUG: bool = False

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

import sys

_INSECURE_DEFAULTS = {"change-this-to-random-secret-in-production", "secret", "changeme"}

if not settings.DEBUG and settings.SECRET_KEY in _INSECURE_DEFAULTS:
    print("FATAL: SECRET_KEY must be changed from the default value in production", file=sys.stderr)
    sys.exit(1)
