'use client';

import type { ReactElement } from 'react';
import type { BenchmarkResultWithRelations } from '@/api/types';
import { useStabilityStats } from './hooks/useStabilityStats';
import { DetailPanel } from './DetailPanel';

interface Props {
  results?: BenchmarkResultWithRelations[];
  onClose: () => void;
}

export function StabilityPanel({ results, onClose }: Props): ReactElement {
  const { rows, champion, championJitter } = useStabilityStats(results);

  return (
    <DetailPanel icon="📊" title="Stability" onClose={onClose} pro="Unlock stability analysis">
      <table className="ranking-table">
        <thead>
          <tr><th>Provider</th><th>Models</th><th>Jitter</th><th>P95/Median</th><th>P99/Median</th><th>Best For</th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.provider}>
              <td className="provider-cell"><span className="provider">{r.provider}</span></td>
              <td>{r.models}</td>
              <td className={r.cls}>σ {r.jitter}ms</td>
              <td>{r.p95Ratio}×</td>
              <td>{r.p99Ratio}×</td>
              <td>{r.bestFor}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="takeaway">
        <div className="takeaway-title">Stability Champion</div>
        <div className="takeaway-text">
          <strong>{champion}</strong> excels with σ {championJitter}ms jitter
          {rows[0] && <> and {rows[0].p99Ratio}× P99/Median ratio</>}.
          {' '}Ideal for <strong>SLA-critical</strong> workloads requiring predictable latency.
        </div>
      </div>
    </DetailPanel>
  );
}
