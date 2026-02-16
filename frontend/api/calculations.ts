/**
 * Calculation Functions for Benchmark Metrics
 *
 * Core formulas for:
 * - Value Score (TPS / Cost Per Million)
 * - Jitter (Standard Deviation of latency)
 * - Statistical aggregations (mean, median, percentiles)
 * - Provider metrics aggregation
 */

import type { BenchmarkResult, ProviderMetrics } from './types';
import { JITTER_THRESHOLDS } from './types';

// ============================================================================
// STATISTICAL HELPERS (internal)
// ============================================================================

function mean(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((sum, val) => sum + val, 0) / values.length;
}

function median(values: number[]): number {
  if (values.length === 0) return 0;

  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);

  return sorted.length % 2 === 0
    ? (sorted[mid - 1] + sorted[mid]) / 2
    : sorted[mid];
}

function percentile(values: number[], p: number): number {
  if (values.length === 0) return 0;

  const sorted = [...values].sort((a, b) => a - b);
  const index = (p / 100) * (sorted.length - 1);
  const lower = Math.floor(index);
  const upper = Math.ceil(index);

  if (lower === upper) return sorted[lower];

  const weight = index - lower;
  return sorted[lower] * (1 - weight) + sorted[upper] * weight;
}

// ============================================================================
// VALUE SCORE (internal)
// ============================================================================

/**
 * Value Score = TPS / Cost Per Million
 * Higher = more tokens per second per dollar
 */
function calculateValueScore(result: BenchmarkResult): number | null {
  if (!result.tps || result.tps <= 0) return null;

  const totalTokens = result.input_tokens + result.output_tokens;
  if (totalTokens === 0) return null;

  const costPerMillion = (result.cost_usd / totalTokens) * 1_000_000;
  const safeCost = costPerMillion > 0 ? costPerMillion : 0.01;

  return Math.round(result.tps / safeCost);
}

function calculateAverageValueScore(results: BenchmarkResult[]): number | null {
  const scores = results
    .map(calculateValueScore)
    .filter((s): s is number => s !== null);

  if (scores.length === 0) return null;
  return Math.round(scores.reduce((sum, s) => sum + s, 0) / scores.length);
}

// ============================================================================
// PRICE PER MILLION (internal)
// ============================================================================

/** Blended price per 1M tokens (input + output) */
function calculatePricePerMillion(result: BenchmarkResult): number {
  const totalTokens = result.input_tokens + result.output_tokens;
  if (totalTokens <= 0 || result.cost_usd <= 0) return 0;
  return (result.cost_usd / totalTokens) * 1_000_000;
}

// ============================================================================
// JITTER / STABILITY (internal)
// ============================================================================

/** Standard deviation of latency values */
function calculateJitter(latencies: number[]): number {
  if (latencies.length < 2) return 0;

  const avg = latencies.reduce((sum, val) => sum + val, 0) / latencies.length;
  const variance =
    latencies.map((val) => (val - avg) ** 2).reduce((sum, val) => sum + val, 0) /
    latencies.length;

  return Math.sqrt(variance);
}

function getJitterColor(jitter: number): 'green' | 'yellow' | 'red' {
  if (jitter < JITTER_THRESHOLDS.GREEN) return 'green';
  if (jitter < JITTER_THRESHOLDS.YELLOW) return 'yellow';
  return 'red';
}

// ============================================================================
// PROVIDER METRICS AGGREGATION (public)
// ============================================================================

/** Aggregate metrics for a single provider from its benchmark results */
function aggregateProviderMetrics(
  providerKey: string,
  results: BenchmarkResult[],
): ProviderMetrics {
  const ttftValues = results
    .map((r) => r.ttft_ms)
    .filter((v): v is number => v !== null && v > 0);

  const latencyValues = results.map((r) => r.total_latency_ms);
  const jitter = calculateJitter(latencyValues);

  const tpsValues = results
    .map((r) => r.tps)
    .filter((v): v is number => v !== null);

  const priceValues = results.map(calculatePricePerMillion).filter((v) => v > 0);

  return {
    provider: providerKey,
    providerDisplayName: providerKey.charAt(0).toUpperCase() + providerKey.slice(1),

    avgTTFT: mean(ttftValues),
    minTTFT: ttftValues.length > 0 ? Math.min(...ttftValues) : 0,
    maxTTFT: ttftValues.length > 0 ? Math.max(...ttftValues) : 0,
    p50TTFT: median(ttftValues),
    p95TTFT: percentile(ttftValues, 95),

    jitter,
    jitterColor: getJitterColor(jitter),

    valueScore: calculateAverageValueScore(results) ?? 0,
    avgTPS: mean(tpsValues),
    avgCost: mean(priceValues),

    sampleSize: results.length,
    lastUpdated: results[0]?.created_at || new Date().toISOString(),
  };
}

/**
 * Aggregate metrics for all providers
 *
 * Groups results by provider key and calculates aggregated metrics for each.
 * This is the only public export — all helpers above are internal.
 */
export function aggregateAllProviderMetrics(
  results: BenchmarkResult[],
): Map<string, ProviderMetrics> {
  const startTime = performance.now();

  // Group by provider
  const byProvider = new Map<string, BenchmarkResult[]>();
  for (const result of results) {
    const provider = result.provider || 'unknown';
    if (!byProvider.has(provider)) {
      byProvider.set(provider, []);
    }
    byProvider.get(provider)!.push(result);
  }

  // Aggregate each
  const metrics = new Map<string, ProviderMetrics>();
  for (const [provider, providerResults] of byProvider.entries()) {
    metrics.set(provider, aggregateProviderMetrics(provider, providerResults));
  }

  if (process.env.NODE_ENV === 'development') {
    const elapsed = (performance.now() - startTime).toFixed(2);
    console.log(`🧮 Aggregated ${metrics.size} providers in ${elapsed}ms`);
  }

  return metrics;
}
