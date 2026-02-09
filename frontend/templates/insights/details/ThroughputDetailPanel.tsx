'use client';

import type { ReactElement } from 'react';
import type { BenchmarkResultWithRelations } from '@/api/types';
import { useThroughputStats } from './hooks/useThroughputStats';
import { DetailPanel } from './DetailPanel';
import { KeyStatsGrid } from './KeyStatsGrid';
import { ThroughputBarChart } from './ThroughputBarChart';

interface Props {
  results?: BenchmarkResultWithRelations[];
  onClose: () => void;
}

export function ThroughputDetailPanel({ results, onClose }: Props): ReactElement {
  const { sortedResults, fastest, slowest, gap, over100, totalModels, fastestProvider, slowestProvider } =
    useThroughputStats(results);

  const keyStats = [
    { label: 'Fastest', value: fastest.toLocaleString(), valueClass: 'acid', context: fastestProvider },
    { label: 'Slowest', value: slowest, valueClass: 'red', context: slowestProvider },
    { label: 'Gap', value: `${gap}×`, context: 'Fast vs slow' },
    { label: '≥100 tok/s', value: over100, valueClass: 'green', context: 'Models' },
  ];

  const tokens = 500;
  const fastTime = fastest > 0 ? (tokens / fastest).toFixed(2) : '0';
  const slowTime = slowest > 0 ? (tokens / slowest).toFixed(1) : '0';

  return (
    <DetailPanel icon="🚀" title="Throughput" onClose={onClose}>
      <KeyStatsGrid stats={keyStats} />
      <ThroughputBarChart results={sortedResults} />

      <div className="takeaway">
        <div className="takeaway-title">Key Takeaway</div>
        <div className="takeaway-text">
          {tokens} tokens: <strong>{fastestProvider} {fastTime}s</strong> vs {slowestProvider} {slowTime}s. Throughput = time &amp; cost savings.
        </div>
      </div>
    </DetailPanel>
  );
}
