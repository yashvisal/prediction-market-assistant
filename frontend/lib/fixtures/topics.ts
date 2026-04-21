import { getMarketById, getMarketEvents, getMarkets } from "@/lib/mock-data"
import type {
  MarketCategory,
  MarketDetail,
  MarketEvent,
  MarketStatus,
} from "@/lib/market-types"
import type { MovementDirection } from "@/lib/intelligence-types"
import type { TopicDetail, TopicMarket, TopicState, TopicSummary, TopicUpdate } from "@/lib/topic-types"

interface TopicSeed {
  id: string
  title: string
  description: string
  query: string
  category: MarketCategory
  tokens: string[]
  entityNames: string[]
}

const topicSeeds: TopicSeed[] = [
  {
    id: "fed-policy",
    title: "Fed Policy Expectations",
    description:
      "Tracks how markets are repricing the path of Federal Reserve policy and inflation-sensitive policy expectations.",
    query: "fed policy expectations",
    category: "finance",
    tokens: ["fed", "fomc", "rate cut", "interest rates", "inflation", "cpi"],
    entityNames: ["Federal Reserve", "FOMC", "Consumer Price Index"],
  },
  {
    id: "ai-regulation",
    title: "AI Regulation",
    description:
      "Tracks whether major regulatory or legislative developments are shifting expectations around AI governance.",
    query: "ai regulation",
    category: "technology",
    tokens: ["ai", "artificial intelligence", "frontier model", "safety bill", "regulation"],
    entityNames: ["AI Safety Regulation", "AI Accountability Act", "OpenAI"],
  },
  {
    id: "bitcoin-market",
    title: "Bitcoin Market Structure",
    description:
      "Tracks macro and institutional developments that are moving bitcoin-related markets.",
    query: "bitcoin market structure",
    category: "crypto",
    tokens: ["bitcoin", "btc", "etf", "crypto"],
    entityNames: ["Bitcoin", "Bitcoin ETFs", "BlackRock"],
  },
  {
    id: "spaceflight",
    title: "Spaceflight Milestones",
    description:
      "Tracks whether major aerospace milestones are shifting confidence in key space programs.",
    query: "spaceflight milestones",
    category: "science",
    tokens: ["spacex", "starship", "orbital flight", "launch license"],
    entityNames: ["Starship", "SpaceX", "FAA"],
  },
  {
    id: "transatlantic-trade",
    title: "US-EU Trade Tensions",
    description:
      "Tracks whether trade friction or negotiation progress is changing expectations around transatlantic economic relations.",
    query: "us eu trade tensions",
    category: "geopolitics",
    tokens: ["trade agreement", "tariff", "eu", "european union", "auto imports"],
    entityNames: ["US-EU Trade Relations", "European Commission", "U.S. Trade Representative"],
  },
  {
    id: "global-health",
    title: "Global Health Risk",
    description:
      "Tracks outbreak, pandemic, and emergency-response developments that are materially shifting global health expectations.",
    query: "global health risk",
    category: "science",
    tokens: ["who", "h5n1", "pheic", "public health emergency", "avian influenza"],
    entityNames: ["World Health Organization", "H5N1 Avian Influenza"],
  },
]

function searchableText(market: MarketDetail, events: MarketEvent[]): string {
  const bits = [market.title, market.description, market.category]
  for (const event of events) {
    bits.push(
      event.title,
      event.summary ?? "",
      event.entities.map((entity) => entity.name).join(" "),
      event.signals.map((signal) => signal.title).join(" "),
      event.signals.map((signal) => signal.source).join(" ")
    )
  }
  return bits.join(" ").toLowerCase()
}

function matchSeed(market: MarketDetail, events: MarketEvent[]): TopicSeed | null {
  const text = searchableText(market, events)
  let bestSeed: TopicSeed | null = null
  let bestScore = 0

  for (const seed of topicSeeds) {
    let score = market.category === seed.category ? 1 : 0
    for (const token of seed.tokens) {
      if (text.includes(token)) {
        score += 2
      }
    }
    for (const entityName of seed.entityNames) {
      if (text.includes(entityName.toLowerCase())) {
        score += 3
      }
    }
    if (score > bestScore) {
      bestScore = score
      bestSeed = seed
    }
  }

  return bestScore >= 3 ? bestSeed : null
}

function toDirection(amount: number): MovementDirection {
  return amount >= 0 ? "up" : "down"
}

function latestEventAt(events: MarketEvent[]): string | undefined {
  return events.reduce<string | undefined>((latest, event) => {
    if (!latest || new Date(event.endTime).getTime() > new Date(latest).getTime()) {
      return event.endTime
    }
    return latest
  }, undefined)
}

