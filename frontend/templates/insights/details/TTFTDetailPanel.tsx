'use client';

import type { ReactElement } from 'react';
import type { BenchmarkResultWithRelations } from '@/api/types';
import { providerOf, modelOf } from './hooks/shared';
import { useTTFTStats } from './hooks/useTTFTStats';
import { DetailPanel } from './DetailPanel';
import { KeyStatsGrid } from './KeyStatsGrid';
import { TTFTBarChart } from './TTFTBarChart';
import { TTFTRankingTable } from './TTFTRankingTable';

interface Props {
  results?: BenchmarkResultWithRelations[];
  onClose: () => void;
}

export function TTFTDetailPanel({ results, onClose }: Props): ReactElement {
  const { sortedResults, fastest, slowest, avgTTFT, voiceReady, totalModels } = useTTFTStats(results);

  const first = sortedResults[0];
  const last = sortedResults.at(-1);

  const voiceReadyProviders = sortedResults
    .filter((r) => (r.ttft_ms || 0) < 300)
    .map(providerOf)
    .filter((v, i, a) => a.indexOf(v) === i)
    .slice(0, 2);

  const keyStats = [
    { label: 'Fastest', value: `${fastest}ms`, valueClass: 'acid', context: first ? `${providerOf(first)} ${modelOf(first)}`.trim() : 'N/A' },
    { label: 'Slowest', value: `${slowest}ms`, valueClass: 'red', context: last ? `${providerOf(last)} ${modelOf(last)}`.trim() : 'N/A' },
    { label: 'Industry Avg', value: `${avgTTFT}ms`, context: `${totalModels} models` },
    { label: 'Voice-Ready', value: voiceReady, valueClass: 'green', context: 'Under 300ms' },
  ];

  return (
    <DetailPanel icon="⚡" title="TTFT Analysis" onClose={onClose}>
      <KeyStatsGrid stats={keyStats} />
      <TTFTBarChart results={sortedResults} />
      <TTFTRankingTable results={sortedResults} fastest={fastest} slowest={slowest} />

      <div className="takeaway">
        <div className="takeaway-title">Key Takeaway</div>
        <div className="takeaway-text">
          {voiceReadyProviders.length > 0 ? (
            <>
              For <strong>voice AI</strong> (&lt;300ms),{' '}
              {voiceReadyProviders.map((p, i) => (
                <span key={p}>{i > 0 && ' and '}<strong>{p}</strong></span>
              ))}{' '}
              qualify. {last ? providerOf(last) : 'N/A'}&apos;s {slowest}ms = &quot;thinking time&quot;.
            </>
          ) : (
            <>No providers currently meet the &lt;300ms voice-ready threshold.</>
          )}
        </div>
      </div>
    </DetailPanel>
  );
}
