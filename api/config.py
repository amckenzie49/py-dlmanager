from typing import Optional
from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration from environment variables"""

    shelve_db_path: str = "data/downloads"
    app_name: str = "py-dlmanager"
    app_version: str = "0.1.0"
    debug: bool = False
    torbox_api_key: SecretStr = SecretStr("")
    torbox_base_url: str = "https://api.torbox.app"
    webdav_url: Optional[str] = None
    webdav_username: Optional[str] = None
    webdav_password: Optional[SecretStr] = None
    webdav_remote_path: str = "/downloads"
    debrid_poll_interval_seconds: float = 10
    debrid_poll_timeout_seconds: float = 86400

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
