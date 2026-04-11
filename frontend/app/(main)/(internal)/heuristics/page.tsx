import Link from "next/link"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import type {
  EventCandidateDebug,
  HeuristicEventOption,
  HeuristicEvaluationResponse,
  SignalCandidateDebug,
  ValidationMarketOption,
} from "@/lib/heuristics-types"
import { formatDate, formatProbability } from "@/lib/formatters"
import {
  getHeuristicEvaluation,
  isHeuristicsApiConfigured,
  listHeuristicMarkets,
  type HeuristicOverrideParams,
} from "@/lib/repositories/heuristics"
import { cn } from "@/lib/utils"

interface Props {
  searchParams: Promise<Record<string, string | string[] | undefined>>
}

const DEFAULT_OVERRIDES: Required<HeuristicOverrideParams> = {
  tracked_market_limit: 12,
  historical_market_limit: 6,
  history_window_days: 30,
  event_threshold: 0.05,
  event_cooldown_points: 2,
  max_events_per_market: 4,
  max_signals_per_event: 12,
  routing_skip_below: 0.03,
  routing_deep_at_or_above: 0.08,
  scoring_base_rules: 0.62,
  scoring_base_snapshot: 0.7,
  scoring_bonus_1h: 0.12,
  scoring_bonus_6h: 0.08,
  scoring_bonus_24h: 0.04,
  selection_recent_movement_weight: 1.6,
  selection_non_zero_ratio_weight: 1.35,
  selection_volume_weight: 0.45,
  selection_open_interest_weight: 0.3,
  selection_history_weight: 0.85,
  selection_recent_trade_weight: 0.45,
  selection_orderbook_weight: 0.35,
  selection_event_volume_weight: 0.25,
  selection_title_quality_weight: 0.4,
  selection_spread_penalty: 0.3,
  selection_zero_price_penalty: 0.9,
  selection_candidate_pool_multiplier: 4,
  selection_min_points: 6,
  selection_min_non_zero_ratio: 0.15,
  selection_min_recent_trades: 2,
  selection_min_history_coverage: 0.1,
}

function stringValue(value: string | string[] | undefined) {
  return Array.isArray(value) ? value[0] : value
}

function numberValue(
  params: Record<string, string | string[] | undefined>,
  key: keyof HeuristicOverrideParams
) {
  const raw = stringValue(params[key])
  if (!raw) {
    return undefined
  }

  const parsed = Number(raw)
  return Number.isFinite(parsed) ? parsed : undefined
}

function buildOverrides(
  params: Record<string, string | string[] | undefined>
): HeuristicOverrideParams {
  return {
    tracked_market_limit: numberValue(params, "tracked_market_limit"),
    historical_market_limit: numberValue(params, "historical_market_limit"),
    history_window_days: numberValue(params, "history_window_days"),
    event_threshold: numberValue(params, "event_threshold"),
    event_cooldown_points: numberValue(params, "event_cooldown_points"),
    max_events_per_market: numberValue(params, "max_events_per_market"),
    max_signals_per_event: numberValue(params, "max_signals_per_event"),
    routing_skip_below: numberValue(params, "routing_skip_below"),
    routing_deep_at_or_above: numberValue(params, "routing_deep_at_or_above"),
    scoring_base_rules: numberValue(params, "scoring_base_rules"),
    scoring_base_snapshot: numberValue(params, "scoring_base_snapshot"),
    scoring_bonus_1h: numberValue(params, "scoring_bonus_1h"),
    scoring_bonus_6h: numberValue(params, "scoring_bonus_6h"),
    scoring_bonus_24h: numberValue(params, "scoring_bonus_24h"),
    selection_recent_movement_weight: numberValue(params, "selection_recent_movement_weight"),
    selection_non_zero_ratio_weight: numberValue(params, "selection_non_zero_ratio_weight"),
    selection_volume_weight: numberValue(params, "selection_volume_weight"),
    selection_open_interest_weight: numberValue(params, "selection_open_interest_weight"),
    selection_history_weight: numberValue(params, "selection_history_weight"),
    selection_recent_trade_weight: numberValue(params, "selection_recent_trade_weight"),
    selection_orderbook_weight: numberValue(params, "selection_orderbook_weight"),
    selection_event_volume_weight: numberValue(params, "selection_event_volume_weight"),
    selection_title_quality_weight: numberValue(params, "selection_title_quality_weight"),
    selection_spread_penalty: numberValue(params, "selection_spread_penalty"),
    selection_zero_price_penalty: numberValue(params, "selection_zero_price_penalty"),
    selection_candidate_pool_multiplier: numberValue(params, "selection_candidate_pool_multiplier"),
    selection_min_points: numberValue(params, "selection_min_points"),
    selection_min_non_zero_ratio: numberValue(params, "selection_min_non_zero_ratio"),
    selection_min_recent_trades: numberValue(params, "selection_min_recent_trades"),
    selection_min_history_coverage: numberValue(params, "selection_min_history_coverage"),
  }
}

