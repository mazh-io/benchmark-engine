import { useMemo } from 'react';
import type { BenchmarkResultWithRelations } from '@/api/types';
import { groupBy, providerOf, modelOf, nums, avg, pricesPerM, rate } from './shared';

export interface ModelData {
  id: string;
  provider: string;
  model: string;
  ttft: number;
  tps: number;
  success: number;
  price: number;
  jitter: number;
  p99Ratio: number;
  efficiency: number;
}

export interface ComparisonMetric {
  key: string;
  label: string;
  format: (v: number) => string;
  lowerIsBetter: boolean;
}

export const COMPARISON_METRICS: ComparisonMetric[] = [
  { key: 'ttft', label: 'TTFT', format: (v) => `${v}ms`, lowerIsBetter: true },
  { key: 'tps', label: 'TPS', format: (v) => `${v} tok/s`, lowerIsBetter: false },
  { key: 'success', label: 'Success', format: (v) => `${v}%`, lowerIsBetter: false },
  { key: 'price', label: 'Price', format: (v) => `$${v.toFixed(2)}/M`, lowerIsBetter: true },
  { key: 'jitter', label: 'Jitter 🔒', format: (v) => `σ ${v}ms`, lowerIsBetter: true },
  { key: 'p99Ratio', label: 'P99/Med 🔒', format: (v) => `${v}×`, lowerIsBetter: true },
  { key: 'efficiency', label: 'Efficiency 🔒', format: (v) => `${v}%`, lowerIsBetter: false },
];

/* ── stat helpers ── */

function jitter(ttfts: number[], mean: number): number {
  if (ttfts.length < 2) return 0;
  const variance = ttfts.reduce((s, v) => s + (v - mean) ** 2, 0) / ttfts.length;
  return Math.round(Math.sqrt(variance));
}

function p99Ratio(ttfts: number[]): number {
  if (ttfts.length <= 10) return 1;
  const sorted = [...ttfts].sort((a, b) => a - b);
  const median = sorted[Math.floor(sorted.length / 2)];
  const p99 = sorted[Math.floor(sorted.length * 0.99)];
  return median > 0 ? Math.round((p99 / median) * 10) / 10 : 1;
}

/* ── hook ── */

export function useHeadToHeadStats(results?: BenchmarkResultWithRelations[]) {
  return useMemo(() => {
    if (!results?.length) return { availableModels: [] };

    const groups = groupBy(results, (r) => `${providerOf(r)}|${modelOf(r)}`);
    const models: ModelData[] = [];

    groups.forEach((rr, key) => {
      const [provider, model] = key.split('|');
      const ttfts = nums(rr, (r) => r.ttft_ms);
      const avgTTFT = avg(ttfts);
      const avgTPS = avg(nums(rr, (r) => r.tps));

      const ok = rr.filter((r) => {
        const goodStatus = r.status_code != null && r.status_code >= 200 && r.status_code < 300;
        const validMetrics = r.ttft_ms != null && r.ttft_ms > 0 && r.tps != null && r.tps > 0;
        const noError = !r.error_message?.trim();
        return (goodStatus || validMetrics) && noError;
      }).length;

      const prices = pricesPerM(rr);
      const avgPrice = prices.length ? prices.reduce((a, b) => a + b, 0) / prices.length : 0;

      models.push({
        id: key,
        provider,
        model,
        ttft: avgTTFT,
        tps: avgTPS,
        success: rate(ok, rr.length),
        price: avgPrice,
        jitter: jitter(ttfts, avgTTFT),
        p99Ratio: p99Ratio(ttfts),
        efficiency: avgTPS > 0 && avgTTFT > 0
          ? Math.min(Math.round((avgTPS / avgTTFT) * 10000), 100)
          : 0,
      });
    });

    models.sort((a, b) => a.ttft - b.ttft);
    return { availableModels: models };
  }, [results]);
}
