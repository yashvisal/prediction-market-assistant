import { LegacySurfaceNotice } from "@/components/legacy/legacy-surface-notice"
import { MarketsPageView } from "@/components/markets/markets-page-view"
import { listMarkets } from "@/lib/repositories/markets"
import {
  marketCategories,
  marketStatuses,
  type MarketStatus,
  type MarketCategory,
} from "@/lib/market-types"

function isMarketStatus(value: string | undefined): value is MarketStatus {
  return value !== undefined && marketStatuses.includes(value as MarketStatus)
}

function isMarketCategory(value: string | undefined): value is MarketCategory {
  return value !== undefined && marketCategories.includes(value as MarketCategory)
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
  const markets = await listMarkets(statusFilter, categoryFilter)

  return (
    <div className="space-y-6">
      <LegacySurfaceNotice
        title="This market gallery is now a legacy compatibility surface."
        description="Use the topic feed for the forward-looking experience. These market pages remain temporarily while topic routes fully replace their role."
      />
      <MarketsPageView markets={markets} />
    </div>
  )
}
