'use client';

import { useBilling } from './useBilling';

const PRO_LABEL = process.env.NEXT_PUBLIC_PRO_LABEL ?? 'Pro';

export function BillingSection() {
  const { view, planName, badge, periodEnd, busy, error, checkout, portal } = useBilling();

  if (view === 'loading') {
    return <p className="st-plan-value" style={{ padding: '2rem 0' }}>Loading billing…</p>;
  }

  return (
    <>
      <h2 className="st-section-title">Current Plan</h2>

      <div className="st-billing-card">
        <div className="st-billing-header">
          <div className="st-billing-plan-name">{view === 'free' ? 'Free' : planName}</div>
          {badge && view !== 'free' && (
            <span className={badge.cls}>{badge.text}</span>
          )}
        </div>

        {(view === 'free' || view === 'expired') && (
          <>
            <p className="st-billing-hint">
              {view === 'free'
                ? 'Upgrade to Pro for cost analysis, efficiency scores, extended data history, API access, and more.'
                : 'Your subscription has expired. Re-subscribe to regain Pro access.'}
            </p>
            <button type="button" className="st-btn st-btn-primary" disabled={busy} onClick={checkout}>
              {busy ? 'Redirecting…' : view === 'free' ? `Get ${PRO_LABEL}` : `Re-subscribe — ${PRO_LABEL}`}
            </button>
          </>
        )}

        {view !== 'free' && view !== 'expired' && (
          <>
            {periodEnd && (
              <div className="st-plan-details">
                <div className="st-plan-detail">
                  <div className="st-plan-label">
                    {view === 'cancelled' ? 'Access until' : 'Next billing'}
                  </div>
                  <div className="st-plan-value">{periodEnd}</div>
                </div>
              </div>
            )}
            <div className="st-billing-actions">
              <button type="button" className="st-btn st-btn-secondary" disabled={busy} onClick={portal}>
                {busy ? 'Loading…' : 'Manage Subscription'}
              </button>
            </div>
          </>
        )}
      </div>

      {error && <p className="st-billing-error">{error}</p>}
    </>
  );
}
