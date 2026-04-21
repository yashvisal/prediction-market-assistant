import Link from "next/link"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { formatMovement, timeAgo } from "@/lib/formatters"
import type { TopicSummary } from "@/lib/topic-types"

interface FeedViewProps {
  topics: TopicSummary[]
}

export function FeedView({ topics }: FeedViewProps) {
  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground/60">
          Live Feed
        </p>
        <h1 className="max-w-4xl text-balance text-3xl font-semibold tracking-tight">
          Track the topics that are actually moving.
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
          This feed groups fragmented market signals into evolving topics so you can see
          what is changing before deeper explanation and digest layers are added.
        </p>
      </section>

      {topics.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border/70 bg-muted/20 px-4 py-12 text-center">
          <p className="text-sm text-muted-foreground">
            No topics are available yet. Check the Prediction Hunt connection or seed set.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {topics.map((topic) => (
            <Link key={topic.id} href={`/topics/${encodeURIComponent(topic.id)}`} className="block">
              <Card
                className="h-full border border-border/60 transition-colors hover:border-border hover:bg-accent/20"
                size="sm"
              >
                <CardHeader className="gap-2">
                  <div className="flex items-center justify-between gap-3">
                    <Badge variant="outline" className="capitalize">
                      {topic.category}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {topic.latestUpdateAt ? timeAgo(topic.latestUpdateAt) : "No recent update"}
                    </span>
                  </div>
                  <CardTitle>{topic.title}</CardTitle>
                  <CardDescription>{topic.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
                    <span>{topic.marketCount} source market{topic.marketCount !== 1 ? "s" : ""}</span>
                    <span>{topic.updateCount} update{topic.updateCount !== 1 ? "s" : ""}</span>
                    <span>{topic.signalCount} signal{topic.signalCount !== 1 ? "s" : ""}</span>
                  </div>
                  <div className="text-sm">
                    <span className="text-muted-foreground">Strongest movement</span>{" "}
                    <span className="font-semibold text-foreground">
                      {formatMovement(
                        topic.strongestMovementPercent,
                        topic.strongestMovementDirection
                      )}
                    </span>
                  </div>
                </CardContent>
                <CardFooter className="justify-between text-xs text-muted-foreground">
                  <span>Canonical Topic State</span>
                  <span className="font-mono">v{topic.stateVersion}</span>
                </CardFooter>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
