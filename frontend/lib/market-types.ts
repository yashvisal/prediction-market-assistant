import type {
  Entity,
  MovementDirection,
  RelatedEvent,
  Signal,
} from "@/lib/intelligence-types"
export type {
  Entity,
  MovementDirection,
  RelatedEvent,
  Signal,
} from "@/lib/intelligence-types"

export const marketStatuses = ["open", "closed", "resolved"] as const
export type MarketStatus = (typeof marketStatuses)[number]

export const marketCategories = [
  "finance",
  "politics",
  "technology",
  "crypto",
  "climate",
  "geopolitics",
  "science",
  "sports",
] as const
export type MarketCategory = (typeof marketCategories)[number]

export type MarketResolution = "yes" | "no"

export interface MarketEvent {
  id: string
  marketId: string
  title: string
  startTime: string
  endTime: string
  probabilityBefore: number
  probabilityAfter: number
  movementPercent: number
  direction: MovementDirection
  signals: Signal[]
  entities: Entity[]
  relatedEvents: RelatedEvent[]
  summary?: string
}

export interface MarketSummary {
  id: string
  title: string
  status: MarketStatus
  category: MarketCategory
  currentProbability: number
  previousClose: number
  volume: number
  liquidity: number
  createdAt: string
  closesAt: string
  resolvedAt?: string
  resolution?: MarketResolution
  eventCount: number
  lastEventAt?: string
}

export interface MarketDetail extends MarketSummary {
  description: string
}

export interface MarketEventFeedItem extends MarketEvent {
  marketTitle: string
  marketCategory: MarketCategory
  marketStatus: MarketStatus
}

export interface DashboardSnapshot {
  activeMarkets: MarketSummary[]
  topEvents: MarketEventFeedItem[]
}

export interface MarketsResponse {
  items: MarketSummary[]
}

export interface MarketEventsResponse {
  items: MarketEvent[]
}

export interface HealthResponse {
  status: "ok"
}
