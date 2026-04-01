export function formatProbability(value: number): string {
  return `${Math.round(value * 100)}%`
}

export function formatMovement(percent: number, direction: "up" | "down"): string {
  const sign = direction === "up" ? "+" : "−"
  return `${sign}${Math.abs(Math.round(percent * 100))}%`
}

export function formatVolume(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`
  return `$${value}`
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  })
}

export function formatDateRange(start: string, end: string): string {
  const s = new Date(start)
  const e = new Date(end)
  const sameMonth = s.getMonth() === e.getMonth() && s.getFullYear() === e.getFullYear()

  const startStr = s.toLocaleDateString("en-US", { month: "short", day: "numeric" })

  if (sameMonth) {
    return `${startStr}–${e.getDate()}, ${e.getFullYear()}`
  }

  const endStr = e.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
  return `${startStr} – ${endStr}`
}

export function timeAgo(iso: string): string {
  const now = new Date()
  const then = new Date(iso)
  const diffMs = now.getTime() - then.getTime()
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffHours < 1) return "just now"
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`
  return formatDate(iso)
}
