'use client';

const PLAN = {
  name: 'Early Access Pro',
  price: '€19/mo',
  nextBilling: 'Feb 15, 2025',
  type: 'Early Access',
  priceLocked: 'Forever ✓',
} as const;

const PAYMENT = {
  last4: '4242',
  expires: '12/26',
  brand: 'Visa',
} as const;

const INVOICES = [
  { date: 'Jan 15, 2025', amount: '€19.00' },
  { date: 'Dec 15, 2024', amount: '€19.00' },
  { date: 'Nov 15, 2024', amount: '€19.00' },
] as const;

export function BillingSection() {
  return (
    <>
      {/* Current Plan */}
      <h2 className="st-section-title">Current Plan</h2>

      <div className="st-billing-card">
        <div className="st-billing-header">
          <div className="st-billing-plan-name">{PLAN.name}</div>
          <span className="st-billing-badge">ACTIVE</span>
        </div>

        <div className="st-plan-details">
          <div className="st-plan-detail">
            <div className="st-plan-label">Price</div>
            <div className="st-plan-value acid">{PLAN.price}</div>
          </div>
          <div className="st-plan-detail">
            <div className="st-plan-label">Next billing</div>
            <div className="st-plan-value">{PLAN.nextBilling}</div>
          </div>
          <div className="st-plan-detail">
            <div className="st-plan-label">Plan type</div>
            <div className="st-plan-value">{PLAN.type}</div>
          </div>
          <div className="st-plan-detail">
            <div className="st-plan-label">Price locked</div>
            <div className="st-plan-value acid">{PLAN.priceLocked}</div>
          </div>
        </div>

        <div className="st-billing-actions">
          <button type="button" className="st-btn st-btn-secondary">
            Manage Subscription
          </button>
          <button type="button" className="st-btn st-btn-danger">
            Cancel Plan
          </button>
        </div>
      </div>

      {/* Payment Method */}
      <h2 className="st-section-title st-mt">Payment Method</h2>

      <div className="st-billing-card">
        <div className="st-billing-header">
          <div>
            <div className="st-billing-plan-name">•••• •••• •••• {PAYMENT.last4}</div>
            <p className="st-payment-expires">Expires {PAYMENT.expires}</p>
          </div>
          <span className="st-payment-brand">{PAYMENT.brand}</span>
        </div>
        <button type="button" className="st-btn st-btn-secondary">
          Update Payment Method
        </button>
      </div>

      {/* Invoices */}
      <h2 className="st-section-title st-mt">Invoices</h2>

      <div className="st-invoice-list">
        {INVOICES.map((invoice) => (
          <div key={invoice.date} className="st-invoice-item">
            <div className="st-invoice-info">
              <span className="st-invoice-date">{invoice.date}</span>
              <span className="st-invoice-amount">{invoice.amount}</span>
              <span className="st-invoice-status">Paid</span>
            </div>
            <a href="#" className="st-invoice-download">
              Download
            </a>
          </div>
        ))}
      </div>
    </>
  );
}

