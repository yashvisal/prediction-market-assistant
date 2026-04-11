from app.config import Settings
from app.services.heuristics import heuristics_from_settings
from app.services.markets import _shortlist_market_seeds
from app.services.provider_types import MarketSeed, ProviderSelectionInputs


def _settings() -> Settings:
    return Settings(
        backend_cors_origins=("http://localhost:3000",),
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="service-role",
        supabase_publishable_key=None,
        supabase_db_url="postgresql://example",
        aws_region="us-east-1",
        aws_access_key_id="key",
        aws_secret_access_key="secret",
        s3_bucket="bucket",
        s3_prefix="dev/",
        dome_api_key="dome-key",
        dome_api_base_url="https://api.domeapi.io/v1",
        tracked_market_limit=12,
        historical_market_limit=6,
        sync_interval_seconds=300,
        history_window_days=30,
        event_threshold=0.05,
        event_cooldown_points=1,
        max_events_per_market=4,
        max_signals_per_event=12,
        persistence_enabled=True,
        validation_market_tickers=("PINNED-1",),
    )


def test_shortlist_market_seeds_keeps_validation_markets_and_best_candidates():
    heuristics = heuristics_from_settings(_settings())
    markets = [
        MarketSeed(
            pool="open",
            raw_market={"market_slug": "LOW-1"},
            raw_event=None,
            prefetch_inputs=ProviderSelectionInputs(0, 0, 0),
        ),
        MarketSeed(
            pool="open",
            raw_market={"market_slug": "PINNED-1"},
            raw_event=None,
            prefetch_inputs=ProviderSelectionInputs(0, 0, 0),
        ),
        MarketSeed(
            pool="open",
            raw_market={"market_slug": "HIGH-1"},
            raw_event=None,
            prefetch_inputs=ProviderSelectionInputs(2500, 900, 0, title_quality=0.8, event_volume=4000),
        ),
    ]

    shortlisted = _shortlist_market_seeds(markets, shortlist_limit=2, heuristics=heuristics)

    assert [market.raw_market["market_slug"] for market in shortlisted] == ["PINNED-1", "HIGH-1"]
