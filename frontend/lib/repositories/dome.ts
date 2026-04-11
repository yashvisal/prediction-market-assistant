import "server-only"

import type {
  DomeMarketDetailResponse,
  DomeMarketDiscoveryResponse,
  DomeEventListResponse,
  DomeMarketListResponse,
} from "@/lib/dome-types"

const API_BASE_URL = process.env.PREDICTION_MARKET_API_BASE_URL?.replace(/\/$/, "")

export function isDomeApiConfigured() {
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

export async function listDomePolymarketMarkets(limit = 12) {
  const response = await fetchApi<DomeMarketListResponse>(
    `/api/internal/dome/polymarket/markets?limit=${limit}`
  )
  return response
}

export async function getDomePolymarketDiscovery(limit = 6) {
  return fetchApi<DomeMarketDiscoveryResponse>(`/api/internal/dome/polymarket/discovery?limit=${limit}`)
}

export async function listDomePolymarketEvents(limit = 8, status = "open") {
  return fetchApi<DomeEventListResponse>(
    `/api/internal/dome/polymarket/events?limit=${limit}&status=${encodeURIComponent(status)}`
  )
}

export async function getDomePolymarketMarket(marketSlug: string) {
  return fetchApi<DomeMarketDetailResponse>(
    `/api/internal/dome/polymarket/markets/${encodeURIComponent(marketSlug)}`
  )
}
