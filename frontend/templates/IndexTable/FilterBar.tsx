'use client';

import { useState, type ReactElement } from 'react';
import type { TimeFilter, ProviderChip } from '@/api/types';

interface FilterBarProps {
  totalProviders: number;
  providerChips: ProviderChip[];
  selectedTime?: TimeFilter;
  onTimeChange?: (time: TimeFilter) => void;
}

export function FilterBar({
  totalProviders,
  providerChips,
  selectedTime = 'live',
  onTimeChange,
}: FilterBarProps): ReactElement {
  const [showPayloads, setShowPayloads] = useState(false);
  const [activeProvider, setActiveProvider] = useState('all');

  return (
    <div className="mt-6">
      <div className="filter-shell">
        {/* ========================= */}
        {/* TOP ROW                  */}
        {/* ========================= */}
        <div className="filter-row">
          {/* USE CASE */}
          <div
            className="relative flex items-center gap-2"
            onMouseEnter={() => setShowPayloads(true)}
            onMouseLeave={() => setShowPayloads(false)}
          >
            <span className="filter-label">Use case</span>

            <div className="filter-pill-group">
              {['Ping', 'Chat', 'RAG', 'Image', 'Cold Start'].map((item) => {
                const active = item === 'Chat';

                return (
                  <button
                    key={item}
                    className={`filter-pill ${
                      active
                        ? 'filter-pill-active'
                        : 'filter-pill-muted'
                    }`}
                  >
                    <span>{item}</span>
                    {!active && (
                      <span className="filter-pill-badge">Q2</span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* PAYLOAD POPOVER */}
            {showPayloads && (
              <div className="absolute top-full left-1/2 z-50 mt-3 w-80 -translate-x-1/2 rounded-2xl border border-[#262626] bg-[#050505] px-5 py-4 shadow-xl">
                <div className="text-center text-[13px] font-semibold mb-3">
                  Test Payloads
                </div>

                <div className="h-px bg-[#262626] mb-3" />

                <div className="space-y-1.5 text-[11px]">
                  {[
                    ['Ping', '~50 tok'],
                    ['Chat', '~500 tok'],
                    ['RAG', '~2000 tok'],
                    ['Image', 'Img + prompt'],
                    ['Cold Start', 'First req'],
                  ].map(([label, value]) => (
                    <div
                      key={label}
                      className="flex justify-between text-muted"
                    >
                      <span>{label}</span>
                      <span className="text-acid">{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* REGION */}
          <div className="flex items-center gap-2">
            <span className="filter-label">Region</span>

            <div className="filter-pill-group">
              {['EU', 'US', 'ASIA'].map((region) => {
                const active = region === 'EU';

                return (
                  <button
                    key={region}
                    className={`filter-pill ${
                      active
                        ? 'filter-pill-active'
                        : 'filter-pill-muted'
                    }`}
                  >
                    <span>{region}</span>
                    {!active && (
                      <span className="filter-pill-badge">Q2</span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* TIME */}
          <div className="flex items-center gap-2">
            <span className="filter-label">Time</span>

            <div className="filter-pill-group">
              {(['LIVE', '1h', '24h', '7d', '30d', '90d'] as const).map((t) => {
                const timeValue = t.toLowerCase() as TimeFilter;
                const active = selectedTime === timeValue;
                const locked = ['7d', '30d', '90d'].includes(t);

                return (
                  <button
                    key={t}
                    disabled={locked}
                    onClick={() => !locked && onTimeChange?.(timeValue)}
                    className={`filter-pill ${
                      active
                        ? 'filter-pill-active'
                        : locked
                        ? 'filter-pill-muted'
                        : 'filter-pill-muted-hover'
                    }`}
                  >
                    <span>{t}</span>
                    {locked && <span className="text-[10px]">🔒</span>}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* ========================= */}
        {/* DIVIDER                  */}
        {/* ========================= */}
        <div className="my-4 h-px bg-[#1f1f1f]" />

        {/* ========================= */}
        {/* SEARCH + PROVIDERS        */}
        {/* ========================= */}
        <div className="flex flex-wrap items-center gap-3">
          {/* SEARCH */}
          <input
            placeholder="Search models..."
            className="filter-search-input"
          />

          {/* PROVIDERS */}
          {[
            {
              name: 'all',
              display: `All ${totalProviders}`,
              count: totalProviders,
            },
            ...providerChips,
          ].map((p) => (
            <button
              key={p.display}
              onClick={() => setActiveProvider(p.name)}
              className={`filter-chip ${
                activeProvider === p.name ? 'active' : ''
              } ${
                p.name.toLowerCase() === 'google'
                  ? 'filter-chip-google'
                  : ''
              }`}
            >
              {p.display}
            </button>
          ))}

          {/* REQUEST */}
          <button className="filter-chip-request">
            <span className="filter-chip-request-plus">+</span>
            <span>Request Model</span>
          </button>
        </div>
      </div>
    </div>
  );
}
