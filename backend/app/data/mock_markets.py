from app.models.intelligence import (
    Entity,
    EntityType,
    MovementDirection,
    RelatedEvent,
    RelationshipType,
    Signal,
    SignalSourceType,
)
from app.models.market import (
    MarketCategory,
    MarketDetail,
    MarketEvent,
    MarketStatus,
)


MARKETS: list[MarketDetail] = [
    MarketDetail(
        id="fed-rate-cut-jul-2026",
        title="Will the Federal Reserve cut interest rates before July 2026?",
        description=(
            "Resolves YES if the Federal Open Market Committee announces a "
            "reduction in the federal funds target rate at any scheduled or "
            "emergency meeting before July 1, 2026."
        ),
        status=MarketStatus.OPEN,
        category=MarketCategory.FINANCE,
        currentProbability=0.72,
        previousClose=0.64,
        volume=2_340_000,
        liquidity=485_000,
        createdAt="2025-11-01T00:00:00Z",
        closesAt="2026-07-01T00:00:00Z",
        eventCount=2,
        lastEventAt="2026-03-20T16:00:00Z",
    ),
    MarketDetail(
        id="ai-safety-bill-2026",
        title="Will Congress pass a major AI safety bill by end of 2026?",
        description=(
            "Resolves YES if a bill primarily focused on AI safety, risk "
            "assessment, or frontier model regulation is signed into law by "
            "December 31, 2026."
        ),
        status=MarketStatus.OPEN,
        category=MarketCategory.TECHNOLOGY,
        currentProbability=0.34,
        previousClose=0.31,
        volume=1_120_000,
        liquidity=210_000,
        createdAt="2025-12-15T00:00:00Z",
        closesAt="2026-12-31T00:00:00Z",
        eventCount=2,
        lastEventAt="2026-03-25T20:00:00Z",
    ),
    MarketDetail(
        id="who-pandemic-declaration",
        title="Will the WHO declare a new Public Health Emergency of International Concern in Q1 2026?",
        description=(
            "Resolved NO. The WHO did not declare a new PHEIC during Q1 2026. "
            "The H5N1 monitoring situation was elevated but did not meet PHEIC criteria."
        ),
        status=MarketStatus.RESOLVED,
        category=MarketCategory.SCIENCE,
        currentProbability=0.0,
        previousClose=0.08,
        volume=340_000,
        liquidity=0,
        createdAt="2025-12-01T00:00:00Z",
        closesAt="2026-03-31T23:59:00Z",
        resolvedAt="2026-03-31T23:59:00Z",
        resolution="no",
        eventCount=2,
        lastEventAt="2026-02-07T00:00:00Z",
    ),
]


