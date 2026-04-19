from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH, override=False)



@dataclass(frozen=True)
class Settings:
    backend_cors_origins: tuple[str, ...]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    cors = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000")
    return Settings(
        backend_cors_origins=tuple(origin.strip() for origin in cors.split(",") if origin.strip()),
    )
