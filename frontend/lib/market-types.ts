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

export const signalSourceTypes = ["news", "tweet", "official", "analysis"] as const
export type SignalSourceType = (typeof signalSourceTypes)[number]

export const entityTypes = ["person", "organization", "topic", "legislation"] as const
export type EntityType = (typeof entityTypes)[number]

export const relationshipTypes = ["shared_entity", "shared_source", "time_overlap"] as const
export type RelationshipType = (typeof relationshipTypes)[number]

export const movementDirections = ["up", "down"] as const
export type MovementDirection = (typeof movementDirections)[number]

export type MarketResolution = "yes" | "no"

export interface Entity {
  id: string
  name: string
  type: EntityType
}

export interface Signal {
  id: string
  title: string
  source: string
  sourceType: SignalSourceType
  url: string
  publishedAt: string
  snippet: string
  relevanceScore: number
  entities: Entity[]
}

export interface RelatedEvent {
  id: string
  marketId: string
  marketTitle: string
  eventTitle: string
  relationship: RelationshipType
  sharedEntities?: string[]
}

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
