import Link from "next/link"

import { ThemeToggle } from "@/components/theme-provider"
import { buttonVariants } from "@/components/ui/button-variants"
import { cn } from "@/lib/utils"

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur-sm">
      <div className="mx-auto flex h-12 max-w-6xl items-center justify-between px-4">
        <Link
          href="/"
          className="rounded-md text-sm font-semibold tracking-tight focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          World Signal Feed
        </Link>
        <div className="flex items-center gap-2">
          <nav aria-label="Primary" className="flex items-center gap-1">
            <Link
              href="/feed"
              className={cn(
                buttonVariants({ variant: "ghost", size: "sm" }),
                "text-muted-foreground"
              )}
            >
              Feed
            </Link>
          </nav>
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