MARKET_EVENTS: dict[str, list[MarketEvent]] = {
    "fed-rate-cut-jul-2026": [
        MarketEvent(
            id="fed-cpi-feb-2026",
            marketId="fed-rate-cut-jul-2026",
            title="February CPI report shows continued disinflation",
            startTime="2026-02-28T09:00:00Z",
            endTime="2026-03-02T20:00:00Z",
            probabilityBefore=0.52,
            probabilityAfter=0.64,
            movementPercent=0.12,
            direction=MovementDirection.UP,
            summary=(
                "The Bureau of Labor Statistics released February CPI data "
                "showing year-over-year inflation fell to 2.4%, the lowest "
                "reading since early 2021. Markets rapidly repriced rate cut expectations."
            ),
            signals=[
                Signal(
                    id="sig-reuters-cpi",
                    title="U.S. inflation cools to 2.4% in February, bolstering rate cut hopes",
                    source="Reuters",
                    sourceType=SignalSourceType.NEWS,
                    url="https://reuters.com/markets/us-cpi-february-2026",
                    publishedAt="2026-02-28T13:35:00Z",
                    snippet=(
                        "Consumer prices rose just 0.1% month-over-month, with core "
                        "CPI also undershooting expectations at 2.8% year-over-year."
                    ),
                    relevanceScore=0.95,
                    entities=[
                        Entity(
                            id="ent-bls",
                            name="Bureau of Labor Statistics",
                            type=EntityType.ORGANIZATION,
                        ),
                        Entity(
                            id="ent-cpi",
                            name="Consumer Price Index",
                            type=EntityType.TOPIC,
                        ),
                    ],
                ),
                Signal(
                    id="sig-fedwatcher-tweet",
                    title="Thread: CPI breakdown and implications for June FOMC",
                    source="@FedWatcher",
                    sourceType=SignalSourceType.TWEET,
                    url="https://x.com/FedWatcher/status/1234567890",
                    publishedAt="2026-02-28T14:20:00Z",
                    snippet=(
                        "Shelter inflation finally cracking. This is the component "
                        "the Fed has been waiting on. June cut now firmly on the table."
                    ),
                    relevanceScore=0.82,
                    entities=[
                        Entity(
                            id="ent-fed",
                            name="Federal Reserve",
                            type=EntityType.ORGANIZATION,
                        ),
                        Entity(
                            id="ent-fomc",
                            name="FOMC",
                            type=EntityType.ORGANIZATION,
                        ),
                    ],
                ),
            ],
            entities=[
                Entity(id="ent-fed", name="Federal Reserve", type=EntityType.ORGANIZATION),
                Entity(
                    id="ent-bls",
                    name="Bureau of Labor Statistics",
                    type=EntityType.ORGANIZATION,
                ),
                Entity(id="ent-cpi", name="Consumer Price Index", type=EntityType.TOPIC),
                Entity(id="ent-fomc", name="FOMC", type=EntityType.ORGANIZATION),
            ],
            relatedEvents=[
                RelatedEvent(
                    id="rel-inflation-target",
                    marketId="inflation-below-3-2026",
                    marketTitle="Will U.S. inflation fall below 3% year-over-year in 2026?",
                    eventTitle="February CPI release",
                    relationship=RelationshipType.SHARED_ENTITY,
                    sharedEntities=["Bureau of Labor Statistics", "Consumer Price Index"],
                )
            ],
        ),
        MarketEvent(
            id="fed-powell-march-2026",
            marketId="fed-rate-cut-jul-2026",
            title="Powell signals patience at March press conference",
            startTime="2026-03-19T18:00:00Z",
            endTime="2026-03-20T16:00:00Z",
            probabilityBefore=0.64,
            probabilityAfter=0.72,
            movementPercent=0.08,
            direction=MovementDirection.UP,
            summary=(
                "Chair Powell acknowledged progress on inflation but emphasized "
                "the committee wants to see a few more months of data before acting."
            ),
            signals=[
                Signal(
                    id="sig-fed-presser",
                    title="FOMC holds rates steady, Powell hints at possible June action",
                    source="Federal Reserve",
                    sourceType=SignalSourceType.OFFICIAL,
                    url="https://federalreserve.gov/newsevents/pressreleases/monetary20260319a.htm",
                    publishedAt="2026-03-19T18:30:00Z",
                    snippet=(
                        "The Committee decided to maintain the target range for the "
                        "federal funds rate."
                    ),
                    relevanceScore=0.97,
                    entities=[
                        Entity(
                            id="ent-fed",
                            name="Federal Reserve",
                            type=EntityType.ORGANIZATION,
                        ),
                        Entity(
                            id="ent-powell",
                            name="Jerome Powell",
                            type=EntityType.PERSON,
                        ),
                    ],
                )
            ],
            entities=[
                Entity(id="ent-powell", name="Jerome Powell", type=EntityType.PERSON),
                Entity(id="ent-fed", name="Federal Reserve", type=EntityType.ORGANIZATION),
                Entity(id="ent-fomc", name="FOMC", type=EntityType.ORGANIZATION),
            ],
            relatedEvents=[],
        ),
    ],
    "ai-safety-bill-2026": [
        MarketEvent(
            id="ai-senate-hearing",
            marketId="ai-safety-bill-2026",
            title="Senate Commerce Committee holds high-profile AI hearing",
            startTime="2026-03-05T14:00:00Z",
            endTime="2026-03-07T20:00:00Z",
            probabilityBefore=0.28,
            probabilityAfter=0.34,
            movementPercent=0.06,
            direction=MovementDirection.UP,
            summary=(
                "Bipartisan interest in a reporting-focused bill emerged, though "
                "major disagreements remain on enforcement."
            ),
            signals=[
                Signal(
                    id="sig-politico-hearing",
                    title="Senators signal bipartisan appetite for AI guardrails",
                    source="Politico",
                    sourceType=SignalSourceType.NEWS,
                    url="https://politico.com/news/2026/03/senate-ai-hearing",
                    publishedAt="2026-03-05T19:00:00Z",
                    snippet=(
                        "Senators from both parties expressed support for mandatory "
                        "incident reporting for frontier AI systems."
                    ),
                    relevanceScore=0.91,
                    entities=[
                        Entity(
                            id="ent-senate-commerce",
                            name="Senate Commerce Committee",
                            type=EntityType.ORGANIZATION,
                        ),
                        Entity(
                            id="ent-ai-safety",
                            name="AI Safety Regulation",
                            type=EntityType.TOPIC,
                        ),
                    ],
                )
            ],
            entities=[
                Entity(
                    id="ent-senate-commerce",
                    name="Senate Commerce Committee",
                    type=EntityType.ORGANIZATION,
                ),
                Entity(id="ent-openai", name="OpenAI", type=EntityType.ORGANIZATION),
                Entity(
                    id="ent-ai-safety",
                    name="AI Safety Regulation",
                    type=EntityType.TOPIC,
                ),
            ],
            relatedEvents=[
                RelatedEvent(
                    id="rel-eu-ai-act",
                    marketId="eu-ai-act-enforcement",
                    marketTitle="Will the EU AI Act enforcement begin on schedule?",
                    eventTitle="EU Commission releases implementation guidelines",
                    relationship=RelationshipType.SHARED_ENTITY,
                    sharedEntities=["AI Safety Regulation"],
                )
            ],
        ),
        MarketEvent(
            id="ai-bill-draft-leak",
            marketId="ai-safety-bill-2026",
            title="Draft bipartisan bill text leaks, faces immediate industry pushback",
            startTime="2026-03-22T10:00:00Z",
            endTime="2026-03-25T20:00:00Z",
            probabilityBefore=0.34,
            probabilityAfter=0.31,
            movementPercent=0.03,
            direction=MovementDirection.DOWN,
            summary=(
                "A leaked draft included mandatory red-teaming and model "
                "registration, prompting immediate industry opposition."
            ),
            signals=[
                Signal(
                    id="sig-axios-leak",
                    title="Leaked AI bill draft includes model registration requirement",
                    source="Axios",
                    sourceType=SignalSourceType.NEWS,
                    url="https://axios.com/2026/03/22/ai-bill-draft-leaked",
                    publishedAt="2026-03-22T11:00:00Z",
                    snippet=(
                        "The draft would require companies developing frontier AI "
                        "models to register with a new federal office."
                    ),
                    relevanceScore=0.93,
                    entities=[
                        Entity(
                            id="ent-ai-accountability-act",
                            name="AI Accountability Act",
                            type=EntityType.LEGISLATION,
                        ),
                        Entity(
                            id="ent-ai-safety",
                            name="AI Safety Regulation",
                            type=EntityType.TOPIC,
                        ),
                    ],
                )
            ],
            entities=[
                Entity(
                    id="ent-ai-accountability-act",
                    name="AI Accountability Act",
                    type=EntityType.LEGISLATION,
                ),
                Entity(
                    id="ent-ai-safety",
                    name="AI Safety Regulation",
                    type=EntityType.TOPIC,
                ),
                Entity(
                    id="ent-senate-commerce",
                    name="Senate Commerce Committee",
                    type=EntityType.ORGANIZATION,
                ),
            ],
            relatedEvents=[],
        ),
    ],
    "who-pandemic-declaration": [
        MarketEvent(
            id="who-h5n1-surge",
            marketId="who-pandemic-declaration",
            title="H5N1 human cases spike in Southeast Asia",
            startTime="2026-01-20T00:00:00Z",
            endTime="2026-01-24T00:00:00Z",
            probabilityBefore=0.05,
            probabilityAfter=0.15,
            movementPercent=0.10,
            direction=MovementDirection.UP,
            summary=(
                "A cluster of confirmed H5N1 human cases raised alarm and briefly "
                "tripled the market probability."
            ),
            signals=[
                Signal(
                    id="sig-who-h5n1",
                    title="WHO convenes emergency committee on H5N1 cluster",
                    source="World Health Organization",
                    sourceType=SignalSourceType.OFFICIAL,
                    url="https://who.int/news/h5n1-emergency-committee-jan-2026",
                    publishedAt="2026-01-22T12:00:00Z",
                    snippet=(
                        "The Director-General convened the Emergency Committee to "
                        "assess the recent cluster of human H5N1 infections."
                    ),
                    relevanceScore=0.97,
                    entities=[
                        Entity(
                            id="ent-who",
                            name="World Health Organization",
                            type=EntityType.ORGANIZATION,
                        ),
                        Entity(
                            id="ent-h5n1",
                            name="H5N1 Avian Influenza",
                            type=EntityType.TOPIC,
                        ),
                    ],
                )
            ],
            entities=[
                Entity(
                    id="ent-who",
                    name="World Health Organization",
                    type=EntityType.ORGANIZATION,
                ),
                Entity(id="ent-h5n1", name="H5N1 Avian Influenza", type=EntityType.TOPIC),
            ],
            relatedEvents=[],
        ),
        MarketEvent(
            id="who-h5n1-contained",
            marketId="who-pandemic-declaration",
            title="WHO determines H5N1 cluster contained, no PHEIC",
            startTime="2026-02-05T00:00:00Z",
            endTime="2026-02-07T00:00:00Z",
            probabilityBefore=0.15,
            probabilityAfter=0.08,
            movementPercent=0.07,
            direction=MovementDirection.DOWN,
            signals=[
                Signal(
                    id="sig-who-no-pheic",
                    title="Emergency Committee advises against PHEIC declaration",
                    source="World Health Organization",
                    sourceType=SignalSourceType.OFFICIAL,
                    url="https://who.int/news/h5n1-no-pheic-feb-2026",
                    publishedAt="2026-02-05T16:00:00Z",
                    snippet=(
                        "Current evidence does not indicate sustained human-to-human "
                        "transmission and does not constitute a PHEIC."
                    ),
                    relevanceScore=0.95,
                    entities=[
                        Entity(
                            id="ent-who",
                            name="World Health Organization",
                            type=EntityType.ORGANIZATION,
                        ),
                        Entity(
                            id="ent-h5n1",
                            name="H5N1 Avian Influenza",
                            type=EntityType.TOPIC,
                        ),
                    ],
                )
            ],
            entities=[
                Entity(
                    id="ent-who",
                    name="World Health Organization",
                    type=EntityType.ORGANIZATION,
                ),
                Entity(id="ent-h5n1", name="H5N1 Avian Influenza", type=EntityType.TOPIC),
            ],
            relatedEvents=[],
        ),
    ],
}


def list_markets(*, status: str | None = None, category: str | None = None) -> list[MarketDetail]:
    items = MARKETS

    if status:
        items = [market for market in items if market.status == status]

    if category:
        items = [market for market in items if market.category == category]

    return items


def get_market(market_id: str) -> MarketDetail | None:
    return next((market for market in MARKETS if market.id == market_id), None)


def get_market_events(market_id: str) -> list[MarketEvent]:
    return MARKET_EVENTS.get(market_id, [])
