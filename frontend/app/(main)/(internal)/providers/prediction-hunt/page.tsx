import Link from "next/link"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import type {
  PredictionHuntDeskSnapshotResponse,
  PredictionHuntEventSummary,
  PredictionHuntMarketSummary,
  PredictionHuntOrderbookLevel,
  PredictionHuntRateLimitSnapshot,
} from "@/lib/prediction-hunt-types"
import { formatDate } from "@/lib/formatters"
import {
  getPredictionHuntDeskSnapshot,
  isPredictionHuntApiConfigured,
} from "@/lib/repositories/prediction-hunt"
import { cn } from "@/lib/utils"

interface Props {
  searchParams: Promise<Record<string, string | string[] | undefined>>
}

const compactNumber = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
})

const currencyNumber = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
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

function formatCount(value: number | undefined) {
  if (value === undefined) {
    return "n/a"
  }
  return compactNumber.format(value)
}

function formatMoney(value: number | undefined) {
  if (value === undefined) {
    return "n/a"
  }
  return currencyNumber.format(value)
}

function buildDeskHref(params: {
  selectedMarketId?: string
  selectedMarketPlatform?: string
  marketQuery?: string
  matchQuery?: string
}) {
  const search = new URLSearchParams()
  if (params.selectedMarketId) {
    search.set("marketId", params.selectedMarketId)
  }
  if (params.selectedMarketPlatform) {
    search.set("platform", params.selectedMarketPlatform)
  }
  if (params.marketQuery) {
    search.set("marketQuery", params.marketQuery)
  }
  if (params.matchQuery) {
    search.set("matchQuery", params.matchQuery)
  }
  const query = search.toString()
  return query ? `/providers/prediction-hunt?${query}` : "/providers/prediction-hunt"
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

function RateLimitStrip({ limits }: { limits?: PredictionHuntRateLimitSnapshot }) {
  if (!limits) {
    return null
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <DeskStat label="Req/sec remaining" value={String(limits.perSecondRemaining ?? "n/a")} />
      <DeskStat label="Req/sec limit" value={String(limits.perSecondLimit ?? "n/a")} />
      <DeskStat label="Month remaining" value={String(limits.perMonthRemaining ?? "n/a")} />
      <DeskStat label="Month limit" value={String(limits.perMonthLimit ?? "n/a")} />
    </div>
  )
}

function PlatformStatusStrip({ snapshot }: { snapshot: PredictionHuntDeskSnapshotResponse }) {
  const platforms = Object.entries(snapshot.status.platforms)

  return (
    <Card className="border border-border/70 bg-card/80">
      <CardHeader>
        <CardTitle>Status And Quota</CardTitle>
        <CardDescription>
          Live provider health plus the most recent rate-limit headers observed during this desk load.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
          <DeskStat
            label="API status"
            value={snapshot.status.status}
            tone={snapshot.status.status === "ok" ? "good" : "warn"}
          />
          {platforms.slice(0, 4).map(([platform, item]) => (
            <div key={platform} className="rounded-lg border border-border/60 bg-background/70 px-3 py-2">
              <div className="flex items-center justify-between gap-2">
                <p className="text-[11px] uppercase tracking-[0.18em] text-muted-foreground">{platform}</p>
                <Badge variant="outline">{item.status}</Badge>
              </div>
              <p className="mt-2 font-mono text-sm text-foreground">{formatCount(item.activeMarkets)} active</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {item.lastUpdated ? formatDate(item.lastUpdated) : "No timestamp"}
              </p>
            </div>
          ))}
        </div>
        <RateLimitStrip
          limits={
            snapshot.events.rateLimits ??
            snapshot.matching?.rateLimits ??
            snapshot.searchedMarkets?.rateLimits ??
            snapshot.markets.rateLimits ??
            snapshot.history?.rateLimits ??
            snapshot.orderbook?.rateLimits ??
            snapshot.status.rateLimits
          }
        />
      </CardContent>
    </Card>
  )
}

function EventCard({
  event,
  active,
  selectedMarket,
  marketQuery,
}: {
  event: PredictionHuntEventSummary
  active: boolean
  selectedMarket?: PredictionHuntMarketSummary
  marketQuery?: string
}) {
  return (
    <Link
      href={buildDeskHref({
        selectedMarketId: selectedMarket?.marketId,
        selectedMarketPlatform: selectedMarket?.platform,
        marketQuery,
        matchQuery: event.eventName,
      })}
      className={cn(
        "block rounded-xl border px-4 py-3 transition-colors",
        active
          ? "border-foreground/15 bg-foreground/8"
          : "border-border/60 bg-background/60 hover:border-border hover:bg-muted/30"
      )}
    >
      <div className="flex flex-wrap items-start gap-2">
        <p className="flex-1 text-sm font-medium leading-snug text-foreground">{event.eventName}</p>
        <Badge variant="outline">{event.eventType}</Badge>
        <Badge variant="outline">{event.status}</Badge>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">{event.eventDate}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {event.groups.slice(0, 3).map((group) => (
          <Badge key={`${event.id}-${group.groupId}`} variant="ghost" className="border border-border/40 bg-transparent">
            {group.title} ({group.platformCount})
          </Badge>
        ))}
      </div>
    </Link>
  )
}

