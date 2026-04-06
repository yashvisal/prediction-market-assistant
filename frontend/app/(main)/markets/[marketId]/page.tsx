import { notFound } from "next/navigation"
import { MarketWorkspace } from "@/components/markets/market-workspace"
import { getMarketDetail, listMarketEvents } from "@/lib/repositories/markets"

interface Props {
  params: Promise<{ marketId: string }>
}

export default async function MarketPage({ params }: Props) {
  const { marketId } = await params
  const [market, events] = await Promise.all([
    getMarketDetail(marketId),
    listMarketEvents(marketId),
  ])

  if (!market) {
    notFound()
  }

  return <MarketWorkspace market={market} events={events} />
}
