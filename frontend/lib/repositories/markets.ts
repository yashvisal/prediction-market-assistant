import "server-only"

import { cache } from "react"

import {
  getMarketById as getFixtureMarketById,
  getMarketEvents as getFixtureMarketEvents,
  getMarkets as getMockMarkets,
} from "@/lib/fixtures/markets"
import { buildDashboardSnapshot } from "@/lib/domain/markets"
import type {
  DashboardSnapshot,
  HealthResponse,
  MarketCategory,
  MarketDetail,
  MarketEvent,
  MarketEventsResponse,
  MarketsResponse,
  MarketStatus,
  MarketSummary,
} from "@/lib/market-types"

const API_BASE_URL = process.env.PREDICTION_MARKET_API_BASE_URL?.replace(/\/$/, "")

interface MarketFilters {
  status?: MarketStatus
  category?: MarketCategory
}

function buildQuery(filters: MarketFilters) {
  const params = new URLSearchParams()

  if (filters.status) {
    params.set("status", filters.status)
  }

  if (filters.category) {
    params.set("category", filters.category)
  }

  const query = params.toString()
  return query ? `?${query}` : ""
}

async function fetchApi<T>(path: string): Promise<T> {
  if (!API_BASE_URL) {
    throw new Error("API base URL is not configured.")
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      Accept: "application/json",
    },
    next: {
      revalidate: 60,
    },
  })

  if (!response.ok) {
    throw new Error(`API request failed for ${path} with status ${response.status}.`)
  }

  return (await response.json()) as T
}

export const checkApiHealth = cache(async (): Promise<HealthResponse | null> => {
  if (!API_BASE_URL) {
    return null
  }

  return fetchApi<HealthResponse>("/api/health")
})

export const listMarkets = cache(
  async (status?: MarketStatus, category?: MarketCategory): Promise<MarketSummary[]> => {
    if (!API_BASE_URL) {
      return getMockMarkets({ status, category })
    }

    const response = await fetchApi<MarketsResponse>(
      `/api/markets${buildQuery({ status, category })}`
    )

    return response.items
  }
)

export const getMarketDetail = cache(async (marketId: string): Promise<MarketDetail | null> => {
  if (!API_BASE_URL) {
    return getFixtureMarketById(marketId) ?? null
  }

  const response = await fetch(`${API_BASE_URL}/api/markets/${marketId}`, {
    headers: {
      Accept: "application/json",
    },
    next: {
      revalidate: 60,
    },
  })

  if (response.status === 404) {
    return null
  }

  if (!response.ok) {
    throw new Error(
      `API request failed for /api/markets/${marketId} with status ${response.status}.`
    )
  }

  return (await response.json()) as MarketDetail
})

export const listMarketEvents = cache(async (marketId: string): Promise<MarketEvent[]> => {
  if (!API_BASE_URL) {
    return getFixtureMarketEvents(marketId)
  }

  const response = await fetch(`${API_BASE_URL}/api/markets/${marketId}/events`, {
    headers: {
      Accept: "application/json",
    },
    next: {
      revalidate: 60,
    },
  })

  if (response.status === 404) {
    return []
  }

  if (!response.ok) {
    throw new Error(
      `API request failed for /api/markets/${marketId}/events with status ${response.status}.`
    )
  }

  const payload = (await response.json()) as MarketEventsResponse
  return payload.items
})

export const getDashboardSnapshot = cache(async (): Promise<DashboardSnapshot> => {
  if (!API_BASE_URL) {
    const markets = getMockMarkets()
    return buildDashboardSnapshot(markets, getFixtureMarketEvents)
  }

  return fetchApi<DashboardSnapshot>("/api/dashboard")
})
