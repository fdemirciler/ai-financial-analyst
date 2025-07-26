from pydantic_settings import BaseSettings
from pydantic import Field
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    # API Keys - Check both LLM_API_KEY and GOOGLE_API_KEY for backward compatibility
    GEMINI_API_KEY: str = Field(
        default_factory=lambda: os.getenv("LLM_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
    )

    # File upload settings
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB in bytes

    # LLM Settings
    LLM_PROVIDER: str = Field(
        default_factory=lambda: os.getenv("LLM_PROVIDER", "gemini")
    )
    LLM_MODEL: str = Field(default_factory=lambda: os.getenv("LLM_MODEL", ""))
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 8192

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
