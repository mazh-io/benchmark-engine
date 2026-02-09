import { useMemo } from 'react';
import type { BenchmarkResultWithRelations } from '@/api/types';
import { groupBy, providerOf, modelOf, nums } from './shared';

export interface ProviderStability {
  provider: string;
  models: number;
  jitter: number;
  p95Ratio: number;
  p99Ratio: number;
  bestFor: string;
  cls: string;
}

function percentile(sorted: number[], p: number): number {
  const idx = Math.floor(sorted.length * p);
  return sorted[Math.min(idx, sorted.length - 1)];
}

function classify(jitter: number): { bestFor: string; cls: string } {
  if (jitter < 20) return { bestFor: 'SLA-critical', cls: 'metric highlight' };
  if (jitter < 35) return { bestFor: 'Predictable', cls: 'metric good' };
  if (jitter < 50) return { bestFor: 'Consistent', cls: 'metric good' };
  if (jitter < 80) return { bestFor: 'Variable', cls: 'metric' };
  return { bestFor: 'Best-effort', cls: 'metric bad' };
}

export function useStabilityStats(results?: BenchmarkResultWithRelations[]) {
  return useMemo(() => {
    if (!results?.length) return { rows: [], champion: 'N/A', championJitter: 0 };

    const groups = groupBy(results, providerOf);
    const rows: ProviderStability[] = [];

    groups.forEach((rr, provider) => {
      const ttfts = nums(rr, (r) => r.ttft_ms);
      if (ttfts.length < 2) return;

      const mean = ttfts.reduce((a, b) => a + b, 0) / ttfts.length;
      const variance = ttfts.reduce((s, v) => s + (v - mean) ** 2, 0) / ttfts.length;
      const jitter = Math.round(Math.sqrt(variance));

      const sorted = [...ttfts].sort((a, b) => a - b);
      const median = sorted[Math.floor(sorted.length / 2)];
      const p95 = percentile(sorted, 0.95);
      const p99 = percentile(sorted, 0.99);

      const p95Ratio = median > 0 ? Math.round((p95 / median) * 10) / 10 : 1;
      const p99Ratio = median > 0 ? Math.round((p99 / median) * 10) / 10 : 1;

      const { bestFor, cls } = classify(jitter);

      rows.push({
        provider,
        models: new Set(rr.map(modelOf)).size,
        jitter,
        p95Ratio,
        p99Ratio,
        bestFor,
        cls,
      });
    });

    rows.sort((a, b) => a.jitter - b.jitter);

    const champion = rows[0]?.provider ?? 'N/A';
    const championJitter = rows[0]?.jitter ?? 0;

    return { rows, champion, championJitter };
  }, [results]);
}

