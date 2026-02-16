'use client';

import { useMemo } from 'react';
import type { BenchmarkDataResult } from '@/hooks/useBenchmarkData';

interface Props {
  data?: BenchmarkDataResult;
}

export function CredibilityStats({ data }: Props) {
  const stats = useMemo(() => {
    if (!data?.results) {
      return [
        { value: '—', label: 'Measurements' },
        { value: '—', label: 'Models' },
        { value: '—', label: 'Providers' },
        { value: '24/7', label: 'Live Data' },
      ];
    }

    const models = new Set<string>();
    const providers = new Set<string>();

    for (const r of data.results) {
      const model = r.model || r.models?.name;
      const provider = r.provider || r.providers?.name;
      if (model) models.add(model);
      if (provider) providers.add(provider);
    }

    return [
      { value: data.results.length.toLocaleString(), label: 'Measurements' },
      { value: String(models.size), label: 'Models' },
      { value: String(providers.size), label: 'Providers' },
      { value: '24/7', label: 'Live Data' },
    ];
  }, [data]);

  return (
    <section className="ea-credibility">
      {stats.map((s) => (
        <div key={s.label} className="ea-cred-stat">
          <div className="ea-cred-value">{s.value}</div>
          <div className="ea-cred-label">{s.label}</div>
        </div>
      ))}
    </section>
  );
}