function toTopicMarket(market: MarketDetail, events: MarketEvent[]): TopicMarket {
  const movement = Number((market.currentProbability - market.previousClose).toFixed(4))
  return {
    id: market.id,
    title: market.title,
    category: market.category,
    status: market.status,
    currentProbability: market.currentProbability,
    previousClose: market.previousClose,
    currentMovementPercent: movement,
    currentDirection: toDirection(movement),
    eventCount: events.length,
    lastEventAt: latestEventAt(events) ?? market.lastEventAt,
  }
}

function toTopicUpdate(market: MarketDetail, event: MarketEvent): TopicUpdate {
  return {
    id: event.id,
    marketId: market.id,
    marketTitle: market.title,
    marketCategory: market.category,
    marketStatus: market.status,
    title: event.title,
    startTime: event.startTime,
    endTime: event.endTime,
    movementPercent: event.movementPercent,
    direction: event.direction,
    summary: event.summary,
    signals: event.signals,
    entities: event.entities,
  }
}

function hashString(value: string): string {
  let hash = 0
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) >>> 0
  }
  return hash.toString(16).padStart(8, "0")
}

function buildStateVersion(topicId: string, markets: TopicMarket[], updates: TopicUpdate[]): string {
  const payload = [
    topicId,
    ...markets.map(
      (market) =>
        `market:${market.id}:${market.status}:${market.currentProbability}:${market.currentMovementPercent}:${market.lastEventAt ?? ""}`
    ),
    ...updates.map((update) => `update:${update.id}:${update.endTime}:${update.movementPercent}`),
  ].join("|")
  return hashString(payload)
}

function buildTopics(): TopicState[] {
  const assignments = new Map<string, Array<{ market: MarketDetail; events: MarketEvent[] }>>()
  for (const seed of topicSeeds) {
    assignments.set(seed.id, [])
  }

  for (const marketSummary of getMarkets({ status: "open" as MarketStatus })) {
    const market = getMarketById(marketSummary.id)
    if (!market) {
      continue
    }
    const events = getMarketEvents(market.id)
    const seed = matchSeed(market, events)
    if (!seed) {
      continue
    }
    assignments.get(seed.id)?.push({ market, events })
  }

  const topics: TopicState[] = []
  for (const seed of topicSeeds) {
    const members = assignments.get(seed.id) ?? []
    if (members.length === 0) {
      continue
    }

    const markets = members
      .map(({ market, events }) => toTopicMarket(market, events))
      .sort(
        (left, right) =>
          Math.abs(right.currentMovementPercent) - Math.abs(left.currentMovementPercent)
      )

    const updates = members
      .flatMap(({ market, events }) => events.map((event) => toTopicUpdate(market, event)))
      .sort(
        (left, right) =>
          new Date(right.endTime).getTime() - new Date(left.endTime).getTime() ||
          Math.abs(right.movementPercent) - Math.abs(left.movementPercent)
      )

    const signalCount = new Set(updates.flatMap((update) => update.signals.map((signal) => signal.id)))
      .size
    let strongestMovementPercent = 0
    let strongestMovementDirection: MovementDirection = "up"

    for (const update of updates) {
      const movement = Math.abs(update.movementPercent)
      if (movement > strongestMovementPercent) {
        strongestMovementPercent = movement
        strongestMovementDirection = update.direction
      }
    }

    for (const market of markets) {
      const movement = Math.abs(market.currentMovementPercent)
      if (movement > strongestMovementPercent) {
        strongestMovementPercent = movement
        strongestMovementDirection = market.currentDirection
      }
    }

    strongestMovementPercent = Number(strongestMovementPercent.toFixed(4))

    topics.push({
      id: seed.id,
      title: seed.title,
      description: seed.description,
      category: seed.category,
      query: seed.query,
      stateVersion: buildStateVersion(seed.id, markets, updates),
      marketCount: markets.length,
      updateCount: updates.length,
      signalCount,
      strongestMovementPercent,
      strongestMovementDirection,
      latestUpdateAt: updates[0]?.endTime ?? markets[0]?.lastEventAt,
      markets,
      updates,
    })
  }

  return topics.sort(
    (left, right) =>
      right.strongestMovementPercent - left.strongestMovementPercent ||
      new Date(right.latestUpdateAt ?? 0).getTime() - new Date(left.latestUpdateAt ?? 0).getTime()
  )
}

export function getTopics(): TopicSummary[] {
  return buildTopics().map((topic) => ({
    id: topic.id,
    title: topic.title,
    description: topic.description,
    category: topic.category,
    query: topic.query,
    stateVersion: topic.stateVersion,
    marketCount: topic.marketCount,
    updateCount: topic.updateCount,
    signalCount: topic.signalCount,
    strongestMovementPercent: topic.strongestMovementPercent,
    strongestMovementDirection: topic.strongestMovementDirection,
    latestUpdateAt: topic.latestUpdateAt,
  }))
}

export function getTopicById(topicId: string): TopicDetail | undefined {
  const topic = buildTopics().find((entry) => entry.id === topicId)
  return topic ? { ...topic } : undefined
}
