import { CHECKOUT } from '@/data/early-access';

export function PricingCard() {
  return (
    <section className="ea-pricing">
      <div className="ea-pricing-inner">
        <div className="ea-card">
          <div className="ea-card-header">
            <div className="ea-card-label">Early Pro Access</div>
            <div className="ea-card-badge">Limited spots</div>
          </div>

          <div className="ea-options">
            <a href={CHECKOUT.monthly} target="_blank" rel="noreferrer" className="ea-option">
              <div className="ea-option-period">Monthly</div>
              <div className="ea-option-amount">&euro;19<span>/mo</span></div>
              <div className="ea-option-note">&nbsp;</div>
              <span className="ea-option-btn">Get Access</span>
            </a>

            <a href={CHECKOUT.yearly} target="_blank" rel="noreferrer" className="ea-option best">
              <div className="ea-option-badge">Best Value</div>
              <div className="ea-option-period">Yearly</div>
              <div className="ea-option-amount">&euro;190<span>/year</span></div>
              <div className="ea-option-note">Save 2 months</div>
              <span className="ea-option-btn">Get Access</span>
            </a>
          </div>

          <div className="ea-card-footer">
            <span><span className="check">✓</span> Price locked forever</span>
            <span><span className="check">✓</span> 30-day money-back</span>
            <span><span className="check">✓</span> Cancel anytime</span>
          </div>

          <div className="ea-card-anchor">
            Regular price will be <strong>&euro;49/mo</strong>
          </div>
        </div>
      </div>
    </section>
  );
}
