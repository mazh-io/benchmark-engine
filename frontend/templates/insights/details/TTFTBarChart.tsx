import { useMemo } from 'react';
import type { ReactElement } from 'react';
import type { BenchmarkResultWithRelations } from '@/api/types';
import { providerOf, modelOf } from './hooks/shared';

const BAR_COLORS = ['acid', 'acid', 'green', 'green', 'green', 'yellow', 'yellow', 'red', 'red'];
const COLOR_HEX: Record<string, string> = { acid: '#caff00', green: '#22c55e', yellow: '#eab308', red: '#ef4444' };

interface Props { results: BenchmarkResultWithRelations[] }

function buildYAxis(max: number): number[] {
  const ceil = Math.ceil(max / 1000) * 1000 || 1000;
  const step = ceil > 5000 ? 1000 : ceil > 2000 ? 500 : 200;
  const labels: number[] = [];
  for (let v = ceil; v >= 0; v -= step) labels.push(v);
  return labels;
}

export function TTFTBarChart({ results }: Props): ReactElement {
  const rows = results.slice(0, 9);
  const max = Math.max(...rows.map((r) => r.ttft_ms || 0));
  const min = Math.min(...rows.map((r) => r.ttft_ms || 0));
  const yAxis = useMemo(() => buildYAxis(max), [max]);

  return (
    <div className="chart-container">
      <div className="chart-bars">
        {rows.map((r, i) => {
          const ttft = r.ttft_ms || 0;
          const pct = max > 0 ? ((ttft - min) / (max - min)) * 90 + 10 : 10;
          const color = BAR_COLORS[i] || 'green';
          const provider = providerOf(r);
          const modelShort = modelOf(r).split('-').slice(0, 2).join(' ');

          return (
            <div key={r.id} className="chart-bar-wrapper" style={{ position: 'relative' }}>
              <div className="chart-bar-container">
                <div
                  className={`chart-bar chart-bar-${color}`}
                  style={{ height: `${pct}%`, backgroundColor: COLOR_HEX[color] }}
                  title={`${provider}: ${Math.round(ttft)}ms`}
                >
                  &nbsp;
                </div>
              </div>
              <div className="chart-bar-label">{provider} {modelShort}</div>
            </div>
          );
        })}
      </div>

      <div className="chart-y-axis">
        {yAxis.map((v) => (
          <div key={v} className="chart-y-label">{v}ms</div>
        ))}
      </div>
    </div>
  );
}
