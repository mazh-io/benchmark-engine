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

/* ── shared buttons ── */

function CardActions({ children }: { children: ReactNode }) {
  return <div className="flex gap-2 w-full px-2">{children}</div>;
}

const Btn = ({ label, accent }: { label: string; accent?: boolean }) => (
  <button className={`highlight-btn ${accent ? 'highlight-btn-accent' : 'highlight-btn-default'}`}>
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
      <div className="highlight-insight-text">
        <span className="text-acid">{fName}</span>
        <span className="text-white"> is </span>
        <span className="text-acid">{mul}× faster</span>
        <span className="text-white"> than </span>
        <span className="text-acid">{sName}</span>
        {sModel && <> <span className="text-acid">{sModel}</span></>}
      </div>

      {isExpanded && (
        <>
          <div className="highlight-divider" />

          <div className="mb-3">
            <div className="highlight-section-label">DATA COMPARISON</div>
            <div className="highlight-comparison-box">
              {[
                { name: fName, model: fModel, ms: fastest.avgTTFT, cls: 'text-acid' },
                { name: sName, model: sModel, ms: slowest.avgTTFT, cls: 'text-red-500' },
              ].map((p) => (
                <div key={p.name} className="highlight-ranking-row">
                  <div className="flex items-center gap-1.5">
                    <span className="highlight-provider-name">{p.name}</span>
                    {p.model && <span className="highlight-model">{p.model}</span>}
                  </div>
                  <span className={`${p.cls} font-semibold`}>{Math.round(p.ms).toLocaleString()}ms</span>
                </div>
              ))}

              <div className="highlight-dashed-divider" />
              <div className="highlight-diff-row">
                <span className="highlight-model">Difference:</span>
                <span className="text-acid font-semibold">{mul}×</span>
                <span className="highlight-model">faster</span>
                <span className="highlight-model">/</span>
                <span className="text-acid font-semibold">{diff.toLocaleString()}ms</span>
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
