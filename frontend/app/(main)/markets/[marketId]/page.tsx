import { notFound } from "next/navigation"
import { LegacySurfaceNotice } from "@/components/legacy/legacy-surface-notice"
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

  return (
    <div className="space-y-6">
      <LegacySurfaceNotice
        title="This market workspace is a legacy drill-down."
        description="It remains available temporarily while the new topic routes and topic views replace market-first navigation."
      />
      <MarketWorkspace market={market} events={events} />
    </div>
  )
}
