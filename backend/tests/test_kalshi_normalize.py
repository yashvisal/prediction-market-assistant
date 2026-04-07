from app.models.market import MarketCategory, MarketStatus
from app.services.kalshi.normalize import normalize_candlesticks, normalize_market


def test_normalize_market_maps_contract_fields():
    raw_market = {
        "ticker": "FED-2026",
        "event_ticker": "FED",
        "title": "Will the Fed cut rates?",
        "yes_sub_title": "Fed cuts rates",
        "created_time": "2026-01-01T00:00:00Z",
        "updated_time": "2026-01-02T00:00:00Z",
        "close_time": "2026-06-01T00:00:00Z",
        "status": "active",
        "last_price_dollars": "0.6200",
        "previous_price_dollars": "0.5400",
        "volume_fp": "1200.00",
        "volume_24h_fp": "300.00",
        "open_interest_fp": "450.00",
        "result": "",
        "rules_primary": "Fed decision market.",
        "rules_secondary": "Secondary rule.",
    }

    normalized = normalize_market(raw_market, web_base_url="https://demo.kalshi.co")

    assert normalized.id == "FED-2026"
    assert normalized.status == MarketStatus.OPEN
    assert normalized.category == MarketCategory.FINANCE
    assert normalized.current_probability == 0.62
    assert normalized.previous_close == 0.54
    assert normalized.volume == 1200
    assert normalized.liquidity == 450


def test_normalize_candlesticks_prefers_trade_close_and_falls_back_to_quotes():
    points = normalize_candlesticks(
        "FED-2026",
        [
            {
                "end_period_ts": 1770000000,
                "price": {"close_dollars": "0.6200"},
                "yes_bid": {"close_dollars": "0.6100"},
                "yes_ask": {"close_dollars": "0.6300"},
                "volume_fp": "10.00",
                "open_interest_fp": "50.00",
            },
            {
                "end_period_ts": 1770003600,
                "price": {"close_dollars": None, "previous_dollars": None},
                "yes_bid": {"close_dollars": "0.6500"},
                "yes_ask": {"close_dollars": "0.6700"},
                "volume_fp": "12.00",
                "open_interest_fp": "55.00",
            },
        ],
        source="live",
    )

    assert [point.probability for point in points] == [0.62, 0.66]
    assert points[0].volume == 10
    assert points[1].open_interest == 55
