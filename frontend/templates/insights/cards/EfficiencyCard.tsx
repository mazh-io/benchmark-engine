import type { BenchmarkResultWithRelations } from '@/api/types';
import { InsightCard } from './InsightCard';
import { useEfficiencyStats } from '../details/hooks/useEfficiencyStats';

interface Props { results?: BenchmarkResultWithRelations[]; isActive?: boolean }

export function EfficiencyCard({ results, isActive }: Props) {
  const { leader, leaderEff } = useEfficiencyStats(results);
  return (
    <InsightCard
      title="💬 Efficiency"
      metric={leaderEff > 0 ? `${leaderEff}` : '—'}
      unit="%"
      color="white"
      description={leaderEff > 0 ? `Top: ${leader}` : 'No data available'}
      isActive={isActive}
      pro
      tooltipHeader="Efficiency 🔒"
      tooltipText="Same answer, fewer tokens."
    />
  );
}
