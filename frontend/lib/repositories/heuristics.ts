import "server-only"

import type {
  HeuristicEvaluationResponse,
  HeuristicMarketListResponse,
} from "@/lib/heuristics-types"

const API_BASE_URL = process.env.PREDICTION_MARKET_API_BASE_URL?.replace(/\/$/, "")

export interface HeuristicOverrideParams {
  tracked_market_limit?: number
  historical_market_limit?: number
  history_window_days?: number
  event_threshold?: number
  event_cooldown_points?: number
  max_events_per_market?: number
  max_signals_per_event?: number
  routing_skip_below?: number
  routing_deep_at_or_above?: number
  scoring_base_rules?: number
  scoring_base_snapshot?: number
  scoring_bonus_1h?: number
  scoring_bonus_6h?: number
  scoring_bonus_24h?: number
  selection_recent_movement_weight?: number
  selection_non_zero_ratio_weight?: number
  selection_volume_weight?: number
  selection_open_interest_weight?: number
  selection_history_weight?: number
  selection_zero_price_penalty?: number
  selection_candidate_pool_multiplier?: number
  selection_min_points?: number
  selection_min_non_zero_ratio?: number
}

export function isHeuristicsApiConfigured() {
  return Boolean(API_BASE_URL)
}

async function fetchApi<T>(path: string): Promise<T> {
  if (!API_BASE_URL) {
    throw new Error("API base URL is not configured.")
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Accept: "application/json" },
    cache: "no-store",
  })

  if (!response.ok) {
    throw new Error(`API request failed for ${path} with status ${response.status}.`)
  }

  return (await response.json()) as T
}

function buildOverrideQuery(overrides: HeuristicOverrideParams) {
  const params = new URLSearchParams()

  for (const [key, value] of Object.entries(overrides)) {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value))
    }
  }

  const query = params.toString()
  return query ? `?${query}` : ""
}

export async function listHeuristicMarkets() {
  const response = await fetchApi<HeuristicMarketListResponse>("/api/internal/heuristics/markets")
  return response.items
}

export async function getHeuristicEvaluation(
  marketId: string,
  overrides: HeuristicOverrideParams
) {
  return fetchApi<HeuristicEvaluationResponse>(
    `/api/internal/heuristics/markets/${marketId}/evaluate${buildOverrideQuery(overrides)}`
  )
}
