from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY: str = Field(..., alias="LLM_API_KEY")

    # File upload settings
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB in bytes

    # LLM Settings
    LLM_MODEL: str
    LLM_TEMPERATURE: float
    LLM_MAX_TOKENS: int

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
