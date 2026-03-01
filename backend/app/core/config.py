import ssl

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """
    Central configuration class for ACMP.
    Reads all values from .env file automatically.
    If any required key is missing — app refuses to start.
    Add new config values here as the platform grows.
    """

    model_config = SettingsConfigDict(
        env_file=".env",            # tells pydantic-settings where to find the .env file
        env_file_encoding="utf-8",  # encoding of the .env file
        case_sensitive=False,       # GROQ_API_KEY and groq_api_key both work
        extra="ignore"              # ignore any extra keys in .env that aren't defined here
    )


    groq_api_key : str 
    model : str

    admin_secret_key : str
    admin_username : str
    admin_password : str

    embedding_model : str

    chroma_host : str
    chroma_port : int
    chroma_collection_name : str

    backend_host : str
    backend_port : int

    max_retries : int
    docker_timeout : int



@lru_cache
def get_settings():
    """
    Returns a cached instance of Settings.
    .env is read exactly ONCE when this is first called.
    Every subsequent call returns the same cached object.
    Use this function everywhere instead of instantiating Settings directly.

    Usage in any file:
        from app.core.config import get_settings
        settings = get_settings()
        print(settings.groq_api_key)
    """
    return Settings()
