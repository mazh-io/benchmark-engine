import { useMemo } from 'react';
import type { BenchmarkResultWithRelations } from '@/api/types';
import { groupBy, providerOf, modelOf, pricesPerM } from './shared';

export interface ProviderCost {
  provider: string;
  models: number;
  avg: number;
  min: number;
  max: number;
  bestFor: string;
  cls: string;
}

function classifyCost(rank: number, total: number): { bestFor: string; cls: string } {
  const pct = rank / total;
  if (rank === 0) return { bestFor: 'Budget', cls: 'metric highlight' };
  if (pct < 0.25) return { bestFor: 'Value', cls: 'metric good' };
  if (pct < 0.5) return { bestFor: 'Balanced', cls: 'metric' };
  if (pct < 0.75) return { bestFor: 'Enterprise', cls: 'metric' };
  return { bestFor: 'Premium', cls: 'metric bad' };
}

export function useCostStats(results?: BenchmarkResultWithRelations[]) {
  return useMemo(() => {
    if (!results?.length) return { rows: [], cheapest: 'N/A', expensive: 'N/A', ratio: '0' };

    const groups = groupBy(results, providerOf);
    const raw: Omit<ProviderCost, 'bestFor' | 'cls'>[] = [];

    groups.forEach((rr, provider) => {
      const prices = pricesPerM(rr);
      if (!prices.length) return;
      raw.push({
        provider,
        models: new Set(rr.map(modelOf)).size,
        avg: prices.reduce((a, b) => a + b, 0) / prices.length,
        min: Math.min(...prices),
        max: Math.max(...prices),
      });
    });

    raw.sort((a, b) => a.avg - b.avg);

    const rows: ProviderCost[] = raw.map((r, i) => {
      const { bestFor, cls } = classifyCost(i, raw.length);
      return { ...r, bestFor, cls };
    });

    const cheapest = rows[0]?.provider ?? 'N/A';
    const expensive = rows.at(-1)?.provider ?? 'N/A';
    const ratio = rows.length >= 2 && rows[0].avg > 0
      ? (rows.at(-1)!.avg / rows[0].avg).toFixed(1)
      : '0';

    return { rows, cheapest, expensive, ratio };
  }, [results]);
}

