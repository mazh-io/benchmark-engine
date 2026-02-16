'use client';

import type { ReactElement } from 'react';
import type { BenchmarkResultWithRelations } from '@/api/types';
import { useReliabilityStats } from './hooks/useReliabilityStats';
import { DetailPanel } from './DetailPanel';
import { KeyStatsGrid } from './KeyStatsGrid';
import { ReliabilityRankingTable } from './ReliabilityRankingTable';

interface Props {
  results?: BenchmarkResultWithRelations[];
  onClose: () => void;
}

export function ReliabilityDetailPanel({ results, onClose }: Props): ReactElement {
  const { providerStats, avgSuccess, totalRequests, stallRate, errors5xx, bestMTBF, bestMTBFProvider } =
    useReliabilityStats(results);

  const keyStats = [
    { label: 'Avg Success', value: `${avgSuccess}%`, valueClass: 'green', context: totalRequests },
    { label: 'Stall Rate', value: `${stallRate}%`, context: '>2s TTFT' },
    { label: '5xx', value: `${errors5xx}%`, context: 'Server errors' },
    { label: 'Best MTBF', value: bestMTBF, valueClass: 'green', context: bestMTBFProvider },
  ];

  const highStall = providerStats.find((p) => p.stall > 20);
  const best = providerStats[0];

  return (
    <DetailPanel icon="🎯" title="Reliability" onClose={onClose}>
      <KeyStatsGrid stats={keyStats} />
      <ReliabilityRankingTable providerStats={providerStats} />

      <div className="takeaway">
        <div className="takeaway-title">Key Takeaway</div>
        <div className="takeaway-text">
          <strong>{bestMTBFProvider}</strong> leads ({best?.success}%, {best?.stall}% stall).
          {highStall && <> {highStall.provider} {highStall.stall}% stall = thinking.</>}
          {' '}Use <strong>multi-provider fallback</strong>.
        </div>
      </div>
    </DetailPanel>
  );
}
