import type { Market } from "./market-types"

export const markets: Market[] = [
  {
    id: "fed-rate-cut-jul-2026",
    title: "Will the Federal Reserve cut interest rates before July 2026?",
    description:
      "Resolves YES if the Federal Open Market Committee announces a reduction in the federal funds target rate at any scheduled or emergency meeting before July 1, 2026.",
    status: "open",
    category: "finance",
    currentProbability: 0.72,
    previousClose: 0.64,
    volume: 2_340_000,
    liquidity: 485_000,
    createdAt: "2025-11-01T00:00:00Z",
    closesAt: "2026-07-01T00:00:00Z",
    events: [
      {
        id: "fed-cpi-feb-2026",
        marketId: "fed-rate-cut-jul-2026",
        title: "February CPI report shows continued disinflation",
        startTime: "2026-02-28T09:00:00Z",
        endTime: "2026-03-02T20:00:00Z",
        probabilityBefore: 0.52,
        probabilityAfter: 0.64,
        movementPercent: 0.12,
        direction: "up",
        summary:
          "The Bureau of Labor Statistics released February CPI data showing year-over-year inflation fell to 2.4%, the lowest reading since early 2021. Markets rapidly repriced rate cut expectations.",
        signals: [
          {
            id: "sig-reuters-cpi",
            title: "U.S. inflation cools to 2.4% in February, bolstering rate cut hopes",
            source: "Reuters",
            sourceType: "news",
            url: "https://reuters.com/markets/us-cpi-february-2026",
            publishedAt: "2026-02-28T13:35:00Z",
            snippet:
              "Consumer prices rose just 0.1% month-over-month, with core CPI also undershooting expectations at 2.8% year-over-year.",
            relevanceScore: 0.95,
            entities: [
              { id: "ent-bls", name: "Bureau of Labor Statistics", type: "organization" },
              { id: "ent-cpi", name: "Consumer Price Index", type: "topic" },
            ],
          },
          {
            id: "sig-fedwatcher-tweet",
            title: "Thread: CPI breakdown and implications for June FOMC",
            source: "@FedWatcher",
            sourceType: "tweet",
            url: "https://x.com/FedWatcher/status/1234567890",
            publishedAt: "2026-02-28T14:20:00Z",
            snippet:
              "Shelter inflation finally cracking — OER down to 3.1%. This is the component the Fed has been waiting on. June cut now firmly on the table.",
            relevanceScore: 0.82,
            entities: [
              { id: "ent-fed", name: "Federal Reserve", type: "organization" },
              { id: "ent-fomc", name: "FOMC", type: "organization" },
            ],
          },
          {
            id: "sig-wsj-analysis",
            title: "Markets bet on June rate cut after inflation surprise",
            source: "Wall Street Journal",
            sourceType: "analysis",
            url: "https://wsj.com/economy/fed-june-rate-cut-odds",
            publishedAt: "2026-03-01T08:00:00Z",
            snippet:
              "Fed funds futures now price in a 78% chance of a 25bp cut at the June meeting, up from 52% before the CPI release.",
            relevanceScore: 0.88,
            entities: [
              { id: "ent-fed", name: "Federal Reserve", type: "organization" },
            ],
          },
        ],
        entities: [
          { id: "ent-fed", name: "Federal Reserve", type: "organization" },
          { id: "ent-bls", name: "Bureau of Labor Statistics", type: "organization" },
          { id: "ent-cpi", name: "Consumer Price Index", type: "topic" },
          { id: "ent-fomc", name: "FOMC", type: "organization" },
        ],
        relatedEvents: [
          {
            id: "rel-inflation-target",
            marketId: "inflation-below-3-2026",
            marketTitle: "Will U.S. inflation fall below 3% year-over-year in 2026?",
            eventTitle: "February CPI release",
            relationship: "shared_entity",
            sharedEntities: ["Bureau of Labor Statistics", "Consumer Price Index"],
          },
        ],
      },
      {
        id: "fed-powell-march-2026",
        marketId: "fed-rate-cut-jul-2026",
        title: "Powell signals patience at March press conference",
        startTime: "2026-03-19T18:00:00Z",
        endTime: "2026-03-20T16:00:00Z",
        probabilityBefore: 0.64,
        probabilityAfter: 0.72,
        movementPercent: 0.08,
        direction: "up",
        summary:
          "Chair Powell acknowledged progress on inflation but emphasized the committee wants to see 'a few more months of data' before acting. Markets interpreted the tone as dovish relative to expectations.",
        signals: [
          {
            id: "sig-fed-presser",
            title: "FOMC holds rates steady, Powell hints at possible June action",
            source: "Federal Reserve",
            sourceType: "official",
            url: "https://federalreserve.gov/newsevents/pressreleases/monetary20260319a.htm",
            publishedAt: "2026-03-19T18:30:00Z",
            snippet:
              "The Committee decided to maintain the target range for the federal funds rate. Recent data suggest inflation is moving sustainably toward our 2 percent objective.",
            relevanceScore: 0.97,
            entities: [
              { id: "ent-fed", name: "Federal Reserve", type: "organization" },
              { id: "ent-powell", name: "Jerome Powell", type: "person" },
            ],
          },
          {
            id: "sig-ft-powell",
            title: "Powell's careful optimism lifts rate cut bets",
            source: "Financial Times",
            sourceType: "news",
            url: "https://ft.com/content/powell-march-2026-fomc",
            publishedAt: "2026-03-20T06:00:00Z",
            snippet:
              "While stopping short of a commitment, Powell's remarks were notably less hawkish than January's press conference, where he pushed back firmly against rate cut speculation.",
            relevanceScore: 0.85,
            entities: [
              { id: "ent-powell", name: "Jerome Powell", type: "person" },
              { id: "ent-fed", name: "Federal Reserve", type: "organization" },
            ],
          },
        ],
        entities: [
          { id: "ent-powell", name: "Jerome Powell", type: "person" },
          { id: "ent-fed", name: "Federal Reserve", type: "organization" },
          { id: "ent-fomc", name: "FOMC", type: "organization" },
        ],
        relatedEvents: [],
      },
    ],
  },
  {
    id: "ai-safety-bill-2026",
    title: "Will Congress pass a major AI safety bill by end of 2026?",
    description:
      "Resolves YES if a bill primarily focused on AI safety, risk assessment, or frontier model regulation is signed into law by December 31, 2026.",
    status: "open",
    category: "technology",
    currentProbability: 0.34,
    previousClose: 0.31,
    volume: 1_120_000,
    liquidity: 210_000,
    createdAt: "2025-12-15T00:00:00Z",
    closesAt: "2026-12-31T00:00:00Z",
    events: [
      {
        id: "ai-senate-hearing",
        marketId: "ai-safety-bill-2026",
        title: "Senate Commerce Committee holds high-profile AI hearing",
        startTime: "2026-03-05T14:00:00Z",
        endTime: "2026-03-07T20:00:00Z",
        probabilityBefore: 0.28,
        probabilityAfter: 0.34,
        movementPercent: 0.06,
        direction: "up",
        summary:
          "The Senate Commerce Committee hearing featured testimony from leading AI researchers and industry executives. Bipartisan interest in a reporting-focused bill emerged, though significant disagreements remain on enforcement mechanisms.",
        signals: [
          {
            id: "sig-politico-hearing",
            title: "Senators signal bipartisan appetite for AI guardrails",
            source: "Politico",
            sourceType: "news",
            url: "https://politico.com/news/2026/03/senate-ai-hearing",
            publishedAt: "2026-03-05T19:00:00Z",
            snippet:
              "Senators from both parties expressed support for mandatory incident reporting for frontier AI systems, though Republican members pushed back on pre-deployment licensing.",
            relevanceScore: 0.91,
            entities: [
              { id: "ent-senate-commerce", name: "Senate Commerce Committee", type: "organization" },
              { id: "ent-ai-safety", name: "AI Safety Regulation", type: "topic" },
            ],
          },
          {
            id: "sig-openai-testimony",
            title: "OpenAI CEO endorses 'light-touch' federal framework",
            source: "TechCrunch",
            sourceType: "news",
            url: "https://techcrunch.com/2026/03/05/openai-senate-testimony",
            publishedAt: "2026-03-05T21:30:00Z",
            snippet:
              "In prepared testimony, the OpenAI CEO expressed support for federal safety standards while cautioning against approaches that could 'cede AI leadership to nations with fewer safeguards.'",
            relevanceScore: 0.78,
            entities: [
              { id: "ent-openai", name: "OpenAI", type: "organization" },
              { id: "ent-ai-safety", name: "AI Safety Regulation", type: "topic" },
            ],
          },
        ],
        entities: [
          { id: "ent-senate-commerce", name: "Senate Commerce Committee", type: "organization" },
          { id: "ent-openai", name: "OpenAI", type: "organization" },
          { id: "ent-ai-safety", name: "AI Safety Regulation", type: "topic" },
        ],
        relatedEvents: [
          {
            id: "rel-eu-ai-act",
            marketId: "eu-ai-act-enforcement",
            marketTitle: "Will the EU AI Act enforcement begin on schedule?",
            eventTitle: "EU Commission releases implementation guidelines",
            relationship: "shared_entity",
            sharedEntities: ["AI Safety Regulation"],
          },
        ],
      },
      {
        id: "ai-bill-draft-leak",
        marketId: "ai-safety-bill-2026",
        title: "Draft bipartisan bill text leaks, faces immediate industry pushback",
        startTime: "2026-03-22T10:00:00Z",
        endTime: "2026-03-25T20:00:00Z",
        probabilityBefore: 0.34,
        probabilityAfter: 0.31,
        movementPercent: 0.03,
        direction: "down",
        summary:
          "A leaked draft of the proposed AI Accountability Act included provisions for mandatory red-teaming and model registration. Major tech companies quickly organized opposition, and two key Republican co-sponsors distanced themselves from the draft.",
        signals: [
          {
            id: "sig-axios-leak",
            title: "Leaked AI bill draft includes model registration requirement",
            source: "Axios",
            sourceType: "news",
            url: "https://axios.com/2026/03/22/ai-bill-draft-leaked",
            publishedAt: "2026-03-22T11:00:00Z",
            snippet:
              "The 47-page draft would require companies developing frontier AI models to register with a new federal office and submit to annual safety audits.",
            relevanceScore: 0.93,
            entities: [
              { id: "ent-ai-accountability-act", name: "AI Accountability Act", type: "legislation" },
              { id: "ent-ai-safety", name: "AI Safety Regulation", type: "topic" },
            ],
          },
          {
            id: "sig-tech-coalition-tweet",
            title: "Major tech trade group calls draft 'unworkable'",
            source: "@TechIndustryCoalition",
            sourceType: "tweet",
            url: "https://x.com/TechIndustryCoalition/status/9876543210",
            publishedAt: "2026-03-23T14:00:00Z",
            snippet:
              "The proposed model registration regime would impose massive compliance costs on startups and small labs while doing little to address actual safety risks. We urge Congress to reconsider.",
            relevanceScore: 0.72,
            entities: [
              { id: "ent-ai-accountability-act", name: "AI Accountability Act", type: "legislation" },
            ],
          },
        ],
        entities: [
          { id: "ent-ai-accountability-act", name: "AI Accountability Act", type: "legislation" },
          { id: "ent-ai-safety", name: "AI Safety Regulation", type: "topic" },
          { id: "ent-senate-commerce", name: "Senate Commerce Committee", type: "organization" },
        ],
        relatedEvents: [],
      },
    ],
  },
  {
    id: "btc-150k-2026",
    title: "Will Bitcoin exceed $150,000 at any point in 2026?",
    description:
      "Resolves YES if the BTC/USD price on any major exchange exceeds $150,000.00 at any point before December 31, 2026 23:59 UTC.",
    status: "open",
    category: "crypto",
    currentProbability: 0.41,
    previousClose: 0.38,
    volume: 4_780_000,
    liquidity: 920_000,
    createdAt: "2025-10-01T00:00:00Z",
    closesAt: "2026-12-31T23:59:00Z",
    events: [
      {
        id: "btc-etf-inflows-march",
        marketId: "btc-150k-2026",
        title: "Record single-day ETF inflows push BTC past $120K",
        startTime: "2026-03-10T14:00:00Z",
        endTime: "2026-03-12T20:00:00Z",
        probabilityBefore: 0.33,
        probabilityAfter: 0.41,
        movementPercent: 0.08,
        direction: "up",
        summary:
          "Spot Bitcoin ETFs saw a record $2.1 billion in net inflows on March 10th, coinciding with BTC breaking through the $120,000 level for the first time. Institutional demand was cited as the primary driver.",
        signals: [
          {
            id: "sig-bloomberg-etf",
            title: "Bitcoin ETFs see record $2.1B daily inflow as BTC breaks $120K",
            source: "Bloomberg",
            sourceType: "news",
            url: "https://bloomberg.com/news/bitcoin-etf-record-inflow-march-2026",
            publishedAt: "2026-03-10T20:00:00Z",
            snippet:
              "BlackRock's iShares Bitcoin Trust led with $890 million in inflows, followed by Fidelity's Wise Origin fund at $540 million. Total spot BTC ETF assets now exceed $125 billion.",
            relevanceScore: 0.94,
            entities: [
              { id: "ent-blackrock", name: "BlackRock", type: "organization" },
              { id: "ent-btc-etf", name: "Bitcoin ETFs", type: "topic" },
            ],
          },
          {
            id: "sig-coindesk-120k",
            title: "Bitcoin breaks $120K: what comes next",
            source: "CoinDesk",
            sourceType: "analysis",
            url: "https://coindesk.com/markets/btc-120k-analysis",
            publishedAt: "2026-03-11T08:00:00Z",
            snippet:
              "On-chain metrics suggest supply on exchanges continues to decline, with long-term holder supply ratio at its highest since 2017. The next major resistance level sits at $135K.",
            relevanceScore: 0.79,
            entities: [
              { id: "ent-bitcoin", name: "Bitcoin", type: "topic" },
            ],
          },
        ],
        entities: [
          { id: "ent-bitcoin", name: "Bitcoin", type: "topic" },
          { id: "ent-btc-etf", name: "Bitcoin ETFs", type: "topic" },
          { id: "ent-blackrock", name: "BlackRock", type: "organization" },
        ],
        relatedEvents: [
          {
            id: "rel-eth-etf",
            marketId: "eth-10k-2026",
            marketTitle: "Will Ethereum exceed $10,000 in 2026?",
            eventTitle: "Crypto rally lifts ETH above $6,000",
            relationship: "time_overlap",
          },
        ],
      },
    ],
  },
  {
    id: "spacex-starship-orbital",
    title: "Will SpaceX complete a fully successful Starship orbital flight by Q3 2026?",
    description:
      "Resolves YES if a SpaceX Starship vehicle completes a full orbital trajectory and lands (or is recovered) successfully before October 1, 2026.",
    status: "open",
    category: "science",
    currentProbability: 0.58,
    previousClose: 0.55,
    volume: 890_000,
    liquidity: 175_000,
    createdAt: "2025-09-15T00:00:00Z",
    closesAt: "2026-10-01T00:00:00Z",
    events: [
      {
        id: "starship-ift7-partial",
        marketId: "spacex-starship-orbital",
        title: "IFT-7 achieves orbit but upper stage breaks up during reentry",
        startTime: "2026-02-14T16:00:00Z",
        endTime: "2026-02-16T12:00:00Z",
        probabilityBefore: 0.48,
        probabilityAfter: 0.55,
        movementPercent: 0.07,
        direction: "up",
        summary:
          "Starship IFT-7 successfully reached orbit for the first time, but the upper stage experienced thermal protection system failure during reentry and was lost. Super Heavy booster was successfully caught. Markets viewed orbital insertion as a strong positive signal despite the reentry failure.",
        signals: [
          {
            id: "sig-spacex-ift7",
            title: "Starship reaches orbit for the first time",
            source: "SpaceX",
            sourceType: "official",
            url: "https://spacex.com/updates/starship-ift7",
            publishedAt: "2026-02-14T17:30:00Z",
            snippet:
              "Starship reached its planned orbital trajectory approximately 8 minutes and 42 seconds after liftoff. All six Raptor engines on the upper stage performed nominally during the ascent burn.",
            relevanceScore: 0.98,
            entities: [
              { id: "ent-spacex", name: "SpaceX", type: "organization" },
              { id: "ent-starship", name: "Starship", type: "topic" },
            ],
          },
          {
            id: "sig-ars-ift7",
            title: "Starship orbits Earth but fails reentry: what it means for the program",
            source: "Ars Technica",
            sourceType: "analysis",
            url: "https://arstechnica.com/space/starship-ift7-orbit-reentry-failure",
            publishedAt: "2026-02-15T10:00:00Z",
            snippet:
              "The heat shield tile system appears to have failed in the same general area as IFT-6, suggesting SpaceX has not yet solved its thermal protection challenges. However, the successful orbital insertion and booster catch mark major milestones.",
            relevanceScore: 0.89,
            entities: [
              { id: "ent-spacex", name: "SpaceX", type: "organization" },
              { id: "ent-starship", name: "Starship", type: "topic" },
            ],
          },
        ],
        entities: [
          { id: "ent-spacex", name: "SpaceX", type: "organization" },
          { id: "ent-starship", name: "Starship", type: "topic" },
          { id: "ent-musk", name: "Elon Musk", type: "person" },
        ],
        relatedEvents: [],
      },
      {
        id: "starship-faa-review",
        marketId: "spacex-starship-orbital",
        title: "FAA clears SpaceX for IFT-8 with expedited review",
        startTime: "2026-03-18T12:00:00Z",
        endTime: "2026-03-19T16:00:00Z",
        probabilityBefore: 0.55,
        probabilityAfter: 0.58,
        movementPercent: 0.03,
        direction: "up",
        signals: [
          {
            id: "sig-faa-clearance",
            title: "FAA grants SpaceX IFT-8 launch license in record time",
            source: "SpaceNews",
            sourceType: "news",
            url: "https://spacenews.com/faa-spacex-ift8-license",
            publishedAt: "2026-03-18T14:00:00Z",
            snippet:
              "The FAA completed its mishap investigation and granted a new launch license in just 32 days, the fastest turnaround for a Starship flight. SpaceX reportedly redesigned portions of the heat shield.",
            relevanceScore: 0.86,
            entities: [
              { id: "ent-faa", name: "FAA", type: "organization" },
              { id: "ent-spacex", name: "SpaceX", type: "organization" },
            ],
          },
        ],
        entities: [
          { id: "ent-faa", name: "FAA", type: "organization" },
          { id: "ent-spacex", name: "SpaceX", type: "organization" },
          { id: "ent-starship", name: "Starship", type: "topic" },
        ],
        relatedEvents: [],
      },
    ],
  },
  {
    id: "us-eu-trade-2026",
    title: "Will the US and EU finalize a new trade agreement in 2026?",
    description:
      "Resolves YES if the United States and European Union sign a comprehensive bilateral trade agreement covering tariffs and/or regulatory alignment before December 31, 2026.",
    status: "open",
    category: "geopolitics",
    currentProbability: 0.18,
    previousClose: 0.22,
    volume: 560_000,
    liquidity: 95_000,
    createdAt: "2026-01-10T00:00:00Z",
    closesAt: "2026-12-31T00:00:00Z",
    events: [
      {
        id: "us-eu-tariff-threat",
        marketId: "us-eu-trade-2026",
        title: "US threatens new tariffs on EU auto imports",
        startTime: "2026-03-08T08:00:00Z",
        endTime: "2026-03-10T20:00:00Z",
        probabilityBefore: 0.22,
        probabilityAfter: 0.18,
        movementPercent: 0.04,
        direction: "down",
        summary:
          "The US Trade Representative announced a 90-day review period for potential 25% tariffs on European automobile imports, citing trade imbalances. EU officials responded with threats of retaliatory measures.",
        signals: [
          {
            id: "sig-ustr-tariffs",
            title: "USTR announces 90-day review of EU auto tariffs",
            source: "U.S. Trade Representative",
            sourceType: "official",
            url: "https://ustr.gov/press-releases/eu-auto-tariff-review-2026",
            publishedAt: "2026-03-08T09:00:00Z",
            snippet:
              "The Office of the United States Trade Representative today initiated a review of tariff options on European Union automobile and auto parts imports under Section 301.",
            relevanceScore: 0.96,
            entities: [
              { id: "ent-ustr", name: "U.S. Trade Representative", type: "organization" },
              { id: "ent-eu-commission", name: "European Commission", type: "organization" },
            ],
          },
          {
            id: "sig-ft-eu-response",
            title: "EU warns of 'swift and proportionate' response to US auto tariffs",
            source: "Financial Times",
            sourceType: "news",
            url: "https://ft.com/content/eu-us-tariff-response-2026",
            publishedAt: "2026-03-09T07:30:00Z",
            snippet:
              "The European Commission said it had a list of retaliatory measures ready, targeting US agricultural exports and tech services, though officials expressed hope for a negotiated solution.",
            relevanceScore: 0.88,
            entities: [
              { id: "ent-eu-commission", name: "European Commission", type: "organization" },
            ],
          },
        ],
        entities: [
          { id: "ent-ustr", name: "U.S. Trade Representative", type: "organization" },
          { id: "ent-eu-commission", name: "European Commission", type: "organization" },
          { id: "ent-us-eu-trade", name: "US-EU Trade Relations", type: "topic" },
        ],
        relatedEvents: [
          {
            id: "rel-eu-retaliation",
            marketId: "eu-retaliatory-tariffs",
            marketTitle: "Will the EU impose retaliatory tariffs on US goods in 2026?",
            eventTitle: "EU prepares retaliation list",
            relationship: "shared_source",
          },
        ],
      },
    ],
  },
  {
    id: "who-pandemic-declaration",
    title: "Will the WHO declare a new Public Health Emergency of International Concern in Q1 2026?",
    description:
      "Resolved NO. The WHO did not declare a new PHEIC during Q1 2026. The H5N1 monitoring situation was elevated but did not meet PHEIC criteria.",
    status: "resolved",
    category: "science",
    currentProbability: 0.0,
    previousClose: 0.08,
    volume: 340_000,
    liquidity: 0,
    createdAt: "2025-12-01T00:00:00Z",
    closesAt: "2026-03-31T23:59:00Z",
    resolvedAt: "2026-03-31T23:59:00Z",
    resolution: "no",
    events: [
      {
        id: "who-h5n1-surge",
        marketId: "who-pandemic-declaration",
        title: "H5N1 human cases spike in Southeast Asia",
        startTime: "2026-01-20T00:00:00Z",
        endTime: "2026-01-24T00:00:00Z",
        probabilityBefore: 0.05,
        probabilityAfter: 0.15,
        movementPercent: 0.1,
        direction: "up",
        summary:
          "A cluster of 12 confirmed H5N1 human cases across Vietnam and Cambodia raised alarm, temporarily tripling the market probability. The WHO convened an emergency committee but determined the situation did not yet warrant a PHEIC declaration.",
        signals: [
          {
            id: "sig-who-h5n1",
            title: "WHO convenes emergency committee on H5N1 cluster",
            source: "World Health Organization",
            sourceType: "official",
            url: "https://who.int/news/h5n1-emergency-committee-jan-2026",
            publishedAt: "2026-01-22T12:00:00Z",
            snippet:
              "The Director-General convened the Emergency Committee under the International Health Regulations to assess the recent cluster of human H5N1 infections in the Western Pacific region.",
            relevanceScore: 0.97,
            entities: [
              { id: "ent-who", name: "World Health Organization", type: "organization" },
              { id: "ent-h5n1", name: "H5N1 Avian Influenza", type: "topic" },
            ],
          },
        ],
        entities: [
          { id: "ent-who", name: "World Health Organization", type: "organization" },
          { id: "ent-h5n1", name: "H5N1 Avian Influenza", type: "topic" },
        ],
        relatedEvents: [],
      },
      {
        id: "who-h5n1-contained",
        marketId: "who-pandemic-declaration",
        title: "WHO determines H5N1 cluster contained, no PHEIC",
        startTime: "2026-02-05T00:00:00Z",
        endTime: "2026-02-07T00:00:00Z",
        probabilityBefore: 0.15,
        probabilityAfter: 0.08,
        movementPercent: 0.07,
        direction: "down",
        signals: [
          {
            id: "sig-who-no-pheic",
            title: "Emergency Committee advises against PHEIC declaration",
            source: "World Health Organization",
            sourceType: "official",
            url: "https://who.int/news/h5n1-no-pheic-feb-2026",
            publishedAt: "2026-02-05T16:00:00Z",
            snippet:
              "The Emergency Committee concluded that while the situation requires heightened surveillance, current evidence does not indicate sustained human-to-human transmission and does not constitute a PHEIC.",
            relevanceScore: 0.95,
            entities: [
              { id: "ent-who", name: "World Health Organization", type: "organization" },
              { id: "ent-h5n1", name: "H5N1 Avian Influenza", type: "topic" },
            ],
          },
        ],
        entities: [
          { id: "ent-who", name: "World Health Organization", type: "organization" },
          { id: "ent-h5n1", name: "H5N1 Avian Influenza", type: "topic" },
        ],
        relatedEvents: [],
      },
    ],
  },
]

const marketsById = new Map(markets.map((m) => [m.id, m]))

export function getMarkets(): Market[] {
  return markets
}

export function getMarketById(id: string): Market | undefined {
  return marketsById.get(id)
}

export function getTopEvents() {
  return markets
    .flatMap((m) =>
      m.events.map((e) => ({
        ...e,
        marketTitle: m.title,
        marketCategory: m.category,
        marketStatus: m.status,
      }))
    )
    .sort((a, b) => Math.abs(b.movementPercent) - Math.abs(a.movementPercent))
    .slice(0, 4)
}

export function getActiveMarkets(): Market[] {
  return markets.filter((m) => m.status === "open")
}
