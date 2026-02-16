'use client';

import type { ReactElement } from 'react';
import type { BenchmarkResultWithRelations } from '@/api/types';
import { useEfficiencyStats } from './hooks/useEfficiencyStats';
import { DetailPanel } from './DetailPanel';

interface Props {
  results?: BenchmarkResultWithRelations[];
  onClose: () => void;
}

export function EfficiencyPanel({ results, onClose }: Props): ReactElement {
  const { rows, leader, leaderEff } = useEfficiencyStats(results);

  return (
    <DetailPanel icon="💬" title="Efficiency" onClose={onClose} pro="Unlock efficiency analysis">
      <table className="ranking-table">
        <thead>
          <tr><th>Provider</th><th>Models</th><th>Efficiency</th><th>Tokens/Cost</th><th>Speed/Cost</th><th>Best For</th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.provider}>
              <td className="provider-cell"><span className="provider">{r.provider}</span></td>
              <td>{r.models}</td>
              <td className={r.cls}>{r.efficiency}%</td>
              <td>{r.tokensPerDollar}</td>
              <td>{r.speedLabel}</td>
              <td>{r.bestFor}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="takeaway">
        <div className="takeaway-title">Efficiency Leader</div>
        <div className="takeaway-text">
          <strong>{leader}</strong> leads with {leaderEff}% efficiency.
          {rows[1] && <> <strong>{rows[1].provider}</strong> follows at {rows[1].efficiency}%.</>}
        </div>
      </div>
    </DetailPanel>
  );
}
