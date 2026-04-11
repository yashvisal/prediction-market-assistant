from app.config import Settings
from app.models.market import MarketCategory, MarketStatus, MovementDirection
from app.services.events.detector import detect_event_windows, evaluate_event_detection
from app.services.heuristics import heuristics_from_settings
from app.services.provider_types import NormalizedHistoryPoint, NormalizedMarket


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
        validation_market_tickers=(),
    )


def test_detect_event_windows_emits_explainable_move():
    market = NormalizedMarket(
        id="MARKET-1",
        provider="dome",
        provider_market_ticker="MARKET-1",
        provider_event_ticker="EVENT-1",
        title="Will rates be cut?",
        description="Fed probability market",
        status=MarketStatus.OPEN,
        category=MarketCategory.FINANCE,
        current_probability=0.62,
        previous_close=0.48,
        volume=1000,
        liquidity=200,
        created_at="2026-04-01T00:00:00Z",
        closes_at="2026-04-10T00:00:00Z",
        resolved_at=None,
        resolution=None,
        detail_url="https://polymarket.com/event/sample-event",
        rules_primary="Rules",
        rules_secondary="Secondary",
        metadata={},
    )
    history = [
        NormalizedHistoryPoint("MARKET-1", "2026-04-01T00:00:00Z", 0.48, None, None, 10, 100, "live", {}),
        NormalizedHistoryPoint("MARKET-1", "2026-04-01T01:00:00Z", 0.51, None, None, 12, 110, "live", {}),
        NormalizedHistoryPoint("MARKET-1", "2026-04-01T02:00:00Z", 0.62, None, None, 18, 120, "live", {}),
        NormalizedHistoryPoint("MARKET-1", "2026-04-01T03:00:00Z", 0.61, None, None, 19, 130, "live", {}),
    ]

    events = detect_event_windows(market, history, heuristics_from_settings(_settings()))

    assert len(events) == 1
    event = events[0]
    assert event.direction == MovementDirection.UP
    assert event.probability_before == 0.48
    assert event.probability_after == 0.62
    assert event.movement_percent == 0.14
    assert "moved up" in event.summary


def test_evaluate_event_detection_exposes_threshold_drop_reason():
    market = NormalizedMarket(
        id="MARKET-2",
        provider="dome",
        provider_market_ticker="MARKET-2",
        provider_event_ticker="EVENT-2",
        title="Will inflation cool?",
        description="Inflation market",
        status=MarketStatus.OPEN,
        category=MarketCategory.FINANCE,
        current_probability=0.52,
        previous_close=0.5,
        volume=1000,
        liquidity=200,
        created_at="2026-04-01T00:00:00Z",
        closes_at="2026-04-10T00:00:00Z",
        resolved_at=None,
        resolution=None,
        detail_url="https://polymarket.com/event/sample-event",
        rules_primary="Rules",
        rules_secondary="Secondary",
        metadata={},
    )
    history = [
        NormalizedHistoryPoint("MARKET-2", "2026-04-01T00:00:00Z", 0.50, None, None, 10, 100, "live", {}),
        NormalizedHistoryPoint("MARKET-2", "2026-04-01T01:00:00Z", 0.52, None, None, 12, 110, "live", {}),
        NormalizedHistoryPoint("MARKET-2", "2026-04-01T02:00:00Z", 0.51, None, None, 18, 120, "live", {}),
    ]

    evaluation = evaluate_event_detection(market, history, heuristics_from_settings(_settings()))

    assert len(evaluation.raw_candidates) == 2
    assert any(candidate.drop_reason == "threshold" for candidate in evaluation.filtered_candidates)
