# MAZH — AI Provider Benchmark Dashboard

Real-time dashboard for monitoring and comparing AI provider performance metrics. Built with Next.js 14, TypeScript, and Supabase.

## Quick Start

```bash
cd frontend
npm install
cp .env.example .env.local   # then add your Supabase credentials
npm run dev                   # opens at http://localhost:3000
```

### Environment Variables

Create `.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
```

Find these in your Supabase dashboard under **Settings > API**.

## Scripts

| Command              | Description                    |
|----------------------|--------------------------------|
| `npm run dev`        | Start dev server               |
| `npm run build`      | Production build               |
| `npm start`          | Start production server        |
| `npm run lint`       | Run ESLint                     |
| `npm run type-check` | Run TypeScript type checking   |

## Tech Stack

| Library                | Purpose                       |
|------------------------|-------------------------------|
| Next.js 14 (App Router)| Framework & routing          |
| TypeScript 5           | Type safety                  |
| TanStack React Query 5 | Data fetching & caching      |
| Supabase               | Database (reads from backend)|
| Recharts               | Chart visualizations         |
| Tailwind CSS 3         | Styling                      |
| Lucide React           | Icons                        |

## Project Structure

```
frontend/
├── app/                        # Next.js App Router
│   ├── layout.tsx              #   Root layout (fonts, metadata, providers)
│   ├── page.tsx                #   Main dashboard page
│   └── providers.tsx           #   React Query provider wrapper
│
├── api/                        # Data layer
│   ├── supabase.ts             #   Supabase client instance
│   ├── calculations.ts         #   Value score, jitter, derived metrics
│   ├── database.types.ts       #   Auto-generated Supabase DB types
│   ├── types.ts                #   Shared TypeScript interfaces
│   └── utils.ts                #   General utility functions
│
├── hooks/                      # Custom React hooks
│   ├── useBenchmarkData.ts     #   Fetches benchmark data with time range
│   └── useDashboardMetric.ts   #   Processes dashboard-level metrics
│
├── data/                       # Static data
│   └── apiDocumentation.ts     #   API endpoint documentation definitions
│
├── layout/                     # Layout components
│   ├── Header.tsx              #   Top bar (logo, live badge, links)
│   ├── MainNav.tsx             #   Tab navigation (Index / Insights / API)
│   └── IndexFooter.tsx         #   Footer with "Show all models" CTA
│
├── templates/                  # Page-level feature sections
│   ├── highlights/             #   Top-of-page metric highlight cards
│   │   ├── HighlightCard.tsx   #     Base card (icon, label, tooltip)
│   │   ├── MetricCard.tsx      #     Metric display (value, provider, ranking)
│   │   └── HighlightsGrid.tsx  #     Grid layout + insight comparison
│   │
│   ├── IndexTable/             #   Main benchmark ranking table
│   │   ├── IndexTable.tsx      #     Table container
│   │   ├── TableRow.tsx        #     Single provider row
│   │   ├── ExpandedRow.tsx     #     Expanded detail row on click
│   │   ├── FilterBar.tsx       #     Provider/type/search filters
│   │   ├── JitterBar.tsx       #     Jitter stability indicator
│   │   ├── helpers.ts          #     Status colors, grid columns, row builder
│   │   └── types.ts            #     RowData type definition
│   │
│   ├── insights/               #   Deep-dive insight panels
│   │   ├── InsightsGrid.tsx    #     Card grid layout
│   │   ├── InsightsToolbar.tsx #     Toolbar (info text)
│   │   ├── InsightsFooter.tsx  #     Pro upgrade CTA
│   │   ├── cards/              #     Insight summary cards (9 cards)
│   │   │   ├── InsightCard.tsx #       Shared card wrapper
│   │   │   ├── TTFTAnalysisCard.tsx
│   │   │   ├── ThroughputCard.tsx
│   │   │   ├── EfficiencyCard.tsx
│   │   │   ├── StabilityCard.tsx
│   │   │   ├── ReliabilityCard.tsx
│   │   │   ├── CostAnalysisCard.tsx
│   │   │   ├── ProviderRankingsCard.tsx
│   │   │   └── PlaceholderCard.tsx
│   │   ├── details/            #     Expanded detail panels (charts, tables)
│   │   │   ├── DetailPanel.tsx #       Panel shell (header, close, content)
│   │   │   ├── KeyStatsGrid.tsx
│   │   │   ├── TTFTDetailPanel.tsx
│   │   │   ├── TTFTBarChart.tsx
│   │   │   ├── TTFTRankingTable.tsx
│   │   │   ├── ThroughputDetailPanel.tsx
│   │   │   ├── ThroughputBarChart.tsx
│   │   │   ├── EfficiencyPanel.tsx
│   │   │   ├── StabilityPanel.tsx
│   │   │   ├── ReliabilityDetailPanel.tsx
│   │   │   ├── ReliabilityRankingTable.tsx
│   │   │   ├── CostAnalysisPanel.tsx
│   │   │   ├── ProviderScorecardPanel.tsx
│   │   │   ├── ProviderScorecardTable.tsx
│   │   │   ├── HeadToHeadPanel.tsx
│   │   │   ├── HeadToHeadTable.tsx
│   │   │   └── HeadToHeadBenchmark.tsx
│   │   ├── details/hooks/      #       Data processing hooks per panel
│   │   │   ├── shared.ts
│   │   │   ├── useTTFTStats.ts
│   │   │   ├── useThroughputStats.ts
│   │   │   ├── useEfficiencyStats.ts
│   │   │   ├── useStabilityStats.ts
│   │   │   ├── useReliabilityStats.ts
│   │   │   ├── useCostStats.ts
│   │   │   ├── useHeadToHeadStats.ts
│   │   │   └── useProviderScorecardStats.ts
│   │   └── utils/
│   │       └── calculations.ts #       Insight-specific math helpers
│   │
│   └── api/                    #   API documentation page
│       ├── APIPage.tsx         #     Page container + tab routing
│       ├── NavCards.tsx        #     Section navigation cards
│       ├── RestSection.tsx     #     REST endpoints section
│       ├── KeysSection.tsx     #     API keys management
│       ├── PlaygroundSection.tsx#    Interactive playground
│       ├── WidgetsSection.tsx  #     Embeddable widgets section
│       ├── syntaxHighlighting.ts#    Code syntax highlighting util
│       ├── types.ts            #     API page type definitions
│       ├── endpoint/           #     Endpoint documentation components
│       │   ├── EndpointDetail.tsx
│       │   ├── EndpointHeader.tsx
│       │   ├── CodeExamples.tsx
│       │   ├── ResponseExample.tsx
│       │   └── RateLimits.tsx
│       └── widgets/            #     Embeddable widget components
│           ├── WidgetChrome.tsx
│           ├── WidgetTime.tsx
│           ├── widgetData.ts
│           ├── leaderboardData.ts
│           ├── ProviderCardWidget.tsx
│           ├── ComparisonWidget.tsx
│           ├── StatusBadgeWidget.tsx
│           ├── InsightWidget.tsx
│           ├── TPSLeaderboardWidget.tsx
│           └── TTFTLeaderboardWidget.tsx
│
├── styles/                     # CSS architecture
│   ├── globals.css             #   Entry point — imports all stylesheets
│   ├── base/
│   │   └── variables.css       #   CSS custom properties (colors, fonts)
│   ├── components/
│   │   ├── header.css          #   Top bar, logo, live badge
│   │   ├── navigation.css      #   Tab bar
│   │   ├── buttons.css         #   Buttons, utilities, recharts overrides
│   │   ├── filters.css         #   Filter bar, pills, chips, search
│   │   ├── highlights.css      #   Highlight cards, tooltips, badges
│   │   ├── index-table.css     #   Table shell, rows, expanded rows, footer
│   │   ├── detail-panels.css   #   Insight panels, key stats, charts, ranking
│   │   ├── head-to-head.css    #   H2H selector, dropdown, comparison table
│   │   ├── insights.css        #   Insights grid layout
│   │   ├── pro-lock.css        #   Pro/locked overlays
│   │   └── footer.css          #   Index footer
│   └── api/
│       ├── api-page.css        #   API page layout
│       └── widgets/            #   Widget-specific styles
│           ├── widget-base.css
│           ├── provider-card.css
│           ├── comparison.css
│           ├── status-badge.css
│           └── insight-card.css
│
├── tailwind.config.ts          # Tailwind theme (acid palette, fonts, animations)
├── tsconfig.json               # TypeScript config (path aliases: @/*)
├── next.config.js              # Next.js config
└── postcss.config.js           # PostCSS + Tailwind
```

