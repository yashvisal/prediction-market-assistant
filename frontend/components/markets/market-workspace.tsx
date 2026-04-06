import { EventCard } from "@/components/markets/event-card"
import {
  getMovementDirectionLabel,
  getMovementDirectionSymbol,
  getMovementMeta,
} from "@/lib/domain/markets"
import { formatDate, formatMovement, formatProbability, formatVolume } from "@/lib/formatters"
import type { MarketDetail, MarketEvent } from "@/lib/market-types"
import { cn } from "@/lib/utils"

interface MarketWorkspaceProps {
  market: MarketDetail
  events: MarketEvent[]
}

export function MarketWorkspace({ market, events }: MarketWorkspaceProps) {
  const movement = getMovementMeta(market.currentProbability, market.previousClose)
  const displayProbability =
    market.status === "resolved"
      ? market.resolution === "yes"
        ? 1
        : market.resolution === "no"
          ? 0
          : market.currentProbability
      : market.currentProbability

  return (
    <div className="space-y-8">
      <section className="space-y-4">
        <p className="text-xs text-muted-foreground capitalize">
          {market.category} · {market.status === "open" ? "Open" : "Resolved"}
        </p>

        <h1 className="max-w-4xl text-balance text-2xl leading-snug font-semibold tracking-tight">
          {market.title}
        </h1>

        <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
          {market.description}
        </p>

        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-semibold tabular-nums">
            {formatProbability(displayProbability)}
          </span>
          {market.status === "open" && movement.hasMovement ? (
            <span
              aria-label={`${getMovementDirectionLabel(movement.direction)} ${formatMovement(
                Math.abs(movement.amount),
                movement.direction
              )} from last close`}
              className={cn(
                "text-sm font-medium tabular-nums",
                movement.direction === "up" ? "text-emerald-600" : "text-red-500"
              )}
            >
              <span aria-hidden="true" className="mr-1">
                {getMovementDirectionSymbol(movement.direction)}
              </span>
              {formatMovement(Math.abs(movement.amount), movement.direction)} from last close
            </span>
          ) : null}
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
        <div aria-hidden="true" className="flex h-28 items-end gap-px">
          {Array.from({ length: 30 }, (_, index) => {
            const baseProbability =
              market.status === "resolved" ? 0.1 : market.currentProbability * 0.6
            const variance =
              Math.sin(index * 0.7) * 0.15 + Math.cos(index * 0.3) * 0.1
            const height = Math.max(
              0.05,
              Math.min(1, baseProbability + variance + index * 0.008)
            )

            return (
              <div
                key={index}
                className="flex-1 rounded-sm bg-foreground/10 transition-colors hover:bg-foreground/20"
                style={{ height: `${height * 100}%` }}
              />
            )
          })}
        </div>
        <p className="text-center text-[11px] text-muted-foreground/50">
          Placeholder. Real chart data will be connected to the backend market history.
        </p>
      </section>

      <section className="space-y-4" aria-labelledby="market-events-heading">
        <h2
          id="market-events-heading"
          className="text-sm font-medium uppercase tracking-wider text-muted-foreground"
        >
          Key Events
          <span className="ml-2 text-muted-foreground/50 normal-case tracking-normal">
            ({events.length})
          </span>
        </h2>
        {events.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border/70 bg-muted/20 px-4 py-10 text-center">
            <p className="text-sm text-muted-foreground">
              No significant events were returned for this market yet.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {events.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
