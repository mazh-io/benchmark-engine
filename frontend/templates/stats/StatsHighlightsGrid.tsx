'use client';

import type { ReactElement } from 'react';
import type { ProviderMetrics, BenchmarkResultWithRelations } from '@/api/types';
import { resolveModelName } from '@/api/utils';
import { StatMetricCard } from './StatMetricCard';
import { StatCard } from '@/templates/stats/StatCard';

type ExpandedKey =
  | 'fastest'
  | 'slowest'
  | 'bestvalue'
  | 'moststable'
  | 'insight'
  | null;

interface Props {
  expandedCard: ExpandedKey;
  setExpandedCard: (k: ExpandedKey) => void;
  topSpeed: ProviderMetrics | null;
  slowestSpeed: ProviderMetrics | null;
  top5Fastest: ProviderMetrics[];
  bottom5Slowest: ProviderMetrics[];
  top5BestValue: ProviderMetrics[];
  top5MostStable: ProviderMetrics[];
  results?: BenchmarkResultWithRelations[];
}

/* ----------------------------- */
/* Insight Card                  */
/* ----------------------------- */

function InsightCard({
  isExpanded,
  onToggle,
  fastest,
  slowest,
  results,
}: {
  isExpanded: boolean;
  onToggle: () => void;
  fastest: ProviderMetrics | null;
  slowest: ProviderMetrics | null;
  results?: BenchmarkResultWithRelations[];
}) {
  if (!fastest || !slowest) {
    return (
      <StatCard title="💡 INSIGHT" isExpanded={isExpanded} onToggle={onToggle}>
        <div className="text-[12px] text-muted">
          No insight available
        </div>
      </StatCard>
    );
  }

  const multiplier = Math.round(slowest.avgTTFT / fastest.avgTTFT);
  const difference = Math.round(slowest.avgTTFT - fastest.avgTTFT);
  
  const fastestModel = resolveModelName(fastest.provider, results);
  const slowestModel = resolveModelName(slowest.provider, results);
  
  const fastestDisplay = fastest.providerDisplayName || fastest.provider;
  const slowestDisplay = slowest.providerDisplayName || slowest.provider;

  return (
    <StatCard title="💡 INSIGHT" isExpanded={isExpanded} onToggle={onToggle}>
      <div className="text-[13px] font-semibold leading-tight">
        <span className="text-[#CAFF00]">{fastestDisplay}</span>
        <span className="text-white"> is </span>
        <span className="text-[#CAFF00]">{multiplier}× faster</span>
        <span className="text-white"> than </span>
        <span className="text-[#CAFF00]">{slowestDisplay}</span>
        {slowestModel && (
          <>
            <span className="text-white"> </span>
            <span className="text-[#CAFF00]">{slowestModel}</span>
          </>
        )}
      </div>

      {isExpanded && (
        <>
          <div className="my-5 h-px bg-[#111111]" />

          {/* DATA COMPARISON */}
          <div className="mb-3">
            <div className="text-[10px] uppercase tracking-wide text-[#6B7280] mb-3">
              DATA COMPARISON
            </div>

            {/* Single box with all data */}
            <div className="bg-black border border-[#1f1f1f] rounded-md px-3 py-3 space-y-2">
              <div className="flex justify-between items-center text-[12px]">
                <div className="flex items-center gap-1.5">
                  <span className="font-semibold text-white">{fastestDisplay}</span>
                  {fastestModel && (
                    <span className="text-[11px] text-[#9CA3AF]">{fastestModel}</span>
                  )}
                </div>
                <span className="text-[#CAFF00] font-semibold">
                  {Math.round(fastest.avgTTFT).toLocaleString()}ms
                </span>
              </div>
              
              <div className="flex justify-between items-center text-[12px]">
                <div className="flex items-center gap-1.5">
                  <span className="font-semibold text-white">{slowestDisplay}</span>
                  {slowestModel && (
                    <span className="text-[11px] text-[#9CA3AF]">{slowestModel}</span>
                  )}
                </div>
                <span className="text-red-500 font-semibold">
                  {Math.round(slowest.avgTTFT).toLocaleString()}ms
                </span>
              </div>

              {/* Divider - Dashed inside box */}
              <div className="my-2 h-px border-t border-dashed border-[#1f1f1f]" />

              {/* Difference inside box */}
              <div className="text-[11px]">
                <div className="flex items-center justify-center gap-2">
                  <span className="text-[#9CA3AF]">Difference:</span>
                  <span className="text-[#CAFF00] font-semibold">
                    {multiplier}×
                  </span>
                  <span className="text-[#9CA3AF] font-normal">faster</span>
                  <span className="text-[#9CA3AF]">/</span>
                  <span className="text-[#CAFF00] font-semibold">
                    {difference.toLocaleString()}ms
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* All Insights Button */}
          <div className="w-full">
            <button className="w-full inline-flex items-center justify-center gap-1.5 rounded-md px-2.5 py-1.5 text-[11px] font-semibold border border-[#CAFF00] bg-[#1a1f0a] text-[#CAFF00]">
              💡 All Insights
            </button>
          </div>
        </>
      )}
    </StatCard>
  );
}

