/* ── Early Access – Static Data ────────────────── */

export const CHECKOUT = {
  monthly: 'https://mazh.lemonsqueezy.com/checkout/buy/early-monthly',
  yearly: 'https://mazh.lemonsqueezy.com/checkout/buy/early-yearly',
} as const;

export const HIGHLIGHTS = [
  { icon: '💰', title: 'Cost Analysis', desc: "See the 300× price spread. Find where you're overpaying." },
  { icon: '💬', title: 'Efficiency Score', desc: 'Which models are chatty? Optimize your token usage.' },
  { icon: '📊', title: 'Stability & P95/P99', desc: 'Plan for worst-case latency. Build reliable SLAs.' },
  { icon: '📅', title: 'Data History', desc: '7, 30, or 90 day lookback. Spot trends over time.' },
  { icon: '⚔️', title: 'Full Head-to-Head', desc: 'Compare all 7 metrics. Make informed trade-offs.' },
  { icon: '🔌', title: 'API Access', desc: 'Build your own dashboards, alerts, and integrations.' },
] as const;

export type CellType = 'check' | 'lock' | 'soon' | '—';

export interface FeatureItem {
  name: string;
  free: CellType;
  pro: CellType;
}

export interface FeatureGroup {
  group: string;
  items: FeatureItem[];
}

export const FEATURES: FeatureGroup[] = [
  {
    group: 'Index',
    items: [
      { name: 'Live TTFT & TPS Rankings', free: 'check', pro: 'check' },
      { name: 'Provider Overview', free: 'check', pro: 'check' },
      { name: 'Success Rates', free: 'check', pro: 'check' },
    ],
  },
  {
    group: 'Insights',
    items: [
      { name: 'TTFT Analysis', free: 'check', pro: 'check' },
      { name: 'Throughput Analysis', free: 'check', pro: 'check' },
      { name: 'Reliability Metrics', free: 'check', pro: 'check' },
      { name: 'Provider Scorecard', free: 'check', pro: 'check' },
      { name: 'Head-to-Head (4 Metrics)', free: 'check', pro: 'check' },
      { name: 'Cost Analysis', free: 'lock', pro: 'check' },
      { name: 'Efficiency Score', free: 'lock', pro: 'check' },
      { name: 'Stability & P95/P99', free: 'lock', pro: 'check' },
      { name: 'Head-to-Head (7 Metrics)', free: 'lock', pro: 'check' },
    ],
  },
  {
    group: 'Filters & Data',
    items: [
      { name: 'Data History (7 days)', free: 'check', pro: 'check' },
      { name: 'Data History (30d / 90d)', free: 'lock', pro: 'check' },
      { name: 'Use Cases (Voice / Batch / Code)', free: 'lock', pro: 'check' },
    ],
  },
  {
    group: 'Tools',
    items: [
      { name: 'API Access', free: 'lock', pro: 'check' },
      { name: 'Export (CSV / JSON)', free: 'lock', pro: 'check' },
    ],
  },
  {
    group: 'Coming Q2',
    items: [
      { name: 'Regions (EU / US / Asia)', free: '—', pro: 'soon' },
      { name: 'Cold Start Analysis', free: '—', pro: 'soon' },
      { name: 'RAG Accuracy Benchmarks', free: '—', pro: 'soon' },
      { name: 'Peak Hours Analysis', free: '—', pro: 'soon' },
      { name: 'Geo Performance', free: '—', pro: 'soon' },
      { name: 'Alerts & Notifications', free: '—', pro: 'soon' },
    ],
  },
];

export const FAQ = [
  {
    q: "What's included in the free version?",
    a: 'Free gives you live TTFT and TPS rankings, basic insights (TTFT, Throughput, Reliability), provider scorecard, head-to-head on 4 metrics, and 7-day data history. Enough to get started.',
  },
  {
    q: 'What does "price locked forever" mean?',
    a: 'Your €19/mo (or €190/year) rate stays the same as long as you remain subscribed. When we raise prices to €49/mo, you keep your founding member rate. No tricks.',
  },
  {
    q: 'Can I cancel anytime?',
    a: 'Yes. Cancel with one click. You keep access until the end of your billing period. No questions, no hoops.',
  },
  {
    q: 'How is the data collected?',
    a: 'We run real API calls to each provider every 5 minutes, 24/7. We measure actual TTFT, TPS, and success rates—not synthetic benchmarks.',
  },
  {
    q: 'What about the Q2 features?',
    a: 'Regions, Cold Start, RAG Accuracy, Peak Hours, Geo, and Alerts are included in Pro at no extra cost. Early Access members get them automatically.',
  },
  {
    q: 'Will there be team plans?',
    a: 'Yes, on the roadmap. For now, Early Pro Access is individual. Need team access sooner? Reach out.',
  },
] as const;
