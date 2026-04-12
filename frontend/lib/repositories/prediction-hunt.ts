import "server-only"

import type { PredictionHuntDeskSnapshotResponse } from "@/lib/prediction-hunt-types"

const API_BASE_URL = process.env.PREDICTION_MARKET_API_BASE_URL?.replace(/\/$/, "")

export function isPredictionHuntApiConfigured() {
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

export async function getPredictionHuntDeskSnapshot(params: {
  selectedMarketId?: string
  selectedMarketPlatform?: string
  marketQuery?: string
  matchQuery?: string
}) {
  const searchParams = new URLSearchParams({
    events_limit: "6",
    markets_limit: "8",
    history_interval: "1h",
  })

  if (params.selectedMarketId) {
    searchParams.set("selected_market_id", params.selectedMarketId)
  }
  if (params.selectedMarketPlatform) {
    searchParams.set("selected_market_platform", params.selectedMarketPlatform)
  }
  if (params.marketQuery) {
    searchParams.set("market_query", params.marketQuery)
  }
  if (params.matchQuery) {
    searchParams.set("match_query", params.matchQuery)
  }

  return fetchApi<PredictionHuntDeskSnapshotResponse>(
    `/api/internal/providers/prediction-hunt/desk?${searchParams.toString()}`
  )
}