/* ----------------------------- */
/* Grid                          */
/* ----------------------------- */

export function StatsHighlightsGrid({
  expandedCard,
  setExpandedCard,
  topSpeed,
  slowestSpeed,
  top5Fastest,
  bottom5Slowest,
  top5BestValue,
  top5MostStable,
  results,
}: Props): ReactElement {
  return (
    <div className="stats-highlights-grid grid grid-cols-1 md:grid-cols-5 gap-3">
      {/* ============================================ */}
      {/* TOP 5 STAT CARDS - For key metrics          */}
      {/* ============================================ */}
      
      {/* TOP 5 STAT CARD: FREE FEATURE */}
      <StatMetricCard
        title="FASTEST TTFT"
        metric={topSpeed}
        list={top5Fastest}
        listTitle="TOP 5 FASTEST"
        formatter={(m) => `${Math.round(m.avgTTFT)}ms`}
        colorClass="text-acid"
        isExpanded={expandedCard === 'fastest'}
        onToggle={() =>
          setExpandedCard(expandedCard === 'fastest' ? null : 'fastest')
        }
        results={results}
        actions={
          <div className="flex gap-2 w-full px-2">
            <button className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-md px-2.5 py-1.5 text-[11px] font-semibold border border-[#262626] bg-[#050505] text-white">
              → View in Grid
            </button>
            <button className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-md px-2.5 py-1.5 text-[11px] font-semibold border border-[#CAFF00] bg-[#1a1f0a] text-[#CAFF00]">
              💡 See Insight
            </button>
          </div>
        }
      />

      {/* TOP 5 STAT CARD: FREE FEATURE */}
      <StatMetricCard
        title="SLOWEST TTFT"
        metric={slowestSpeed}
        list={bottom5Slowest}
        listTitle="BOTTOM 5 SLOWEST"
        formatter={(m) => `${Math.round(m.avgTTFT)}ms`}
        colorClass="text-red-500"
        isExpanded={expandedCard === 'slowest'}
        onToggle={() =>
          setExpandedCard(expandedCard === 'slowest' ? null : 'slowest')
        }
        results={results}
        actions={
          <div className="flex gap-2 w-full px-2">
            <button className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-md px-2.5 py-1.5 text-[11px] font-semibold border border-[#262626] bg-[#050505] text-white">
              → View in Grid
            </button>
            <button className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-md px-2.5 py-1.5 text-[11px] font-semibold border border-[#CAFF00] bg-[#1a1f0a] text-[#CAFF00]">
              💡 See Insight
            </button>
          </div>
        }
      />

      {/* TOP 5 STAT CARD: PRO FEATURE (requires subscription) */}
      <StatMetricCard
        title="BEST VALUE 🔒"
        pro
        list={top5BestValue}
        listTitle="TOP 5 VALUE"
        formatter={(m) => m.valueScore.toFixed(2)}
        isExpanded={expandedCard === 'bestvalue'}
        onToggle={() =>
          setExpandedCard(expandedCard === 'bestvalue' ? null : 'bestvalue')
        }
        results={results}
        actions={
          <div className="flex gap-2 w-full px-2">
            <button className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-md px-2.5 py-1.5 text-[11px] font-semibold border border-[#CAFF00] bg-[#1a1f0a] text-[#CAFF00]">
              🔒 Unlock Pro
            </button>
            <button className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-md px-2.5 py-1.5 text-[11px] font-semibold border border-[#262626] bg-[#050505] text-white">
              💡 See Insight
            </button>
          </div>
        }
      />

      {/* TOP 5 STAT CARD: PRO FEATURE (requires subscription) */}
      <StatMetricCard
        title="MOST STABLE 🔒"
        pro
        list={top5MostStable}
        listTitle="TOP 5 MOST STABLE"
        formatter={(m) => `${m.jitter.toFixed(2)}ms`}
        isExpanded={expandedCard === 'moststable'}
        onToggle={() =>
          setExpandedCard(expandedCard === 'moststable' ? null : 'moststable')
        }
        results={results}
        actions={
          <div className="flex gap-2 w-full px-2">
            <button className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-md px-2.5 py-1.5 text-[11px] font-semibold border border-[#CAFF00] bg-[#1a1f0a] text-[#CAFF00]">
              🔒 Unlock Pro
            </button>
            <button className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-md px-2.5 py-1.5 text-[11px] font-semibold border border-[#262626] bg-[#050505] text-white">
              💡 See Insight
            </button>
          </div>
        }
      />

      {/* TOP 5 STAT CARD: INSIGHT CARD */}
      <InsightCard
        isExpanded={expandedCard === 'insight'}
        onToggle={() =>
          setExpandedCard(expandedCard === 'insight' ? null : 'insight')
        }
        fastest={topSpeed}
        slowest={slowestSpeed}
        results={results}
      />
    </div>
  );
}
