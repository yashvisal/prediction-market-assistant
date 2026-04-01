import { notFound } from "next/navigation"
import { getMarketById } from "@/lib/mock-data"
import {
  formatProbability,
  formatVolume,
  formatDate,
  formatMovement,
} from "@/lib/formatters"
import { EventCard } from "@/components/markets/event-card"
import { cn } from "@/lib/utils"

interface Props {
  params: Promise<{ marketId: string }>
}

export default async function MarketPage({ params }: Props) {
  const { marketId } = await params
  const market = getMarketById(marketId)

  if (!market) {
    notFound()
  }

  const movement = market.currentProbability - market.previousClose
  const direction = movement >= 0 ? "up" : "down"
  const hasMovement = Math.abs(movement) >= 0.005

  return (
    <div className="space-y-8">
      <section className="space-y-4">
        <p className="text-xs text-muted-foreground capitalize">
          {market.category} · {market.status === "open" ? "Open" : "Resolved"}
        </p>

        <h1 className="text-2xl font-semibold tracking-tight leading-snug">
          {market.title}
        </h1>

        <p className="text-sm text-muted-foreground leading-relaxed max-w-2xl">
          {market.description}
        </p>

        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-semibold tabular-nums">
            {formatProbability(
              market.status === "resolved"
                ? market.resolution === "yes" ? 1 : 0
                : market.currentProbability
            )}
          </span>
          {market.status === "open" && hasMovement && (
            <span
              className={cn(
                "text-sm font-medium tabular-nums",
                direction === "up" ? "text-emerald-600" : "text-red-500"
              )}
            >
              {formatMovement(Math.abs(movement), direction)} from last close
            </span>
          )}
        </div>

        <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-muted-foreground">
          <span>
            <span className="text-muted-foreground/60">Volume</span>{" "}
            {formatVolume(market.volume)}
          </span>
          <span>
            <span className="text-muted-foreground/60">Liquidity</span>{" "}
            {formatVolume(market.liquidity)}
          </span>
          <span>
            <span className="text-muted-foreground/60">Created</span>{" "}
            {formatDate(market.createdAt)}
          </span>
          <span>
            <span className="text-muted-foreground/60">Closes</span>{" "}
            {formatDate(market.closesAt)}
          </span>
        </div>
      </section>

      <section className="space-y-3 rounded-xl border border-border/60 bg-muted/20 p-4">
        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          Price History
        </p>
        <div className="flex h-28 items-end gap-px">
          {Array.from({ length: 30 }, (_, i) => {
            const baseProb =
              market.status === "resolved"
                ? 0.1
                : market.currentProbability * 0.6
            const variance = Math.sin(i * 0.7) * 0.15 + Math.cos(i * 0.3) * 0.1
            const height = Math.max(0.05, Math.min(1, baseProb + variance + i * 0.008))

            return (
              <div
                key={i}
                className="flex-1 rounded-sm bg-foreground/10 transition-colors hover:bg-foreground/20"
                style={{ height: `${height * 100}%` }}
              />
            )
          })}
        </div>
        <p className="text-[11px] text-muted-foreground/50 text-center">
          Placeholder — real chart data will be connected to the Kalshi API
        </p>
      </section>

      <section className="space-y-4">
        <h2 className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
          Key Events
          <span className="ml-2 text-muted-foreground/50 normal-case tracking-normal">
            ({market.events.length})
          </span>
        </h2>
        {market.events.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No significant events detected yet.
          </p>
        ) : (
          <div className="space-y-2">
            {market.events.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
