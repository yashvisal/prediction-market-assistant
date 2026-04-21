import type {
  MarketCategory,
  MarketStatus,
} from "@/lib/market-types"
import type { Entity, MovementDirection, Signal } from "@/lib/intelligence-types"

export interface TopicMarket {
  id: string
  title: string
  category: MarketCategory
  status: MarketStatus
  currentProbability: number
  previousClose: number
  currentMovementPercent: number
  currentDirection: MovementDirection
  eventCount: number
  lastEventAt: string | null
}

export interface TopicUpdate {
  id: string
  marketId: string
  marketTitle: string
  marketCategory: MarketCategory
  marketStatus: MarketStatus
  title: string
  startTime: string
  endTime: string
  movementPercent: number
  direction: MovementDirection
  summary: string | null
  signals: Signal[]
  entities: Entity[]
}

export interface TopicSummary {
  id: string
  title: string
  description: string
  category: MarketCategory
  query: string
  stateVersion: string
  marketCount: number
  updateCount: number
  signalCount: number
  strongestMovementPercent: number
  strongestMovementDirection: MovementDirection
  latestUpdateAt: string | null
}

export interface TopicState extends TopicSummary {
  markets: TopicMarket[]
  updates: TopicUpdate[]
}

export type TopicDetail = TopicState

export interface TopicsResponse {
  items: TopicSummary[]
}
