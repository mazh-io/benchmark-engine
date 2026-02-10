import type { BenchmarkResultWithRelations, ProviderMetrics } from '@/api/types';
import { PROVIDER_CATEGORIES } from '@/api/types';
import type { RowData } from './types';

/* ── shared palette ── */

export const STATUS_COLORS = {
  green: { bg: 'bg-[#22c55e]', text: 'text-[#22c55e]', hex: '#22c55e' },
  yellow: { bg: 'bg-yellow-400', text: 'text-yellow-400', hex: '#eab308' },
  red: { bg: 'bg-red-500', text: 'text-red-500', hex: '#ef4444' },
} as const;

export type JitterColor = keyof typeof STATUS_COLORS;

export function getStatusColor(color: JitterColor) {
  return STATUS_COLORS[color];
}

/* ── grid template ── */

export const INDEX_GRID_COLS =
  'grid-cols-[26px_56px_76px_160px_minmax(200px,1fr)_150px_96px_96px_100px_100px_100px_130px]';

export function buildRows(
  results: BenchmarkResultWithRelations[],
  metrics: Map<string, ProviderMetrics>,
  limit = 21,
): RowData[] {
  if (!results.length || !metrics.size) return [];

  const seen = new Set<string>();
  const rows: RowData[] = [];

  for (const result of results) {
    const providerKey =
      (result.provider || result.providers?.name || 'unknown').toLowerCase();
    const modelName = result.models?.name || result.model || 'unknown';
    const key = `${providerKey}:${modelName}`;

    if (seen.has(key)) continue;
    seen.add(key);

    const metric = metrics.get(providerKey);
    if (!metric) continue;

    const category = PROVIDER_CATEGORIES[providerKey] || 'direct';
    const ttft = result.ttft_ms ?? metric.avgTTFT ?? null;
    const tps = result.tps ?? metric.avgTPS ?? null;

    const ttftDelta24h =
      ttft != null && metric.avgTTFT
        ? ((ttft - metric.avgTTFT) / metric.avgTTFT) * 100
        : null;
    const tpsDelta24h =
      tps != null && metric.avgTPS
        ? ((tps - metric.avgTPS) / metric.avgTPS) * 100
        : null;

    rows.push({
      rank: rows.length + 1,
      providerKey,
      providerDisplay:
        metric.providerDisplayName ??
        providerKey.charAt(0).toUpperCase() + providerKey.slice(1),
      modelName,
      type: category === 'proxy' ? 'PROP' : 'OPEN',
      ttftMs: ttft,
      tps,
      ttftDelta24h,
      tpsDelta24h,
      jitterMs: metric.jitter,
      jitterColor: metric.jitterColor,
      pricePerM: metric.avgCost,
      valueScore: metric.valueScore,
    });

    if (rows.length >= limit) break;
  }

  return rows
    .sort((a, b) => (a.ttftMs ?? Infinity) - (b.ttftMs ?? Infinity))
    .map((row, i) => ({ ...row, rank: i + 1 }));
}
