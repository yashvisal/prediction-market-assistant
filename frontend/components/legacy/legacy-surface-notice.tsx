import Link from "next/link"

import { buttonVariants } from "@/components/ui/button-variants"
import { cn } from "@/lib/utils"

interface LegacySurfaceNoticeProps {
  title: string
  description: string
}

export function LegacySurfaceNotice({ title, description }: LegacySurfaceNoticeProps) {
  return (
    <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 px-4 py-3">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-wider text-amber-700 dark:text-amber-400">
            Legacy Surface
          </p>
          <h2 className="text-sm font-semibold">{title}</h2>
          <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">{description}</p>
        </div>
        <Link
          href="/feed"
          className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "text-muted-foreground")}
        >
          Open Feed
        </Link>
      </div>
    </div>
  )
}
