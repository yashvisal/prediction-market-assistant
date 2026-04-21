"use client"

import * as React from "react"

import { Badge } from "@/components/ui/badge"
import {
  getMovementDirectionLabel,
  getMovementDirectionSymbol,
} from "@/lib/domain/markets"
import { formatDateRange, formatMovement } from "@/lib/formatters"
import type { TopicUpdate } from "@/lib/topic-types"
import { cn } from "@/lib/utils"

const sourceTypeConfig: Record<string, { label: string; accent: string }> = {
  news: { label: "News", accent: "bg-blue-500" },
  tweet: { label: "Social", accent: "bg-sky-400" },
  official: { label: "Official", accent: "bg-amber-500" },
  analysis: { label: "Analysis", accent: "bg-violet-500" },
}

export function TopicUpdateCard({ update }: { update: TopicUpdate }) {
  const [expanded, setExpanded] = React.useState(false)

  return (
    <div className="rounded-lg border border-border/60 bg-card">
      <button
        type="button"
        aria-expanded={expanded}
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-accent/30 focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
      >
        <span aria-hidden="true" className="text-xs text-muted-foreground select-none">
          {expanded ? "▾" : "▸"}
        </span>

        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium leading-snug">{update.title}</p>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {update.marketTitle} · {formatDateRange(update.startTime, update.endTime)}
          </p>
        </div>

        <span
          aria-label={`${getMovementDirectionLabel(update.direction)} ${formatMovement(
            update.movementPercent,
            update.direction
          )}`}
          className={cn(
            "shrink-0 text-sm font-semibold tabular-nums",
            update.direction === "up" ? "text-emerald-600" : "text-red-500"
          )}
        >
          <span aria-hidden="true" className="mr-1">
            {getMovementDirectionSymbol(update.direction)}
          </span>
          {formatMovement(update.movementPercent, update.direction)}
        </span>
      </button>

      {expanded ? (
        <div className="space-y-4 border-t px-4 pb-4 pt-3">
          {update.summary ? (
            <p className="text-sm leading-relaxed text-muted-foreground">{update.summary}</p>
          ) : null}

          {update.signals.length > 0 ? (
            <div className="space-y-2">
              <h4 className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Signals
              </h4>
              <div className="space-y-2">
                {update.signals.map((signal) => {
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
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium leading-snug underline-offset-2 group-hover/signal:underline">
                            {signal.title}
                          </p>
                          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                            {signal.snippet}
                          </p>
                        </div>
                        <span className="mt-0.5 shrink-0 text-xs text-muted-foreground/40 transition-colors group-hover/signal:text-muted-foreground">
                          ↗
                        </span>
                      </div>
                      <div className="mt-2 flex items-center gap-2 text-[11px] text-muted-foreground/70">
                        <span className={cn("inline-block size-1.5 shrink-0 rounded-full", config.accent)} />
                        <span>{config.label}</span>
                        <span className="text-border">·</span>
                        <span>{signal.source}</span>
                      </div>
                    </a>
                  )
                })}
              </div>
            </div>
          ) : null}

          {update.entities.length > 0 ? (
            <div className="space-y-1.5">
              <h4 className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Entities
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {update.entities.map((entity) => (
                  <Badge key={entity.id} variant="outline" className="text-[11px] font-normal">
                    {entity.name}
                  </Badge>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
