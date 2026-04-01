import Link from "next/link"
import type { Market } from "@/lib/market-types"
import { formatProbability, formatVolume, formatMovement } from "@/lib/formatters"
import { cn } from "@/lib/utils"

export function MarketCard({ market }: { market: Market }) {
  const movement = market.currentProbability - market.previousClose
  const direction = movement >= 0 ? "up" : "down"
  const hasMovement = Math.abs(movement) >= 0.005
  const isResolved = market.status === "resolved"
  const resolvedProb = market.resolution === "yes" ? 1 : 0

  return (
    <Link
      href={`/markets/${market.id}`}
      className={cn(
        "group flex flex-col gap-3 rounded-xl border border-border/60 bg-card p-4 transition-colors hover:border-border hover:bg-accent/30",
        isResolved && "opacity-70"
      )}
    >
      <h3 className="text-[15px] leading-snug font-medium group-hover:text-foreground">
        {market.title}
      </h3>

      <div className="flex items-baseline gap-1.5">
        <span className="text-lg font-semibold tabular-nums leading-none">
          {formatProbability(isResolved ? resolvedProb : market.currentProbability)}
        </span>
        {!isResolved && hasMovement && (
          <span
            className={cn(
              "text-xs tabular-nums",
              direction === "up" ? "text-emerald-600" : "text-red-500"
            )}
          >
            {formatMovement(Math.abs(movement), direction)}
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
          <span>{market.events.length} event{market.events.length !== 1 ? "s" : ""}</span>
        )}
      </div>
    </Link>
  )
}
