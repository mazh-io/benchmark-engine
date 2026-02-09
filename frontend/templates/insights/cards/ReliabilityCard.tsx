import type { BenchmarkResultWithRelations } from '@/api/types';
import { InsightCard } from './InsightCard';
import { calculateReliability } from '../utils/calculations';

interface Props { results?: BenchmarkResultWithRelations[]; isActive?: boolean }

export function ReliabilityCard({ results, isActive }: Props) {
  const rate = calculateReliability(results);
  return (
    <InsightCard
      title="🎯 Reliability"
      metric={rate > 0 ? `${rate}%` : '—'}
      color="green"
      description="Avg success rate"
      isActive={isActive}
      tooltipHeader="Reliability"
      tooltipText="Success rate, errors, MTBF."
    />
  );
}
