"""Configuração da aplicação via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Porta 5544 no host (o container Postgres publica em 5544; 5432/5433 estão
    # ocupadas por instalações locais de PostgreSQL). Override por .env.
    database_url: str = "postgresql+psycopg://cs2:cs2@localhost:5544/cs2_lab"
    redis_url: str = "redis://localhost:6379/0"
    api_title: str = "cs2-lab API"
    log_level: str = "INFO"


settings = Settings()
