import { useMemo } from 'react';
import type { BenchmarkResultWithRelations } from '@/api/types';

export function useTTFTStats(results?: BenchmarkResultWithRelations[]) {
  return useMemo(() => {
    const sorted = results
      ? [...results].sort((a, b) => (a.ttft_ms || 0) - (b.ttft_ms || 0))
      : [];

    const fastest = Math.round(sorted[0]?.ttft_ms || 0);
    const slowest = Math.round(sorted.at(-1)?.ttft_ms || 0);
    const avgTTFT = sorted.length
      ? Math.round(sorted.reduce((s, r) => s + (r.ttft_ms || 0), 0) / sorted.length)
      : 0;

    return {
      sortedResults: sorted,
      fastest,
      slowest,
      avgTTFT,
      voiceReady: sorted.filter((r) => (r.ttft_ms || 0) < 300).length,
      totalModels: results?.length || 0,
    };
  }, [results]);
}