## Architecture

### Data Flow

There is no traditional backend API (no Laravel, no Express). The frontend queries the database directly via the Supabase client library. A separate Python worker writes benchmark data to the same database on a schedule.

```
Python worker ──WRITES──▶  Supabase (PostgreSQL)  ◀──READS── Next.js frontend
(cron job)                  (shared database)                  (Supabase JS client)
```

The request chain inside the frontend:

```
supabase.ts          →  useBenchmarkData hook  →  page.tsx  →  components
(DB client & queries)   (React Query cache)       (state)      (props)
```

1. `api/supabase.ts` configures the Supabase client and exports query functions that read directly from PostgreSQL
2. `hooks/useBenchmarkData.ts` wraps queries in React Query for caching (30s stale), auto-refresh (60s), and retry logic
3. `app/page.tsx` holds top-level state (active tab, time filter, expanded cards) and passes data down via props
4. `api/calculations.ts` derives computed metrics (top speed, best value, efficiency) from raw results

### Three Main Views

| Tab        | Components                                     | Purpose                          |
|------------|------------------------------------------------|----------------------------------|
| **Index**  | FilterBar, IndexTable, TableRow, ExpandedRow   | Sortable benchmark ranking table |
| **Insights** | InsightsGrid, InsightCards, DetailPanels     | Deep-dive analysis per metric    |
| **API**    | APIPage, RestSection, KeysSection, Widgets     | API docs + embeddable widgets    |

### CSS Architecture

Styles are organized by component responsibility — one file per concern. All CSS is imported through `globals.css` inside a `@layer components` block. The project uses a combination of:

- **CSS custom properties** (`variables.css`) for the acid-green dark theme
- **Tailwind utility classes** in JSX for layout and spacing
- **Component CSS classes** for complex, reusable visual patterns

### State Management

No external state library. The app uses:

- **React Query** for server state (caching, refetching, stale time)
- **React useState** for UI state (active tab, expanded cards, filters)
- **Props drilling** for component communication (flat hierarchy, no deep nesting)

## Deployment

### Vercel (Recommended)

1. Push to GitHub
2. Import in Vercel
3. Set environment variables (`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`)
4. Deploy

### Other Platforms

Works on any platform supporting Next.js: Netlify, Railway, AWS Amplify, or self-hosted with `npm run build && npm start`.

## Troubleshooting

| Problem                  | Solution                                        |
|--------------------------|-------------------------------------------------|
| Failed to load data      | Check `.env.local` credentials                  |
| Port in use              | `lsof -ti:3000 \| xargs kill -9` or use `PORT=3001` |
| Module not found         | `rm -rf node_modules && npm install`            |
| TypeScript errors        | `rm -rf .next && npm run dev`                   |
| Stale styles             | `npm run build` to rebuild Tailwind             |
