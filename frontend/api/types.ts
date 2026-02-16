/**
 * TypeScript Types for Benchmark Engine Dashboard
 *
 * Core types used across the frontend application.
 * Mirrors the Supabase database schema for type safety.
 */

// ============================================================================
// DATABASE TYPES
// ============================================================================

/** Provider record from `providers` table */
export interface Provider {
  id: string;
  name: string;
  base_url: string | null;
  logo_url: string | null;
  created_at: string;
}

/** Model record from `models` table */
export interface Model {
  id: string;
  name: string;
  provider_id: string;
  context_window: number | null;
  active: boolean;
  last_seen_at: string;
  created_at: string;
}

/** Benchmark result from `benchmark_results` table */
export interface BenchmarkResult {
  id: string;
  run_id: string;

  // Foreign keys
  provider_id: string | null;
  model_id: string | null;

  // Legacy text fields (backward compatibility)
  provider: string | null;
  model: string | null;

  // Performance metrics
  input_tokens: number;
  output_tokens: number;
  total_latency_ms: number;
  ttft_ms: number | null;
  tps: number | null;

  // Status
  status_code: number | null;
  success: boolean;
  error_message: string | null;
  response_text: string | null;

  // Cost
  cost_usd: number;
  tokens_per_dollar: number | null;

  // Timestamp
  created_at: string;
}

/** Extended benchmark result with joined provider and model data */
export interface BenchmarkResultWithRelations extends BenchmarkResult {
  providers: Provider | null;
  models: Model | null;
}

// ============================================================================
// COMPUTED METRICS
// ============================================================================

/** Aggregated metrics for a single provider */
export interface ProviderMetrics {
  provider: string;
  providerDisplayName: string;

  // Speed
  avgTTFT: number;
  minTTFT: number;
  maxTTFT: number;
  p50TTFT: number;
  p95TTFT: number;

  // Stability
  jitter: number;
  jitterColor: 'green' | 'yellow' | 'red';

  // Value
  valueScore: number;
  avgTPS: number;
  avgCost: number;

  // Metadata
  sampleSize: number;
  lastUpdated: string;
}

// ============================================================================
// FILTERS & UI TYPES
// ============================================================================

/** Direct vs Proxy categorization */
export type ProviderCategory = 'direct' | 'proxy';

/** Time filter options for dashboard */
export type TimeFilter = 'live' | '1h' | '24h' | '7d' | '30d' | '90d';

/** Provider chip for filter bar display */
export interface ProviderChip {
  name: string;
  count: number;
  display: string;
}

// ============================================================================
// CONSTANTS
// ============================================================================

/** Provider classification map (direct API vs aggregator/proxy) */
export const PROVIDER_CATEGORIES: Record<string, ProviderCategory> = {
  // Direct providers
  openai: 'direct',
  anthropic: 'direct',
  google: 'direct',
  deepseek: 'direct',
  groq: 'direct',
  cerebras: 'direct',
  mistral: 'direct',
  fireworks: 'direct',
  sambanova: 'direct',
  together: 'direct',

  // Proxy/Router providers
  openrouter: 'proxy',
};

/** Jitter thresholds in milliseconds */
export const JITTER_THRESHOLDS = {
  GREEN: 200,
  YELLOW: 500,
} as const;

/** Time range options in milliseconds */
export const TIME_RANGES: Record<TimeFilter, number> = {
  live: 0,
  '1h': 1 * 60 * 60 * 1000,
  '24h': 24 * 60 * 60 * 1000,
  '7d': 7 * 24 * 60 * 60 * 1000,
  '30d': 30 * 24 * 60 * 60 * 1000,
  '90d': 90 * 24 * 60 * 60 * 1000,
};
