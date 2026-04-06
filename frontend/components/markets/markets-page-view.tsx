import { Suspense } from "react"

import { MarketCard } from "@/components/markets/market-card"
import { MarketFilters } from "@/components/markets/market-filters"
import type { MarketSummary } from "@/lib/market-types"

interface MarketsPageViewProps {
  markets: MarketSummary[]
}

export function MarketsPageView({ markets }: MarketsPageViewProps) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-balance text-xl font-semibold tracking-tight">Markets</h1>
        <p className="mt-1 max-w-2xl text-sm leading-relaxed text-muted-foreground">
          Browse prediction markets and explore the event history behind each move.
        </p>
      </div>

      <Suspense
        fallback={<div className="h-7 rounded-lg border border-border/40 bg-muted/20" />}
      >
        <MarketFilters />
      </Suspense>

      {markets.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border/70 bg-muted/20 px-4 py-12 text-center">
          <p className="text-sm text-muted-foreground">
            No markets match the current filters. Clear one or both filters to broaden
            the list.
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
