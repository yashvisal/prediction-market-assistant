from app.config import Settings
from app.services.heuristics import heuristics_from_settings
from app.services.markets import _shortlist_raw_markets


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
        kalshi_api_key="kalshi-key",
        kalshi_api_base_url="https://demo-api.kalshi.co/trade-api/v2",
        kalshi_private_key_path=__import__("pathlib").Path("dummy.key"),
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


def test_shortlist_raw_markets_keeps_validation_tickers_and_best_candidates():
    heuristics = heuristics_from_settings(_settings())
    markets = [
        {
            "ticker": "LOW-1",
            "volume_fp": "0",
            "open_interest_fp": "0",
            "last_price_dollars": "0.0",
            "previous_price_dollars": "0.0",
            "yes_bid_dollars": "0.0",
            "yes_ask_dollars": "0.0",
        },
        {
            "ticker": "PINNED-1",
            "volume_fp": "0",
            "open_interest_fp": "0",
            "last_price_dollars": "0.0",
            "previous_price_dollars": "0.0",
            "yes_bid_dollars": "0.0",
            "yes_ask_dollars": "0.0",
        },
        {
            "ticker": "HIGH-1",
            "volume_fp": "2500",
            "open_interest_fp": "900",
            "last_price_dollars": "0.62",
            "previous_price_dollars": "0.58",
            "yes_bid_dollars": "0.61",
            "yes_ask_dollars": "0.63",
        },
    ]

    shortlisted = _shortlist_raw_markets(markets, shortlist_limit=2, heuristics=heuristics)

    assert [market["ticker"] for market in shortlisted] == ["PINNED-1", "HIGH-1"]
