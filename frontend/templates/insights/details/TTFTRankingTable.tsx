import type { ReactElement } from 'react';
import type { BenchmarkResultWithRelations } from '@/api/types';
import { providerOf, modelOf } from './hooks/shared';

const RANK_CLASSES: Record<number, string> = { 1: 'rank gold', 2: 'rank silver', 3: 'rank bronze' };

interface Props {
  results: BenchmarkResultWithRelations[];
  fastest: number;
  slowest: number;
}

export function TTFTRankingTable({ results, fastest, slowest }: Props): ReactElement {
  return (
    <table className="ranking-table">
      <thead>
        <tr><th>#</th><th>Provider / Model</th><th>TTFT</th><th>vs Best</th><th>Dist</th></tr>
      </thead>
      <tbody>
        {results.slice(0, 6).map((r, i) => {
          const rank = i + 1;
          const ttft = r.ttft_ms || 0;
          const vsHost = fastest ? Math.round((ttft / fastest - 1) * 100) : 0;
          const distPct = fastest ? Math.min((ttft / slowest) * 100, 100) : 0;
          const barColor = rank <= 3 ? 'acid' : vsHost > 100 ? 'red' : 'green';

          return (
            <tr key={r.id}>
              <td className={RANK_CLASSES[rank] || 'rank'}>{rank}</td>
              <td className="provider-cell">
                <span className="provider">{providerOf(r)}</span>{' '}
                <span className="model">{modelOf(r)}</span>
              </td>
              <td className={rank === 1 ? 'metric highlight' : vsHost > 100 ? 'metric bad' : 'metric'}>
                {Math.round(ttft)}ms
              </td>
              <td className={vsHost === 0 ? 'metric good' : vsHost > 100 ? 'metric bad' : 'metric'}>
                {vsHost === 0 ? '—' : `+${vsHost}%`}
              </td>
              <td>
                <div className="mini-bar">
                  <div className={`mini-bar-fill ${barColor}`} style={{ width: `${distPct}%` }} />
                </div>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