function WarningPanel({ warnings }: { warnings: string[] }) {
  if (warnings.length === 0) {
    return null
  }

  return (
    <Card className="border border-amber-500/40 bg-amber-500/5">
      <CardHeader>
        <CardTitle>Upstream Warnings</CardTitle>
        <CardDescription>
          This desk now focuses on the endpoints your key can actually probe. Any warning here is a real upstream limitation, not a frontend failure.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {warnings.map((warning, index) => (
          <p key={`${warning}-${index}`} className="text-sm text-muted-foreground">
            {warning}
          </p>
        ))}
      </CardContent>
    </Card>
  )
}

function EndpointProbeStrip({ snapshot }: { snapshot: PredictionHuntDeskSnapshotResponse }) {
  const searchedCount = snapshot.searchedMarkets?.markets.length ?? 0
  const matchingCount = snapshot.matching?.count ?? 0
  const historyCount = snapshot.history?.candles.length ?? 0

  return (
    <Card className="border border-border/70 bg-card/80">
      <CardHeader>
        <CardTitle>Accessible Endpoint Probe</CardTitle>
        <CardDescription>
          This is the core spike readout: raw market listing, query-based market search, cross-platform matching, and optional depth/history evidence.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <DeskStat label="/status" value="ok" tone="good" />
        <DeskStat label="/markets" value={`${snapshot.markets.markets.length} rows`} tone="good" />
        <DeskStat
          label={`/markets?q=${snapshot.marketQuery ?? "n/a"}`}
          value={`${searchedCount} rows`}
          tone={snapshot.marketQuery ? "good" : "warn"}
        />
        <DeskStat
          label={`/matching-markets?q=${snapshot.matchingQuery ?? "n/a"}`}
          value={snapshot.matching ? `${matchingCount} events` : "not run"}
          tone={snapshot.matching ? "good" : "warn"}
        />
        <DeskStat
          label="History / Orderbook"
          value={`${historyCount} candles / ${snapshot.orderbook ? "book ok" : "book n/a"}`}
          tone={snapshot.history || snapshot.orderbook ? "good" : "warn"}
        />
      </CardContent>
    </Card>
  )
}

function MarketRailItem({
  market,
  active,
  marketQuery,
  matchQuery,
}: {
  market: PredictionHuntMarketSummary
  active: boolean
  marketQuery?: string
  matchQuery?: string
}) {
  return (
    <Link
      href={buildDeskHref({
        selectedMarketId: market.marketId,
        selectedMarketPlatform: market.platform,
        marketQuery,
        matchQuery,
      })}
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
          {market.platform}
        </Badge>
      </div>
      <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-muted-foreground">
        <span>{market.category ?? "uncategorized"}</span>
        <span>{market.status}</span>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2 text-[11px]">
        <Badge variant="outline">last {formatProbability(market.price.lastPrice)}</Badge>
        <Badge variant="outline">liq {formatMoney(market.price.liquidity)}</Badge>
      </div>
    </Link>
  )
}

