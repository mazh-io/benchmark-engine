'use client';

import type { ReactElement, ReactNode } from 'react';
import type { ProviderMetrics, BenchmarkResultWithRelations } from '@/api/types';
import { resolveModelName } from '@/api/utils';
import { MetricCard } from './MetricCard';
import { HighlightCard } from './HighlightCard';

type ExpandedKey = 'fastest' | 'slowest' | 'bestvalue' | 'moststable' | 'insight' | null;

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

/* ── shared action buttons ── */

function CardActions({ children }: { children: ReactNode }) {
  return <div className="flex gap-2 w-full px-2">{children}</div>;
}

const btnGrid = 'flex-1 inline-flex items-center justify-center gap-1.5 rounded-md px-2.5 py-1.5 text-[11px] font-semibold';
const Btn = ({ label, accent }: { label: string; accent?: boolean }) => (
  <button className={`${btnGrid} ${accent ? 'border border-[#CAFF00] bg-[#1a1f0a] text-[#CAFF00]' : 'border border-[#262626] bg-[#050505] text-white'}`}>
    {label}
  </button>
);

const FreeActions = () => <CardActions><Btn label="→ View in Grid" /><Btn label="💡 See Insight" accent /></CardActions>;
const ProActions = () => <CardActions><Btn label="🔒 Unlock Pro" accent /><Btn label="💡 See Insight" /></CardActions>;

/* ── insight card ── */

function InsightCard({
  isExpanded, onToggle, fastest, slowest, results,
}: {
  isExpanded: boolean; onToggle: () => void;
  fastest: ProviderMetrics | null; slowest: ProviderMetrics | null;
  results?: BenchmarkResultWithRelations[];
}) {
  if (!fastest || !slowest) {
    return (
      <HighlightCard title="💡 INSIGHT" isExpanded={isExpanded} onToggle={onToggle}>
        <div className="text-[12px] text-muted">No insight available</div>
      </HighlightCard>
    );
  }

  const mul = Math.round(slowest.avgTTFT / fastest.avgTTFT);
  const diff = Math.round(slowest.avgTTFT - fastest.avgTTFT);
  const fName = fastest.providerDisplayName || fastest.provider;
  const sName = slowest.providerDisplayName || slowest.provider;
  const fModel = resolveModelName(fastest.provider, results);
  const sModel = resolveModelName(slowest.provider, results);

  return (
    <HighlightCard title="💡 INSIGHT" isExpanded={isExpanded} onToggle={onToggle}>
      <div className="text-[13px] font-semibold leading-tight">
        <span className="text-[#CAFF00]">{fName}</span>
        <span className="text-white"> is </span>
        <span className="text-[#CAFF00]">{mul}× faster</span>
        <span className="text-white"> than </span>
        <span className="text-[#CAFF00]">{sName}</span>
        {sModel && <> <span className="text-[#CAFF00]">{sModel}</span></>}
      </div>

      {isExpanded && (
        <>
          <div className="my-5 h-px bg-[#111111]" />

          <div className="mb-3">
            <div className="text-[10px] uppercase tracking-wide text-[#6B7280] mb-3">DATA COMPARISON</div>
            <div className="bg-black border border-[#1f1f1f] rounded-md px-3 py-3 space-y-2">
              {[
                { name: fName, model: fModel, ms: fastest.avgTTFT, cls: 'text-[#CAFF00]' },
                { name: sName, model: sModel, ms: slowest.avgTTFT, cls: 'text-red-500' },
              ].map((p) => (
                <div key={p.name} className="flex justify-between items-center text-[12px]">
                  <div className="flex items-center gap-1.5">
                    <span className="font-semibold text-white">{p.name}</span>
                    {p.model && <span className="text-[11px] text-[#9CA3AF]">{p.model}</span>}
                  </div>
                  <span className={`${p.cls} font-semibold`}>{Math.round(p.ms).toLocaleString()}ms</span>
                </div>
              ))}

              <div className="my-2 h-px border-t border-dashed border-[#1f1f1f]" />
              <div className="text-[11px] flex items-center justify-center gap-2">
                <span className="text-[#9CA3AF]">Difference:</span>
                <span className="text-[#CAFF00] font-semibold">{mul}×</span>
                <span className="text-[#9CA3AF]">faster</span>
                <span className="text-[#9CA3AF]">/</span>
                <span className="text-[#CAFF00] font-semibold">{diff.toLocaleString()}ms</span>
              </div>
            </div>
          </div>

          <Btn label="💡 All Insights" accent />
        </>
      )}
    </HighlightCard>
  );
}

/* ── main grid ── */

export function HighlightsGrid({
  expandedCard, setExpandedCard,
  topSpeed, slowestSpeed, top5Fastest, bottom5Slowest,
  top5BestValue, top5MostStable, results,
}: Props): ReactElement {
  const toggle = (k: ExpandedKey) => setExpandedCard(expandedCard === k ? null : k);

  return (
    <div className="stats-highlights-grid grid grid-cols-1 md:grid-cols-5 gap-3">
      <MetricCard title="FASTEST TTFT" metric={topSpeed} list={top5Fastest}
        listTitle="TOP 5 FASTEST" formatter={(m) => `${Math.round(m.avgTTFT)}ms`}
        colorClass="text-acid" isExpanded={expandedCard === 'fastest'}
        onToggle={() => toggle('fastest')} results={results} actions={<FreeActions />} />

      <MetricCard title="SLOWEST TTFT" metric={slowestSpeed} list={bottom5Slowest}
        listTitle="BOTTOM 5 SLOWEST" formatter={(m) => `${Math.round(m.avgTTFT)}ms`}
        colorClass="text-red-500" isExpanded={expandedCard === 'slowest'}
        onToggle={() => toggle('slowest')} results={results} actions={<FreeActions />} />

      <MetricCard title="BEST VALUE 🔒" pro list={top5BestValue}
        listTitle="TOP 5 VALUE" formatter={(m) => m.valueScore.toFixed(2)}
        isExpanded={expandedCard === 'bestvalue'}
        onToggle={() => toggle('bestvalue')} results={results} actions={<ProActions />} />

      <MetricCard title="MOST STABLE 🔒" pro list={top5MostStable}
        listTitle="TOP 5 MOST STABLE" formatter={(m) => `${m.jitter.toFixed(2)}ms`}
        isExpanded={expandedCard === 'moststable'}
        onToggle={() => toggle('moststable')} results={results} actions={<ProActions />} />

      <InsightCard isExpanded={expandedCard === 'insight'} onToggle={() => toggle('insight')}
        fastest={topSpeed} slowest={slowestSpeed} results={results} />
    </div>
  );
}
