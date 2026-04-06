import type {
  DashboardSnapshot,
  MarketDetail,
  MarketEvent,
  MarketEventFeedItem,
  MarketSummary,
  MovementDirection,
} from "@/lib/market-types"

const MOVEMENT_THRESHOLD = 0.005

export function getMovementMeta(currentProbability: number, previousClose: number): {
  amount: number
  direction: MovementDirection
  hasMovement: boolean
} {
  const amount = currentProbability - previousClose

  return {
    amount,
    direction: amount >= 0 ? "up" : "down",
    hasMovement: Math.abs(amount) >= MOVEMENT_THRESHOLD,
  }
}

export function getResolvedProbability(market: Pick<MarketDetail, "resolution">): number {
  return market.resolution === "yes" ? 1 : 0
}

export function getMovementDirectionSymbol(direction: MovementDirection): string {
  return direction === "up" ? "↑" : "↓"
}

export function getMovementDirectionLabel(direction: MovementDirection): string {
  return direction === "up" ? "Up" : "Down"
}

export function buildDashboardSnapshot(
  markets: MarketSummary[],
  getEventsForMarket: (marketId: string) => MarketEvent[]
): DashboardSnapshot {
  const topEvents = markets
    .flatMap<MarketEventFeedItem>((market) =>
      getEventsForMarket(market.id).map((event) => ({
        ...event,
        marketTitle: market.title,
        marketCategory: market.category,
        marketStatus: market.status,
      }))
    )
    .sort((a, b) => Math.abs(b.movementPercent) - Math.abs(a.movementPercent))
    .slice(0, 4)

  return {
    activeMarkets: markets.filter((market) => market.status === "open"),
    topEvents,
  }
}
