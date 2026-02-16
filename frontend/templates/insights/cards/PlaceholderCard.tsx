import { InsightCard } from './InsightCard';

interface Props {
  title: string;
  value: string;
  unit?: string;
  isLarge?: boolean;
  tooltipHeader?: string;
  tooltipText?: string;
  pro?: boolean;
  locked?: boolean;
  isActive?: boolean;
}

export function PlaceholderCard({
  title, value, unit, isLarge = true,
  tooltipHeader, tooltipText, pro, locked, isActive,
}: Props) {
  const desc = pro ? 'Pro feature' : locked ? 'Coming Q2' : 'Compare any 2 models';
  return (
    <InsightCard
      title={title}
      metric={value}
      color="white"
      large={isLarge}
      unit={unit}
      description={desc}
      isActive={isActive}
      pro={pro}
      locked={locked}
      tooltipHeader={tooltipHeader}
      tooltipText={tooltipText}
    />
  );
}
