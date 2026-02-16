'use client';

import { useState, type ReactElement } from 'react';
import type { BenchmarkResultWithRelations, ProviderMetrics } from '@/api/types';
import { TTFTAnalysisCard } from './cards/TTFTAnalysisCard';
import { ThroughputCard } from './cards/ThroughputCard';
import { ReliabilityCard } from './cards/ReliabilityCard';
import { ProviderRankingsCard } from './cards/ProviderRankingsCard';
import { CostAnalysisCard } from './cards/CostAnalysisCard';
import { PlaceholderCard } from './cards/PlaceholderCard';
import { EfficiencyCard } from './cards/EfficiencyCard';
import { StabilityCard } from './cards/StabilityCard';
import { TTFTDetailPanel } from './details/TTFTDetailPanel';
import { ThroughputDetailPanel } from './details/ThroughputDetailPanel';
import { ReliabilityDetailPanel } from './details/ReliabilityDetailPanel';
import { ProviderScorecardPanel } from './details/ProviderScorecardPanel';
import { HeadToHeadPanel } from './details/HeadToHeadPanel';
import { CostAnalysisPanel } from './details/CostAnalysisPanel';
import { EfficiencyPanel } from './details/EfficiencyPanel';
import { StabilityPanel } from './details/StabilityPanel';

interface Props {
  results?: BenchmarkResultWithRelations[];
  metrics?: Map<string, ProviderMetrics>;
}

type InsightType = 'ttft' | 'throughput' | 'reliability' | 'providers' | 'head-to-head' | 'cost' | 'efficiency' | 'stability' | null;

const Q2_CARDS: { title: string; value: string; unit?: string; isLarge?: boolean; header: string; tip: string }[] = [
  { title: '❄️ Cold Start', value: '+347', unit: 'ms', isLarge: false, header: 'Cold Start', tip: 'Coming Q2 with multi-region.' },
  { title: '🎯 RAG Accuracy', value: '94.2', unit: '%', header: 'RAG Accuracy', tip: 'Coming Q2 with RAG workload.' },
  { title: '⏰ Peak Hours', value: '+82', unit: '%', header: 'Peak Hours', tip: 'Coming Q2 with 24h data.' },
  { title: '🌍 Geo Performance', value: 'EU vs US', isLarge: false, header: 'Geo Performance', tip: 'Coming Q2 with multi-region.' },
];

export function InsightsGrid({ results, metrics }: Props): ReactElement {
  const [active, setActive] = useState<InsightType>(null);
  const toggle = (t: InsightType) => setActive(active === t ? null : t);
  const close = () => setActive(null);

  const viewProviders = () => {
    setActive('providers');
    setTimeout(() => {
      document.querySelector('.insight-detail.active')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  };

  return (
    <>
      <div className="insights-grid">
        <div onClick={() => toggle('ttft')}>
          <TTFTAnalysisCard results={results} isActive={active === 'ttft'} />
        </div>
        <div onClick={() => toggle('throughput')}>
          <ThroughputCard results={results} isActive={active === 'throughput'} />
        </div>
        <div onClick={() => toggle('reliability')}>
          <ReliabilityCard results={results} isActive={active === 'reliability'} />
        </div>
        <div onClick={() => toggle('providers')}>
          <ProviderRankingsCard results={results} isActive={active === 'providers'} />
        </div>
        <div onClick={() => toggle('head-to-head')}>
          <PlaceholderCard title="⚔️ Head-to-Head" value="VS" isLarge={false}
            tooltipHeader="Head-to-Head" tooltipText="Compare any 2 models." isActive={active === 'head-to-head'} />
        </div>
        <div onClick={() => toggle('cost')}>
          <CostAnalysisCard metrics={metrics} isActive={active === 'cost'} />
        </div>
        <div onClick={() => toggle('efficiency')}>
          <EfficiencyCard results={results} isActive={active === 'efficiency'} />
        </div>
        <div onClick={() => toggle('stability')}>
          <StabilityCard results={results} isActive={active === 'stability'} />
        </div>

        {Q2_CARDS.map((c) => (
          <PlaceholderCard key={c.title} title={c.title} value={c.value} unit={c.unit}
            isLarge={c.isLarge} locked tooltipHeader={c.header} tooltipText={c.tip} />
        ))}
      </div>

      {active === 'ttft' && <TTFTDetailPanel results={results} onClose={close} />}
      {active === 'throughput' && <ThroughputDetailPanel results={results} onClose={close} />}
      {active === 'reliability' && <ReliabilityDetailPanel results={results} onClose={close} />}
      {active === 'providers' && <ProviderScorecardPanel results={results} onClose={close} />}
      {active === 'head-to-head' && <HeadToHeadPanel results={results} onClose={close} onViewProviders={viewProviders} />}
      {active === 'cost' && <CostAnalysisPanel results={results} onClose={close} />}
      {active === 'efficiency' && <EfficiencyPanel results={results} onClose={close} />}
      {active === 'stability' && <StabilityPanel results={results} onClose={close} />}
    </>
  );
}
