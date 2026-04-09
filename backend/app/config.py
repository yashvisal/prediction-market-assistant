from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH, override=False)


def _get_required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _get_optional(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    return int(value)


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if not value:
        return default
    return float(value)


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _get_csv(name: str) -> tuple[str, ...]:
    value = os.getenv(name, "")
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    backend_cors_origins: tuple[str, ...]
    supabase_url: str
    supabase_service_role_key: str
    supabase_publishable_key: str | None
    supabase_db_url: str
    aws_region: str
    aws_access_key_id: str
    aws_secret_access_key: str
    s3_bucket: str
    s3_prefix: str
    kalshi_api_key: str
    kalshi_api_base_url: str
    kalshi_private_key_path: Path
    tracked_market_limit: int
    historical_market_limit: int
    sync_interval_seconds: int
    history_window_days: int
    event_threshold: float
    event_cooldown_points: int
    max_events_per_market: int
    max_signals_per_event: int
    persistence_enabled: bool
    validation_market_tickers: tuple[str, ...]

    @property
    def kalshi_web_base_url(self) -> str:
        return "https://demo.kalshi.co" if "demo-api" in self.kalshi_api_base_url else "https://kalshi.com"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    cors = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000")
    publishable = _get_optional("SUPABASE_PUBLISHABLE_KEY") or _get_optional("SUPABASE_ANON_KEY")
    kalshi_api_key = _get_optional("KALSHI_API_KEY") or _get_optional("KALSHI_API_KEY_ID")
    if not kalshi_api_key:
        raise RuntimeError("Missing required environment variable: KALSHI_API_KEY or KALSHI_API_KEY_ID")

    return Settings(
        backend_cors_origins=tuple(origin.strip() for origin in cors.split(",") if origin.strip()),
        supabase_url=_get_required("SUPABASE_URL"),
        supabase_service_role_key=_get_required("SUPABASE_SERVICE_ROLE_KEY"),
        supabase_publishable_key=publishable,
        supabase_db_url=_get_required("SUPABASE_DB_URL"),
        aws_region=_get_required("AWS_REGION"),
        aws_access_key_id=_get_required("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=_get_required("AWS_SECRET_ACCESS_KEY"),
        s3_bucket=_get_required("S3_BUCKET"),
        s3_prefix=_get_optional("S3_PREFIX", "dev/") or "dev/",
        kalshi_api_key=kalshi_api_key,
        kalshi_api_base_url=_get_required("KALSHI_API_BASE_URL").rstrip("/"),
        kalshi_private_key_path=Path(_get_required("KALSHI_PRIVATE_KEY_PATH")),
        tracked_market_limit=_get_int("TRACKED_MARKET_LIMIT", 12),
        historical_market_limit=_get_int("HISTORICAL_MARKET_LIMIT", 6),
        sync_interval_seconds=_get_int("SYNC_INTERVAL_SECONDS", 300),
        history_window_days=_get_int("HISTORY_WINDOW_DAYS", 30),
        event_threshold=_get_float("EVENT_THRESHOLD", 0.05),
        event_cooldown_points=_get_int("EVENT_COOLDOWN_POINTS", 2),
        max_events_per_market=_get_int("MAX_EVENTS_PER_MARKET", 4),
        max_signals_per_event=_get_int("MAX_SIGNALS_PER_EVENT", 12),
        persistence_enabled=_get_bool("PERSISTENCE_ENABLED", True),
        validation_market_tickers=_get_csv("VALIDATION_MARKET_TICKERS"),
    )
