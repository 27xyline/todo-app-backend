from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    sql_echo: bool = False

    cors_origins: list[str]


@lru_cache
def get_settings() -> Settings:
    # Значения обязательных полей загружаются BaseSettings из .env во время запуска.
    return Settings()  # type: ignore[call-arg]
