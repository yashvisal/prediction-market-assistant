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
        That workspace could not be found.
      </h1>
      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
        The market may have been removed, or the URL may be incorrect. Go back to the
        markets gallery and open another workspace.
      </p>

      <div className="mt-6 flex flex-wrap gap-3">
        <Link href="/markets" className={buttonVariants()}>
          Browse Markets
        </Link>
        <Link
          href="/dashboard"
          className={cn(buttonVariants({ variant: "ghost" }), "text-muted-foreground")}
        >
          Open Dashboard
        </Link>
      </div>
    </div>
  )
}
