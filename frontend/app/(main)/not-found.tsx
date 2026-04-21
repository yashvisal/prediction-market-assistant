import Link from "next/link"

import { buttonVariants } from "@/components/ui/button-variants"
import { cn } from "@/lib/utils"

export default function AppNotFound() {
  return (
    <div className="mx-auto max-w-2xl rounded-2xl border border-dashed border-border/70 bg-muted/20 p-6">
      <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
        Not Found
      </p>
      <h1 className="mt-3 text-balance text-2xl font-semibold tracking-tight">
        That topic view could not be found.
      </h1>
      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
        The topic may have been removed, or the URL may be incorrect. Go back to the feed
        and open another topic.
      </p>

      <div className="mt-6 flex flex-wrap gap-3">
        <Link href="/feed" className={buttonVariants()}>
          Open Feed
        </Link>
        <Link
          href="/topics"
          className={cn(buttonVariants({ variant: "ghost" }), "text-muted-foreground")}
        >
          View Topics
        </Link>
      </div>
    </div>
  )
}
