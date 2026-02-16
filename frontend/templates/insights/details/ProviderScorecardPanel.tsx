'use client';

import type { ReactElement } from 'react';
import type { BenchmarkResultWithRelations } from '@/api/types';
import { useProviderScorecardStats } from './hooks/useProviderScorecardStats';
import { DetailPanel } from './DetailPanel';
import { ProviderScorecardTable } from './ProviderScorecardTable';

interface Props {
  results?: BenchmarkResultWithRelations[];
  onClose: () => void;
}

const USE_CASE_MAP = [
  { match: 'Voice', emoji: '🎙️', label: 'Voice' },
  { match: 'Batch', emoji: '📦', label: 'Batch' },
  { match: 'Reasoning', emoji: '🔬', label: 'Reasoning' },
] as const;

export function ProviderScorecardPanel({ results, onClose }: Props): ReactElement {
  const { providerScores } = useProviderScorecardStats(results);

  const budgetLeader = providerScores.find((p) => p.avgTTFT > 0)?.provider;
  const leaders = USE_CASE_MAP
    .map((uc) => ({ ...uc, provider: providerScores.find((p) => p.bestFor.includes(uc.match))?.provider }))
    .filter((uc) => uc.provider);

  return (
    <DetailPanel icon="🏆" title="Provider Scorecard" onClose={onClose}>
      <ProviderScorecardTable providerScores={providerScores} />

      <div className="takeaway">
        <div className="takeaway-title">Use Case Guide</div>
        <div className="takeaway-text">
          {leaders.map((uc) => (
            <span key={uc.label}><strong>{uc.emoji} {uc.label}:</strong> {uc.provider} | </span>
          ))}
          {budgetLeader && <><strong>💰 Budget:</strong> {budgetLeader}</>}
          {!leaders.length && !budgetLeader && <>No enough data for use case recommendations.</>}
        </div>
      </div>
    </DetailPanel>
  );
}
