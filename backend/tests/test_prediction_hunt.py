from app.services.prediction_hunt import (
    _to_candle,
    _to_event_summary,
    _to_market_summary,
    _to_matching_event,
    _to_orderbook_side,
)


def test_prediction_hunt_event_summary_parses_groups():
    event = _to_event_summary(
        {
            "id": 101,
            "event_name": "2028 Presidential Election Winner",
            "event_type": "election",
            "event_date": "2028-11-07",
            "status": "active",
            "groups": [
                {
                    "group_id": 55,
                    "title": "democratic nominee wins",
                    "platform_count": 3,
                    "platforms": ["polymarket", "kalshi", "predictit"],
                }
            ],
        }
    )

    assert event.id == 101
    assert event.eventName == "2028 Presidential Election Winner"
    assert event.groups[0].platformCount == 3
    assert event.groups[0].platforms == ["polymarket", "kalshi", "predictit"]


def test_prediction_hunt_market_history_and_matching_parsing():
    market = _to_market_summary(
        {
            "id": 44,
            "market_id": "poly-btc-100k",
            "platform": "polymarket",
            "title": "Will Bitcoin hit $100k this year?",
            "category": "economics",
            "status": "active",
            "expiration_date": "2026-12-31T23:59:59Z",
            "source_url": "https://example.com/market",
            "price": {
                "yes_bid": 0.47,
                "yes_ask": 0.49,
                "no_bid": 0.51,
                "no_ask": 0.53,
                "last_price": 0.48,
                "volume": 120340,
                "liquidity": 8200.5,
            },
        }
    )
    candle = _to_candle(
        {
            "timestamp": "2026-04-12T10:00:00Z",
            "open": 0.45,
            "high": 0.5,
            "low": 0.44,
            "close": 0.48,
            "yes_bid": 0.47,
            "yes_ask": 0.49,
            "mid": 0.48,
            "volume": 1800,
            "dollar_volume": 864.0,
        }
    )
    matching = _to_matching_event(
        {
            "title": "Will the Fed cut rates in September?",
            "event_type": "economics",
            "event_date": "2026-09-18",
            "confidence": "high",
            "groups": [
                {
                    "title": "fed cuts rates",
                    "markets": [
                        {"source": "polymarket", "source_url": "https://poly", "id": "poly-fed"},
                        {"source": "kalshi", "source_url": "https://kalshi", "id": "KXFEDCUT"},
                    ],
                }
            ],
        }
    )
    orderbook = _to_orderbook_side(
        {
            "bids": [{"price": 0.47, "size": 1000}, {"price": 0.46, "size": 600}],
            "asks": [{"price": 0.49, "size": 1200}],
        }
    )

    assert market.marketId == "poly-btc-100k"
    assert market.price.lastPrice == 0.48
    assert candle.close == 0.48
    assert candle.dollarVolume == 864.0
    assert matching.groups[0].markets[1].source == "kalshi"
    assert orderbook.bids[0].size == 1000