function buildMarketHref(
  marketId: string,
  overrides: HeuristicOverrideParams
) {
  const params = new URLSearchParams()
  params.set("marketId", marketId)

  for (const [key, value] of Object.entries(overrides)) {
    if (value !== undefined) {
      params.set(key, String(value))
    }
  }

  return `/heuristics?${params.toString()}`
}

function Stat({
  label,
  value,
  tone = "default",
}: {
  label: string
  value: string
  tone?: "default" | "good" | "bad"
}) {
  return (
    <div className="rounded-lg border border-border/60 bg-background/60 px-3 py-2">
      <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">{label}</p>
      <p
        className={cn(
          "mt-1 font-mono text-sm tabular-nums text-foreground",
          tone === "good" && "text-emerald-600 dark:text-emerald-400",
          tone === "bad" && "text-red-500 dark:text-red-400"
        )}
      >
        {value}
      </p>
    </div>
  )
}

function CandidateTable({
  title,
  description,
  items,
}: {
  title: string
  description: string
  items: EventCandidateDebug[]
}) {
  return (
    <Card size="sm" className="border border-border/70 bg-card/80">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">No candidates in this stage.</p>
        ) : (
          <div className="overflow-hidden rounded-lg border border-border/60">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/40 text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 font-medium">Window</th>
                  <th className="px-3 py-2 font-medium">Move</th>
                  <th className="px-3 py-2 font-medium">State</th>
                  <th className="px-3 py-2 font-medium">Debug</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={`${item.stage}-${item.candidateId}`} className="border-t border-border/60">
                    <td className="px-3 py-2 align-top">
                      <p className="font-medium text-foreground">{item.title}</p>
                      <p className="mt-1 font-mono text-[11px] text-muted-foreground">
                        {formatDate(item.startTime)}
                        {item.endTime ? ` -> ${formatDate(item.endTime)}` : ""}
                      </p>
                    </td>
                    <td className="px-3 py-2 align-top font-mono tabular-nums text-foreground">
                      {formatProbability(item.probabilityBefore)}
                      {" -> "}
                      {item.probabilityAfter !== undefined
                        ? formatProbability(item.probabilityAfter)
                        : "n/a"}
                      <div className="mt-1 text-[11px] text-muted-foreground">
                        {Math.round(item.movementPercent * 100)}%
                      </div>
                    </td>
                    <td className="px-3 py-2 align-top">
                      <span
                        className={cn(
                          "inline-flex rounded-full border px-2 py-1 font-mono text-[11px]",
                          item.kept
                            ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
                            : "border-red-500/40 bg-red-500/10 text-red-600 dark:text-red-300"
                        )}
                      >
                        {item.kept ? "kept" : item.dropReason ?? "dropped"}
                      </span>
                    </td>
                    <td className="px-3 py-2 align-top">
                      <pre className="max-w-[28rem] overflow-x-auto whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-muted-foreground">
                        {JSON.stringify(item.debugPayload, null, 2)}
                      </pre>
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

function SignalTable({ items }: { items: SignalCandidateDebug[] }) {
  return (
    <Card size="sm" className="border border-border/70 bg-card/80">
      <CardHeader>
        <CardTitle>Signal Candidates</CardTitle>
        <CardDescription>
          Provider-backed signal candidates before and after the trim step.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">No signals attached for the current events.</p>
        ) : (
          <div className="space-y-2">
            {items.map((item) => (
              <div
                key={`${item.eventId}-${item.title}`}
                className="rounded-lg border border-border/60 bg-background/60 px-3 py-3"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium text-foreground">{item.title}</span>
                  <span className="rounded-full border border-border/60 px-2 py-0.5 font-mono text-[11px] text-muted-foreground">
                    {item.sourceType}
                  </span>
                  <span
                    className={cn(
                      "rounded-full border px-2 py-0.5 font-mono text-[11px]",
                      item.kept
                        ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
                        : "border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-300"
                    )}
                  >
                    {item.kept ? "kept" : "trimmed"}
                  </span>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">{item.snippet}</p>
                <div className="mt-2 flex flex-wrap gap-4 font-mono text-[11px] text-muted-foreground">
                  <span>event={item.eventId}</span>
                  <span>score={item.relevanceScore.toFixed(2)}</span>
                  <span>{formatDate(item.publishedAt)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function ValidationStrip({
  items,
  overrides,
}: {
  items: ValidationMarketOption[]
  overrides: HeuristicOverrideParams
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <Link
          key={item.marketId}
          href={buildMarketHref(item.marketId, overrides)}
          className={cn(
            "rounded-full border px-3 py-1.5 text-xs transition-colors",
            item.selected
              ? "border-foreground/20 bg-foreground/10 text-foreground"
              : "border-border/60 bg-background/60 text-muted-foreground hover:border-border hover:bg-muted/40"
          )}
        >
          <span className="font-medium">{item.eventTitle ? `${item.eventTitle} · ` : ""}{item.marketId}</span>
          <span className="ml-2 font-mono">{item.score.toFixed(2)}</span>
          {item.knownGood ? (
            <span className="ml-2 rounded-full border border-emerald-500/40 bg-emerald-500/10 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-emerald-700 dark:text-emerald-300">
              known-good
            </span>
          ) : null}
        </Link>
      ))}
    </div>
  )
}

function EventStrip({ items }: { items: HeuristicEventOption[] }) {
  if (items.length === 0) {
    return null
  }

  return (
    <div className="space-y-2">
      <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">Event shortlist</p>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <span
            key={item.eventId}
            className="rounded-full border border-border/60 bg-background/60 px-3 py-1.5 text-xs text-muted-foreground"
          >
            <span className="font-medium text-foreground">{item.title}</span>
            <span className="ml-2 font-mono">{item.score.toFixed(2)}</span>
            <span className="ml-2">{item.marketCount} markets</span>
          </span>
        ))}
      </div>
    </div>
  )
}

export default async function InternalHeuristicsPage({ searchParams }: Props) {
  const params = await searchParams
  const configured = isHeuristicsApiConfigured()
  const overrides = buildOverrides(params)
  const requestedMarketId = stringValue(params.marketId)

  if (!configured) {
    return (
      <div className="space-y-6">
        <section className="space-y-2">
          <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Internal</p>
          <h1 className="text-2xl font-semibold tracking-tight">Heuristics Playground</h1>
          <p className="max-w-3xl text-sm leading-relaxed text-muted-foreground">
            This page needs `PREDICTION_MARKET_API_BASE_URL` so it can call the backend
            evaluation endpoints.
          </p>
        </section>
      </div>
    )
  }

  let markets: ValidationMarketOption[] = []
  let events: HeuristicEventOption[] = []
  let evaluation: HeuristicEvaluationResponse | null = null
  let errorMessage: string | null = null

  try {
    const discovery = await listHeuristicMarkets()
    markets = discovery.items
    events = discovery.events
    const marketId = requestedMarketId ?? markets[0]?.marketId
    if (marketId) {
      evaluation = await getHeuristicEvaluation(marketId, overrides)
    }
  } catch (error) {
    errorMessage = error instanceof Error ? error.message : "Failed to load heuristics data."
  }

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Internal</p>
        <h1 className="text-2xl font-semibold tracking-tight">Heuristics Playground</h1>
        <p className="max-w-3xl text-sm leading-relaxed text-muted-foreground">
          Read-only evaluation console for event-first discovery, market selection, event
          detection, and signal routing. It reuses the live backend pipeline without writing
          persistence side effects.
        </p>
      </section>

      <Card className="border border-border/70 bg-card/80">
        <CardHeader>
          <CardTitle>Evaluation Controls</CardTitle>
          <CardDescription>
            Choose a market, tune the main heuristics, and re-run the analysis through query
            params.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <EventStrip items={events} />
          {markets.length > 0 ? <ValidationStrip items={markets} overrides={overrides} /> : null}
          <form method="GET" className="grid gap-4 lg:grid-cols-3">
            <label className="space-y-1 text-sm">
              <span className="text-muted-foreground">Market slug</span>
              <select
                name="marketId"
                defaultValue={requestedMarketId ?? markets[0]?.marketId ?? ""}
                className="w-full rounded-lg border border-border/60 bg-background px-3 py-2 text-sm outline-none ring-0"
              >
                {markets.map((item) => (
                  <option key={item.marketId} value={item.marketId}>
                    {item.eventTitle ? `${item.eventTitle} · ` : ""}
                    {item.marketId} · {item.title}
                  </option>
                ))}
              </select>
            </label>
            {(
              [
                ["tracked_market_limit", "Tracked open limit"],
                ["historical_market_limit", "Historical limit"],
                ["history_window_days", "History window days"],
                ["event_threshold", "Event threshold"],
                ["event_cooldown_points", "Cooldown points"],
                ["max_events_per_market", "Max events"],
                ["max_signals_per_event", "Max signals"],
                ["routing_skip_below", "Route skip <"],
                ["routing_deep_at_or_above", "Route deep >="],
                ["scoring_base_rules", "Rules base score"],
                ["scoring_base_snapshot", "Snapshot base score"],
                ["scoring_bonus_1h", "Scoring bonus 1h"],
                ["scoring_bonus_6h", "Scoring bonus 6h"],
                ["scoring_bonus_24h", "Scoring bonus 24h"],
                ["selection_recent_movement_weight", "Selection movement weight"],
                ["selection_non_zero_ratio_weight", "Selection non-zero weight"],
                ["selection_volume_weight", "Selection volume weight"],
                ["selection_open_interest_weight", "Selection open interest weight"],
                ["selection_history_weight", "Selection history weight"],
                ["selection_recent_trade_weight", "Selection trade weight"],
                ["selection_orderbook_weight", "Selection orderbook weight"],
                ["selection_event_volume_weight", "Selection event volume weight"],
                ["selection_title_quality_weight", "Selection title quality weight"],
                ["selection_spread_penalty", "Selection spread penalty"],
                ["selection_zero_price_penalty", "Zero-price penalty"],
                ["selection_candidate_pool_multiplier", "Candidate pool multiplier"],
                ["selection_min_points", "Minimum points"],
                ["selection_min_non_zero_ratio", "Min non-zero ratio"],
                ["selection_min_recent_trades", "Min recent trades"],
                ["selection_min_history_coverage", "Min history coverage"],
              ] as const
            ).map(([key, label]) => (
              <label key={key} className="space-y-1 text-sm">
                <span className="text-muted-foreground">{label}</span>
                <input
                  name={key}
                  defaultValue={String(overrides[key] ?? DEFAULT_OVERRIDES[key])}
                  className="w-full rounded-lg border border-border/60 bg-background px-3 py-2 font-mono text-sm outline-none ring-0"
                />
              </label>
            ))}
            <div className="flex items-end">
              <button className="rounded-lg border border-foreground/15 bg-foreground px-4 py-2 text-sm font-medium text-background transition-opacity hover:opacity-90">
                Run evaluation
              </button>
            </div>
          </form>
        </CardContent>
      </Card>

      {errorMessage ? (
        <Card className="border border-red-500/40 bg-red-500/5">
          <CardHeader>
            <CardTitle>Evaluation Error</CardTitle>
            <CardDescription>{errorMessage}</CardDescription>
          </CardHeader>
        </Card>
      ) : null}

      {evaluation ? (
        <>
          <section className="grid gap-4 xl:grid-cols-[1.2fr_0.9fr_0.9fr]">
            <Card className="border border-border/70 bg-card/80">
              <CardHeader>
                <CardTitle>{evaluation.market.title}</CardTitle>
                <CardDescription>{evaluation.market.id}</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3 sm:grid-cols-2">
                <Stat label="Current" value={formatProbability(evaluation.market.currentProbability)} />
                <Stat label="Previous close" value={formatProbability(evaluation.market.previousClose)} />
                <Stat
                  label="Selection score"
                  value={evaluation.selectionDebug.score.toFixed(2)}
                  tone={evaluation.selectionDebug.selected ? "good" : "default"}
                />
                <Stat
                  label="Pool / rank"
                  value={`${evaluation.selectionDebug.pool}${evaluation.selectionDebug.rank ? ` · #${evaluation.selectionDebug.rank}` : ""}`}
                />
              </CardContent>
            </Card>

            <Card className="border border-border/70 bg-card/80">
              <CardHeader>
                <CardTitle>Market Quality</CardTitle>
                <CardDescription>Signal density and detector fitness summary.</CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-3">
                <Stat label="Points" value={String(evaluation.marketQuality.pointCount)} />
                <Stat label="Non-zero" value={`${Math.round(evaluation.marketQuality.nonZeroPointRatio * 100)}%`} />
                <Stat label="Variance" value={evaluation.marketQuality.probabilityVariance.toFixed(4)} />
                <Stat label="Spread" value={`${Math.round(evaluation.marketQuality.probabilitySpread * 100)}%`} />
                <Stat
                  label="Recent move"
                  value={`${Math.round(evaluation.marketQuality.recentMovement * 100)}%`}
                  tone={evaluation.marketQuality.recentMovement > 0 ? "good" : "default"}
                />
                <Stat
                  label="Detector input"
                  value={evaluation.marketQuality.usableDetectorInput ? "usable" : "weak"}
                  tone={evaluation.marketQuality.usableDetectorInput ? "good" : "bad"}
                />
              </CardContent>
            </Card>

            <Card className="border border-border/70 bg-card/80">
              <CardHeader>
                <CardTitle>History Summary</CardTitle>
                <CardDescription>
                  {evaluation.historySummary.source} · {evaluation.historySummary.pointCount} points
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3">
                <Stat
                  label="Range"
                  value={
                    evaluation.historySummary.minProbability !== undefined &&
                    evaluation.historySummary.maxProbability !== undefined
                      ? `${formatProbability(evaluation.historySummary.minProbability)} -> ${formatProbability(evaluation.historySummary.maxProbability)}`
                      : "n/a"
                  }
                />
                <Stat
                  label="Current"
                  value={
                    evaluation.historySummary.currentProbability !== undefined
                      ? formatProbability(evaluation.historySummary.currentProbability)
                      : "n/a"
                  }
                />
                <div className="rounded-lg border border-border/60 bg-background/60 px-3 py-2">
                  <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                    Time range
                  </p>
                  <p className="mt-1 font-mono text-xs text-foreground">
                    {evaluation.historySummary.firstTimestamp
                      ? formatDate(evaluation.historySummary.firstTimestamp)
                      : "n/a"}
                    {" -> "}
                    {evaluation.historySummary.lastTimestamp
                      ? formatDate(evaluation.historySummary.lastTimestamp)
                      : "n/a"}
                  </p>
                </div>
              </CardContent>
            </Card>
          </section>

          <section className="grid gap-4 xl:grid-cols-[1fr_1fr]">
            <Card size="sm" className="border border-border/70 bg-card/80">
              <CardHeader>
                <CardTitle>Selection Debug</CardTitle>
                <CardDescription>Why this market ranked where it did.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-2 sm:grid-cols-2">
                  {Object.entries(evaluation.selectionDebug.components).map(([key, value]) => (
                    <Stat key={key} label={key} value={value.toFixed(2)} />
                  ))}
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <p className="mb-2 text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                      Reasons
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {evaluation.selectionDebug.reasons.map((item) => (
                        <span
                          key={item}
                          className="rounded-full border border-emerald-500/40 bg-emerald-500/10 px-2 py-1 font-mono text-[11px] text-emerald-700 dark:text-emerald-300"
                        >
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="mb-2 text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                      Penalties
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {evaluation.selectionDebug.penalties.length > 0 ? (
                        evaluation.selectionDebug.penalties.map((item) => (
                          <span
                            key={item}
                            className="rounded-full border border-red-500/40 bg-red-500/10 px-2 py-1 font-mono text-[11px] text-red-600 dark:text-red-300"
                          >
                            {item}
                          </span>
                        ))
                      ) : (
                        <span className="rounded-full border border-border/60 px-2 py-1 font-mono text-[11px] text-muted-foreground">
                          none
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card size="sm" className="border border-border/70 bg-card/80">
              <CardHeader>
                <CardTitle>Routing Decisions</CardTitle>
                <CardDescription>Per-event research routing after detection.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {evaluation.routingDecisions.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No routing decisions yet.</p>
                ) : (
                  evaluation.routingDecisions.map((item) => (
                    <div
                      key={item.eventId}
                      className="rounded-lg border border-border/60 bg-background/60 px-3 py-3"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs text-muted-foreground">{item.eventId}</span>
                        <span className="rounded-full border border-border/60 px-2 py-0.5 font-mono text-[11px] text-foreground">
                          {item.decision}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          candidates={item.candidateCount}
                        </span>
                      </div>
                      <p className="mt-2 text-sm text-muted-foreground">{item.reason}</p>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </section>

          <CandidateTable
            title="Raw Candidates"
            description="Best movement candidate from each anchor before filters apply."
            items={evaluation.rawCandidates}
          />

          <CandidateTable
            title="Filtered Candidates"
            description="Threshold, cooldown, merge, and cap outcomes for each candidate."
            items={evaluation.filteredCandidates}
          />

          <Card size="sm" className="border border-border/70 bg-card/80">
            <CardHeader>
              <CardTitle>Final Events</CardTitle>
              <CardDescription>
                Final detector windows that survive filtering and signal attachment.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {evaluation.finalEvents.length === 0 ? (
                <p className="text-sm text-muted-foreground">No final events for this market.</p>
              ) : (
                <div className="space-y-3">
                  {evaluation.finalEvents.map((event) => (
                    <div
                      key={event.id}
                      className="rounded-lg border border-border/60 bg-background/60 px-4 py-3"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-medium text-foreground">{event.title}</span>
                        <span className="rounded-full border border-border/60 px-2 py-0.5 font-mono text-[11px] text-muted-foreground">
                          {event.direction}
                        </span>
                        <span className="font-mono text-[11px] text-muted-foreground">
                          {Math.round(event.movementPercent * 100)}%
                        </span>
                      </div>
                      {event.summary ? (
                        <p className="mt-2 text-sm text-muted-foreground">{event.summary}</p>
                      ) : null}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <SignalTable items={evaluation.signalCandidates} />
        </>
      ) : null}
    </div>
  )
}
