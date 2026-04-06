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

  return <MarketsPageView markets={markets} />
}
