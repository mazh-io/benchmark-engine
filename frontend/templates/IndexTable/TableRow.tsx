'use client';

import { useMemo, type ReactElement } from 'react';
import type { RowData } from './types';
import type { JitterColor } from './helpers';
import { INDEX_GRID_COLS, getStatusColor } from './helpers';
import { JitterBar } from './JitterBar';

const BAR_N = 10;
const MAX_JITTER = 10_000;

function TrendChart({ color, value }: { color: JitterColor; value: number }) {
  const { bg } = getStatusColor(color);

  const bars = useMemo(() => {
    const n = Math.min(100, Math.max(10, 100 - (value / MAX_JITTER) * 100));
    return Array.from({ length: BAR_N }, (_, i) =>
      Math.max(2, n * (Math.sin((i / BAR_N) * Math.PI * 2) * 0.3 + 0.7)),
    );
  }, [value]);

  return (
    <div className="flex items-end gap-0.5 h-3">
      {bars.map((h, i) => (
        <div key={i} className={`w-1 rounded-sm ${bg}`} style={{ height: `${h}%` }} />
      ))}
    </div>
  );
}

function Metric({ value, unit, cls }: { value: number | null; unit?: string; cls: string }) {
  if (value == null) return <span className="index-metric-empty">—</span>;
  return (
    <>
      <span className={`index-metric-value ${cls}`}>
        {Math.round(value).toLocaleString()}
      </span>
      {unit && <span className="index-metric-unit">{unit}</span>}
    </>
  );
}

interface Props {
  row: RowData;
  isExpanded: boolean;
  onToggle: () => void;
}

export function TableRow({ row, isExpanded, onToggle }: Props): ReactElement {
  const s = getStatusColor(row.jitterColor);

  return (
    <div
      className={`grid ${INDEX_GRID_COLS} index-row-main cursor-pointer`}
      onClick={onToggle}
    >
      <div
        className="index-row-expand"
        style={{ transform: isExpanded ? 'rotate(90deg)' : undefined, transition: 'transform .15s' }}
      >
        ›
      </div>

      <div className="index-row-rank">
        <span className={s.text}>{row.rank}</span>
      </div>

      <div className="index-row-status">
        <span className={`index-status-dot ${s.bg} animate-status-dot`} />
      </div>

      <div className="index-row-provider">{row.providerDisplay}</div>
      <div className="index-row-model">{row.modelName}</div>

      <div className="index-row-type">
        <span className="index-type-badge">{row.type}</span>
      </div>

      <div className="index-row-metric">
        <Metric value={row.ttftMs} unit="ms" cls={s.text} />
      </div>

      <div className="index-row-metric">
        <Metric value={row.tps} cls={s.text} />
      </div>

      <div className="index-row-jitter">
        <div className="index-jitter-blur"><JitterBar color={row.jitterColor} /></div>
        <span className="index-lock-icon">🔒</span>
      </div>

      <div className="index-row-price">
        <span className={`index-price-value ${s.text}`}>${row.pricePerM.toFixed(2)}</span>
        <span className="index-price-unit"> /M</span>
      </div>

      <div className="index-row-value">
        <span className="index-value-blur">{Math.round(row.valueScore).toLocaleString()}</span>
        <span className="index-lock-icon">🔒</span>
      </div>

      <div className="index-row-trend">
        <div className="flex flex-col items-end gap-1">
          <TrendChart color={row.jitterColor} value={row.jitterMs} />
          <span className="index-trend-delta" style={{ color: s.hex }}>
            {Math.round(row.jitterMs).toLocaleString()}ms
          </span>
        </div>
      </div>
    </div>
  );
}
