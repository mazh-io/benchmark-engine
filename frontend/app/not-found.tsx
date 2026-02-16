import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="error-page">
      {/* Header */}
      <header className="error-header">
        <Link href="/" className="error-logo">MAZH</Link>
      </header>

      {/* 404 Content */}
      <main className="error-container">
        <div className="error-code">404</div>
        <h1 className="error-title">Lost in the void</h1>
        <p className="error-message">
          This page doesn&apos;t exist. It never did. Or maybe it did and we
          broke it. Either way, it&apos;s not here anymore.
        </p>
        <Link href="/" className="error-btn">Take me home</Link>
      </main>

      {/* Footer */}
      <footer className="error-footer">
        <p className="error-footer-text">
          &copy; {new Date().getFullYear()} skot UG &middot;{' '}
          <Link href="/privacy">Privacy</Link> &middot;{' '}
          <Link href="/terms">Terms</Link> &middot;{' '}
          <Link href="/imprint">Imprint</Link>
        </p>
      </footer>
    </div>
  );
}
