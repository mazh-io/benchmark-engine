import { useMemo } from 'react';
import type { BenchmarkResultWithRelations } from '@/api/types';
import { InsightCard } from './InsightCard';
import { calculatePeakTPS } from '../utils/calculations';

interface Props { results?: BenchmarkResultWithRelations[]; isActive?: boolean }

export function ThroughputCard({ results, isActive }: Props) {
  const { value, provider } = useMemo(() => calculatePeakTPS(results), [results]);
  return (
    <InsightCard
      title="🚀 Throughput"
      metric={value > 0 ? Math.round(value).toLocaleString() : '—'}
      color="green"
      description={value > 0 ? `Peak tok/s (${provider})` : 'No data available'}
      isActive={isActive}
      tooltipHeader="TPS"
      tooltipText="Generation speed. Higher = faster streaming."
    />
  );
}
