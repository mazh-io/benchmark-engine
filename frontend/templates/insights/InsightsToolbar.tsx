'use client';

import type { ReactElement, ReactNode } from 'react';
import type { TimeFilter } from '@/api/types';

interface Props {
  selectedTime?: TimeFilter;
  onTimeChange?: (time: TimeFilter) => void;
}

const STATIC_FILTERS: { label: string; pills: { text: string; active?: boolean; badge?: string }[] }[] = [
  {
    label: 'Use case',
    pills: [
      { text: 'Ping', badge: 'Q2' },
      { text: 'Chat', active: true },
      { text: 'RAG', badge: 'Q2' },
      { text: 'Image', badge: 'Q2' },
    ],
  },
  {
    label: 'Region',
    pills: [
      { text: 'EU', active: true },
      { text: 'US', badge: 'Q2' },
      { text: 'ASIA', badge: 'Q2' },
    ],
  },
];

const TIME_OPTIONS: { label: string; value: TimeFilter }[] = [
  { label: 'LIVE', value: 'live' },
  { label: '1h', value: '1h' },
  { label: '24h', value: '24h' },
];

const LOCKED_TIMES = ['7d', '30d'];

function FilterGroup({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-center gap-2">
      <span className="filter-label">{label}</span>
      <div className="filter-pill-group">{children}</div>
    </div>
  );
}

export function InsightsToolbar({ selectedTime = 'live', onTimeChange }: Props): ReactElement {
  return (
    <div className="toolbar">
      <div className="filter-row">
        {STATIC_FILTERS.map((group) => (
          <FilterGroup key={group.label} label={group.label}>
            {group.pills.map((p) => (
              <button key={p.text} className={`filter-pill ${p.active ? 'filter-pill-active' : 'filter-pill-muted'}`}>
                <span>{p.text}</span>
                {p.badge && <span className="filter-pill-badge">{p.badge}</span>}
              </button>
            ))}
          </FilterGroup>
        ))}

        <FilterGroup label="Time">
          {TIME_OPTIONS.map((t) => (
            <button key={t.value}
              className={`filter-pill ${selectedTime === t.value ? 'filter-pill-active' : 'filter-pill-muted-hover'}`}
              onClick={() => onTimeChange?.(t.value)}
            >
              <span>{t.label}</span>
            </button>
          ))}
          {LOCKED_TIMES.map((t) => (
            <button key={t} className="filter-pill filter-pill-muted" disabled>
              <span>{t}</span>
              <span className="text-[10px]">🔒</span>
            </button>
          ))}
        </FilterGroup>

        <button className="filter-chip-request-insight ml-auto" onClick={() => alert('Request submitted!')}>
          <span>+</span>
          <span>Request Insight</span>
        </button>
      </div>
    </div>
  );
}
