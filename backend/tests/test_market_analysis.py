from app.config import Settings
from app.models.evaluation import MarketQualitySummary
from app.services.heuristics import HeuristicOverrides, apply_heuristic_overrides, heuristics_from_settings
from app.services.market_analysis import build_selection_debug
from app.services.provider_types import ProviderSelectionInputs


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
    zero_price_market = ProviderSelectionInputs(
        volume=1000,
        liquidity=600,
        non_zero_price_fields=0,
        recent_trade_count=0,
        has_orderbook=False,
        spread=None,
        title_quality=0.2,
        event_volume=2000,
        event_market_count=2,
        history_coverage_ratio=0.05,
    )
    active_market = ProviderSelectionInputs(
        volume=2500,
        liquidity=900,
        non_zero_price_fields=3,
        recent_trade_count=5,
        has_orderbook=True,
        spread=0.02,
        title_quality=0.7,
        event_volume=4000,
        event_market_count=2,
        history_coverage_ratio=0.4,
    )

    penalized = build_selection_debug(zero_price_market, quality, "open", heuristics)
    active = build_selection_debug(active_market, quality, "open", heuristics)

    assert "all_zero_price_fields" in penalized.penalties
    assert active.score > penalized.score
