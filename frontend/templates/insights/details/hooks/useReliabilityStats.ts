import { useMemo } from 'react';
import type { BenchmarkResultWithRelations } from '@/api/types';
import { groupBy, providerOf, rate } from './shared';

type R = BenchmarkResultWithRelations;

/* ── predicates (reused for per-provider + overall) ── */

const isOk = (r: R) => r.success === true || r.status_code === 200;

const is5xx = (r: R) =>
  (r.status_code != null && r.status_code >= 500 && r.status_code < 600) ||
  (r.success === false && r.error_message != null);

const isStalled = (r: R) => (r.ttft_ms || 0) > 2000;

function mtbf(total: number, ok: number): string {
  const failures = total - ok;
  if (failures === 0) return '∞';
  if (total < 10) return 'N/A';
  const hours = total / 12 / failures; // 12 req/hour (1 every 5 min)
  if (hours >= 100) return '99+h';
  if (hours < 0.1) return '<0.1h';
  return `${hours.toFixed(1)}h`;
}

interface ProviderReliability {
  provider: string;
  success: number;
  stall: number;
  errors5xx: number;
  mtbf: string;
}

export function useReliabilityStats(results?: BenchmarkResultWithRelations[]) {
  return useMemo(() => {
    if (!results?.length) {
      return {
        providerStats: [], avgSuccess: 0, totalRequests: '0/0',
        stallRate: 0, errors5xx: 0, bestMTBF: '0h', bestMTBFProvider: 'N/A',
      };
    }

    const groups = groupBy(results, providerOf);
    const providerStats: ProviderReliability[] = [];

    groups.forEach((rr, provider) => {
      const total = rr.length;
      const ok = rr.filter(isOk).length;
      providerStats.push({
        provider,
        success: rate(ok, total),
        stall: rate(rr.filter(isStalled).length, total),
        errors5xx: rate(rr.filter(is5xx).length, total),
        mtbf: mtbf(total, ok),
      });
    });

    providerStats.sort((a, b) => b.success - a.success);

    const total = results.length;
    const ok = results.filter(isOk).length;
    const best = providerStats[0];

    return {
      providerStats,
      avgSuccess: rate(ok, total),
      totalRequests: `${ok.toLocaleString()}/${total.toLocaleString()}`,
      stallRate: rate(results.filter(isStalled).length, total),
      errors5xx: rate(results.filter(is5xx).length, total),
      bestMTBF: best?.mtbf ?? '0h',
      bestMTBFProvider: best?.provider ?? 'N/A',
    };
  }, [results]);
}
