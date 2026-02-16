import type { BenchmarkResultWithRelations } from '@/api/types';
import { InsightCard } from './InsightCard';
import { calculateSpeedGap } from '../utils/calculations';

interface Props { results?: BenchmarkResultWithRelations[]; isActive?: boolean }

export function TTFTAnalysisCard({ results, isActive }: Props) {
  const gap = calculateSpeedGap(results);
  return (
    <InsightCard
      title="⚡ TTFT Analysis"
      metric={gap > 0 ? `${gap}×` : '—'}
      color="acid"
      description={gap > 0 ? 'Speed gap: fastest vs slowest' : 'No data available'}
      isActive={isActive}
      featured
      tooltipHeader="TTFT"
      tooltipText="Time from request to first token. Critical for voice AI."
    />
  );
}
