export const signalSourceTypes = ["news", "tweet", "official", "analysis"] as const
export type SignalSourceType = (typeof signalSourceTypes)[number]

export const entityTypes = ["person", "organization", "topic", "legislation"] as const
export type EntityType = (typeof entityTypes)[number]

export const relationshipTypes = ["shared_entity", "shared_source", "time_overlap"] as const
export type RelationshipType = (typeof relationshipTypes)[number]

export const movementDirections = ["up", "down"] as const
export type MovementDirection = (typeof movementDirections)[number]

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
