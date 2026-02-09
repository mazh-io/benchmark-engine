import type { BenchmarkResultWithRelations } from '@/api/types';
import { InsightCard } from './InsightCard';
import { calculateProviderCount } from '../utils/calculations';

interface Props { results?: BenchmarkResultWithRelations[]; isActive?: boolean }

export function ProviderRankingsCard({ results, isActive }: Props) {
  const count = calculateProviderCount(results);
  return (
    <InsightCard
      title="🏆 Provider Rankings"
      metric={count > 0 ? String(count) : '—'}
      color="acid"
      description="Providers compared"
      isActive={isActive}
      tooltipHeader="Scorecard"
      tooltipText="All providers compared."
    />
  );
}
