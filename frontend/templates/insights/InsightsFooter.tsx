import type { ReactElement } from 'react';

export function InsightsFooter(): ReactElement {
  return (
    <footer className="insights-footer">
      <div className="insights-footer-brand">mazh.io</div>
      <div className="insights-footer-links">
        <a href="#" className="insights-footer-link">Docs</a>
        <a href="#" className="insights-footer-link">Changelog</a>
        <a href="#" className="insights-footer-link">Status</a>
      </div>
    </footer>
  );
}

