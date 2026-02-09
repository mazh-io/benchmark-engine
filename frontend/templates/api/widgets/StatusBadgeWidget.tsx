'use client';

import { useState } from 'react';
import type { WidgetSize } from './WidgetChrome';
import { WidgetChrome } from './WidgetChrome';
import { useProviderCardData } from './widgetData';

const MARKDOWN_CODE =
  '[![Groq Status](https://mazh.io/badge/groq.svg)](https://mazh.io)';

const BADGE_CONTAINER_STYLE = {
  padding: 20,
  background: '#000000',
  borderRadius: 8,
  border: '1px solid var(--border)',
} as const;

export function StatusBadgeWidget() {
  const [size, setSize] = useState<WidgetSize>('s');
  const providerData = useProviderCardData('groq');

  return (
    <WidgetChrome
      id="widget-status-badge"
      title="Status Badge"
      description="Inline badge for READMEs and docs. Shows live success rate."
      size={size}
      onSizeChange={setSize}
      embedCode={MARKDOWN_CODE}
      embedLabel="Embed Code (Markdown)"
      preview={
        <div className="widget-frame" style={BADGE_CONTAINER_STYLE}>
          <div className="w-status-badge">
            <span className="w-status-dot" />
            {size !== 's' && providerData && (
              <span className="w-status-provider">{providerData.providerName}</span>
            )}
            <span className="w-status-text">
              {providerData ? `${providerData.successRate}%` : 'Loading...'}
            </span>
            {size === 'l' && providerData && (
              <span className="w-status-value">· {providerData.ttft}ms TTFT</span>
            )}
          </div>
        </div>
      }
    />
  );
}
