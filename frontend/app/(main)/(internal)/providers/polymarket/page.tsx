import Link from "next/link"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import type {
  DomeEventSummary,
  DomeMarketCoverageSummary,
  DomeMarketDetailResponse,
  DomeMarketSampleItem,
  DomeOrderbookLevel,
} from "@/lib/dome-types"
import { formatDate } from "@/lib/formatters"
import {
  getDomePolymarketDiscovery,
  getDomePolymarketMarket,
  isDomeApiConfigured,
  listDomePolymarketEvents,
} from "@/lib/repositories/dome"
import { cn } from "@/lib/utils"

interface Props {
  searchParams: Promise<Record<string, string | string[] | undefined>>
}

const compactNumber = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
})

function stringValue(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value
}

function formatProbability(value: number | undefined) {
  if (value === undefined) {
    return "n/a"
  }
  return `${Math.round(value * 100)}%`
}

function formatCount(value: number) {
  return compactNumber.format(value)
}

function formatRatio(value: number) {
  return `${Math.round(value * 100)}%`
}

function buildMarketHref(marketSlug: string) {
  return `/providers/polymarket?marketSlug=${encodeURIComponent(marketSlug)}`
}

function DeskStat({
  label,
  value,
  tone = "default",
}: {
  label: string
  value: string
  tone?: "default" | "good" | "warn"
}) {
  return (
    <div className="rounded-lg border border-border/60 bg-background/70 px-3 py-2">
      <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
      <p
        className={cn(
          "mt-1 font-mono text-sm tabular-nums text-foreground",
          tone === "good" && "text-emerald-600 dark:text-emerald-300",
          tone === "warn" && "text-amber-600 dark:text-amber-300"
        )}
      >
        {value}
      </p>
    </div>
  )
}

