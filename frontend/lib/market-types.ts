export type MarketStatus = "open" | "closed" | "resolved"

export type MarketCategory =
  | "finance"
  | "politics"
  | "technology"
  | "crypto"
  | "climate"
  | "geopolitics"
  | "science"
  | "sports"

export type SignalSourceType = "news" | "tweet" | "official" | "analysis"
export type EntityType = "person" | "organization" | "topic" | "legislation"
export type RelationshipType = "shared_entity" | "shared_source" | "time_overlap"
export type MovementDirection = "up" | "down"

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

export interface Market {
  id: string
  title: string
  description: string
  status: MarketStatus
  category: MarketCategory
  currentProbability: number
  previousClose: number
  volume: number
  liquidity: number
  createdAt: string
  closesAt: string
  resolvedAt?: string
  resolution?: "yes" | "no"
  events: MarketEvent[]
}
