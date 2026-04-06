export function DashboardSkeleton() {
  return (
    <div className="space-y-10" aria-hidden="true">
      <section className="space-y-2">
        <div className="h-7 w-40 rounded-md bg-muted" />
        <div className="h-4 w-full max-w-xl rounded-md bg-muted/70" />
      </section>

      <section className="space-y-4">
        <div className="h-4 w-24 rounded-md bg-muted/70" />
        <div className="grid gap-3 sm:grid-cols-2">
          {Array.from({ length: 4 }, (_, index) => (
            <div key={index} className="space-y-3 rounded-xl border border-border/60 bg-card p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="h-3 w-20 rounded-md bg-muted/70" />
                <div className="h-4 w-12 rounded-md bg-muted" />
              </div>
              <div className="h-5 w-full rounded-md bg-muted" />
              <div className="h-3 w-3/4 rounded-md bg-muted/70" />
              <div className="h-3 w-1/2 rounded-md bg-muted/70" />
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <div className="h-4 w-28 rounded-md bg-muted/70" />
        <div className="space-y-2">
          {Array.from({ length: 5 }, (_, index) => (
            <div key={index} className="flex items-center gap-4 rounded-lg border border-border/40 px-4 py-3">
              <div className="min-w-0 flex-1 space-y-2">
                <div className="h-4 w-full max-w-xl rounded-md bg-muted" />
                <div className="h-3 w-36 rounded-md bg-muted/70" />
              </div>
              <div className="h-4 w-20 rounded-md bg-muted" />
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
