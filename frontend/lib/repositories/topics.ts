import "server-only"

import { cache } from "react"

import { getTopicById, getTopics as getFixtureTopics } from "@/lib/fixtures/topics"
import type { TopicDetail, TopicSummary, TopicsResponse } from "@/lib/topic-types"

const API_BASE_URL = process.env.PREDICTION_MARKET_API_BASE_URL?.replace(/\/$/, "")

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

export const listTopics = cache(async (): Promise<TopicSummary[]> => {
  if (!API_BASE_URL) {
    return getFixtureTopics()
  }

  try {
    const response = await fetchApi<TopicsResponse>("/api/topics")
    return response.items
  } catch {
    return getFixtureTopics()
  }
})

export const getTopicDetail = cache(async (topicId: string): Promise<TopicDetail | null> => {
  if (!API_BASE_URL) {
    return getTopicById(topicId) ?? null
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/topics/${topicId}`, {
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
      throw new Error(`API request failed for /api/topics/${topicId} with status ${response.status}.`)
    }

    return (await response.json()) as TopicDetail
  } catch {
    return getTopicById(topicId) ?? null
  }
})
