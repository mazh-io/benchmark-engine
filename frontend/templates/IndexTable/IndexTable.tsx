'use client';

import { Fragment, useState } from 'react';
import type { BenchmarkResultWithRelations, ProviderMetrics } from '@/api/types';
import { buildRows, INDEX_GRID_COLS } from './index.helper';
import type { IndexRow } from './index.types';
import { IndexRow as Row } from './row/IndexRow';
import { IndexRowExpanded } from './row/IndexRowExpanded';

/* ── column definitions ── */

interface ColDef {
  label: string;
  tip?: { title: string; lines: string[]; width?: string };
  cls?: string;
}

const COLUMNS: ColDef[] = [
  { label: '' },
  { label: '#', cls: 'pl-1' },
  { label: 'Status', tip: { title: 'Status', lines: ['🟢 Operational', '🟡 Degraded', '🔴 Outage'], width: 'w-44' } },
  { label: 'Provider' },
  { label: 'Model' },
  { label: 'Type', tip: { title: 'License', lines: ['Open = Open source', 'Prop = Proprietary'], width: 'w-48' }, cls: 'flex items-center justify-center pl-6' },
  { label: 'TTFT ↑', tip: { title: 'Time to First Token', lines: ['Lower = better'] } },
  { label: 'TPS ↕', tip: { title: 'Tokens/Second', lines: ['Higher = faster'] } },
  { label: 'Jitter', tip: { title: 'Latency σ', lines: ['Lower = stable 🔒'] } },
  { label: 'Price', tip: { title: '$/1M Tokens', lines: ['Blended I/O'] } },
  { label: 'Value', tip: { title: 'Tokens/$', lines: ['Higher = better 🔒'] }, cls: 'text-right' },
  { label: '24h Trend', tip: { title: '24h Trend', lines: ['Click headers to change'] }, cls: 'index-header-trend text-right' },
];

function ColHeader({ label, tip, cls }: ColDef) {
  if (!tip) return <div className={cls}>{label}</div>;

  const group = (
    <div className="index-col-header group">
      <span>{label}</span>
      <div className={`index-col-tooltip ${tip.width ?? 'w-52'}`}>
        <div className="index-col-tooltip-title">{tip.title}</div>
        {tip.lines.map((l) => <div key={l}>{l}</div>)}
      </div>
    </div>
  );

  return cls ? <div className={cls}>{group}</div> : group;
}

/* ── time formatter ── */

const fmtTime = () =>
  new Date().toLocaleTimeString('en-GB', {
    hour: '2-digit', minute: '2-digit', second: '2-digit', timeZone: 'UTC',
  });

/* ── main table ── */

interface Props {
  results: BenchmarkResultWithRelations[];
  metrics: Map<string, ProviderMetrics>;
}

export function IndexTable({ results, metrics }: Props) {
  const [expanded, setExpanded] = useState<number | null>(null);
  const allRows: IndexRow[] = buildRows(results, metrics, 21);
  const primaryCount = Math.min(6, allRows.length);
  const primaryRows = allRows.slice(0, primaryCount);
  const tailRow = allRows.length > primaryCount ? allRows[allRows.length - 1] : null;
  const rows = tailRow ? [...primaryRows, tailRow] : primaryRows;
  const totalCount = allRows.length;

  if (!rows.length) return null;

  return (
    <section className="mt-8 mb-20">
      <div className="index-shell">
        <div className="index-header-row">
          <div className="flex items-center gap-3">
            <span className="index-title">Index</span>
            <a href="#" className="index-title-link">How we test ↗</a>
          </div>
          <div className="index-meta">
            <span>Showing 1–{tailRow ? primaryCount : rows.length}</span>
            <span>{tailRow ? tailRow.rank : totalCount} of {totalCount}</span>
            <span>Last update: <span className="text-[#9CA3AF]">{fmtTime()}</span></span>
          </div>
        </div>

        <div className={`index-header-cols ${INDEX_GRID_COLS}`}>
          {COLUMNS.map((col, i) => <ColHeader key={col.label || i} {...col} />)}
        </div>

        <div className="index-rows-container divide-y divide-[#111111]">
          {rows.map((row) => (
            <Fragment key={row.rank}>
              <Row
                row={row}
                isExpanded={expanded === row.rank}
                onToggle={() => setExpanded(expanded === row.rank ? null : row.rank)}
              />
              {expanded === row.rank && <IndexRowExpanded row={row} />}
            </Fragment>
          ))}
        </div>

        <div className="index-footer">
          <button className="index-footer-btn-locked" disabled>
            Show all {totalCount || rows.length} models ↓
          </button>
        </div>
      </div>
    </section>
  );
}
