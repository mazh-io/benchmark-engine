'use client';

import { useState } from 'react';

export function KeysSection() {
  const [isProView, setIsProView] = useState(false);

  return (
    <div className="api-section-sm">
      <div>
        <h2 className="api-section-title">API Keys</h2>
        <p className="api-section-desc">Manage your API keys and monitor usage.</p>
      </div>

      {!isProView && (
        <div className="api-keys-lock">
          <div className="api-keys-lock-icon">🔒</div>
          <h3 className="api-keys-lock-title">API Access requires Pro</h3>
          <p className="api-keys-lock-desc">
            Get access to the mazh API with 1,000 requests/hour, all endpoints, and the ability to
            remove widget branding.
          </p>

          <a href="/pricing" className="api-keys-cta">
            Get Early Pro Access — €19/mo
          </a>

          <div className="api-keys-features">
            <span><span className="api-keys-check">✓</span> 1,000 req/hour</span>
            <span><span className="api-keys-check">✓</span> All endpoints</span>
            <span><span className="api-keys-check">✓</span> Remove branding</span>
          </div>
        </div>
      )}

      {isProView && (
        <div className="api-keys-pro">
          <div className="api-keys-card">
            <div className="api-keys-card-header">
              <span className="api-keys-card-label">Your API Key</span>
              <span className="api-keys-card-status">
                <span className="api-keys-card-dot" />
                Active
              </span>
            </div>

            <div className="api-keys-input-row">
              <div className="api-keys-input">mzh_••••••••••••••••••••••••</div>
              <button className="api-keys-action-btn">Show</button>
              <button className="api-keys-action-btn">Copy</button>
            </div>

            <p className="api-keys-card-meta">Created Jan 15, 2025 · Last used 2 hours ago</p>
          </div>

          <div className="api-keys-stats">
            <div className="api-keys-stat">
              <div className="api-keys-stat-value acid">847</div>
              <div className="api-keys-stat-label">Requests today</div>
            </div>
            <div className="api-keys-stat">
              <div className="api-keys-stat-value">12,483</div>
              <div className="api-keys-stat-label">This month</div>
            </div>
            <div className="api-keys-stat">
              <div className="api-keys-stat-value green">153</div>
              <div className="api-keys-stat-label">Remaining/hour</div>
            </div>
          </div>

          <div className="api-keys-regen">
            <div>
              <div className="api-keys-regen-title">Regenerate Key</div>
              <div className="api-keys-regen-desc">Your old key will stop working immediately.</div>
            </div>
            <button className="api-keys-regen-btn">Regenerate</button>
          </div>
        </div>
      )}

      <div className="api-keys-demo">
        <button type="button" onClick={() => setIsProView((v) => !v)} className="api-keys-demo-btn">
          Toggle Free/Pro View (Demo)
        </button>
      </div>
    </div>
  );
}
