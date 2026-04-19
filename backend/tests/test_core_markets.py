from fastapi.testclient import TestClient

from app.main import app
from app.models.market import (
    MarketCategory,
    MarketDetail,
    MarketEvent,
    MarketStatus,
    MovementDirection,
)
from app.models.prediction_hunt import PredictionHuntCandle, PredictionHuntMarketSummary, PredictionHuntPriceSnapshot
from app.services.markets import (
    _build_recent_move_event,
    _candle_probability,
    _current_probability,
    _map_prediction_hunt_market,
)


def _raw_market() -> PredictionHuntMarketSummary:
    return PredictionHuntMarketSummary(
        id=7,
        marketId="poly-fed-cut",
        platform="polymarket",
        title="Will the Fed cut rates by September?",
        category="politics",
        status="active",
        expirationDate="2026-09-18T00:00:00Z",
        sourceUrl="https://example.com/markets/poly-fed-cut",
        price=PredictionHuntPriceSnapshot(
            yesBid=0.56,
            yesAsk=0.58,
            noBid=0.42,
            noAsk=0.44,
            lastPrice=0.57,
            volume=10500,
            liquidity=2200.0,
        ),
    )


def _market_detail() -> MarketDetail:
    return _map_prediction_hunt_market(_raw_market())


def test_zero_probability_values_are_not_treated_as_missing():
    raw = PredictionHuntMarketSummary(
        id=1,
        marketId="zero-prob",
        platform="polymarket",
        title="Zero case",
        status="active",
        expirationDate="2026-09-18T00:00:00Z",
        price=PredictionHuntPriceSnapshot(
            lastPrice=0.0,
            yesBid=0.0,
            yesAsk=0.0,
            volume=0,
            liquidity=0.0,
        ),
    )
    assert _current_probability(raw) == 0.0
    assert _candle_probability(
        PredictionHuntCandle(timestamp="2026-01-01T00:00:00Z", close=0.0, mid=None)
    ) == 0.0


def test_prediction_hunt_market_maps_into_core_contract():
    market = _map_prediction_hunt_market(_raw_market())

    assert market.id == "poly-fed-cut"
    assert market.status == MarketStatus.OPEN
    assert market.category == MarketCategory.POLITICS
    assert market.currentProbability == 0.57
    assert market.previousClose == 0.57
    assert "Prediction Hunt market" in market.description


def test_recent_move_event_is_built_from_prediction_hunt_history():
    event = _build_recent_move_event(
        market=_market_detail(),
        platform="polymarket",
        candles=[
            PredictionHuntCandle(timestamp="2026-09-16T00:00:00Z", close=0.42),
            PredictionHuntCandle(timestamp="2026-09-16T01:00:00Z", close=0.58),
        ],
    )

    assert event is not None
    assert event.marketId == "poly-fed-cut"
    assert event.direction == MovementDirection.UP
    assert event.movementPercent == 0.16
    assert event.signals[0].source == "Prediction Hunt"


def test_core_markets_route_returns_market_summary_shape(monkeypatch):
    monkeypatch.setattr("app.api.routes.list_market_summaries", lambda status=None, category=None: [_market_detail()])

    client = TestClient(app)
    response = client.get("/api/markets")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["id"] == "poly-fed-cut"
    assert payload["items"][0]["status"] == "open"
    assert "description" not in payload["items"][0]


def test_core_market_events_route_returns_market_event_shape(monkeypatch):
    monkeypatch.setattr("app.api.routes.get_market_detail", lambda market_id: _market_detail())
    monkeypatch.setattr(
        "app.api.routes.list_market_events",
        lambda market_id: [
            MarketEvent(
                id="poly-fed-cut:recent-move",
                marketId="poly-fed-cut",
                title="Recent market movement",
                startTime="2026-09-16T00:00:00Z",
                endTime="2026-09-16T01:00:00Z",
                probabilityBefore=0.42,
                probabilityAfter=0.58,
                movementPercent=0.16,
                direction=MovementDirection.UP,
                signals=[],
                entities=[],
                relatedEvents=[],
                summary="Synthetic recent-move event",
            )
        ],
    )

    client = TestClient(app)
    response = client.get("/api/markets/poly-fed-cut/events")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["id"] == "poly-fed-cut:recent-move"
    assert payload["items"][0]["direction"] == "up"
