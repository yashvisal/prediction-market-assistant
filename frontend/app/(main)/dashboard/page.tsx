import { DashboardView } from "@/components/dashboard/dashboard-view"
import { getDashboardSnapshot } from "@/lib/repositories/markets"

export default async function DashboardPage() {
  const { topEvents, activeMarkets } = await getDashboardSnapshot()

  return <DashboardView topEvents={topEvents} activeMarkets={activeMarkets} />
}
