from functools import lru_cache
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str | None = None
    openai_admin_key: str | None = None
    e2b_api_key: str | None = None
    database_url: str | None = None
    supabase_url: str | None = None
    supabase_key: str | None = None
    csv_bucket_name: str = "data_csv"
    image_bucket_name: str = "data_image"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def apply_to_environment(self) -> None:
        env_values = {
            "OPENAI_API_KEY": self.openai_api_key,
            "OPENAI_ADMIN_KEY": self.openai_admin_key,
            "E2B_API_KEY": self.e2b_api_key,
            "DATABASE_URL": self.database_url,
            "SUPABASE_URL": self.supabase_url,
            "SUPABASE_KEY": self.supabase_key,
        }
        for key, value in env_values.items():
            if value:
                os.environ.setdefault(key, value)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.apply_to_environment()
    return settings
