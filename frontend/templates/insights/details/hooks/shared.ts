import type { BenchmarkResultWithRelations } from '@/api/types';

type R = BenchmarkResultWithRelations;

/** Provider display name from a result */
export const providerOf = (r: R) => r.providers?.name || r.provider || 'Unknown';

/** Model display name from a result */
export const modelOf = (r: R) => r.models?.name || r.model || 'Unknown';

/** Group results by a key function */
export function groupBy(results: R[], keyFn: (r: R) => string) {
  const map = new Map<string, R[]>();
  for (const r of results) {
    const k = keyFn(r);
    const arr = map.get(k);
    arr ? arr.push(r) : map.set(k, [r]);
  }
  return map;
}

/** Extract valid positive numbers from results */
export function nums(results: R[], get: (r: R) => number | null | undefined): number[] {
  return results.map(get).filter((v): v is number => v != null && v > 0);
}

/** Rounded average (0 if empty) */
export function avg(values: number[]): number {
  return values.length ? Math.round(values.reduce((a, b) => a + b, 0) / values.length) : 0;
}

/** Percentage with one decimal: rate(8, 10) → 80.0 */
export function rate(count: number, total: number): number {
  return total > 0 ? Math.round((count / total) * 1000) / 10 : 0;
}

/** Price per 1M tokens (filtered for sanity) */
export function pricesPerM(results: R[]): number[] {
  return results
    .filter((r) => r.cost_usd && r.cost_usd > 0 && r.output_tokens && r.output_tokens > 0)
    .map((r) => (r.cost_usd! / r.output_tokens!) * 1_000_000)
    .filter((p) => p > 0 && p < 1000);
}

