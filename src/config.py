# not using:
"""
from pydantic_settings import BaseSettings, SettingsConfigDict

# use @lru_cache to cache the settings and only read from .env once

class Settings(BaseSettings):
    app_name: str = "Awesome API"
    admin_email: str
    items_per_user: int = 50

    model_config = SettingsConfigDict(env_file=".env")
"""
