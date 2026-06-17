from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = Path(__file__).resolve().parents[3]
ENV_FILES = (BACKEND_DIR / '.env', PROJECT_DIR / '.env')


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILES, env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Simple Support API'
    api_prefix: str = '/api'

    secret_key: str = 'change-me-super-secret-key'
    algorithm: str = 'HS256'
    access_token_expire_minutes: int = 480

    database_url: str = 'sqlite:///./data/app.db'
    cors_origins: str = '*'

    smtp_enabled: bool = True
    smtp_host: str = ''
    smtp_port: int = 587
    smtp_username: str = ''
    smtp_password: str = ''
    smtp_from_email: str = ''
    smtp_from_name: str = 'Служба поддержки'
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    smtp_timeout_seconds: int = 10
    email_outbox_dir: str = './data/outbox'

    @property
    def cors_origins_list(self) -> List[str]:
        if self.cors_origins.strip() == '*':
            return ['*']
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
