export function MarketsPageSkeleton() {
  return (
    <div className="space-y-6" aria-hidden="true">
      <div className="space-y-2">
        <div className="h-7 w-32 rounded-md bg-muted" />
        <div className="h-4 w-full max-w-xl rounded-md bg-muted/70" />
      </div>

      <div className="flex items-center justify-between gap-4">
        <div className="flex gap-2">
          {Array.from({ length: 3 }, (_, index) => (
            <div key={index} className="h-7 w-16 rounded-lg bg-muted" />
          ))}
        </div>
        <div className="h-7 w-32 rounded-lg bg-muted" />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }, (_, index) => (
          <div key={index} className="space-y-3 rounded-xl border border-border/60 bg-card p-4">
            <div className="h-10 w-full rounded-md bg-muted" />
            <div className="h-6 w-24 rounded-md bg-muted" />
            <div className="h-3 w-40 rounded-md bg-muted/70" />
          </div>
        ))}
      </div>
    </div>
  )
}
