'use client';

import { useState } from 'react';
import type { WidgetSize } from './WidgetChrome';
import { WidgetChrome } from './WidgetChrome';
import { WidgetTime } from './WidgetTime';
import { useInsightData } from './widgetData';

const IFRAME_CODE =
  '<iframe src="https://mazh.io/embed/insight?type=fastest&theme=dark" width="280" height="180" frameborder="0"></iframe>';

export function InsightWidget() {
  const [size, setSize] = useState<WidgetSize>('s');
  const data = useInsightData();

  const width = size === 's' ? 280 : size === 'm' ? 560 : undefined;
  const label = size === 'l' ? 'Insight of the Day' : 'Insight';

  // Bar widths for M/L sizes
  const maxTTFT = data ? Math.max(data.fastestProvider.ttft, data.slowestProvider.ttft) : 1;
  const fastBarWidth = data ? Math.round((data.fastestProvider.ttft / maxTTFT) * 100) : 0;
  const slowBarWidth = data ? Math.round((data.slowestProvider.ttft / maxTTFT) * 100) : 0;

  return (
    <WidgetChrome
      id="widget-insight"
      title="Insight Card"
      description="Eye-catching comparison facts. Perfect for blog posts and social shares."
      size={size}
      onSizeChange={setSize}
      embedCode={IFRAME_CODE}
      preview={
        <div className="widget-frame w-insight-frame" style={{ width }}>
          <div className={`widget-frame-body w-insight-body ${size}`}>
            <div className={`w-insight-label ${size}`}>💡 {label}</div>

            {!data ? (
              <div className={`w-insight-title ${size}`}>Loading...</div>
            ) : (
              <>
                <div className={`w-insight-title ${size}`}>
                  <span className="w-insight-provider">{data.fastestProvider.name}</span>{' '}
                  {data.fastestProvider.model}
                  {size === 's' ? (
                    <>
                      {' '}is<br />
                      <span className="w-insight-multiplier s">{data.multiplier}×</span> faster than
                      <br />
                      <span className="w-insight-competitor">{data.slowestProvider.name}</span>{' '}
                      {data.slowestProvider.model}
                    </>
                  ) : (
                    <>
                      {' '}is{' '}
                      <span className="w-insight-multiplier">{data.multiplier}×</span> faster than{' '}
                      <span className="w-insight-competitor">{data.slowestProvider.name}</span>{' '}
                      {data.slowestProvider.model}
                    </>
                  )}
                </div>

                {size === 's' && (
                  <div className="w-insight-metrics">
                    {data.fastestProvider.ttft}ms vs {data.slowestProvider.ttft.toLocaleString()}ms
                  </div>
                )}

                {size !== 's' && (
                  <div className={`w-insight-bars ${size}`}>
                    {/* Fastest bar */}
                    <div className={`w-insight-bar-row ${size}`}>
                      <span className={`w-insight-bar-label ${size}`}>
                        <span className={`w-insight-bar-label-provider ${size}`}>
                          {data.fastestProvider.name}
                        </span>{' '}
                        {data.fastestProvider.model}
                      </span>
                      <div className={`w-insight-bar-container ${size}`}>
                        <div className={`w-insight-bar-fill ${size}`} style={{ width: `${fastBarWidth}%` }} />
                      </div>
                      <span className={`w-insight-bar-value ${size}`}>{data.fastestProvider.ttft}ms</span>
                    </div>

                    {/* Slowest bar */}
                    <div className={`w-insight-bar-row ${size}`}>
                      <span className={`w-insight-bar-label ${size}`}>
                        <span className={`w-insight-bar-label-competitor ${size}`}>
                          {data.slowestProvider.name}
                        </span>{' '}
                        {data.slowestProvider.model}
                      </span>
                      <div className={`w-insight-bar-container ${size}`}>
                        <div className={`w-insight-bar-fill ${size} red`} style={{ width: `${slowBarWidth}%` }} />
                      </div>
                      <span className={`w-insight-bar-value ${size} red`}>
                        {data.slowestProvider.ttft.toLocaleString()}ms
                      </span>
                    </div>
                  </div>
                )}

                {size === 'l' && (
                  <div className="w-insight-stats">
                    <div className="w-insight-stat">
                      <div className="w-insight-stat-value acid">{data.multiplier}×</div>
                      <div className="w-insight-stat-label">Faster</div>
                    </div>
                    <div className="w-insight-stat">
                      <div className="w-insight-stat-value white">{data.difference.toLocaleString()}ms</div>
                      <div className="w-insight-stat-label">Difference</div>
                    </div>
                  </div>
                )}
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
