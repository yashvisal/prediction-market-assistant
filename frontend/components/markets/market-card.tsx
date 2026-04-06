import Link from "next/link"
import type { MarketSummary } from "@/lib/market-types"
import {
  getMovementDirectionLabel,
  getMovementDirectionSymbol,
  getMovementMeta,
  getResolvedProbability,
} from "@/lib/domain/markets"
import { formatProbability, formatVolume, formatMovement } from "@/lib/formatters"
import { cn } from "@/lib/utils"

export function MarketCard({ market }: { market: MarketSummary }) {
  const movement = getMovementMeta(market.currentProbability, market.previousClose)
  const isResolved = market.status === "resolved"
  const resolvedProb = getResolvedProbability(market)

  return (
    <Link
      href={`/markets/${market.id}`}
      className={cn(
        "group flex min-w-0 flex-col gap-3 rounded-xl border border-border/60 bg-card p-4 transition-colors hover:border-border hover:bg-accent/30 focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50",
        isResolved && "opacity-70"
      )}
    >
      <h3 className="text-pretty text-[15px] leading-snug font-medium group-hover:text-foreground">
        {market.title}
      </h3>

      <div className="flex items-baseline gap-1.5">
        <span className="text-lg font-semibold tabular-nums leading-none">
          {formatProbability(isResolved ? resolvedProb : market.currentProbability)}
        </span>
        {!isResolved && movement.hasMovement && (
          <span
            aria-label={`${getMovementDirectionLabel(movement.direction)} ${formatMovement(
              Math.abs(movement.amount),
              movement.direction
            )}`}
            className={cn(
              "text-xs tabular-nums",
              movement.direction === "up" ? "text-emerald-600" : "text-red-500"
            )}
          >
            <span aria-hidden="true" className="mr-1">
              {getMovementDirectionSymbol(movement.direction)}
            </span>
            {formatMovement(Math.abs(movement.amount), movement.direction)}
          </span>
        )}
      </div>

      <div className="mt-auto flex items-center gap-3 text-xs text-muted-foreground">
        <span className="capitalize">{market.category}</span>
        <span className="text-border">·</span>
        <span>{formatVolume(market.volume)} vol</span>
        <span className="text-border">·</span>
        {isResolved ? (
          <span>Resolved</span>
        ) : (
          <span>
            {market.eventCount} event{market.eventCount !== 1 ? "s" : ""}
          </span>
        )}
      </div>
    </Link>
  )
}
