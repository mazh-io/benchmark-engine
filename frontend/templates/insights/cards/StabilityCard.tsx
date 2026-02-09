import type { BenchmarkResultWithRelations } from '@/api/types';
import { InsightCard } from './InsightCard';
import { useStabilityStats } from '../details/hooks/useStabilityStats';

interface Props { results?: BenchmarkResultWithRelations[]; isActive?: boolean }

export function StabilityCard({ results, isActive }: Props) {
  const { rows, champion } = useStabilityStats(results);
  const p99 = rows[0]?.p99Ratio ?? 0;
  return (
    <InsightCard
      title="📊 Stability"
      metric={p99 > 0 ? `${p99}` : '—'}
      unit="×"
      color="white"
      description={p99 > 0 ? `P99/Med (${champion})` : 'No data available'}
      isActive={isActive}
      pro
      tooltipHeader="Stability 🔒"
      tooltipText="Jitter, P95/P99 for SLA."
    />
  );
}
