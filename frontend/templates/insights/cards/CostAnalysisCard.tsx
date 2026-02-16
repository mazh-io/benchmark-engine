import type { ProviderMetrics } from '@/api/types';
import { InsightCard } from './InsightCard';
import { calculateCostSpread } from '../utils/calculations';

interface Props { metrics?: Map<string, ProviderMetrics>; isActive?: boolean }

export function CostAnalysisCard({ metrics, isActive }: Props) {
  const spread = calculateCostSpread(metrics);
  return (
    <InsightCard
      title="💰 Cost Analysis"
      metric={spread > 0 ? `${spread}×` : '—'}
      color="red"
      description={spread > 0 ? 'Price spread' : 'No data available'}
      isActive={isActive}
      pro
      tooltipHeader="Cost 🔒"
      tooltipText="Price analysis & optimization."
    />
  );
}