function MarketRailItem({
  item,
  active,
}: {
  item: DomeMarketSampleItem
  active: boolean
}) {
  const { market, quality } = item
  return (
    <Link
      href={buildMarketHref(market.marketSlug)}
      className={cn(
        "block rounded-xl border px-3 py-3 transition-colors",
        active
          ? "border-foreground/15 bg-foreground/8"
          : "border-border/60 bg-background/60 hover:border-border hover:bg-muted/30"
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="line-clamp-2 text-sm font-medium leading-snug text-foreground">{market.title}</p>
        <Badge variant="outline" className="shrink-0 font-mono">
          {market.status}
        </Badge>
      </div>
      <div className="mt-2 flex flex-wrap gap-3 font-mono text-[11px] text-muted-foreground">
        <span>1w {formatCount(market.volume1Week)}</span>
        <span>total {formatCount(market.volumeTotal)}</span>
      </div>
      <div className="mt-2 flex flex-wrap gap-2 text-[11px]">
        <Badge variant="outline" className={quality.hasPrices ? "border-emerald-500/40" : "border-amber-500/40"}>
          prices {quality.hasPrices ? "yes" : "no"}
        </Badge>
        <Badge
          variant="outline"
          className={quality.hasRecentTrades ? "border-emerald-500/40" : "border-amber-500/40"}
        >
          trades {quality.recentTradeCount}
        </Badge>
        <Badge variant="outline" className={quality.hasOrderbook ? "border-emerald-500/40" : "border-amber-500/40"}>
          book {quality.hasOrderbook ? "yes" : "no"}
        </Badge>
      </div>
      <div className="mt-2 flex flex-wrap gap-1">
        {market.tags.slice(0, 3).map((tag) => (
          <Badge key={tag} variant="ghost" className="border border-border/40 bg-transparent">
            {tag}
          </Badge>
        ))}
      </div>
    </Link>
  )
}

function CoverageStrip({ coverage }: { coverage: DomeMarketCoverageSummary }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      <DeskStat label="Sample size" value={String(coverage.sampleSize)} />
      <DeskStat label="Price coverage" value={formatRatio(coverage.priceCoverageRatio)} tone="good" />
      <DeskStat label="Trade coverage" value={formatRatio(coverage.tradeCoverageRatio)} tone="good" />
      <DeskStat label="Orderbook coverage" value={formatRatio(coverage.orderbookCoverageRatio)} />
      <DeskStat
        label="Avg spread"
        value={coverage.averageSpread !== undefined ? formatProbability(coverage.averageSpread) : "n/a"}
        tone={coverage.averageSpread !== undefined ? "good" : "warn"}
      />
    </div>
  )
}

function EventDiscoveryStrip({ events }: { events: DomeEventSummary[] }) {
  if (events.length === 0) {
    return null
  }

  return (
    <Card className="border border-border/70 bg-card/80">
      <CardHeader>
        <CardTitle>Event-First Discovery</CardTitle>
        <CardDescription>
          Higher-level Polymarket events are often the better daily starting point than isolated raw contracts.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {events.map((event) => (
          <div
            key={event.eventSlug}
            className="rounded-xl border border-border/60 bg-background/60 px-4 py-3"
          >
            <div className="flex flex-wrap items-center gap-2">
              <p className="font-medium text-foreground">{event.title}</p>
              <Badge variant="outline">{event.status}</Badge>
              <Badge variant="outline">{formatCount(event.marketCount)} markets</Badge>
              <Badge variant="outline">vol {formatCount(event.volumeFiatAmount)}</Badge>
            </div>
            {event.subtitle ? (
              <p className="mt-2 text-sm text-muted-foreground">{event.subtitle}</p>
            ) : null}
            <div className="mt-2 flex flex-wrap gap-2">
              {event.markets.slice(0, 3).map((market) => (
                <Badge key={market.marketSlug} variant="ghost" className="border border-border/40 bg-transparent">
                  {market.title}
                </Badge>
              ))}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

function OrderbookColumn({
  title,
  items,
  tone,
}: {
  title: string
  items: DomeOrderbookLevel[]
  tone: "bid" | "ask"
}) {
  return (
    <div className="rounded-xl border border-border/60 bg-background/60">
      <div className="flex items-center justify-between border-b border-border/60 px-3 py-2">
        <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">{title}</p>
        <Badge
          variant="outline"
          className={cn(
            tone === "bid"
              ? "border-emerald-500/40 text-emerald-700 dark:text-emerald-300"
              : "border-amber-500/40 text-amber-700 dark:text-amber-300"
          )}
        >
          top 5
        </Badge>
      </div>
      <div className="divide-y divide-border/50">
        {items.map((item) => (
          <div key={`${title}-${item.price}-${item.size}`} className="grid grid-cols-2 gap-3 px-3 py-2 text-sm">
            <span className="font-mono text-foreground">{formatProbability(item.price)}</span>
            <span className="text-right font-mono text-muted-foreground">{formatCount(item.size)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function PriceHistoryTable({ detail }: { detail: DomeMarketDetailResponse }) {
  return (
    <Card className="border border-border/70 bg-card/80">
      <CardHeader>
        <CardTitle>Sampled Price History</CardTitle>
        <CardDescription>
          Quick read on whether this market has enough continuity for ongoing analysis, not just a current quote.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {detail.priceHistory.length === 0 ? (
          <p className="text-sm text-muted-foreground">No sampled history returned.</p>
        ) : (
          <div className="overflow-hidden rounded-lg border border-border/60">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/40 text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 font-medium">Sample</th>
                  <th className="px-3 py-2 font-medium">At</th>
                  <th className="px-3 py-2 font-medium">{detail.market.sideA.label}</th>
                  <th className="px-3 py-2 font-medium">{detail.market.sideB.label}</th>
                </tr>
              </thead>
              <tbody>
                {detail.priceHistory.map((point) => (
                  <tr key={`${point.label}-${point.atTime}`} className="border-t border-border/60">
                    <td className="px-3 py-2 font-mono uppercase text-muted-foreground">{point.label}</td>
                    <td className="px-3 py-2 font-mono text-muted-foreground">{formatDate(point.atTime)}</td>
                    <td className="px-3 py-2 font-mono text-foreground">
                      {formatProbability(point.sideAPrice)}
                    </td>
                    <td className="px-3 py-2 font-mono text-foreground">
                      {formatProbability(point.sideBPrice)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function TradeTable({ detail }: { detail: DomeMarketDetailResponse }) {
  return (
    <Card className="border border-border/70 bg-card/80">
      <CardHeader>
        <CardTitle>Recent Trades</CardTitle>
        <CardDescription>
          Evidence of actual flow for this market, not just listed metadata.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {detail.recentTrades.length === 0 ? (
          <p className="text-sm text-muted-foreground">No recent trades returned.</p>
        ) : (
          <div className="overflow-hidden rounded-lg border border-border/60">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/40 text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 font-medium">Time</th>
                  <th className="px-3 py-2 font-medium">Side</th>
                  <th className="px-3 py-2 font-medium">Token</th>
                  <th className="px-3 py-2 font-medium">Price</th>
                  <th className="px-3 py-2 font-medium">Shares</th>
                </tr>
              </thead>
              <tbody>
                {detail.recentTrades.map((trade, index) => (
                  <tr
                    key={`${trade.txHash}-${trade.tokenId}-${trade.side}-${index}`}
                    className="border-t border-border/60"
                  >
                    <td className="px-3 py-2 font-mono text-muted-foreground">{formatDate(trade.timestamp)}</td>
                    <td className="px-3 py-2">
                      <Badge
                        variant="outline"
                        className={cn(
                          trade.side === "BUY"
                            ? "border-emerald-500/40 text-emerald-700 dark:text-emerald-300"
                            : "border-red-500/40 text-red-600 dark:text-red-300"
                        )}
                      >
                        {trade.side}
                      </Badge>
                    </td>
                    <td className="px-3 py-2 text-foreground">{trade.tokenLabel}</td>
                    <td className="px-3 py-2 font-mono text-foreground">{formatProbability(trade.price)}</td>
                    <td className="px-3 py-2 font-mono text-muted-foreground">
                      {formatCount(trade.sharesNormalized)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default async function PolymarketProviderPage({ searchParams }: Props) {
  const params = await searchParams
  const configured = isDomeApiConfigured()
  const requestedSlug = stringValue(params.marketSlug)

  if (!configured) {
    return (
      <div className="space-y-4">
        <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Internal Provider Spike</p>
        <h1 className="text-2xl font-semibold tracking-tight">Dome Polymarket Desk</h1>
        <p className="max-w-3xl text-sm leading-relaxed text-muted-foreground">
          This page needs `PREDICTION_MARKET_API_BASE_URL`, and the backend needs a
          configured `DOME_API_KEY`.
        </p>
      </div>
    )
  }

  let discoveryResponse = null
  let eventsResponse = null
  let detail: DomeMarketDetailResponse | null = null
  let errorMessage: string | null = null

  try {
    if (requestedSlug) {
      const [sampleResponse, eventsList, marketDetail] = await Promise.all([
        getDomePolymarketDiscovery(5),
        listDomePolymarketEvents(5, "open"),
        getDomePolymarketMarket(requestedSlug),
      ])
      discoveryResponse = sampleResponse
      eventsResponse = eventsList
      detail = marketDetail
    } else {
      const [sampleResponse, eventsList] = await Promise.all([
        getDomePolymarketDiscovery(5),
        listDomePolymarketEvents(5, "open"),
      ])
      discoveryResponse = sampleResponse
      eventsResponse = eventsList
      const firstSlug = discoveryResponse.items[0]?.market.marketSlug
      detail = firstSlug ? await getDomePolymarketMarket(firstSlug) : null
    }
  } catch (error) {
    errorMessage = error instanceof Error ? error.message : "Failed to load Dome market data."
  }

  const discoveryItems = discoveryResponse?.items ?? []
  const coverage = discoveryResponse?.coverage
  const events = eventsResponse?.items ?? []
  const activeSlug = detail?.market.marketSlug ?? requestedSlug ?? ""

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Internal Provider Spike</p>
        <h1 className="text-2xl font-semibold tracking-tight">Dome Polymarket Desk</h1>
        <p className="max-w-3xl text-sm leading-relaxed text-muted-foreground">
          This version is meant to look closer to daily product use: discover a small recent-open sample,
          see how often those markets actually have prices, trades, and depth, then inspect one market for
          continuity over time. That gives us a much better answer than a single raw payload.
        </p>
      </section>

      {errorMessage ? (
        <Card className="border border-red-500/40 bg-red-500/5">
          <CardHeader>
            <CardTitle>Provider Error</CardTitle>
            <CardDescription>{errorMessage}</CardDescription>
          </CardHeader>
        </Card>
      ) : null}

      {coverage ? (
        <Card className="border border-border/70 bg-card/80">
          <CardHeader>
            <CardTitle>Discovery Coverage Sample</CardTitle>
            <CardDescription>
              Recent-market sample sized for quick iteration: are most markets populated enough to support ranking and analysis?
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <CoverageStrip coverage={coverage} />
            <p className="text-sm leading-relaxed text-muted-foreground">
              A stronger provider should keep these coverage ratios high across a recency-based sample, not just on one cherry-picked market.
            </p>
          </CardContent>
        </Card>
      ) : null}

      <EventDiscoveryStrip events={events} />

      <div className="grid gap-5 xl:grid-cols-[320px_minmax(0,1fr)]">
        <Card className="border border-border/70 bg-card/80">
          <CardHeader>
            <CardTitle>Discovery Shortlist</CardTitle>
            <CardDescription>
              Recent markets annotated with whether Dome returns live-enough evidence for each one.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {discoveryItems.length === 0 ? (
              <p className="text-sm text-muted-foreground">No markets returned.</p>
            ) : (
              discoveryItems.map((item) => (
                <MarketRailItem
                  key={item.market.marketSlug}
                  item={item}
                  active={item.market.marketSlug === activeSlug}
                />
              ))
            )}
          </CardContent>
        </Card>

        {detail ? (
          <div className="space-y-5">
            <Card className="border border-border/70 bg-card/80">
              <CardHeader>
                <CardTitle className="max-w-4xl text-balance">{detail.market.title}</CardTitle>
                <CardDescription className="font-mono text-[11px]">
                  {detail.market.marketSlug}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">{detail.market.status}</Badge>
                  <Badge variant="outline">1w {formatCount(detail.market.volume1Week)}</Badge>
                  <Badge variant="outline">total {formatCount(detail.market.volumeTotal)}</Badge>
                  {detail.market.tags.slice(0, 6).map((tag) => (
                    <Badge key={tag} variant="ghost" className="border border-border/40 bg-transparent">
                      {tag}
                    </Badge>
                  ))}
                </div>

                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  <DeskStat
                    label={detail.market.sideA.label}
                    value={formatProbability(detail.market.sideA.price)}
                    tone="good"
                  />
                  <DeskStat
                    label={detail.market.sideB.label}
                    value={formatProbability(detail.market.sideB.price)}
                  />
                  <DeskStat
                    label="Recent trades"
                    value={String(detail.quality.recentTradeCount)}
                    tone={detail.quality.hasRecentTrades ? "good" : "warn"}
                  />
                  <DeskStat
                    label="Spread"
                    value={formatProbability(detail.quality.spread)}
                    tone={detail.quality.spread !== undefined ? "good" : "warn"}
                  />
                </div>

                <Separator />

                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
                  <DeskStat label="Market age" value={`${detail.quality.marketAgeHours}h`} />
                  <DeskStat label="Recent shares" value={formatCount(detail.quality.totalRecentShares)} />
                  <DeskStat
                    label="Best bid"
                    value={formatProbability(detail.quality.bestBid)}
                    tone={detail.quality.bestBid !== undefined ? "good" : "warn"}
                  />
                  <DeskStat
                    label="Best ask"
                    value={formatProbability(detail.quality.bestAsk)}
                    tone={detail.quality.bestAsk !== undefined ? "good" : "warn"}
                  />
                  <DeskStat
                    label="Last trade"
                    value={detail.quality.lastTradeAt ? formatDate(detail.quality.lastTradeAt) : "n/a"}
                  />
                </div>
              </CardContent>
            </Card>

            <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
              <TradeTable detail={detail} />
              <PriceHistoryTable detail={detail} />
            </div>

            <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
              <Card className="border border-border/70 bg-card/80">
                <CardHeader>
                  <CardTitle>Orderbook Snapshot</CardTitle>
                  <CardDescription>
                    Top-of-book depth from Dome for the selected market side.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {detail.orderbook ? (
                    <>
                      <div className="grid gap-3 sm:grid-cols-2">
                        <DeskStat label="Indexed at" value={formatDate(detail.orderbook.indexedAt)} />
                        <DeskStat label="Snapshot time" value={formatDate(detail.orderbook.timestamp)} />
                        <DeskStat label="Bid levels" value={String(detail.orderbook.bidDepthLevels)} />
                        <DeskStat label="Ask levels" value={String(detail.orderbook.askDepthLevels)} />
                      </div>
                      <div className="grid gap-4 sm:grid-cols-2">
                        <OrderbookColumn title="Bids" items={detail.orderbook.topBids} tone="bid" />
                        <OrderbookColumn title="Asks" items={detail.orderbook.topAsks} tone="ask" />
                      </div>
                    </>
                  ) : (
                    <p className="text-sm text-muted-foreground">No orderbook snapshot returned.</p>
                  )}
                </CardContent>
              </Card>
            </div>

            <Card className="border border-border/70 bg-card/80">
              <CardHeader>
                <CardTitle>Raw Payload Evidence</CardTitle>
                <CardDescription>
                  Raw market, price, trade, and orderbook data for quick provider sanity checks.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <pre className="max-h-[32rem] overflow-auto rounded-xl border border-border/60 bg-background/70 p-4 font-mono text-[11px] leading-relaxed text-muted-foreground">
                  {JSON.stringify(detail.raw, null, 2)}
                </pre>
              </CardContent>
            </Card>
          </div>
        ) : (
          <Card className="border border-border/70 bg-card/80">
            <CardHeader>
              <CardTitle>No market selected</CardTitle>
              <CardDescription>Pick a recent market to inspect provider quality.</CardDescription>
            </CardHeader>
          </Card>
        )}
      </div>
    </div>
  )
}
