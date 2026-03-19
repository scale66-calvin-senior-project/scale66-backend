import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    output_dir: str = "./output"
    save_local_output: bool = True
    
    supabase_url: Optional[str] = None
    supabase_service_key: Optional[str] = None
    supabase_jwt_secret: Optional[str] = None
    
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-5"
    gemini_image_model: str = "gemini-3-pro-image-preview"
    gemini_text_model: str = "gemini-3-pro-preview"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
os.makedirs(settings.output_dir, exist_ok=True)
