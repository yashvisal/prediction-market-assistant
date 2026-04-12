export interface PredictionHuntRateLimitSnapshot {
  perSecondLimit?: number
  perSecondRemaining?: number
  perMonthLimit?: number
  perMonthRemaining?: number
  retryAfterSeconds?: number
}

export interface PredictionHuntMatchGroupSummary {
  groupId: number
  title: string
  platformCount: number
  platforms: string[]
}

export interface PredictionHuntEventSummary {
  id: number
  eventName: string
  eventType: string
  eventDate: string
  status: string
  groups: PredictionHuntMatchGroupSummary[]
}

export interface PredictionHuntEventsResponse {
  events: PredictionHuntEventSummary[]
  nextCursor?: string
  totalCount: number
  rateLimits?: PredictionHuntRateLimitSnapshot
}

export interface PredictionHuntPriceSnapshot {
  yesBid?: number
  yesAsk?: number
  noBid?: number
  noAsk?: number
  lastPrice?: number
  volume?: number
  liquidity?: number
}

export interface PredictionHuntMarketSummary {
  id: number
  marketId: string
  platform: string
  title: string
  category?: string
  status: string
  expirationDate?: string
  sourceUrl?: string
  price: PredictionHuntPriceSnapshot
}

export interface PredictionHuntMarketsResponse {
  markets: PredictionHuntMarketSummary[]
  nextCursor?: string
  totalCount: number
  rateLimits?: PredictionHuntRateLimitSnapshot
}

export interface PredictionHuntMatchingMarket {
  source: string
  sourceUrl?: string
  id: string
}

export interface PredictionHuntMatchingGroup {
  title: string
  markets: PredictionHuntMatchingMarket[]
}

export interface PredictionHuntMatchingEvent {
  title: string
  eventType?: string
  eventDate?: string
  confidence?: string
  groups: PredictionHuntMatchingGroup[]
}

export interface PredictionHuntMatchingMarketsResponse {
  success: boolean
  count: number
  events: PredictionHuntMatchingEvent[]
  rateLimits?: PredictionHuntRateLimitSnapshot
}

export interface PredictionHuntCandle {
  timestamp: string
  open?: number
  high?: number
  low?: number
  close?: number
  yesBid?: number
  yesAsk?: number
  mid?: number
  volume?: number
  dollarVolume?: number
}

export interface PredictionHuntPriceHistoryResponse {
  marketId: string
  platform: string
  interval: string
  candles: PredictionHuntCandle[]
  rateLimits?: PredictionHuntRateLimitSnapshot
}

export interface PredictionHuntOrderbookLevel {
  price: number
  size: number
}

export interface PredictionHuntOrderbookSide {
  bids: PredictionHuntOrderbookLevel[]
  asks: PredictionHuntOrderbookLevel[]
}

export interface PredictionHuntOrderbookResponse {
  marketId: string
  platform: string
  timestamp?: string
  yes: PredictionHuntOrderbookSide
  no: PredictionHuntOrderbookSide
  rateLimits?: PredictionHuntRateLimitSnapshot
}

export interface PredictionHuntPlatformStatus {
  status: string
  lastUpdated?: string
  activeMarkets: number
}

export interface PredictionHuntStatusResponse {
  status: string
  platforms: Record<string, PredictionHuntPlatformStatus>
  rateLimits?: PredictionHuntRateLimitSnapshot
}

export interface PredictionHuntDeskSnapshotResponse {
  status: PredictionHuntStatusResponse
  events: PredictionHuntEventsResponse
  markets: PredictionHuntMarketsResponse
  searchedMarkets?: PredictionHuntMarketsResponse
  matching?: PredictionHuntMatchingMarketsResponse
  history?: PredictionHuntPriceHistoryResponse
  orderbook?: PredictionHuntOrderbookResponse
  selectedMarket?: PredictionHuntMarketSummary
  marketQuery?: string
  matchingQuery?: string
  warnings: string[]
  raw: Record<string, unknown>
}
