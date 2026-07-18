from pathlib import Path
from typing import ClassVar, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FILE_BAZAAR_")

    working_dir: Path = "."
    default_locale: str = "en"

    _instance: ClassVar[Optional["Settings"]] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, *args, **kwargs):
        if getattr(self, "_initialized", False):
            return

        super().__init__(*args, **kwargs)
        self._initialized = True


settings = Settings()
