'use client';

import { useMemo } from 'react';
import { useBenchmarkData } from '@/hooks/useBenchmarkData';
import { useDashboardMetrics } from '@/hooks/useDashboardMetric';

/** Provider Card Widget */

interface ProviderCardData {
  providerName: string;
  modelName: string;
  ttft: number;
  tps: number;
  successRate: number;
  sparklineData: number[];
}

export function useProviderCardData(providerSlug = 'groq'): ProviderCardData | null {
  const { data } = useBenchmarkData();

  return useMemo(() => {
    if (!data?.metrics) return null;

    const slug = providerSlug.toLowerCase();
    const metric = Array.from(data.metrics.values()).find(
      (m) => m.provider?.toLowerCase() === slug,
    );
    if (!metric) return null;

    const providerResults = data.results.filter(
      (r) => r.provider?.toLowerCase() === slug,
    );

    const successCount = providerResults.filter((r) => r.success).length;
    const successRate = providerResults.length > 0
      ? successCount / providerResults.length
      : 0;

    // Sparkline from recent TTFT values (normalized 0–100%)
    const recentTTFTs = providerResults
      .filter((r) => r.ttft_ms)
      .slice(-12)
      .map((r) => r.ttft_ms ?? 0);
    const maxVal = Math.max(...recentTTFTs, 1);
    const sparklineData = recentTTFTs.map((v) => Math.round((v / maxVal) * 100));

    return {
      providerName: metric.providerDisplayName || providerSlug,
      modelName: providerResults[0]?.model || 'Unknown',
      ttft: Math.round(metric.avgTTFT),
      tps: Math.round(metric.avgTPS),
      successRate: Math.round(successRate * 1000) / 10,
      sparklineData,
    };
  }, [data, providerSlug]);
}

/** Comparison Widget */

interface ComparisonProviderStats {
  name: string;
  model: string;
  ttft: number;
  tps: number;
  successRate: number;
}

interface ComparisonData {
  provider1: ComparisonProviderStats;
  provider2: ComparisonProviderStats;
}

export function useComparisonData(
  provider1Slug = 'groq',
  provider2Slug = 'together',
): ComparisonData | null {
  const { data } = useBenchmarkData();

  return useMemo(() => {
    if (!data?.metrics) return null;

    const metrics = Array.from(data.metrics.values());

    // Try exact match first, then fall back to fastest/next-fastest
    let m1 = metrics.find((m) => m.provider?.toLowerCase() === provider1Slug.toLowerCase()) ?? null;
    let m2 = metrics.find((m) => m.provider?.toLowerCase() === provider2Slug.toLowerCase()) ?? null;

    if (!m1 || !m2) {
      const sorted = [...metrics].sort((a, b) => a.avgTTFT - b.avgTTFT);
      m1 = m1 ?? sorted[0] ?? null;
      m2 = m2 ?? sorted.find((m) => m.provider !== m1?.provider) ?? sorted[1] ?? null;
    }
    if (!m1 || !m2) return null;

    const buildStats = (metric: typeof m1): ComparisonProviderStats => {
      const slug = metric!.provider?.toLowerCase() ?? '';
      const results = data.results.filter((r) => r.provider?.toLowerCase() === slug);
      const successRate = results.length > 0
        ? results.filter((r) => r.success).length / results.length
        : 0;

      return {
        name: metric!.providerDisplayName || metric!.provider || 'Unknown',
        model: results[0]?.model || metric!.provider || 'Unknown',
        ttft: Math.round(metric!.avgTTFT),
        tps: Math.round(metric!.avgTPS),
        successRate: Math.round(successRate * 1000) / 10,
      };
    };

    return { provider1: buildStats(m1), provider2: buildStats(m2) };
  }, [data, provider1Slug, provider2Slug]);
}

/** Insight Widget */

interface InsightData {
  fastestProvider: { name: string; model: string; ttft: number };
  slowestProvider: { name: string; model: string; ttft: number };
  multiplier: number;
  difference: number;
}

export function useInsightData(): InsightData | null {
  const { data } = useBenchmarkData();
  const { topSpeed, slowestSpeed } = useDashboardMetrics(data);

  return useMemo(() => {
    if (!topSpeed || !slowestSpeed || !data) return null;

    const fastResult = data.results.find((r) => r.provider === topSpeed.provider);
    const slowResult = data.results.find((r) => r.provider === slowestSpeed.provider);

    return {
      fastestProvider: {
        name: topSpeed.providerDisplayName || topSpeed.provider || 'Unknown',
        model: fastResult?.model || 'Unknown',
        ttft: Math.round(topSpeed.avgTTFT),
      },
      slowestProvider: {
        name: slowestSpeed.providerDisplayName || slowestSpeed.provider || 'Unknown',
        model: slowResult?.model || 'Unknown',
        ttft: Math.round(slowestSpeed.avgTTFT),
      },
      multiplier: Math.round(slowestSpeed.avgTTFT / topSpeed.avgTTFT),
      difference: Math.round(slowestSpeed.avgTTFT - topSpeed.avgTTFT),
    };
  }, [data, topSpeed, slowestSpeed]);
}
