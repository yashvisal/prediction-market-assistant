import { DashboardView } from "@/components/dashboard/dashboard-view"
import { LegacySurfaceNotice } from "@/components/legacy/legacy-surface-notice"
import { getDashboardSnapshot } from "@/lib/repositories/markets"

export default async function DashboardPage() {
  const { topEvents, activeMarkets } = await getDashboardSnapshot()

  return (
    <div className="space-y-6">
      <LegacySurfaceNotice
        title="This dashboard is a legacy market-first view."
        description="It remains available temporarily for compatibility, but the forward-looking product surface is now the topic feed."
      />
      <DashboardView topEvents={topEvents} activeMarkets={activeMarkets} />
    </div>
  )
}
