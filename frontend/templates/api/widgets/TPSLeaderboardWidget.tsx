'use client';

import { useState } from 'react';
import type { WidgetSize } from './WidgetChrome';
import { WidgetChrome } from './WidgetChrome';
import { useTpsLeaderboardRows } from './leaderboardData';
import { WidgetTime } from './WidgetTime';

const IFRAME_CODE =
  '<iframe src="https://mazh.io/embed/leaderboard?metric=tps&theme=dark" width="300" height="200" frameborder="0"></iframe>';

export function TPSLeaderboardWidget() {
  const [size, setSize] = useState<WidgetSize>('s');
  const visibleRows = useTpsLeaderboardRows(size);

  const widthStyle = size === 's' ? { width: 300 } : size === 'm' ? { width: 640 } : undefined;
  const header = size === 's' ? 'TPS Leaderboard' : 'TPS Leaderboard – Tokens per Second';

  return (
    <WidgetChrome
      id="widget-tps-leaderboard"
      title="TPS Leaderboard"
      description="Who's got the highest throughput? Ranked by Tokens per Second."
      size={size}
      onSizeChange={setSize}
      embedCode={IFRAME_CODE}
      preview={
        <div className={`widget-frame widget-ttft-leaderboard-${size}`} style={widthStyle}>
          <div className="widget-frame-header">{header}</div>
          <div className="widget-frame-body">
            {visibleRows.map((row) => (
              <div key={row.rank} className="w-leaderboard-item">
                <span className={`w-rank ${row.rank === 1 ? 'gold' : ''}`}>{row.rank}</span>
                <span className="w-provider">{row.provider}</span>
                <div className="w-bar-wrap">
                  <div className="w-bar" style={{ width: `${row.barWidthPercent}%` }} />
                </div>
                <span className="w-value">{row.value}</span>
              </div>
            ))}
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
