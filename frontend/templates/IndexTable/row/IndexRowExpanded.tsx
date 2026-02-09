'use client';

import type { ReactElement } from 'react';
import type { IndexRow } from '../index.types';
import { getStatusColor } from '../index.helper';

const TIME_RANGES = ['1h', '24h', '7d', '30d', '90d'] as const;
const PRICE_COMPARISONS = ['Fireworks', 'Together'] as const;

type Accent = 'acid' | 'green' | '';

/* ── helpers ── */

const fmt = (v: number | null) =>
  v != null ? Math.round(v).toLocaleString() : '—';

function ComparisonValue({
  label, idx, locked, delta,
}: {
  label: string; idx: number; locked: boolean; delta: number | null;
}): ReactElement {
  // 24h real delta (unlocked metrics only)
  if (idx === 1 && !locked && typeof delta === 'number') {
    const up = delta <= 0;
    return (
      <span className={`index-expand-comparison-value ${up ? 'up' : 'down'}`}>
        {up ? '▲' : '▼'} {Math.abs(delta).toFixed(0)}%
      </span>
    );
  }

  // Locked: all ranges for locked metrics, 7d+ for TTFT/TPS
  if (locked || ((label === 'TTFT' || label === 'TPS') && idx >= 2)) {
    return <span className="index-expand-comparison-value locked">🔒</span>;
  }

  return <span className="opacity-40">—</span>;
}

/* ── metric card ── */

interface CardProps {
  label: string;
  value: string;
  unit?: string;
  accent?: Accent;
  locked?: boolean;
  delta?: number | null;
}

function MetricCard({ label, value, unit, accent = '', locked = false, delta = null }: CardProps) {
  const isPrice = label === 'Price';

  return (
    <div className="index-expand-metric-card">
      <div className="index-expand-metric-label">
        <span className="index-expand-metric-label-text">{label}</span>
      </div>

      <div className="index-expand-metric-value-wrapper">
        <div className={`index-expand-metric-value ${accent} ${locked ? 'locked' : ''}`}>
          {value}
        </div>
        {unit && <div className="index-expand-metric-unit">{unit}</div>}
      </div>

      <div className="index-expand-metric-divider" />

      <div className="index-expand-metric-comparison">
        {isPrice
          ? PRICE_COMPARISONS.map((name) => (
              <div key={name} className="index-expand-comparison-row">
                <span>vs. {name}</span>
                <span className="index-expand-comparison-value blur">{value}</span>
              </div>
            ))
          : TIME_RANGES.map((t, i) => (
              <div key={t} className="index-expand-comparison-row">
                <span>vs. {t}</span>
                <ComparisonValue label={label} idx={i} locked={locked} delta={delta} />
              </div>
            ))}
      </div>

      <div className="index-expand-metric-footer">
        {(['Best', 'Worst'] as const).map((k) => (
          <div key={k} className="index-expand-footer-row">
            <span>{k}</span><span>—</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── main expanded row ── */

export function IndexRowExpanded({ row }: { row: IndexRow }): ReactElement {
  const priceAccent: Accent = row.jitterColor === 'green' ? 'green' : '';

  const cards: CardProps[] = [
    { label: 'TTFT', value: fmt(row.ttftMs), unit: 'ms', accent: 'acid', delta: row.ttftDelta24h },
    { label: 'TPS', value: fmt(row.tps), unit: 'tok/s', accent: 'green', delta: row.tpsDelta24h },
    { label: 'Jitter', value: fmt(row.jitterMs), unit: 'ms σ', locked: true },
    { label: 'Price', value: `$${row.pricePerM.toFixed(2)}`, unit: '/1M tok', accent: priceAccent },
    { label: 'Value', value: fmt(row.valueScore), unit: 'tok/$', locked: true },
  ];

  return (
    <div className="index-expand-row">
      <div className="index-expand-metric-grid">
        {cards.map((c) => <MetricCard key={c.label} {...c} />)}
      </div>

      <div className="index-expand-actions">
        <button className="index-expand-btn-primary">🔒 Unlock Pro</button>
        <button className="index-expand-btn">⚔ Head-to-Head</button>
        <button className="index-expand-btn">→ Detail Page</button>
      </div>
    </div>
  );
}
