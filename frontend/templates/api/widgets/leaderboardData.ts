'use client';

import { useMemo } from 'react';
import { useBenchmarkData } from '@/hooks/useBenchmarkData';
import { useDashboardMetrics } from '@/hooks/useDashboardMetric';
import type { ProviderMetrics } from '@/api/types';
import type { WidgetSize } from './WidgetChrome';

interface LeaderboardRow {
  rank: number;
  provider: string;
  value: string;
  barWidthPercent: number;
}

/** TTFT rows: lower is better → bar scale relative to fastest */
function buildTtftRows(metrics: ProviderMetrics[]): LeaderboardRow[] {
  if (!metrics.length) return [];
  const fastest = metrics[0].avgTTFT || 1;

  return metrics.map((m, i) => ({
    rank: i + 1,
    provider: m.providerDisplayName,
    value: `${Math.round(m.avgTTFT)}ms`,
    barWidthPercent: Math.round((fastest / Math.max(m.avgTTFT, 1)) * 100),
  }));
}

/** TPS rows: higher is better → bar scale relative to best */
function buildTpsRows(metrics: ProviderMetrics[]): LeaderboardRow[] {
  if (!metrics.length) return [];
  const best = metrics[0].avgTPS || 1;

  return metrics.map((m, i) => ({
    rank: i + 1,
    provider: m.providerDisplayName,
    value: `${Math.round(m.avgTPS)}/s`,
    barWidthPercent: Math.round((m.avgTPS / best) * 100),
  }));
}

function sliceForSize<T>(rows: T[], size: WidgetSize): T[] {
  if (size === 's') return rows.slice(0, 3);
  if (size === 'm') return rows.slice(0, 5);
  return rows;
}

export function useTtftLeaderboardRows(size: WidgetSize): LeaderboardRow[] {
  const { data } = useBenchmarkData();
  const { top5Fastest } = useDashboardMetrics(data);

  return useMemo(
    () => sliceForSize(buildTtftRows(top5Fastest ?? []), size),
    [size, top5Fastest],
  );
}

export function useTpsLeaderboardRows(size: WidgetSize): LeaderboardRow[] {
  const { data } = useBenchmarkData();

  const sorted = useMemo<ProviderMetrics[]>(() => {
    if (!data?.metrics) return [];
    return Array.from(data.metrics.values())
      .filter((m) => m.avgTPS > 0)
      .sort((a, b) => b.avgTPS - a.avgTPS)
      .slice(0, 5);
  }, [data]);

  return useMemo(
    () => sliceForSize(buildTpsRows(sorted), size),
    [sorted, size],
  );
}
