import { useMemo } from 'react';
import type { BenchmarkResultWithRelations } from '@/api/types';
import { groupBy, providerOf, modelOf, nums, avg } from './shared';

export interface ProviderEfficiency {
  provider: string;
  models: number;
  efficiency: number;
  tokensPerDollar: string;
  speedLabel: string;
  bestFor: string;
  cls: string;
}

function speedLabel(tps: number): string {
  if (tps > 1000) return 'Ultra-fast';
  if (tps > 400) return 'Fast';
  if (tps > 200) return 'Balanced';
  if (tps > 100) return 'Moderate';
  return 'Slow';
}

function bestFor(tps: number, eff: number): string {
  if (tps > 1000) return 'Streaming';
  if (eff >= 85) return 'Real-time';
  if (eff >= 70) return 'Batch';
  if (eff >= 50) return 'Mixed';
  if (eff >= 30) return 'Quality';
  return 'Budget';
}

function effCls(eff: number): string {
  if (eff >= 80) return 'metric highlight';
  if (eff >= 60) return 'metric good';
  if (eff >= 40) return 'metric';
  return 'metric';
}

function formatTokens(tpd: number): string {
  if (tpd >= 1_000_000) return `${(tpd / 1_000_000).toFixed(1)}M/$`;
  if (tpd >= 1_000) return `${Math.round(tpd / 1_000)}K/$`;
  return `${Math.round(tpd)}/$`;
}

export function useEfficiencyStats(results?: BenchmarkResultWithRelations[]) {
  return useMemo(() => {
    if (!results?.length) return { rows: [], leader: 'N/A', leaderEff: 0 };

    const groups = groupBy(results, providerOf);
    const rows: ProviderEfficiency[] = [];

    groups.forEach((rr, provider) => {
      const tpsVals = nums(rr, (r) => r.tps);
      const avgTPS = avg(tpsVals);

      // Tokens per dollar
      const totalTokens = rr.reduce((s, r) => s + (r.output_tokens || 0), 0);
      const totalCost = rr.reduce((s, r) => s + (r.cost_usd || 0), 0);
      const tpd = totalCost > 0 ? totalTokens / totalCost : 0;

      // Efficiency score: normalized TPS × success / cost (0–100)
      const successRate = rr.filter((r) => r.success === true || r.status_code === 200).length / rr.length;
      const costPerToken = totalCost > 0 && totalTokens > 0 ? totalCost / totalTokens : 1;
      const rawEff = avgTPS * successRate / (costPerToken * 1_000_000);
      // Will normalize after collecting all providers

      rows.push({
        provider,
        models: new Set(rr.map(modelOf)).size,
        efficiency: rawEff,
        tokensPerDollar: formatTokens(tpd),
        speedLabel: speedLabel(avgTPS),
        bestFor: bestFor(avgTPS, 0), // placeholder, update after normalize
        cls: '',
      });
    });

    // Normalize efficiency to 0–100
    const maxEff = Math.max(...rows.map((r) => r.efficiency), 1);
    rows.forEach((r) => {
      r.efficiency = Math.round((r.efficiency / maxEff) * 100);
      r.cls = effCls(r.efficiency);
      r.bestFor = bestFor(0, r.efficiency);
    });

    // Override bestFor with speed-based label for top TPS providers
    rows.forEach((r) => {
      if (r.speedLabel === 'Ultra-fast') r.bestFor = 'Streaming';
      else if (r.speedLabel === 'Fast' && r.efficiency >= 80) r.bestFor = 'Real-time';
    });

    rows.sort((a, b) => b.efficiency - a.efficiency);

    const leader = rows[0]?.provider ?? 'N/A';
    const leaderEff = rows[0]?.efficiency ?? 0;

    return { rows, leader, leaderEff };
  }, [results]);
}

