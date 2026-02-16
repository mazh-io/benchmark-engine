'use client';

import { useState } from 'react';
import type { WidgetSize } from './WidgetChrome';
import { WidgetChrome } from './WidgetChrome';
import { WidgetTime } from './WidgetTime';
import { useProviderCardData } from './widgetData';

const IFRAME_CODE =
  '<iframe src="https://mazh.io/embed/provider/groq?theme=dark" width="200" height="120" frameborder="0"></iframe>';

export function ProviderCardWidget() {
  const [size, setSize] = useState<WidgetSize>('s');
  const providerData = useProviderCardData('groq');

  const isExpanded = size !== 's';
  const width = size === 's' ? 200 : size === 'm' ? 360 : 480;

  return (
    <WidgetChrome
      id="widget-provider-card"
      title="Provider Card"
      description="Single provider stats at a glance. Perfect for status pages."
      size={size}
      onSizeChange={setSize}
      embedCode={IFRAME_CODE}
      preview={
        <div className="widget-frame" style={{ width }}>
          <div className="widget-frame-body">
            <div className="w-provider-card">
              <div className="w-provider-name">
                {providerData?.providerName ?? 'Loading...'}
              </div>

              {isExpanded && providerData && (
                <div className="w-provider-model">{providerData.modelName}</div>
              )}

              {providerData && (
                <div className="w-provider-stats">
                  <div className="w-provider-stat">
                    <div className="w-provider-stat-value">{providerData.ttft}ms</div>
                    <div className="w-provider-stat-label">TTFT</div>
                  </div>

                  {isExpanded && (
                    <>
                      <div className="w-provider-stat">
                        <div className="w-provider-stat-value">{providerData.tps}</div>
                        <div className="w-provider-stat-label">TPS</div>
                      </div>
                      <div className="w-provider-stat">
                        <div className="w-provider-stat-value green">
                          {providerData.successRate}%
                        </div>
                        <div className="w-provider-stat-label">Success</div>
                      </div>
                    </>
                  )}
                </div>
              )}

              {size === 'l' && providerData && providerData.sparklineData.length > 0 && (
                <div className="w-sparkline">
                  {providerData.sparklineData.map((height, idx) => (
                    <div key={idx} className="w-spark-bar" style={{ height: `${height}%` }} />
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="w-footer">
            {size === 's' ? (
              <a href="https://mazh.io">mazh ↗</a>
            ) : (
              <>
                <WidgetTime />
                <a href="https://mazh.io">Powered by mazh ↗</a>
              </>
            )}
          </div>
        </div>
      }
    />
  );
}
