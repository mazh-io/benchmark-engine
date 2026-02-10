'use client';

import type { ReactNode } from 'react';
import type { ProviderMetrics, BenchmarkResultWithRelations } from '@/api/types';
import { resolveModelName } from '@/api/utils';
import { HighlightCard } from './HighlightCard';

/* ── sub-components ── */

function PrimaryValue({
  value, suffix, provider, model, colorClass, blurred,
}: {
  value: string; suffix?: string; provider?: string; model?: string;
  colorClass?: string; blurred?: boolean;
}) {
  return (
    <div className={blurred ? 'blur-locked' : ''}>
      <div className={`text-[24px] font-semibold leading-none ${colorClass ?? 'text-white'}`}>
        {value}{suffix}
      </div>
      {(provider || model) && (
        <div className="mt-1 flex items-center gap-1.5">
          {provider && <span className="text-[11px] font-semibold text-white">{provider}</span>}
          {model && <span className="text-[11px] text-[#9CA3AF]">{model}</span>}
        </div>
      )}
    </div>
  );
}

function RankingList({
  title, items, formatter, blurred, results, accentClass,
}: {
  title: string; items: ProviderMetrics[];
  formatter: (m: ProviderMetrics) => string;
  blurred?: boolean; results?: BenchmarkResultWithRelations[];
  accentClass?: string;
}) {
  if (!items.length) return null;
  return (
    <div className="mt-5">
      <div className="index-expand-label mb-2">{title}</div>
      <div className={`space-y-2 ${blurred ? 'blur-locked' : ''}`}>
        {items.map((m, i) => {
          const model = resolveModelName(m.provider, results);
          return (
            <div key={m.provider} className="flex justify-between items-center text-[12px]">
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-white">{m.providerDisplayName || m.provider}</span>
                {model && <span className="text-[11px] text-[#9CA3AF]">{model}</span>}
              </div>
              <span className={i === 0 ? (accentClass || 'text-acid') : 'text-white'}>
                {formatter(m)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ── main card ── */

interface Props {
  title: string;
  metric?: ProviderMetrics | null;
  list?: ProviderMetrics[];
  listTitle?: string;
  formatter?: (m: ProviderMetrics) => string;
  colorClass?: string;
  locked?: boolean;
  pro?: boolean;
  isExpanded: boolean;
  onToggle: () => void;
  actions?: ReactNode;
  results?: BenchmarkResultWithRelations[];
}

export function MetricCard({
  title, metric, list = [], listTitle, formatter, colorClass,
  locked = false, pro = false, isExpanded, onToggle, actions, results,
}: Props) {
  const provider = metric?.providerDisplayName || metric?.provider;
  const model = metric ? resolveModelName(metric.provider, results) : undefined;
  const isBlurred = pro || locked;

  return (
    <HighlightCard title={title} locked={locked} pro={pro}
      isExpanded={isExpanded} onToggle={onToggle} showBadge={false}>
      {metric ? (
        <PrimaryValue value={Math.round(metric.avgTTFT).toLocaleString()} suffix="ms"
          provider={provider} model={model} colorClass={colorClass} blurred={isBlurred} />
      ) : (
        <PrimaryValue value="—" blurred={isBlurred} />
      )}

      {isExpanded && (
        <>
          <div className="my-5 h-px bg-[#111111]" />
          {listTitle && formatter && (
            <RankingList title={listTitle} items={list} formatter={formatter}
              blurred={isBlurred} results={results} accentClass={colorClass} />
          )}
          {actions && <div className="mt-5">{actions}</div>}
        </>
      )}
    </HighlightCard>
  );
}
