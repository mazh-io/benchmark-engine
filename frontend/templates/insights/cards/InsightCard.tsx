import { StatCard } from '@/templates/stats/StatCard';

type Color = 'acid' | 'green' | 'red' | 'white';

export interface InsightCardProps {
  title: string;
  metric: string;
  color?: Color;
  large?: boolean;
  description: string;
  unit?: string;
  isActive?: boolean;
  featured?: boolean;
  pro?: boolean;
  locked?: boolean;
  tooltipHeader?: string;
  tooltipText?: string;
}

export function InsightCard({
  title, metric, color = 'acid', large = true, description, unit,
  isActive, featured, pro, locked, tooltipHeader, tooltipText,
}: InsightCardProps) {
  const cls = large ? `insight-metric-large-${color}` : 'insight-metric-medium';

  return (
    <StatCard
      title={title}
      featured={featured}
      pro={pro}
      locked={locked}
      isExpanded={false}
      onToggle={() => {}}
      showChevron={false}
      tooltipHeader={tooltipHeader}
      tooltipText={tooltipText}
      isActive={isActive}
    >
      <div className="insight-card-content">
        <div className={cls}>
          {metric}
          {unit && <span className="insight-metric-unit">{unit}</span>}
        </div>
        <div className="insight-description">{description}</div>
      </div>
    </StatCard>
  );
}

