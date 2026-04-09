import type {
  MarketDetail,
  MarketEvent,
  MovementDirection,
  SignalSourceType,
} from "@/lib/market-types"

export interface MarketQualitySummary {
  pointCount: number
  nonZeroPointRatio: number
  probabilityVariance: number
  probabilitySpread: number
  recentMovement: number
  hasRealHistory: boolean
  usableDetectorInput: boolean
}

export interface SelectionDebugInfo {
  score: number
  rank?: number
  pool: "open" | "historical"
  selected: boolean
  reasons: string[]
  penalties: string[]
  components: Record<string, number>
}

export interface ValidationMarketOption {
  marketId: string
  title: string
  status: string
  pool: "open" | "historical"
  score: number
  selected: boolean
  knownGood: boolean
}

export interface HistorySummary {
  source: string
  firstTimestamp?: string
  lastTimestamp?: string
  minProbability?: number
  maxProbability?: number
  currentProbability?: number
  pointCount: number
}

export interface EventCandidateDebug {
  candidateId: string
  stage: "raw" | "filtered" | "final"
  kept: boolean
  dropReason?: string
  title: string
  startTime: string
  endTime?: string
  probabilityBefore: number
  probabilityAfter?: number
  movementPercent: number
  direction?: MovementDirection
  debugPayload: Record<string, unknown>
}

export interface SignalCandidateDebug {
  eventId: string
  title: string
  source: string
  sourceType: SignalSourceType
  url: string
  publishedAt: string
  snippet: string
  relevanceScore: number
  kept: boolean
  debugPayload: Record<string, unknown>
}

export interface RoutingDecisionDebug {
  eventId: string
  decision: "skip" | "light_research" | "deep_research"
  reason: string
  candidateCount: number
}

export interface HeuristicEvaluationResponse {
  market: MarketDetail
  historySummary: HistorySummary
  marketQuality: MarketQualitySummary
  selectionDebug: SelectionDebugInfo
  rawCandidates: EventCandidateDebug[]
  filteredCandidates: EventCandidateDebug[]
  finalEvents: MarketEvent[]
  signalCandidates: SignalCandidateDebug[]
  routingDecisions: RoutingDecisionDebug[]
  validationMarkets: ValidationMarketOption[]
}

export interface HeuristicMarketListResponse {
  items: ValidationMarketOption[]
}
