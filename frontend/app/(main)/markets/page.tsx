import { Suspense } from "react"
import { getMarkets } from "@/lib/mock-data"
import { MarketCard } from "@/components/markets/market-card"
import { MarketFilters } from "@/components/markets/market-filters"
import type { MarketStatus, MarketCategory } from "@/lib/market-types"

const MARKET_STATUSES: MarketStatus[] = ["open", "closed", "resolved"]
const MARKET_CATEGORIES: MarketCategory[] = [
  "finance",
  "politics",
  "technology",
  "crypto",
  "climate",
  "geopolitics",
  "science",
  "sports",
]

function isMarketStatus(value: string | undefined): value is MarketStatus {
  return value !== undefined && MARKET_STATUSES.includes(value as MarketStatus)
}

function isMarketCategory(value: string | undefined): value is MarketCategory {
  return (
    value !== undefined && MARKET_CATEGORIES.includes(value as MarketCategory)
  )
}

interface Props {
  searchParams: Promise<{ status?: string; category?: string }>
}

export default async function MarketsPage({ searchParams }: Props) {
  const params = await searchParams
  const statusFilter = isMarketStatus(params.status) ? params.status : undefined
  const categoryFilter = isMarketCategory(params.category)
    ? params.category
    : undefined

  let markets = getMarkets()

  if (statusFilter) {
    markets = markets.filter((m) => m.status === statusFilter)
  }
  if (categoryFilter) {
    markets = markets.filter((m) => m.category === categoryFilter)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Markets</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Browse prediction markets and explore their event history.
        </p>
      </div>

      <Suspense>
        <MarketFilters />
      </Suspense>

      {markets.length === 0 ? (
        <div className="py-12 text-center">
          <p className="text-sm text-muted-foreground">
            No markets match the current filters.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {markets.map((market) => (
            <MarketCard key={market.id} market={market} />
          ))}
        </div>
      )}
    </div>
  )
}
