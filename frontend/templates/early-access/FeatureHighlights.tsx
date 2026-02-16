import { HIGHLIGHTS } from '@/data/early-access';

export function FeatureHighlights() {
  return (
    <section className="ea-highlights">
      <div className="ea-section-header">
        <h2 className="ea-section-title">Unlock Pro Features</h2>
        <p className="ea-section-subtitle">
          The intelligence you need to make better infrastructure decisions.
        </p>
      </div>

      <div className="ea-highlights-grid">
        {HIGHLIGHTS.map((h) => (
          <div key={h.title} className="ea-highlight">
            <div className="ea-highlight-icon">{h.icon}</div>
            <div className="ea-highlight-title">{h.title}</div>
            <div className="ea-highlight-desc">{h.desc}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
