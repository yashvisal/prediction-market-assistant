import Link from "next/link"
import { getTopEvents, getActiveMarkets } from "@/lib/mock-data"
import { formatProbability, formatMovement, formatDateRange } from "@/lib/formatters"
import { cn } from "@/lib/utils"
import { buttonVariants } from "@/components/ui/button-variants"

export default function DashboardPage() {
  const topEvents = getTopEvents()
  const activeMarkets = getActiveMarkets()

  return (
    <div className="space-y-10">
      <section>
        <h1 className="text-xl font-semibold tracking-tight">Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Explore the information environment around prediction market movements.
        </p>
      </section>

      <section className="space-y-4">
        <div className="flex items-baseline justify-between">
          <h2 className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
            Top Events
          </h2>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {topEvents.map((event) => (
            <Link
              key={event.id}
              href={`/markets/${event.marketId}`}
              className="group flex flex-col gap-2 rounded-xl border border-border/60 bg-card p-4 transition-colors hover:border-border hover:bg-accent/30"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs text-muted-foreground capitalize">
                  {event.marketCategory}
                </span>
                <span
                  className={cn(
                    "text-sm font-semibold tabular-nums",
                    event.direction === "up"
                      ? "text-emerald-600"
                      : "text-red-500"
                  )}
                >
                  {formatMovement(event.movementPercent, event.direction)}
                </span>
              </div>
              <p className="text-sm font-medium leading-snug">{event.title}</p>
              <p className="text-xs text-muted-foreground line-clamp-1">
                {event.marketTitle}
              </p>
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

      <section className="space-y-4">
        <div className="flex items-baseline justify-between">
          <h2 className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
            Active Markets
          </h2>
          <Link
            href="/markets"
            className={cn(
              buttonVariants({ variant: "ghost", size: "sm" }),
              "text-muted-foreground"
            )}
          >
            View all →
          </Link>
        </div>
        <div className="space-y-2">
          {activeMarkets.slice(0, 5).map((market) => {
            const movement = market.currentProbability - market.previousClose
            const direction = movement >= 0 ? "up" : "down"
            const hasMovement = Math.abs(movement) >= 0.005

            return (
              <Link
                key={market.id}
                href={`/markets/${market.id}`}
                className="group flex items-center gap-4 rounded-lg border border-border/40 px-4 py-3 transition-colors hover:border-border hover:bg-accent/30"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium leading-snug truncate">
                    {market.title}
                  </p>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {market.events.length} event
                    {market.events.length !== 1 ? "s" : ""} ·{" "}
                    {market.category.charAt(0).toUpperCase() +
                      market.category.slice(1)}
                  </p>
                </div>
                <div className="flex items-baseline gap-1.5 shrink-0">
                  <span className="text-base font-semibold tabular-nums">
                    {formatProbability(market.currentProbability)}
                  </span>
                  {hasMovement && (
                    <span
                      className={cn(
                        "text-xs tabular-nums",
                        direction === "up"
                          ? "text-emerald-600"
                          : "text-red-500"
                      )}
                    >
                      {formatMovement(Math.abs(movement), direction)}
                    </span>
                  )}
                </div>
              </Link>
            )
          })}
        </div>
      </section>
    </div>
  )
}
