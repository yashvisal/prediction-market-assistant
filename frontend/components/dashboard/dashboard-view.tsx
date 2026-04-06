import Link from "next/link"

import { buttonVariants } from "@/components/ui/button-variants"
import {
  getMovementDirectionLabel,
  getMovementDirectionSymbol,
  getMovementMeta,
} from "@/lib/domain/markets"
import type { MarketEventFeedItem, MarketSummary } from "@/lib/market-types"
import { formatDateRange, formatMovement, formatProbability } from "@/lib/formatters"
import { cn } from "@/lib/utils"

interface DashboardViewProps {
  topEvents: MarketEventFeedItem[]
  activeMarkets: MarketSummary[]
}

export function DashboardView({ topEvents, activeMarkets }: DashboardViewProps) {
  return (
    <div className="space-y-10">
      <section>
        <h1 className="text-balance text-xl font-semibold tracking-tight">Dashboard</h1>
        <p className="mt-1 max-w-2xl text-sm leading-relaxed text-muted-foreground">
          Explore the information environment around prediction market movements.
        </p>
      </section>

      <section className="space-y-4" aria-labelledby="top-events-heading">
        <div className="flex items-baseline justify-between">
          <h2
            id="top-events-heading"
            className="text-sm font-medium uppercase tracking-wider text-muted-foreground"
          >
            Top Events
          </h2>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {topEvents.map((event) => (
            <Link
              key={event.id}
              href={`/markets/${event.marketId}`}
              className="group flex min-w-0 flex-col gap-2 rounded-xl border border-border/60 bg-card p-4 transition-colors hover:border-border hover:bg-accent/30 focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs text-muted-foreground capitalize">
                  {event.marketCategory}
                </span>
                <span
                  aria-label={`${getMovementDirectionLabel(event.direction)} ${formatMovement(
                    event.movementPercent,
                    event.direction
                  )}`}
                  className={cn(
                    "text-sm font-semibold tabular-nums",
                    event.direction === "up" ? "text-emerald-600" : "text-red-500"
                  )}
                >
                  <span aria-hidden="true" className="mr-1">
                    {getMovementDirectionSymbol(event.direction)}
                  </span>
                  {formatMovement(event.movementPercent, event.direction)}
                </span>
              </div>
              <p className="text-sm font-medium leading-snug text-pretty">
                {event.title}
              </p>
              <p className="truncate text-xs text-muted-foreground">{event.marketTitle}</p>
              <div className="mt-auto flex items-center gap-2 text-[11px] text-muted-foreground/70">
                <span>{formatDateRange(event.startTime, event.endTime)}</span>
                <span className="text-border">·</span>
                <span>
                  {formatProbability(event.probabilityBefore)} →{" "}
                  {formatProbability(event.probabilityAfter)}
                </span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="space-y-4" aria-labelledby="active-markets-heading">
        <div className="flex items-baseline justify-between">
          <h2
            id="active-markets-heading"
            className="text-sm font-medium uppercase tracking-wider text-muted-foreground"
          >
            Active Markets
          </h2>
          <Link
            href="/markets"
            className={cn(
              buttonVariants({ variant: "ghost", size: "sm" }),
              "text-muted-foreground"
            )}
          >
            View All
          </Link>
        </div>
        <div className="space-y-2">
          {activeMarkets.slice(0, 5).map((market) => {
            const movement = getMovementMeta(market.currentProbability, market.previousClose)

            return (
              <Link
                key={market.id}
                href={`/markets/${market.id}`}
                className="group flex items-center gap-4 rounded-lg border border-border/40 px-4 py-3 transition-colors hover:border-border hover:bg-accent/30 focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium leading-snug">{market.title}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {market.eventCount} event
                    {market.eventCount !== 1 ? "s" : ""} ·{" "}
                    {market.category.charAt(0).toUpperCase() + market.category.slice(1)}
                  </p>
                </div>
                <div className="flex shrink-0 items-baseline gap-1.5">
                  <span className="text-base font-semibold tabular-nums">
                    {formatProbability(market.currentProbability)}
                  </span>
                  {movement.hasMovement ? (
                    <span
                      aria-label={`${getMovementDirectionLabel(movement.direction)} ${formatMovement(
                        Math.abs(movement.amount),
                        movement.direction
                      )}`}
                      className={cn(
                        "text-xs tabular-nums",
                        movement.direction === "up"
                          ? "text-emerald-600"
                          : "text-red-500"
                      )}
                    >
                      <span aria-hidden="true" className="mr-1">
                        {getMovementDirectionSymbol(movement.direction)}
                      </span>
                      {formatMovement(Math.abs(movement.amount), movement.direction)}
                    </span>
                  ) : null}
                </div>
              </Link>
            )
          })}
        </div>
      </section>
    </div>
  )
}
