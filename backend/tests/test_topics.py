from fastapi.testclient import TestClient

from app.main import app
from app.models.intelligence import Entity, EntityType, MovementDirection, Signal, SignalSourceType
from app.models.market import (
    MarketCategory,
    MarketDetail,
    MarketEvent,
    MarketStatus,
)
from app.models.topic import TopicDetail, TopicSummary
from app.services.topics import _build_topic_details, clear_topic_state_cache


def _market_detail(
    *,
    market_id: str,
    title: str,
    category: MarketCategory,
    current_probability: float,
    previous_close: float,
    last_event_at: str | None = None,
) -> MarketDetail:
    return MarketDetail(
        id=market_id,
        title=title,
        description=f"Context for {title}.",
        status=MarketStatus.OPEN,
        category=category,
        currentProbability=current_probability,
        previousClose=previous_close,
        volume=1000,
        liquidity=500,
        createdAt="2026-01-01T00:00:00Z",
        closesAt="2026-12-31T00:00:00Z",
        eventCount=1,
        lastEventAt=last_event_at,
    )


def _event(*, market_id: str, title: str, summary: str, movement: float, end_time: str):
    return {
        "id": f"{market_id}:{title}",
        "marketId": market_id,
        "title": title,
        "startTime": "2026-03-01T00:00:00Z",
        "endTime": end_time,
        "probabilityBefore": 0.4,
        "probabilityAfter": 0.4 + movement,
        "movementPercent": movement,
        "direction": MovementDirection.UP if movement >= 0 else MovementDirection.DOWN,
        "signals": [
            Signal(
                id=f"{market_id}:signal",
                title="Signal",
                source="Example",
                sourceType=SignalSourceType.NEWS,
                url="https://example.com",
                publishedAt=end_time,
                snippet=summary,
                relevanceScore=0.9,
                entities=[Entity(id="fed", name="Federal Reserve", type=EntityType.ORGANIZATION)],
            )
        ],
        "entities": [Entity(id="fed", name="Federal Reserve", type=EntityType.ORGANIZATION)],
        "relatedEvents": [],
        "summary": summary,
    }


def test_topic_service_groups_markets_into_seeded_topics(monkeypatch):
    clear_topic_state_cache()
    fed_market = _market_detail(
        market_id="fed-cut",
        title="Will the Fed cut rates this summer?",
        category=MarketCategory.FINANCE,
        current_probability=0.72,
        previous_close=0.61,
        last_event_at="2026-03-20T16:00:00Z",
    )
    ai_market = _market_detail(
        market_id="ai-bill",
        title="Will Congress pass a major AI safety bill?",
        category=MarketCategory.TECHNOLOGY,
        current_probability=0.34,
        previous_close=0.29,
        last_event_at="2026-03-07T20:00:00Z",
    )

    monkeypatch.setattr(
        "app.services.topics.list_market_activity",
        lambda status=None: [
            (
                fed_market,
                [
                    MarketEvent.model_validate(
                        _event(
                            market_id="fed-cut",
                            title="Fed repricing after CPI",
                            summary="Inflation data changed Fed expectations.",
                            movement=0.11,
                            end_time="2026-03-20T16:00:00Z",
                        )
                    )
                ],
            ),
            (
                ai_market,
                [
                    MarketEvent.model_validate(
                        _event(
                            market_id="ai-bill",
                            title="Senate AI hearing",
                            summary="Lawmakers debated frontier model regulation.",
                            movement=0.05,
                            end_time="2026-03-07T20:00:00Z",
                        )
                    )
                ],
            ),
        ],
    )

    topics = _build_topic_details()

    assert [topic.id for topic in topics] == ["fed-policy", "ai-regulation"]
    assert topics[0].marketCount == 1
    assert topics[0].updateCount == 1
    assert topics[0].strongestMovementPercent == 0.11
    assert topics[0].strongestMovementDirection == MovementDirection.UP
    assert topics[0].stateVersion


def test_topic_service_tracks_downward_strongest_movement(monkeypatch):
    clear_topic_state_cache()
    space_market = _market_detail(
        market_id="starship",
        title="Will Starship reach orbit this year?",
        category=MarketCategory.SCIENCE,
        current_probability=0.28,
        previous_close=0.41,
        last_event_at="2026-04-02T10:00:00Z",
    )

    monkeypatch.setattr(
        "app.services.topics.list_market_activity",
        lambda status=None: [
            (
                space_market,
                [
                    MarketEvent.model_validate(
                        _event(
                            market_id="starship",
                            title="Launch delay extends review",
                            summary="Regulatory delays pushed expectations lower.",
                            movement=-0.13,
                            end_time="2026-04-02T10:00:00Z",
                        )
                    )
                ],
            )
        ],
    )

    topics = _build_topic_details()

    assert topics[0].id == "spaceflight"
    assert topics[0].strongestMovementPercent == 0.13
    assert topics[0].strongestMovementDirection == MovementDirection.DOWN


def test_topics_route_returns_topic_summary_shape(monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.list_topics",
        lambda: [
            TopicSummary(
                id="fed-policy",
                title="Fed Policy Expectations",
                description="Tracks rate-cut repricing.",
                category=MarketCategory.FINANCE,
                query="fed policy expectations",
                stateVersion="abc123",
                marketCount=1,
                updateCount=1,
                signalCount=1,
                strongestMovementPercent=0.11,
                strongestMovementDirection=MovementDirection.UP,
                latestUpdateAt="2026-03-20T16:00:00Z",
            )
        ],
    )

    client = TestClient(app)
    response = client.get("/api/topics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"][0]["id"] == "fed-policy"
    assert payload["items"][0]["stateVersion"] == "abc123"
    assert payload["items"][0]["strongestMovementDirection"] == "up"


def test_topic_detail_route_returns_topic_detail_shape(monkeypatch):
    monkeypatch.setattr(
        "app.api.routes.get_topic_detail",
        lambda topic_id: TopicDetail(
            id=topic_id,
            title="Fed Policy Expectations",
            description="Tracks rate-cut repricing.",
            category=MarketCategory.FINANCE,
            query="fed policy expectations",
            stateVersion="abc123",
            marketCount=1,
            updateCount=1,
            signalCount=1,
            strongestMovementPercent=0.11,
            strongestMovementDirection=MovementDirection.UP,
            latestUpdateAt="2026-03-20T16:00:00Z",
            markets=[],
            updates=[],
        ),
    )

    client = TestClient(app)
    response = client.get("/api/topics/fed-policy")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "fed-policy"
    assert payload["category"] == "finance"
    assert payload["strongestMovementDirection"] == "up"


def test_topic_detail_route_returns_404_when_missing(monkeypatch):
    monkeypatch.setattr("app.api.routes.get_topic_detail", lambda topic_id: None)

    client = TestClient(app)
    response = client.get("/api/topics/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Topic not found."
