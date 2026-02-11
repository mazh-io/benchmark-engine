import Link from 'next/link';

export function IndexFooter() {
  return (
    <footer className="ea-footer">
      <div className="ea-footer-inner">
        <div className="ea-footer-brand">
          <div className="ea-footer-logo">MAZH</div>
          <div className="ea-footer-tagline">
            Independent LLM latency benchmarks. Real data, no marketing fluff.
          </div>
        </div>

        <div className="ea-footer-links">
          <div className="ea-footer-col">
            <h4>Product</h4>
            <Link href="/">Index</Link>
            <Link href="/?tab=insights">Insights</Link>
            <Link href="/?tab=api">API</Link>
          </div>
          <div className="ea-footer-col">
            <h4>Company</h4>
            <Link href="/">About</Link>
            <Link href="/">Methodology</Link>
            <Link href="/">Contact</Link>
          </div>
          <div className="ea-footer-col">
            <h4>Legal</h4>
            <Link href="/privacy">Privacy</Link>
            <Link href="/terms">Terms</Link>
            <Link href="/imprint">Imprint</Link>
          </div>
        </div>

        <div className="ea-footer-bottom">
          <span>&copy; {new Date().getFullYear()} mazh.io</span>
          <div className="ea-footer-social">
            <a href="https://x.com/mazh_io" target="_blank" rel="noreferrer">𝕏</a>
            <a href="https://github.com/mazh-io" target="_blank" rel="noreferrer">GitHub</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
