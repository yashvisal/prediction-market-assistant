"use client"

import { useRouter, useSearchParams } from "next/navigation"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { HugeiconsIcon } from "@hugeicons/react"
import { UnfoldMoreIcon, Tick02Icon } from "@hugeicons/core-free-icons"
import {
  marketCategories,
  marketStatuses,
  type MarketStatus,
  type MarketCategory,
} from "@/lib/market-types"

const statuses: ReadonlyArray<{ value: MarketStatus | "all"; label: string }> = [
  { value: "all", label: "All" },
  ...marketStatuses.map((status) => ({
    value: status,
    label: status.charAt(0).toUpperCase() + status.slice(1),
  })),
]

const categories: ReadonlyArray<{ value: MarketCategory | "all"; label: string }> = [
  { value: "all", label: "All categories" },
  ...marketCategories.map((category) => ({
    value: category,
    label: category.charAt(0).toUpperCase() + category.slice(1),
  })),
]

export function MarketFilters() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const activeStatus = searchParams.get("status") ?? "all"
  const activeCategory = searchParams.get("category") ?? "all"
  const activeCategoryLabel =
    categories.find((c) => c.value === activeCategory)?.label ?? "All categories"

  function setFilter(key: string, value: string) {
    const params = new URLSearchParams(searchParams.toString())
    if (value === "all") {
      params.delete(key)
    } else {
      params.set(key, value)
    }
    router.push(`/markets${params.size > 0 ? `?${params.toString()}` : ""}`)
  }

  return (
    <div className="flex items-center justify-between gap-4">
      <div className="flex items-center gap-1">
        {statuses.map((s) => (
          <Button
            key={s.value}
            variant={activeStatus === s.value ? "secondary" : "ghost"}
            size="sm"
            onClick={() => setFilter("status", s.value)}
          >
            {s.label}
          </Button>
        ))}
      </div>

      <DropdownMenu>
        <DropdownMenuTrigger
          aria-label="Filter markets by category"
          className={cn(
            "inline-flex h-7 items-center gap-1.5 rounded-[min(var(--radius-md),10px)] border border-input bg-transparent px-2.5 text-[0.8rem] whitespace-nowrap text-foreground transition-colors outline-none select-none hover:bg-accent focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
          )}
        >
          {activeCategoryLabel}
          <HugeiconsIcon
            icon={UnfoldMoreIcon}
            strokeWidth={2}
            className="size-3.5 text-foreground"
          />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="min-w-40">
          {categories.map((c) => (
            <DropdownMenuItem
              key={c.value}
              onClick={() => setFilter("category", c.value)}
              className="flex items-center justify-between gap-3"
            >
              {c.label}
              {activeCategory === c.value && (
                <HugeiconsIcon
                  icon={Tick02Icon}
                  strokeWidth={2}
                  className="size-3.5 text-foreground"
                />
              )}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
