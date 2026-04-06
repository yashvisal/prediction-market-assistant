export function MarketWorkspaceSkeleton() {
  return (
    <div className="space-y-8" aria-hidden="true">
      <section className="space-y-4">
        <div className="h-3 w-28 rounded-md bg-muted/70" />
        <div className="h-10 w-full max-w-4xl rounded-md bg-muted" />
        <div className="h-4 w-full max-w-2xl rounded-md bg-muted/70" />
        <div className="h-8 w-28 rounded-md bg-muted" />
        <div className="flex flex-wrap gap-4">
          {Array.from({ length: 4 }, (_, index) => (
            <div key={index} className="h-4 w-28 rounded-md bg-muted/70" />
          ))}
        </div>
      </section>

      <section className="space-y-3 rounded-xl border border-border/60 bg-muted/20 p-4">
        <div className="h-3 w-24 rounded-md bg-muted/70" />
        <div className="flex h-28 items-end gap-px">
          {Array.from({ length: 30 }, (_, index) => (
            <div
              key={index}
              className="flex-1 rounded-sm bg-muted"
              style={{ height: `${35 + ((index * 7) % 50)}%` }}
            />
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <div className="h-4 w-28 rounded-md bg-muted/70" />
        <div className="space-y-2">
          {Array.from({ length: 3 }, (_, index) => (
            <div key={index} className="space-y-3 rounded-lg border border-border/60 bg-card p-4">
              <div className="flex items-center justify-between gap-3">
                <div className="h-4 w-full max-w-lg rounded-md bg-muted" />
                <div className="h-4 w-20 rounded-md bg-muted/70" />
              </div>
              <div className="h-3 w-40 rounded-md bg-muted/70" />
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
