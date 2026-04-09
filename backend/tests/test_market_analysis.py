from app.config import Settings
from app.models.evaluation import MarketQualitySummary
from app.services.heuristics import HeuristicOverrides, apply_heuristic_overrides, heuristics_from_settings
from app.services.market_analysis import build_selection_debug


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
        validation_market_tickers=("FED-2026",),
    )


def test_apply_heuristic_overrides_is_request_scoped():
    base = heuristics_from_settings(_settings())
    overridden = apply_heuristic_overrides(
        base,
        HeuristicOverrides(event_threshold=0.12, routing_skip_below=0.05),
    )

    assert base.event_threshold == 0.05
    assert overridden.event_threshold == 0.12
    assert overridden.routing_skip_below == 0.05


def test_selection_debug_penalizes_zero_price_markets():
    heuristics = heuristics_from_settings(_settings())
    quality = MarketQualitySummary(
        pointCount=8,
        nonZeroPointRatio=0.8,
        probabilityVariance=0.01,
        probabilitySpread=0.22,
        recentMovement=0.09,
        hasRealHistory=True,
        usableDetectorInput=True,
    )
    zero_price_market = {
        "ticker": "ZERO-1",
        "volume_fp": "1000",
        "open_interest_fp": "600",
        "last_price_dollars": "0.0",
        "previous_price_dollars": "0.0",
        "yes_bid_dollars": "0.0",
        "yes_ask_dollars": "0.0",
    }
    active_market = {
        **zero_price_market,
        "ticker": "ACTIVE-1",
        "last_price_dollars": "0.42",
        "yes_bid_dollars": "0.41",
    }

    penalized = build_selection_debug(zero_price_market, quality, "open", heuristics)
    active = build_selection_debug(active_market, quality, "open", heuristics)

    assert "all_zero_price_fields" in penalized.penalties
    assert active.score > penalized.score
