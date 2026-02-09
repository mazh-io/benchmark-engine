'use client';

import { useState, useMemo } from 'react';
import type { WidgetSize } from './WidgetChrome';
import { WidgetChrome } from './WidgetChrome';
import { WidgetTime } from './WidgetTime';
import { useComparisonData } from './widgetData';

const IFRAME_CODE =
  '<iframe src="https://mazh.io/embed/compare/groq/together?theme=dark" width="300" height="180" frameborder="0"></iframe>';

interface MetricRow {
  metric: string;
  provider1: string;
  provider2: string;
  provider1Width: number;
  provider2Width: number;
}

export function ComparisonWidget() {
  const [size, setSize] = useState<WidgetSize>('s');
  const data = useComparisonData('groq', 'together');

  const rows = useMemo<MetricRow[]>(() => {
    if (!data) return [];

    const { provider1, provider2 } = data;
    const maxTTFT = Math.max(provider1.ttft, provider2.ttft);
    const maxTPS = Math.max(provider1.tps, provider2.tps);
    const maxSuccess = Math.max(provider1.successRate, provider2.successRate);

    const all: MetricRow[] = [
      {
        metric: 'TTFT',
        provider1: `${provider1.ttft}ms`,
        provider2: `${provider2.ttft}ms`,
        provider1Width: Math.round((provider1.ttft / maxTTFT) * 100),
        provider2Width: Math.round((provider2.ttft / maxTTFT) * 100),
      },
      {
        metric: 'TPS',
        provider1: `${provider1.tps}/s`,
        provider2: `${provider2.tps}/s`,
        provider1Width: Math.round((provider1.tps / maxTPS) * 100),
        provider2Width: Math.round((provider2.tps / maxTPS) * 100),
      },
      {
        metric: 'Success',
        provider1: `${provider1.successRate}%`,
        provider2: `${provider2.successRate}%`,
        provider1Width: Math.round((provider1.successRate / maxSuccess) * 100),
        provider2Width: Math.round((provider2.successRate / maxSuccess) * 100),
      },
    ];

    if (size === 's') return [all[0]];
    if (size === 'm') return all.slice(0, 2);
    return all;
  }, [data, size]);

  const width = size === 's' ? 300 : size === 'm' ? 600 : undefined;
  const loading = !data || rows.length === 0;

  const headerText = loading
    ? 'Loading...'
    : `${data.provider1.name} vs ${data.provider2.name}${
        size === 'm' ? ' – Performance Comparison' : size === 'l' ? ' – Full Comparison' : ''
      }`;

  return (
    <WidgetChrome
      id="widget-comparison"
      title="Comparison"
      description="Head-to-head: Compare two providers side by side."
      size={size}
      onSizeChange={setSize}
      embedCode={IFRAME_CODE}
      preview={
        <div className="widget-frame" style={{ width }}>
          <div className="widget-frame-header">{headerText}</div>
          <div className="widget-frame-body">
            {loading ? (
              <div className="w-compare-row">
                <span className="w-compare-label">Loading data...</span>
              </div>
            ) : (
              <>
                {rows.map((row) => (
                  <div key={row.metric} className="w-compare-row">
                    <span className="w-compare-label">{row.metric}</span>
                    <div className="w-compare-bars">
                      <div className="w-compare-bar a" style={{ width: `${row.provider1Width}%` }}>
                        <span>{row.provider1}</span>
                      </div>
                      <div className="w-compare-bar b" style={{ width: `${row.provider2Width}%` }}>
                        <span>{row.provider2}</span>
                      </div>
                    </div>
                  </div>
                ))}

                <div className="w-compare-legend">
                  <span className="w-compare-legend-item">
                    <span className="w-compare-legend-dot a" />
                    {data.provider1.name}
                  </span>
                  <span className="w-compare-legend-item">
                    <span className="w-compare-legend-dot b" />
                    {size === 'l'
                      ? `${data.provider2.name} ${data.provider2.model}`
                      : data.provider2.name}
                  </span>
                </div>
              </>
            )}
          </div>
          <div className="w-footer">
            <WidgetTime />
            <a href="https://mazh.io">Powered by mazh ↗</a>
          </div>
        </div>
      }
    />
  );
}
