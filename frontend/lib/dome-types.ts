export interface DomeMarketSide {
  id: string
  label: string
  price?: number
}

export interface DomeMarketSummary {
  marketSlug: string
  conditionId?: string
  eventSlug?: string
  title: string
  status: string
  startTime: string
  endTime: string
  volume1Week: number
  volumeTotal: number
  tags: string[]
  description?: string
  image?: string
  sideA: DomeMarketSide
  sideB: DomeMarketSide
}

export interface DomeTradeRecord {
  tokenId: string
  tokenLabel: string
  side: string
  price: number
  sharesNormalized: number
  timestamp: string
  txHash: string
  user: string
  taker: string
}

export interface DomeOrderbookLevel {
  price: number
  size: number
}

export interface DomeOrderbookSummary {
  timestamp: string
  indexedAt: string
  bestBid?: number
  bestAsk?: number
  spread?: number
  bidDepthLevels: number
  askDepthLevels: number
  topBids: DomeOrderbookLevel[]
  topAsks: DomeOrderbookLevel[]
}

export interface DomeMarketQualitySummary {
  hasPrices: boolean
  hasRecentTrades: boolean
  hasOrderbook: boolean
  recentTradeCount: number
  totalRecentShares: number
  lastTradeAt?: string
  bestBid?: number
  bestAsk?: number
  spread?: number
  marketAgeHours: number
}

export interface DomePriceSamplePoint {
  label: string
  atTime: string
  sideAPrice?: number
  sideBPrice?: number
}

export interface DomeMarketSampleItem {
  market: DomeMarketSummary
  quality: DomeMarketQualitySummary
}

export interface DomeEventMarket {
  marketSlug: string
  title: string
  status: string
  volumeTotal: number
}

export interface DomeEventSummary {
  eventSlug: string
  title: string
  subtitle?: string
  status: string
  startTime: string
  endTime: string
  volumeFiatAmount: number
  tags: string[]
  marketCount: number
  markets: DomeEventMarket[]
}

export interface DomeMarketCoverageSummary {
  sampleSize: number
  priceCoverageRatio: number
  tradeCoverageRatio: number
  orderbookCoverageRatio: number
  averageRecentTradeCount: number
  averageSpread?: number
}

export interface DomeMarketListResponse {
  items: DomeMarketSummary[]
  total: number
  hasMore: boolean
}

export interface DomeEventListResponse {
  items: DomeEventSummary[]
  total: number
  hasMore: boolean
}

export interface DomeMarketDiscoveryResponse {
  items: DomeMarketSampleItem[]
  coverage: DomeMarketCoverageSummary
  total: number
  hasMore: boolean
}

export interface DomeMarketDetailResponse {
  market: DomeMarketSummary
  quality: DomeMarketQualitySummary
  priceHistory: DomePriceSamplePoint[]
  recentTrades: DomeTradeRecord[]
  orderbook?: DomeOrderbookSummary
  raw: Record<string, unknown>
}
