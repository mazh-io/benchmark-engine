# Frontend Dashboard - Benchmark Engine

A professional Next.js 14 dashboard for visualizing AI provider benchmark results in real-time.

## 📁 Project Location

The frontend project is located in the `frontend/` directory:

```
benchmark-engine/
└── frontend/          # This is the frontend project
    ├── app/          # Next.js app router
    ├── components/   # React components
    ├── lib/          # Utilities and types
    ├── hooks/        # React hooks
    └── styles/       # Global styles
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18+ (recommended: 20.x)
- **npm** or **yarn** or **pnpm**
- **Supabase account** (same as backend)

### Installation

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

3. **Create environment file:**
   ```bash
   cp .env.example .env.local
   ```

4. **Configure environment variables:**
   
   Edit `.env.local` and add your Supabase credentials:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
   ```
   
   **Note:** These are the same credentials used by the Python backend.

5. **Run development server:**
   ```bash
   npm run dev
   # or
   yarn dev
   # or
   pnpm dev
   ```

6. **Open your browser:**
   ```
   http://localhost:3001
   ```

## 📦 Dependencies

### Core Technologies

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **React Query** - Data fetching and caching
- **Supabase** - Database client
- **Recharts** - Chart visualizations
- **Tailwind CSS** - Styling
- **Lucide React** - Icons

### Key Packages

```json
{
  "next": "^14.x",
  "react": "^18.x",
  "@supabase/supabase-js": "^2.x",
  "@tanstack/react-query": "^5.x",
  "recharts": "^2.x",
  "tailwindcss": "^3.x"
}
```

## 🏗️ Project Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout with Acid Theme
│   ├── page.tsx                # Dashboard homepage
│   └── globals.css             # Global styles (imported in layout)
├── components/
│   ├── charts/
│   │   └── SpeedChart.tsx      # TTFT bar chart
│   ├── dashboard/
│   │   └── StatsPanel.tsx      # Right sidebar stats
│   ├── filters/
│   │   └── ProviderFilter.tsx  # Direct/Proxy filter
│   ├── metrics/
│   │   ├── StabilityIndicator.tsx  # Jitter traffic light
│   │   └── ValueScore.tsx         # Value score display
│   └── ui/
│       └── LockedState.tsx     # Freemium placeholder
├── hooks/
│   └── useBenchmarkData.ts     # Data fetching hook
├── lib/
│   ├── supabase.ts             # Supabase client
│   ├── types.ts                # TypeScript interfaces
│   ├── calculations.ts         # Value Score & Jitter formulas
│   └── utils.ts                # Helper functions
├── styles/
│   └── globals.css             # Acid Theme styles
├── .env.local                  # Environment variables (not in git)
├── package.json                # Dependencies
├── tsconfig.json               # TypeScript config
├── tailwind.config.ts          # Tailwind config
└── next.config.js              # Next.js config
```

## 🎨 Features

### Dashboard Components

- **Speed Chart** - Bar chart showing TTFT (Time to First Token) for each provider
- **Stability Indicator** - Traffic light showing jitter (green/yellow/red)
- **Value Score** - Calculated metric: TPS / Cost Per Million
- **Provider Filter** - Toggle between Direct and Proxy providers
- **Stats Panel** - Top performers and quick statistics
- **Insights** - Real-time performance insights

### Real-time Updates

- Auto-refresh every 60 seconds
- React Query caching for optimal performance
- SSR for fast initial load (< 1s)

## 🔧 Configuration

### Environment Variables

Create `.env.local` in the `frontend/` directory:

```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
```

**Where to find these:**
1. Go to your Supabase project dashboard
2. Navigate to **Settings** → **API**
3. Copy **Project URL** → `NEXT_PUBLIC_SUPABASE_URL`
4. Copy **anon/public key** → `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### Port Configuration

By default, Next.js runs on port `3000`. To change it:

```bash
# Option 1: Environment variable
PORT=3001 npm run dev

# Option 2: Package.json script
# Edit package.json and add:
"dev": "next dev -p 3001"
```

## 📊 Available Scripts

```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint code
npm run lint

# Type check
npm run type-check
```

## 🎯 Usage

### Viewing Dashboard

1. Start the development server:
   ```bash
   npm run dev
   ```

2. Open browser:
   ```
   http://localhost:3001
   ```

3. The dashboard will automatically:
   - Fetch data from Supabase
   - Display provider metrics
   - Update every 60 seconds

### Filtering Providers

- Click **"All Providers"** to see all
- Click **"Direct"** to see native API providers (OpenAI, Groq, etc.)
- Click **"Proxy"** to see aggregator services (OpenRouter)

### Time Range Selection

Use the time range selector in the header:
- **1h** - Last hour
- **24h** - Last 24 hours
- **7d** - Last 7 days
- **30d** - Last 30 days

## 🐛 Troubleshooting

### Common Issues

**1. "Failed to Load Data" error**
- Check that `.env.local` exists and has correct Supabase credentials
- Verify Supabase project is active (not paused)
- Check browser console for detailed error messages

**2. Port already in use**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use different port
PORT=3001 npm run dev
```

**3. Module not found errors**
```bash
# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**4. TypeScript errors**
```bash
# Clear Next.js cache
rm -rf .next
npm run dev
```

**5. Styling issues**
```bash
# Rebuild Tailwind
npm run build
```

## 🔗 Integration with Backend

The frontend connects directly to the same Supabase database used by the Python backend:

- **Same database tables**: `benchmark_results`, `providers`, `models`, `runs`
- **Same credentials**: Uses Supabase anon key (read-only access)
- **Real-time sync**: Frontend reads data that backend writes

## 📝 Development

### Adding New Components

1. Create component in `components/` directory
2. Import and use in `app/page.tsx`
3. Follow existing patterns for styling (Acid Theme)

### Modifying Metrics

- **Value Score**: Edit `lib/calculations.ts`
- **Jitter**: Edit `lib/calculations.ts`
- **Charts**: Edit `components/charts/SpeedChart.tsx`

### Styling

- Uses **Tailwind CSS** with custom Acid Theme
- Color palette defined in `tailwind.config.ts`
- Global styles in `styles/globals.css`

## 🚀 Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Import project in Vercel
3. Add environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
4. Deploy!

### Other Platforms

The app can be deployed to any platform that supports Next.js:
- **Netlify**
- **Railway**
- **AWS Amplify**
- **Self-hosted** (Node.js server)

## 📚 Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [React Query Documentation](https://tanstack.com/query/latest)
- [Supabase Documentation](https://supabase.com/docs)
- [Recharts Documentation](https://recharts.org/)

## 🆘 Support

For issues or questions:
1. Check the main [README.md](../README.md) in the root directory
2. Review backend setup in `backend/README.md`
3. Check Supabase dashboard for database issues

---

**Built with ❤️ using Next.js 14 + TypeScript + Tailwind CSS**
