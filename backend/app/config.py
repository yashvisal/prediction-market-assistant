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
    topic_state_cache_ttl_seconds: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    cors = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000")
    raw_topic_cache_ttl = os.getenv("TOPIC_STATE_CACHE_TTL_SECONDS", "300")
    try:
        topic_cache_ttl = int(raw_topic_cache_ttl)
    except ValueError:
        topic_cache_ttl = 300
    return Settings(
        backend_cors_origins=tuple(origin.strip() for origin in cors.split(",") if origin.strip()),
        topic_state_cache_ttl_seconds=max(topic_cache_ttl, 0),
    )
