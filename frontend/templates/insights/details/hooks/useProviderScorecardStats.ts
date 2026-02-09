import { useMemo } from 'react';
import type { BenchmarkResultWithRelations } from '@/api/types';
import { groupBy, providerOf, modelOf, nums, avg, pricesPerM } from './shared';

interface ProviderScore {
  provider: string;
  modelCount: number;
  avgTTFT: number;
  avgTPS: number;
  priceRange: string;
  bestFor: string;
}

function formatPriceRange(prices: number[]): string {
  if (!prices.length) return 'N/A';
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  return Math.abs(max - min) < 0.1
    ? `$${min.toFixed(2)}`
    : `$${min.toFixed(2)}–$${max.toFixed(2)}`;
}

function classify(ttft: number, tps: number): string {
  if (!ttft || !tps) return 'General';
  if (ttft < 300 && tps > 400) return 'Voice, real-time';
  if (tps > 1000) return 'Batch, throughput';
  if (ttft < 500) return 'Balanced';
  if (ttft > 2000) return 'Long context';
  if (ttft > 1500) return 'Reasoning';
  return 'General';
}

export function useProviderScorecardStats(results?: BenchmarkResultWithRelations[]) {
  return useMemo(() => {
    if (!results?.length) return { providerScores: [] };

    const groups = groupBy(results, providerOf);
    const scores: ProviderScore[] = [];

    groups.forEach((rr, provider) => {
      const ttft = avg(nums(rr, (r) => r.ttft_ms));
      const tps = avg(nums(rr, (r) => r.tps));
      scores.push({
        provider,
        modelCount: new Set(rr.map(modelOf)).size,
        avgTTFT: ttft,
        avgTPS: tps,
        priceRange: formatPriceRange(pricesPerM(rr)),
        bestFor: classify(ttft, tps),
      });
    });

    scores.sort((a, b) => (a.avgTTFT || Infinity) - (b.avgTTFT || Infinity));
    return { providerScores: scores };
  }, [results]);
}
