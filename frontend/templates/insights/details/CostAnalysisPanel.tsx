'use client';

import type { ReactElement } from 'react';
import type { BenchmarkResultWithRelations } from '@/api/types';
import { useCostStats } from './hooks/useCostStats';
import { DetailPanel } from './DetailPanel';

interface Props {
  results?: BenchmarkResultWithRelations[];
  onClose: () => void;
}

const fmt = (v: number) => `$${v.toFixed(2)}/M`;

export function CostAnalysisPanel({ results, onClose }: Props): ReactElement {
  const { rows, cheapest, expensive, ratio } = useCostStats(results);

  return (
    <DetailPanel icon="💰" title="Cost Analysis" onClose={onClose} pro="Unlock cost analysis">
      <table className="ranking-table">
        <thead>
          <tr><th>Provider</th><th>Models</th><th>Avg Cost</th><th>Min Cost</th><th>Max Cost</th><th>Best For</th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.provider}>
              <td className="provider-cell"><span className="provider">{r.provider}</span></td>
              <td>{r.models}</td>
              <td className={r.cls}>{fmt(r.avg)}</td>
              <td>{fmt(r.min)}</td>
              <td>{fmt(r.max)}</td>
              <td>{r.bestFor}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="takeaway">
        <div className="takeaway-title">Cost Optimization</div>
        <div className="takeaway-text">
          <strong>{cheapest}</strong> offers {ratio}× cheaper pricing than <strong>{expensive}</strong>. Consider {cheapest} for high-volume workloads.
        </div>
      </div>
    </DetailPanel>
  );
}
