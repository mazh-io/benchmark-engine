'use client';

import { TTFTLeaderboardWidget } from './widgets/TTFTLeaderboardWidget';
import { TPSLeaderboardWidget } from './widgets/TPSLeaderboardWidget';
import { ProviderCardWidget } from './widgets/ProviderCardWidget';
import { ComparisonWidget } from './widgets/ComparisonWidget';
import { StatusBadgeWidget } from './widgets/StatusBadgeWidget';
import { InsightWidget } from './widgets/InsightWidget';

export function WidgetsSection() {
  return (
    <div className="api-section">
      <div>
        <h2 className="api-section-title">Embeddable Widgets</h2>
        <p className="api-section-desc">
          Embed live mazh charts on your website, blog, or documentation. Free to use – just copy
          the code.
        </p>
      </div>

      <TTFTLeaderboardWidget />
      <TPSLeaderboardWidget />
      <ProviderCardWidget />
      <ComparisonWidget />
      <StatusBadgeWidget />
      <InsightWidget />

      <div className="api-widgets-note">
        <p>
          <strong>Note:</strong> All widgets are free to embed. They display free metrics only
          (TTFT, TPS, Success Rate).
        </p>
        <p>
          Pro users can remove the &quot;Powered by mazh&quot; branding by adding{' '}
          <code>&amp;branding=false</code> to the embed URL.
        </p>
      </div>
    </div>
  );
}
