'use client';

import { useState, type ReactElement } from 'react';
import type { BenchmarkResultWithRelations } from '@/api/types';
import { useHeadToHeadStats, COMPARISON_METRICS } from './hooks/useHeadToHeadStats';
import { DetailPanel } from './DetailPanel';
import { HeadToHeadTable } from './HeadToHeadTable';
import { HeadToHeadBenchmark } from './HeadToHeadBenchmark';

interface Props {
  results?: BenchmarkResultWithRelations[];
  onClose: () => void;
  onViewProviders: () => void;
}

export function HeadToHeadPanel({ results, onClose, onViewProviders }: Props): ReactElement {
  const { availableModels } = useHeadToHeadStats(results);
  const [selectedModel1, setSelectedModel1] = useState(availableModels[0]?.id || '');
  const [selectedModel2, setSelectedModel2] = useState(availableModels[1]?.id || '');

  const model1 = availableModels.find((m) => m.id === selectedModel1) || availableModels[0];
  const model2 = availableModels.find((m) => m.id === selectedModel2) || availableModels[1];

  if (!model1 || !model2) {
    return (
      <DetailPanel icon="⚔️" title="Head-to-Head" onClose={onClose}>
        <p style={{ textAlign: 'center', padding: '40px', color: 'var(--text-3)' }}>
          Not enough models for comparison
        </p>
      </DetailPanel>
    );
  }

  return (
    <DetailPanel icon="⚔️" title="Head-to-Head" onClose={onClose}>
      <HeadToHeadTable
        model1={model1}
        model2={model2}
        metrics={COMPARISON_METRICS}
        availableModels={availableModels}
        selectedModel1={selectedModel1}
        selectedModel2={selectedModel2}
        onChangeModel1={setSelectedModel1}
        onChangeModel2={setSelectedModel2}
      />
      <HeadToHeadBenchmark
        model1={model1}
        model2={model2}
        allModels={availableModels}
        onViewProviders={onViewProviders}
      />
    </DetailPanel>
  );
}