function MarketSamplePanel({
  title,
  description,
  markets,
  selectedMarket,
  marketQuery,
  matchQuery,
}: {
  title: string
  description: string
  markets: PredictionHuntMarketSummary[]
  selectedMarket?: PredictionHuntMarketSummary
  marketQuery?: string
  matchQuery?: string
}) {
  return (
    <Card className="border border-border/70 bg-card/80">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {markets.length === 0 ? (
          <p className="text-sm text-muted-foreground">No rows returned.</p>
        ) : (
          markets.map((market) => (
            <MarketRailItem
              key={`${title}-${market.platform}-${market.marketId}`}
              market={market}
              active={
                selectedMarket?.marketId === market.marketId &&
                selectedMarket?.platform === market.platform
              }
              marketQuery={marketQuery}
              matchQuery={matchQuery}
            />
          ))
        )}
      </CardContent>
    </Card>
  )
}

function MatchingPanel({ snapshot }: { snapshot: PredictionHuntDeskSnapshotResponse }) {
  if (!snapshot.matchingQuery) {
    return null
  }

  const matching = snapshot.matching
  if (!matching || matching.events.length === 0) {
    return (
      <Card className="border border-border/70 bg-card/80">
        <CardHeader>
          <CardTitle>Matching Probe</CardTitle>
          <CardDescription>
            No matched groups came back for `{snapshot.matchingQuery}`.
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card className="border border-border/70 bg-card/80">
      <CardHeader>
        <CardTitle>Matching Probe</CardTitle>
        <CardDescription>
          `matching-markets` is the most useful semantic layer you currently have access to. This is where Prediction Hunt starts looking like the grouped market/event model you actually want.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {matching.events.map((event, index) => {
          const groups = Array.isArray(event.groups) ? event.groups : []
          return (
            <div
              key={`e-${index}-${event.title}`}
              className="flex flex-col gap-3 rounded-xl border border-border/60 bg-background/60 px-4 py-3"
            >
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-medium text-foreground">{event.title}</p>
                {event.eventType ? <Badge variant="outline">{event.eventType}</Badge> : null}
                {event.confidence ? <Badge variant="outline">{event.confidence}</Badge> : null}
                {event.eventDate ? <Badge variant="outline">{event.eventDate}</Badge> : null}
              </div>
              {groups.map((group, groupIndex) => (
                <div key={`g-${index}-${groupIndex}-${group.title}`} className="rounded-lg border border-border/50 px-3 py-3">
                  <p className="text-sm font-medium text-foreground">{group.title}</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(group.markets ?? []).map((market) => (
                      <a
                        key={`${group.title}-${market.source}-${market.id}`}
                        href={market.sourceUrl ?? "#"}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-2 rounded-full border border-border/50 px-3 py-1 text-xs text-muted-foreground hover:text-foreground"
                      >
                        <span className="font-medium">{market.source}</span>
                        <span className="font-mono">{market.id}</span>
                      </a>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}

function MarketSummaryCard({ market }: { market?: PredictionHuntMarketSummary }) {
  if (!market) {
    return null
  }

  return (
    <Card className="border border-border/70 bg-card/80">
      <CardHeader>
        <CardTitle>Selected Contract Probe</CardTitle>
        <CardDescription>
          This is one concrete contract chosen from the returned rows so the desk can test downstream history and orderbook access.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-base font-medium text-foreground">{market.title}</p>
          <Badge variant="outline">{market.platform}</Badge>
          <Badge variant="outline">{market.status}</Badge>
          {market.category ? <Badge variant="outline">{market.category}</Badge> : null}
        </div>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <DeskStat label="Last" value={formatProbability(market.price.lastPrice)} tone="good" />
          <DeskStat
            label="YES bid/ask"
            value={`${formatProbability(market.price.yesBid)} / ${formatProbability(market.price.yesAsk)}`}
          />
          <DeskStat label="Volume" value={formatCount(market.price.volume)} />
          <DeskStat label="Liquidity" value={formatMoney(market.price.liquidity)} />
        </div>
        <div className="flex flex-wrap gap-3 text-sm text-muted-foreground">
          <span className="font-mono">marketId: {market.marketId}</span>
          {market.expirationDate ? <span>expires {formatDate(market.expirationDate)}</span> : null}
          {market.sourceUrl ? (
            <a href={market.sourceUrl} target="_blank" rel="noreferrer" className="underline underline-offset-4">
              Source market
            </a>
          ) : null}
        </div>
      </CardContent>
    </Card>
  )
}

function HistoryTable({ snapshot }: { snapshot: PredictionHuntDeskSnapshotResponse }) {
  const history = snapshot.history
  if (!history) {
    return (
      <Card className="border border-border/70 bg-card/80">
        <CardHeader>
          <CardTitle>Price History Probe</CardTitle>
          <CardDescription>No history request was run or no usable response came back.</CardDescription>
        </CardHeader>
      </Card>
    )
  }

  const candles = history.candles.slice(-10).reverse()

  return (
    <Card className="border border-border/70 bg-card/80">
      <CardHeader>
        <CardTitle>Price History Probe</CardTitle>
        <CardDescription>
          Last ten {history.interval} candles for the selected contract. Empty candles means the endpoint works but the chosen contract has no populated history in the returned range.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {candles.length === 0 ? (
          <p className="text-sm text-muted-foreground">No candles returned for this market.</p>
        ) : (
          <div className="overflow-hidden rounded-lg border border-border/60">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/40 text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 font-medium">Time</th>
                  <th className="px-3 py-2 font-medium">Close</th>
                  <th className="px-3 py-2 font-medium">Mid</th>
                  <th className="px-3 py-2 font-medium">Volume</th>
                  <th className="px-3 py-2 font-medium">$ Volume</th>
                </tr>
              </thead>
              <tbody>
                {candles.map((candle) => (
                  <tr key={candle.timestamp} className="border-t border-border/60">
                    <td className="px-3 py-2 font-mono text-muted-foreground">{formatDate(candle.timestamp)}</td>
                    <td className="px-3 py-2 font-mono text-foreground">{formatProbability(candle.close)}</td>
                    <td className="px-3 py-2 font-mono text-foreground">{formatProbability(candle.mid)}</td>
                    <td className="px-3 py-2 font-mono text-muted-foreground">{formatCount(candle.volume)}</td>
                    <td className="px-3 py-2 font-mono text-muted-foreground">{formatMoney(candle.dollarVolume)}</td>
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

function OrderbookLevels({
  title,
  items,
  tone,
}: {
  title: string
  items: PredictionHuntOrderbookLevel[]
  tone: "bid" | "ask"
}) {
  return (
    <div className="rounded-xl border border-border/60 bg-background/60">
      <div className="flex items-center justify-between border-b border-border/60 px-3 py-2">
        <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">{title}</p>
        <Badge
          variant="outline"
          className={
            tone === "bid"
              ? "border-emerald-500/40 text-emerald-700 dark:text-emerald-300"
              : "border-amber-500/40 text-amber-700 dark:text-amber-300"
          }
        >
          top {items.length}
        </Badge>
      </div>
      <div className="divide-y divide-border/50">
        {items.map((item, index) => (
          <div key={`${title}-${item.price}-${item.size}-${index}`} className="grid grid-cols-2 gap-3 px-3 py-2 text-sm">
            <span className="font-mono text-foreground">{formatProbability(item.price)}</span>
            <span className="text-right font-mono text-muted-foreground">{formatCount(item.size)}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function OrderbookPanel({ snapshot }: { snapshot: PredictionHuntDeskSnapshotResponse }) {
  const orderbook = snapshot.orderbook
  if (!orderbook) {
    return (
      <Card className="border border-border/70 bg-card/80">
        <CardHeader>
          <CardTitle>Orderbook Probe</CardTitle>
          <CardDescription>
            No orderbook snapshot came back for the selected contract. This can mean unsupported platform, missing source depth, or upstream rate limiting.
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card className="border border-border/70 bg-card/80">
      <CardHeader>
        <CardTitle>Orderbook Probe</CardTitle>
        <CardDescription>
          Snapshot at {orderbook.timestamp ? formatDate(orderbook.timestamp) : "unknown time"}.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4 xl:grid-cols-2">
        <div className="space-y-3">
          <p className="text-sm font-medium text-foreground">YES ladder</p>
          <div className="grid gap-3 md:grid-cols-2">
            <OrderbookLevels title="YES bids" items={orderbook.yes.bids.slice(0, 5)} tone="bid" />
            <OrderbookLevels title="YES asks" items={orderbook.yes.asks.slice(0, 5)} tone="ask" />
          </div>
        </div>
        <div className="space-y-3">
          <p className="text-sm font-medium text-foreground">NO ladder</p>
          <div className="grid gap-3 md:grid-cols-2">
            <OrderbookLevels title="NO bids" items={orderbook.no.bids.slice(0, 5)} tone="bid" />
            <OrderbookLevels title="NO asks" items={orderbook.no.asks.slice(0, 5)} tone="ask" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default async function PredictionHuntProviderPage({ searchParams }: Props) {
  const params = await searchParams
  const configured = isPredictionHuntApiConfigured()
  const selectedMarketId = stringValue(params.marketId)
  const selectedMarketPlatform = stringValue(params.platform)
  const marketQuery = stringValue(params.marketQuery) ?? "trump"
  const matchQuery = stringValue(params.matchQuery) ?? marketQuery

  if (!configured) {
    return (
      <div className="space-y-4">
        <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Internal Provider Spike</p>
        <h1 className="text-2xl font-semibold tracking-tight">Prediction Hunt Desk</h1>
        <p className="max-w-3xl text-sm leading-relaxed text-muted-foreground">
          This page needs `PREDICTION_MARKET_API_BASE_URL`, and the backend needs `PREDICTION_HUNT_API_KEY`.
        </p>
      </div>
    )
  }

  let snapshot: PredictionHuntDeskSnapshotResponse | null = null
  let errorMessage: string | null = null

  try {
    snapshot = await getPredictionHuntDeskSnapshot({
      selectedMarketId,
      selectedMarketPlatform,
      marketQuery,
      matchQuery,
    })
  } catch (error) {
    errorMessage = error instanceof Error ? error.message : "Failed to load Prediction Hunt data."
  }

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Internal Provider Spike</p>
        <h1 className="text-2xl font-semibold tracking-tight">Prediction Hunt Desk</h1>
        <p className="max-w-3xl text-sm leading-relaxed text-muted-foreground">
          This version is intentionally endpoint-first. It does not assume Prediction Hunt’s `events`
          model matches ours. Instead it shows the endpoints your key can really use and what each one
          returns: raw market rows, searched market rows, grouped matching results, and optional
          history/orderbook evidence on one selected contract.
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

      {snapshot ? (
        <>
          <PlatformStatusStrip snapshot={snapshot} />
          <WarningPanel warnings={snapshot.warnings} />
          <EndpointProbeStrip snapshot={snapshot} />

          <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
            <Card className="border border-border/70 bg-card/80">
              <CardHeader>
                <CardTitle>Event Sample</CardTitle>
                <CardDescription>
                  This is the higher-level event/group surface from Prediction Hunt. It is closer to how we think about meaningful market clusters than the raw leaf-contract rows below.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {snapshot.events.events.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No event rows returned.</p>
                ) : (
                  snapshot.events.events.map((event) => (
                    <EventCard
                      key={event.id}
                      event={event}
                      active={snapshot.matchingQuery === event.eventName}
                      selectedMarket={snapshot.selectedMarket}
                      marketQuery={snapshot.marketQuery}
                    />
                  ))
                )}
              </CardContent>
            </Card>

            <MatchingPanel snapshot={snapshot} />
          </div>

          <div className="grid gap-6 xl:grid-cols-2">
            <MarketSamplePanel
              title="Raw /markets Sample"
              description="This is the provider’s plain active market listing. Read these as raw leaf contract rows, not as our final event/market abstraction."
              markets={snapshot.markets.markets}
              selectedMarket={snapshot.selectedMarket}
              marketQuery={snapshot.marketQuery}
              matchQuery={snapshot.matchingQuery}
            />
            <MarketSamplePanel
              title={`Search Probe: /markets?q=${snapshot.marketQuery ?? ""}`}
              description="This simulates the practical search surface you can actually use today. It is useful for probing how Prediction Hunt returns sibling contracts and title matching."
              markets={snapshot.searchedMarkets?.markets ?? []}
              selectedMarket={snapshot.selectedMarket}
              marketQuery={snapshot.marketQuery}
              matchQuery={snapshot.matchingQuery}
            />
          </div>

          <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
            <MarketSummaryCard market={snapshot.selectedMarket} />
            <div className="space-y-6">
              <HistoryTable snapshot={snapshot} />
              <OrderbookPanel snapshot={snapshot} />
            </div>
          </div>
        </>
      ) : null}
    </div>
  )
}
