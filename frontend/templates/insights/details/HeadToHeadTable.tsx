'use client';

import { useState, useRef, useEffect } from 'react';
import type { ReactElement } from 'react';
import type { ModelData, ComparisonMetric } from './hooks/useHeadToHeadStats';

/* ── delta helper ── */

function computeDelta(v1: number, v2: number, m: ComparisonMetric) {
  if (v1 == null || v2 == null) return { winner: 'equal' as const, text: '—' };
  if (Math.abs(v1 - v2) < 0.01) return { winner: 'equal' as const, text: 'Equal' };

  const winner: 'violet' | 'teal' = m.lowerIsBetter
    ? (v1 < v2 ? 'violet' : 'teal')
    : (v1 > v2 ? 'violet' : 'teal');

  const [hi, lo] = v1 > v2 ? [v1, v2] : [v2, v1];
  const text = m.key === 'success'
    ? `+${(hi - lo).toFixed(1)}%`
    : `${(hi / lo).toFixed(1)}× ${m.lowerIsBetter ? 'faster' : 'higher'}`;

  return { winner, text };
}

/* ── dropdown hook ── */

function useDropdown(models: ModelData[]) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const ref = useRef<HTMLDivElement>(null);

  const filtered = models.filter((m) =>
    `${m.provider} ${m.model}`.toLowerCase().includes(query.toLowerCase()),
  );

  const close = () => { setOpen(false); setQuery(''); };
  return { open, setOpen, query, setQuery, ref, filtered, close };
}

/* ── model selector column header ── */

function ModelSelector({
  model, accent, dd, selectedId, onSelect,
}: {
  model: ModelData;
  accent: string;
  dd: ReturnType<typeof useDropdown>;
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  const grouped = new Map<string, ModelData[]>();
  dd.filtered.forEach((m) => {
    const arr = grouped.get(m.provider);
    arr ? arr.push(m) : grouped.set(m.provider, [m]);
  });

  const label = `${model.provider} ${model.model}`;

  return (
    <th className={`h2h-col-val ${accent}`}>
      <div className="h2h-header-selector" ref={dd.ref}>
        <input
          type="text"
          className="h2h-search-input"
          placeholder={dd.open ? 'Search models...' : label}
          value={dd.open ? dd.query : label}
          onChange={(e) => dd.setQuery(e.target.value)}
          onClick={() => dd.setOpen(true)}
          onFocus={() => dd.setOpen(true)}
        />
        {dd.open && (
          <div className="h2h-super-dropdown active">
            {Array.from(grouped).map(([provider, models]) => (
              <div key={provider} className="h2h-dropdown-group">
                <div className="h2h-dropdown-group-header">{provider}</div>
                {models.map((m) => (
                  <div
                    key={m.id}
                    className={`h2h-dropdown-item ${m.id === selectedId ? 'selected' : ''}`}
                    onClick={() => { onSelect(m.id); dd.close(); }}
                  >
                    <div className="h2h-dropdown-item-name">
                      <span className="h2h-dropdown-provider">{m.provider}</span>
                      <span className="h2h-dropdown-model">{m.model}</span>
                    </div>
                    <div className="h2h-dropdown-item-stats">
                      <span className="h2h-dropdown-stat acid">{m.ttft}ms</span>
                      <span className="h2h-dropdown-stat green">{m.tps} tok/s</span>
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
    </th>
  );
}

/* ── main table ── */

interface Props {
  model1: ModelData;
  model2: ModelData;
  metrics: ComparisonMetric[];
  availableModels: ModelData[];
  selectedModel1: string;
  selectedModel2: string;
  onChangeModel1: (id: string) => void;
  onChangeModel2: (id: string) => void;
}

export function HeadToHeadTable({
  model1, model2, metrics, availableModels,
  selectedModel1, selectedModel2, onChangeModel1, onChangeModel2,
}: Props): ReactElement {
  const dd1 = useDropdown(availableModels);
  const dd2 = useDropdown(availableModels);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dd1.ref.current && !dd1.ref.current.contains(e.target as Node)) dd1.close();
      if (dd2.ref.current && !dd2.ref.current.contains(e.target as Node)) dd2.close();
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <div className="h2h-container">
      <table className="h2h-table">
        <thead>
          <tr>
            <th className="h2h-col-metric">METRIC</th>
            <ModelSelector model={model1} accent="violet" dd={dd1} selectedId={selectedModel1} onSelect={onChangeModel1} />
            <ModelSelector model={model2} accent="teal" dd={dd2} selectedId={selectedModel2} onSelect={onChangeModel2} />
            <th className="h2h-col-delta">Delta</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map((metric) => {
            const v1 = model1[metric.key as keyof ModelData] as number;
            const v2 = model2[metric.key as keyof ModelData] as number;
            const { winner, text } = computeDelta(v1, v2, metric);
            const isPro = metric.label.includes('🔒');

            return (
              <tr key={metric.key} className={isPro ? 'pro-row' : ''}>
                <td className="h2h-metric-cell">{metric.label}</td>
                <td className="h2h-val-cell">{v1 != null ? metric.format(v1) : '—'}</td>
                <td className="h2h-val-cell">{v2 != null ? metric.format(v2) : '—'}</td>
                <td className={`h2h-delta-cell ${winner}`}>{text}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
