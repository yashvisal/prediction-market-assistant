from app.services.dome_markets import (
    _build_quality_summary,
    _sample_price_history,
    _to_market_summary,
    _to_orderbook_summary,
    _to_trade_record,
)


def test_dome_market_parsing_and_quality_summary():
    market = _to_market_summary(
        {
            "market_slug": "sample-market",
            "event_slug": "sample-event",
            "title": "Will sample market resolve yes?",
            "status": "open",
            "start_time": 1775745835,
            "end_time": 1775750400,
            "volume_1_week": 4260.5,
            "volume_total": 12000.1,
            "tags": ["politics", "elections"],
            "description": "Sample description",
            "image": "https://example.com/market.png",
            "side_a": {"id": "yes-token", "label": "Yes"},
            "side_b": {"id": "no-token", "label": "No"},
        },
        side_a_price=0.164,
        side_b_price=0.836,
    )
    trade = _to_trade_record(
        {
            "token_id": "yes-token",
            "token_label": "Yes",
            "side": "BUY",
            "price": 0.164,
            "shares_normalized": 48,
            "timestamp": 1775748027,
            "tx_hash": "0xabc",
            "user": "0xuser",
            "taker": "0xtaker",
        }
    )
    orderbook = _to_orderbook_summary(
        {
            "snapshots": [
                {
                    "timestamp": 1775748030631,
                    "indexedAt": 1775748030763,
                    "bids": [{"price": "0.163", "size": "567.79"}],
                    "asks": [{"price": "0.165", "size": "2103.98"}],
                }
            ]
        }
    )

    assert market.sideA.price == 0.164
    assert market.sideB.price == 0.836
    assert trade.sharesNormalized == 48
    assert orderbook is not None
    assert orderbook.bestBid == 0.163
    assert orderbook.bestAsk == 0.165
    assert orderbook.spread == 0.002

    quality = _build_quality_summary(market=market, recent_trades=[trade], orderbook=orderbook)

    assert quality.hasPrices is True
    assert quality.hasRecentTrades is True
    assert quality.hasOrderbook is True
    assert quality.recentTradeCount == 1
    assert quality.totalRecentShares == 48


class _FakePriceClient:
    def get_market_price(self, token_id: str):
        return {"price": 0.61 if token_id == "yes-token" else 0.39, "at_time": 1775749000}

    def get_historical_market_price(self, token_id: str, at_time: int):
        base = 0.55 if token_id == "yes-token" else 0.45
        return {"price": base, "at_time": at_time}


def test_sample_price_history_includes_recent_checkpoints():
    history = _sample_price_history(
        client=_FakePriceClient(),
        raw_market={
            "start_time": 1775740000,
            "side_a": {"id": "yes-token"},
            "side_b": {"id": "no-token"},
        },
    )

    assert [point.label for point in history] == ["now", "1h", "6h", "24h"]
    assert history[0].sideAPrice == 0.61
    assert history[1].sideAPrice == 0.55
