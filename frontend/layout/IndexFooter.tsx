export function IndexFooter() {
  return (
    <footer className="index-footer">
      <div className="index-footer-inner">
        {/* LEFT — Brand & Description */}
        <div className="index-footer-brand">
          <div className="index-footer-logo">MAZH</div>
          <p className="index-footer-tagline">
            The Inference Index. Live LLM latency benchmarks for AI infrastructure teams.
          </p>
        </div>

        {/* RIGHT — Links Grid */}
        <div className="index-footer-links">
          <div className="index-footer-column">
            <h4 className="index-footer-column-title">PRODUCT</h4>
            <a href="#" className="index-footer-link">The Grid</a>
            <a href="#" className="index-footer-link">Insights</a>
            <a href="#" className="index-footer-link">API</a>
            <a href="#" className="index-footer-link">Pricing</a>
          </div>

          <div className="index-footer-column">
            <h4 className="index-footer-column-title">RESOURCES</h4>
            <a href="#" className="index-footer-link">Documentation</a>
            <a href="#" className="index-footer-link">Changelog</a>
            <a href="#" className="index-footer-link">Status</a>
          </div>

          <div className="index-footer-column">
            <h4 className="index-footer-column-title">COMPANY</h4>
            <a href="#" className="index-footer-link">About</a>
            <a href="#" className="index-footer-link">Blog</a>
            <a href="#" className="index-footer-link">Contact</a>
          </div>
        </div>

        {/* BOTTOM — Copyright & Social */}
        <div className="index-footer-bottom">
          <span className="index-footer-copyright">
            © {new Date().getFullYear()} mazh. All rights reserved.
          </span>
          <div className="index-footer-social-wrapper">
            <a href="https://x.com/mazh_io" target="_blank" rel="noreferrer" className="index-footer-social">
              𝕏 @mazh_io
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
