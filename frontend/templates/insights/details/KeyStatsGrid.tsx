import type { ReactElement } from 'react';

interface KeyStat {
  label: string;
  value: string | number;
  valueClass?: string;
  context: string;
}

interface Props {
  stats: KeyStat[];
}

export function KeyStatsGrid({ stats }: Props): ReactElement {
  return (
    <div className="key-stats-grid">
      {stats.map((stat, index) => (
        <div key={index} className="key-stat">
          <div className="key-stat-label">{stat.label}</div>
          <div className={`key-stat-value ${stat.valueClass || ''}`}>
            {stat.value}
          </div>
          <div className="key-stat-context">{stat.context}</div>
        </div>
      ))}
    </div>
  );
}

