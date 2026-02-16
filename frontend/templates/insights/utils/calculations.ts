import type { BenchmarkResultWithRelations, ProviderMetrics } from '@/api/types';

/** Speed gap: slowest TTFT ÷ fastest TTFT */
export function calculateSpeedGap(results?: BenchmarkResultWithRelations[]): number {
  if (!results?.length) return 0;
  const ttfts = results.map((r) => r.ttft_ms).filter((t): t is number => t != null);
  if (ttfts.length < 2) return 0;
  return Math.round(Math.max(...ttfts) / Math.min(...ttfts));
}

/** Cost spread: most expensive ÷ cheapest */
export function calculateCostSpread(metrics?: Map<string, ProviderMetrics>): number {
  if (!metrics?.size) return 0;
  const costs = Array.from(metrics.values()).map((m) => m.avgCost);
  const max = Math.max(...costs);
  const min = Math.min(...costs);
  return max && min ? Math.round((max / min) * 10) / 10 : 0;
}

/** Peak TPS + provider name */
export function calculatePeakTPS(
  results?: BenchmarkResultWithRelations[],
): { value: number; provider: string } {
  if (!results?.length) return { value: 0, provider: 'N/A' };
  const top = results
    .filter((r) => r.tps != null && r.tps > 0)
    .sort((a, b) => (b.tps || 0) - (a.tps || 0))[0];
  return {
    value: top?.tps || 0,
    provider: top?.providers?.name || top?.provider || 'N/A',
  };
}

/** Average success rate (%) */
export function calculateReliability(results?: BenchmarkResultWithRelations[]): number {
  const total = results?.length || 0;
  if (!total) return 0;
  const ok = results!.filter((r) => r.status_code === 200).length;
  return Math.round((ok / total) * 1000) / 10;
}

/** Number of unique providers */
export function calculateProviderCount(results?: BenchmarkResultWithRelations[]): number {
  return new Set(
    results?.map((r) => r.providers?.name || r.provider).filter(Boolean),
  ).size;
}
