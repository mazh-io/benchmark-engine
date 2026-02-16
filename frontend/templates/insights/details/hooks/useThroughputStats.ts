import { useMemo } from 'react';
import type { BenchmarkResultWithRelations } from '@/api/types';
import { providerOf } from './shared';

export function useThroughputStats(results?: BenchmarkResultWithRelations[]) {
  return useMemo(() => {
    const sorted = results
      ? [...results].sort((a, b) => (b.tps || 0) - (a.tps || 0))
      : [];

    const first = sorted[0];
    const last = sorted.at(-1);
    const fastest = Math.round(first?.tps || 0);
    const slowest = Math.round(last?.tps || 0);

    return {
      sortedResults: sorted,
      fastest,
      slowest,
      gap: fastest && slowest ? Math.round(fastest / slowest) : 0,
      over100: sorted.filter((r) => (r.tps || 0) >= 100).length,
      totalModels: results?.length || 0,
      fastestProvider: first ? providerOf(first) : 'N/A',
      slowestProvider: last ? providerOf(last) : 'N/A',
    };
  }, [results]);
}
