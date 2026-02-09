'use client';

import type { ReactNode } from 'react';
import type {
  ProviderMetrics,
  BenchmarkResultWithRelations,
} from '@/api/types';
import { resolveModelName } from '@/api/utils';
import { StatCard } from '@/templates/stats/StatCard';

/* ============================================================================
   Primary Value (Top Metric)
============================================================================ */

function PrimaryValue({
  value,
  suffix,
  provider,
  model,
  colorClass,
  blurred,
}: {
  value: string;
  suffix?: string;
  provider?: string;
  model?: string;
  colorClass?: string;
  blurred?: boolean;
}) {
  return (
    <div className={blurred ? 'blur-locked' : ''}>
      <div
        className={`text-[24px] font-semibold leading-none ${
          colorClass ?? 'text-white'
        }`}
      >
        {value}
        {suffix}
      </div>

      {(provider || model) && (
        <div className="mt-1 flex items-center gap-1.5">
          {provider && (
            <span className="text-[11px] font-semibold text-white">
              {provider}
            </span>
          )}
          {model && (
            <span className="text-[11px] text-[#9CA3AF]">
              {model}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

/* ============================================================================
   Expanded Metric List
============================================================================ */

function MetricList({
  title,
  items,
  formatter,
  blurred,
  results,
  firstItemColorClass,
}: {
  title: string;
  items: ProviderMetrics[];
  formatter: (m: ProviderMetrics) => string;
  blurred?: boolean;
  results?: BenchmarkResultWithRelations[];
  firstItemColorClass?: string;
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
                <span className="font-semibold text-white">
                  {m.providerDisplayName || m.provider}
                </span>
                {model && (
                  <span className="text-[11px] text-[#9CA3AF]">
                    {model}
                  </span>
                )}
              </div>

              <span className={i === 0 ? (firstItemColorClass || 'text-acid') : 'text-white'}>
                {formatter(m)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ============================================================================
   Stat Metric Card
============================================================================ */

interface StatMetricCardProps {
  title: string;
  metric?: ProviderMetrics | null;
  list?: ProviderMetrics[];
  listTitle?: string;
  formatter?: (m: ProviderMetrics) => string;
  colorClass?: string;
  locked?: boolean; // For Q2 features (coming soon)
  pro?: boolean; // For Pro features (requires subscription)
  isExpanded: boolean;
  onToggle: () => void;
  actions?: ReactNode;
  results?: BenchmarkResultWithRelations[];
}

export function StatMetricCard({
  title,
  metric,
  list = [],
  listTitle,
  formatter,
  colorClass,
  locked = false,
  pro = false,
  isExpanded,
  onToggle,
  actions,
  results,
}: StatMetricCardProps) {
  const provider = metric?.providerDisplayName || metric?.provider;
  const model = metric
    ? resolveModelName(metric.provider, results)
    : undefined;

  // For TOP 5 STAT CARDS: Use pro for blurring (requires subscription)
  const isBlurred = pro || locked;

  return (
    <StatCard
      title={title}
      locked={locked}
      pro={pro}
      isExpanded={isExpanded}
      onToggle={onToggle}
      showBadge={false}
    >
      {metric ? (
        <PrimaryValue
          value={Math.round(metric.avgTTFT).toLocaleString()}
          suffix="ms"
          provider={provider}
          model={model}
          colorClass={colorClass}
          blurred={isBlurred}
        />
      ) : (
        <PrimaryValue value="—" blurred={isBlurred} />
      )}

      {isExpanded && (
        <>
          <div className="my-5 h-px bg-[#111111]" />

          {listTitle && formatter && (
            <MetricList
              title={listTitle}
              items={list}
              formatter={formatter}
              blurred={isBlurred}
              results={results}
              firstItemColorClass={colorClass}
            />
          )}

          {actions && <div className="mt-5">{actions}</div>}
        </>
      )}
    </StatCard>
  );
}
