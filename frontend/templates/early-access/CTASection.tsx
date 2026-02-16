import { CHECKOUT } from '@/data/early-access';

export function CTASection() {
  return (
    <section className="ea-cta">
      <h2 className="ea-cta-title">Ready to see the full picture?</h2>
      <p className="ea-cta-subtitle">
        Join the founding members. Lock in &euro;19/mo forever.
      </p>
      <a href={CHECKOUT.monthly} target="_blank" rel="noreferrer" className="ea-cta-btn">
        Get Early Access
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5}>
          <path d="M5 12h14M12 5l7 7-7 7" />
        </svg>
      </a>
    </section>
  );
}
