import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { formatMovement, formatProbability, timeAgo } from "@/lib/formatters"
import type { TopicDetail } from "@/lib/topic-types"

import { TopicUpdateCard } from "./topic-update-card"

export function TopicDetailView({ topic }: { topic: TopicDetail }) {
  return (
    <div className="space-y-8">
      <section className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline" className="capitalize">
            {topic.category}
          </Badge>
          <span className="text-xs text-muted-foreground">
            {topic.latestUpdateAt ? timeAgo(topic.latestUpdateAt) : "No recent update"}
          </span>
          <span className="text-xs font-mono text-muted-foreground">v{topic.stateVersion}</span>
        </div>
        <div className="space-y-2">
          <h1 className="max-w-4xl text-balance text-3xl font-semibold tracking-tight">
            {topic.title}
          </h1>
          <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
            {topic.description}
          </p>
        </div>
        <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
          <span>{topic.marketCount} source market{topic.marketCount !== 1 ? "s" : ""}</span>
          <span>{topic.updateCount} update{topic.updateCount !== 1 ? "s" : ""}</span>
          <span>{topic.signalCount} signal{topic.signalCount !== 1 ? "s" : ""}</span>
          <span>
            Strongest move{" "}
            {formatMovement(topic.strongestMovementPercent, topic.strongestMovementDirection ?? "up")}
          </span>
        </div>
      </section>

      <section className="space-y-4" aria-labelledby="source-markets-heading">
        <h2
          id="source-markets-heading"
          className="text-sm font-medium uppercase tracking-wider text-muted-foreground"
        >
          Source Markets
        </h2>
        <div className="grid gap-3 md:grid-cols-2">
          {topic.markets.map((market) => (
            <Card key={market.id} size="sm" className="border border-border/60">
              <CardHeader className="gap-2">
                <div className="flex items-center justify-between gap-3">
                  <Badge variant="outline" className="capitalize">
                    {market.category}
                  </Badge>
                  <span className="text-xs capitalize text-muted-foreground">{market.status}</span>
                </div>
                <CardTitle>{market.title}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-muted-foreground">
                <div className="flex items-center justify-between gap-3">
                  <span>Current probability</span>
                  <span className="font-semibold text-foreground">
                    {formatProbability(market.currentProbability)}
                  </span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>Current movement</span>
                  <span className="font-semibold text-foreground">
                    {formatMovement(
                      Math.abs(market.currentMovementPercent),
                      market.currentDirection
                    )}
                  </span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>Attached updates</span>
                  <span className="text-foreground">{market.eventCount}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="space-y-4" aria-labelledby="topic-updates-heading">
        <h2
          id="topic-updates-heading"
          className="text-sm font-medium uppercase tracking-wider text-muted-foreground"
        >
          Topic Updates
        </h2>
        {topic.updates.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border/70 bg-muted/20 px-4 py-10 text-center">
            <p className="text-sm text-muted-foreground">
              No updates were returned for this topic yet.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {topic.updates.map((update) => (
              <TopicUpdateCard key={update.id} update={update} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
