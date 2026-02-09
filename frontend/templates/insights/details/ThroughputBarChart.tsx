import { useMemo } from 'react';
import type { ReactElement } from 'react';
import type { BenchmarkResultWithRelations } from '@/api/types';
import { providerOf, modelOf } from './hooks/shared';

const BAR_COLORS = ['acid', 'green', 'green', 'green', 'yellow', 'yellow', 'red', 'red', 'red'];
const COLOR_HEX: Record<string, string> = { acid: '#caff00', green: '#22c55e', yellow: '#eab308', red: '#ef4444' };

interface Props { results: BenchmarkResultWithRelations[] }

function buildXAxis(max: number): number[] {
  const ceil = Math.ceil(max / 200) * 200 || 200;
  const labels: number[] = [];
  for (let v = 0; v <= ceil; v += 200) labels.push(v);
  return labels;
}

export function ThroughputBarChart({ results }: Props): ReactElement {
  const rows = results.slice(0, 9);
  const maxTPS = Math.max(...rows.map((r) => r.tps || 0));
  const xAxis = useMemo(() => buildXAxis(maxTPS), [maxTPS]);

  return (
    <div className="throughput-chart-container">
      <div className="throughput-chart-bars">
        {rows.map((r, i) => {
          const tps = r.tps || 0;
          const pct = maxTPS > 0 ? (tps / maxTPS) * 100 : 0;
          const color = BAR_COLORS[i] || 'green';
          const provider = providerOf(r);
          const model = modelOf(r);
          const label = model.includes('8b') ? `${provider} 8b`
            : model.includes('70b') ? `${provider} 70b`
            : provider;

          return (
            <div key={r.id} className="throughput-bar-row">
              <div className="throughput-bar-label">{label}</div>
              <div className="throughput-bar-container">
                <div
                  className={`throughput-bar throughput-bar-${color}`}
                  style={{ width: `${pct}%`, backgroundColor: COLOR_HEX[color] }}
                >
                  <div className="chart-bar-tooltip">
                    <div className="chart-bar-tooltip-name">{provider}</div>
                    <div className={`chart-bar-tooltip-value ${color}`}>
                      TPS: {Math.round(tps).toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="throughput-x-axis">
        {xAxis.map((v) => (
          <div key={v} className="throughput-x-label">{v} tok/s</div>
        ))}
      </div>
    </div>
  );
}
