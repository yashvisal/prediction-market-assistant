"use client"

import * as React from "react"
import {
  getMovementDirectionLabel,
  getMovementDirectionSymbol,
} from "@/lib/domain/markets"
import type { MarketEvent } from "@/lib/market-types"
import { formatMovement, formatDateRange, formatProbability } from "@/lib/formatters"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

const sourceTypeConfig: Record<string, { label: string; accent: string }> = {
  news: { label: "News", accent: "bg-blue-500" },
  tweet: { label: "Social", accent: "bg-sky-400" },
  official: { label: "Official", accent: "bg-amber-500" },
  analysis: { label: "Analysis", accent: "bg-violet-500" },
}

export function EventCard({ event }: { event: MarketEvent }) {
  const [expanded, setExpanded] = React.useState(false)

  return (
    <div className="rounded-lg border border-border/60 bg-card">
      <button
        type="button"
        aria-expanded={expanded}
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-accent/30 focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
      >
        <span aria-hidden="true" className="text-muted-foreground text-xs select-none">
          {expanded ? "▾" : "▸"}
        </span>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium leading-snug truncate">
            {event.title}
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {formatDateRange(event.startTime, event.endTime)}
          </p>
        </div>

        <div className="flex items-baseline gap-1.5 shrink-0">
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
          <span className="text-xs text-muted-foreground tabular-nums">
            → {formatProbability(event.probabilityAfter)}
          </span>
        </div>
      </button>

      {expanded && (
        <div className="border-t px-4 pb-4 pt-3 space-y-4">
          {event.summary && (
            <p className="text-sm text-muted-foreground leading-relaxed">
              {event.summary}
            </p>
          )}

          {event.signals.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Signals
              </h4>
              <div className="space-y-2">
                {event.signals.map((signal) => {
                  const config = sourceTypeConfig[signal.sourceType] ?? {
                    label: signal.sourceType,
                    accent: "bg-muted-foreground",
                  }

                  return (
                    <a
                      key={signal.id}
                      href={signal.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group/signal block rounded-md border border-border/40 bg-muted/30 px-3 py-2.5 transition-colors hover:border-border hover:bg-muted/50"
                    >
                      <div className="flex items-start gap-2">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium leading-snug group-hover/signal:underline underline-offset-2">
                            {signal.title}
                          </p>
                          <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
                            {signal.snippet}
                          </p>
                        </div>
                        <span className="mt-0.5 shrink-0 text-muted-foreground/40 text-xs transition-colors group-hover/signal:text-muted-foreground">
                          ↗
                        </span>
                      </div>
                      <div className="mt-2 flex items-center gap-2 text-[11px] text-muted-foreground/70">
                        <span
                          className={cn(
                            "inline-block size-1.5 rounded-full shrink-0",
                            config.accent
                          )}
                        />
                        <span>{config.label}</span>
                        <span className="text-border">·</span>
                        <span>{signal.source}</span>
                      </div>
                    </a>
                  )
                })}
              </div>
            </div>
          )}

          {event.entities.length > 0 && (
            <div className="space-y-1.5">
              <h4 className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Entities
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {event.entities.map((entity) => (
                  <Badge key={entity.id} variant="outline" className="text-[11px] font-normal">
                    {entity.name}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {event.relatedEvents.length > 0 && (
            <div className="space-y-1.5">
              <h4 className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Related
              </h4>
              <div className="space-y-1">
                {event.relatedEvents.map((rel) => (
                  <div
                    key={rel.id}
                    className="flex items-center gap-2 text-xs text-muted-foreground"
                  >
                    <span className="text-border">→</span>
                    <span>{rel.marketTitle}</span>
                    {rel.sharedEntities && rel.sharedEntities.length > 0 && (
                      <span className="text-muted-foreground/50">
                        via {rel.sharedEntities.join(", ")}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
