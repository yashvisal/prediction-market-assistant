import Link from "next/link"
import { ScrollTo } from "@/components/scroll-to"

export default function LandingPage() {
  return (
    <main id="main-content" className="min-h-svh">
      {/* ───── Hero ───── */}
      <section className="landing-dot-grid relative flex min-h-svh flex-col items-center justify-center overflow-hidden px-6 text-center">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-background" />

        <div className="relative z-10 mx-auto max-w-3xl">
          <p className="landing-fade-up text-xs font-medium uppercase tracking-[0.25em] text-muted-foreground">
            World Signal Feed
          </p>

          <h1 className="landing-fade-up landing-delay-1 mt-8 font-serif text-5xl leading-[1.1] tracking-tight sm:text-6xl md:text-7xl">
            Distributed signals
            <br />
            <em className="text-muted-foreground">become coherent topics</em>
          </h1>

          <p className="landing-fade-up landing-delay-2 mx-auto mt-8 max-w-xl text-lg leading-relaxed text-muted-foreground">
            Prediction markets are one of the clearest real-time signals of changing
            beliefs. We organize those fragmented moves into evolving topics so you can
            quickly see what is changing and why it matters.
          </p>

          <div className="landing-fade-up landing-delay-3 mt-10 flex items-center justify-center gap-4">
            <Link
              href="/feed"
              className="inline-flex h-10 items-center rounded-lg bg-foreground px-5 text-sm font-medium text-background transition-opacity hover:opacity-80 focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
            >
              Open Feed
            </Link>
            <ScrollTo
              target="thesis"
              className="inline-flex h-10 items-center rounded-lg border border-border px-5 text-sm font-medium text-muted-foreground transition-colors hover:border-foreground/20 hover:text-foreground focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
            >
              How It Works
            </ScrollTo>
          </div>
        </div>

        <div className="landing-fade-in landing-delay-5 absolute bottom-10 left-1/2 flex -translate-x-1/2 flex-col items-center gap-2 text-center text-muted-foreground/40">
          <span className="text-[11px] uppercase tracking-widest">Scroll</span>
          <div className="h-8 w-px bg-gradient-to-b from-muted-foreground/30 to-transparent" />
        </div>
      </section>

      {/* ───── Strip ───── */}
      <section className="border-y bg-muted/30 py-5">
        <div className="mx-auto grid max-w-4xl grid-cols-1 items-center gap-y-2 px-6 text-center text-[11px] uppercase tracking-widest text-muted-foreground/50 sm:grid-cols-3 sm:gap-x-6 sm:gap-y-0">
          <span className="justify-self-center">Prediction Hunt signal layer</span>
          <span className="justify-self-center">Topic state first</span>
          <span className="justify-self-center">Evidence before explanation</span>
        </div>
      </section>

      {/* ───── Thesis ───── */}
      <section id="thesis" className="scroll-mt-4 px-6 py-28 sm:py-36">
        <div className="mx-auto max-w-2xl">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground/50">
            The problem
          </p>
          <h2 className="mt-5 font-serif text-3xl leading-snug tracking-tight sm:text-4xl">
            A global topic suddenly shifts.
            <br />
            <span className="text-muted-foreground">Was it a policy change, a new report, or a shift in collective belief?</span>
          </h2>
          <p className="mt-8 text-base leading-relaxed text-muted-foreground">
            Today, the signals exist but they arrive as fragmented market moves, isolated
            news items, and disconnected source material. Most of the work is figuring
            out which pieces belong to the same story.
          </p>
          <p className="mt-4 text-base leading-relaxed text-muted-foreground">
            This system is being built to turn that fragmentation into a structured view
            of the world.
          </p>
        </div>
      </section>

      {/* ───── Hierarchy ───── */}
      <section className="border-y bg-muted/20 px-6 py-28 sm:py-36">
        <div className="mx-auto max-w-4xl">
          <div className="text-center">
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground/50">
              How it works
            </p>
            <h2 className="mt-5 font-serif text-3xl tracking-tight sm:text-4xl">
              Three layers of topic intelligence
            </h2>
            <p className="mx-auto mt-4 max-w-lg text-sm leading-relaxed text-muted-foreground">
              Signals are assembled into topic state first. Everything else is built on
              top of that shared state.
            </p>
          </div>

          <div className="mt-16 grid gap-6 sm:grid-cols-3">
            <div className="group relative flex h-full flex-col rounded-2xl border border-border/60 bg-background p-6 transition-colors hover:border-border">
              <div className="flex size-10 items-center justify-center rounded-xl bg-foreground text-lg font-serif text-background">
                S
              </div>
              <h3 className="mt-5 text-base font-semibold">Signals</h3>
              <p className="mt-2 min-h-[4.5rem] text-sm leading-relaxed text-muted-foreground">
                Prediction Hunt markets, price movements, and event windows provide the
                cheap, continuous signal layer.
              </p>
              <div className="mt-5 space-y-1.5">
                <div className="flex min-h-[3.75rem] flex-col justify-between rounded-lg border border-border/40 bg-muted/30 px-3 py-2">
                  <p className="text-xs font-medium truncate">Fed rate cut expectations jump after CPI</p>
                  <div className="mt-1 flex items-baseline gap-1.5">
                    <span className="text-sm font-semibold tabular-nums">72%</span>
                    <span className="text-[11px] text-emerald-600 tabular-nums">+8%</span>
                  </div>
                </div>
                <div className="flex min-h-[3.75rem] flex-col justify-between rounded-lg border border-border/40 bg-muted/30 px-3 py-2">
                  <p className="text-xs font-medium truncate">Bitcoin rally broadens across ETF-driven markets</p>
                  <div className="mt-1 flex items-baseline gap-1.5">
                    <span className="text-sm font-semibold tabular-nums">41%</span>
                    <span className="text-[11px] text-emerald-600 tabular-nums">+3%</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="group relative flex h-full flex-col rounded-2xl border border-border/60 bg-background p-6 transition-colors hover:border-border">
              <div className="flex size-10 items-center justify-center rounded-xl bg-foreground text-lg font-serif text-background">
                T
              </div>
              <h3 className="mt-5 text-base font-semibold">Topic State</h3>
              <p className="mt-2 min-h-[4.5rem] text-sm leading-relaxed text-muted-foreground">
                Related signals are grouped into canonical topic state that downstream
                feed, explanation, and digest layers all share.
              </p>
              <div className="mt-5 space-y-1.5">
                <div className="flex min-h-[3.75rem] flex-col justify-between rounded-lg border border-border/40 bg-muted/30 px-3 py-2">
                  <p className="text-xs font-medium truncate">Fed Policy Expectations</p>
                  <div className="mt-1 flex items-center gap-2 text-[11px] text-muted-foreground">
                    <span className="font-semibold text-emerald-600 tabular-nums">+12%</span>
                    <span>2 markets · 3 updates</span>
                  </div>
                </div>
                <div className="flex min-h-[3.75rem] flex-col justify-between rounded-lg border border-border/40 bg-muted/30 px-3 py-2">
                  <p className="text-xs font-medium truncate">AI Regulation</p>
                  <div className="mt-1 flex items-center gap-2 text-[11px] text-muted-foreground">
                    <span className="font-semibold text-emerald-600 tabular-nums">+6%</span>
                    <span>1 market · 2 updates</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="group relative flex h-full flex-col rounded-2xl border border-border/60 bg-background p-6 transition-colors hover:border-border">
              <div className="flex size-10 items-center justify-center rounded-xl bg-foreground text-lg font-serif text-background">
                E
              </div>
              <h3 className="mt-5 text-base font-semibold">Explanations</h3>
              <p className="mt-2 min-h-[4.5rem] text-sm leading-relaxed text-muted-foreground">
                Explanations and digests come later, built selectively on top of Topic
                State rather than recomputing the world from scratch.
              </p>
              <div className="mt-5 space-y-1.5">
                <div className="flex min-h-[3.75rem] flex-col justify-between rounded-lg border border-border/40 bg-muted/30 px-3 py-2">
                  <div className="flex items-center gap-2">
                    <span className="inline-block size-1.5 rounded-full bg-blue-500" />
                    <span className="text-[11px] text-muted-foreground">Future digest</span>
                  </div>
                  <p className="mt-0.5 text-xs font-medium truncate">Why Fed expectations moved this week</p>
                </div>
                <div className="flex min-h-[3.75rem] flex-col justify-between rounded-lg border border-border/40 bg-muted/30 px-3 py-2">
                  <div className="flex items-center gap-2">
                    <span className="inline-block size-1.5 rounded-full bg-sky-400" />
                    <span className="text-[11px] text-muted-foreground">Future brief</span>
                  </div>
                  <p className="mt-0.5 text-xs font-medium truncate">How AI regulation signals are evolving</p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 flex justify-center">
            <div className="flex items-center gap-3 text-xs text-muted-foreground/40">
              <div className="h-px w-8 bg-border" />
              <span className="uppercase tracking-widest">Signal → Topic State → Intelligence</span>
              <div className="h-px w-8 bg-border" />
            </div>
          </div>
        </div>
      </section>

      {/* ───── Principles ───── */}
      <section className="px-6 py-28 sm:py-36">
        <div className="mx-auto max-w-4xl">
          <div className="text-center">
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground/50">
              Principles
            </p>
            <h2 className="mt-5 font-serif text-3xl tracking-tight sm:text-4xl">
              Built on conviction, not convention
            </h2>
          </div>

          <div className="mt-16 grid gap-px overflow-hidden rounded-2xl border border-border/60 bg-border/60 sm:grid-cols-3">
            <div className="bg-background p-8">
              <p className="text-2xl font-serif">01</p>
              <h3 className="mt-3 text-sm font-semibold">Evidence-first</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                Every insight traces back to a real, retrievable source. No unsupported
                claims, no fabricated confidence, no hallucinated reasoning.
              </p>
            </div>
            <div className="bg-background p-8">
              <p className="text-2xl font-serif">02</p>
              <h3 className="mt-3 text-sm font-semibold">Exploratory</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                The system structures information. You form the judgment. This is a
                research tool, not an oracle — investigation over answers.
              </p>
            </div>
            <div className="bg-background p-8">
              <p className="text-2xl font-serif">03</p>
              <h3 className="mt-3 text-sm font-semibold">Structured</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                Clear hierarchy from signal to topic state to downstream intelligence.
                Relationships are explicit and inspectable. No black boxes in Phase 1.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ───── Final CTA ───── */}
      <section className="border-t bg-muted/20 px-6 py-28 sm:py-36">
        <div className="mx-auto max-w-xl text-center">
          <h2 className="font-serif text-3xl tracking-tight sm:text-4xl">
            Open the live feed
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
            Follow the topics that are moving now, inspect their source markets, and see
            the updates that currently define their state.
          </p>
          <div className="mt-8 flex items-center justify-center gap-4">
            <Link
              href="/feed"
              className="inline-flex h-10 items-center rounded-lg bg-foreground px-5 text-sm font-medium text-background transition-opacity hover:opacity-80 focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
            >
              Open Feed
            </Link>
            <Link
              href="/topics"
              className="inline-flex h-10 items-center rounded-lg border border-border px-5 text-sm font-medium text-muted-foreground transition-colors hover:border-foreground/20 hover:text-foreground focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
            >
              View Topics
            </Link>
          </div>
        </div>
      </section>
    </main>
  )
}
