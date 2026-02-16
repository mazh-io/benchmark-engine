import { useMemo } from 'react';
import type { ProviderMetrics } from '@/api/types';
import type { BenchmarkDataResult } from '@/hooks/useBenchmarkData';

/** Derived dashboard metrics from raw benchmark data */
export function useDashboardMetrics(data?: BenchmarkDataResult) {
  return useMemo(() => {
    if (!data?.metrics) {
      return {
        metrics: [],
        topSpeed: null,
        slowestSpeed: null,
        top5Fastest: [],
        bottom5Slowest: [],
        top5BestValue: [],
        top5MostStable: [],
        providerChips: [],
      };
    }

    const metrics = Array.from(data.metrics.values());

    // Sort once, reuse for both single + top-5
    const byTTFTAsc = [...metrics].sort((a, b) => a.avgTTFT - b.avgTTFT);
    const byTTFTDesc = [...metrics].sort((a, b) => b.avgTTFT - a.avgTTFT);
    const byValueDesc = [...metrics].sort((a, b) => b.valueScore - a.valueScore);
    const byJitterAsc = [...metrics].sort((a, b) => a.jitter - b.jitter);

    // Build provider → models map for chips
    const providerMap = new Map<string, Set<string>>();
    for (const r of data.results) {
      const providerName = r.provider || r.providers?.name;
      const modelName = r.model || r.models?.name;
      if (!providerName || !modelName) continue;

      if (!providerMap.has(providerName)) {
        providerMap.set(providerName, new Set());
      }
      providerMap.get(providerName)!.add(modelName);
    }

    const providerChips = [...providerMap.entries()]
      .map(([name, models]) => ({
        name: name.toLowerCase(),
        count: models.size,
        display: `${name} ${models.size}`,
      }))
      .sort((a, b) => a.name.localeCompare(b.name));

    return {
      metrics,
      topSpeed: byTTFTAsc[0] ?? null,
      slowestSpeed: byTTFTDesc[0] ?? null,
      top5Fastest: byTTFTAsc.slice(0, 5),
      bottom5Slowest: byTTFTDesc.slice(0, 5),
      top5BestValue: byValueDesc.slice(0, 5),
      top5MostStable: byJitterAsc.slice(0, 5),
      providerChips,
    };
  }, [data]);
}
