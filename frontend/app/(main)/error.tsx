"use client"

import Link from "next/link"
import { useEffect } from "react"

import { buttonVariants } from "@/components/ui/button-variants"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="mx-auto max-w-2xl rounded-2xl border border-border/60 bg-card p-6">
      <div className="space-y-3">
        <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          Something Went Wrong
        </p>
        <h1 className="text-balance text-2xl font-semibold tracking-tight">
          The page could not load this data.
        </h1>
        <p className="text-sm leading-relaxed text-muted-foreground">
          Try reloading the view. If the problem persists, check the backend URL and
          confirm the API is running.
        </p>
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <Button type="button" onClick={() => reset()}>
          Try Again
        </Button>
        <Link
          href="/feed"
          className={cn(buttonVariants({ variant: "ghost" }), "text-muted-foreground")}
        >
          Back to Feed
        </Link>
      </div>
    </div>
  )
}
