'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const NAV = [
  { href: '/privacy', label: 'Privacy Policy' },
  { href: '/terms', label: 'Terms of Service' },
  { href: '/imprint', label: 'Imprint' },
] as const;

interface LegalShellProps {
  title: string;
  lastUpdated: string;
  children: React.ReactNode;
}

export function LegalShell({ title, lastUpdated, children }: LegalShellProps) {
  const path = usePathname();

  return (
    <div style={{ fontFamily: 'var(--font-space), system-ui, sans-serif', fontSize: '15px' }}>
      {/* Header */}
      <header className="legal-header">
        <div className="legal-header-left">
          <Link href="/" className="legal-logo">MAZH</Link>
          <div className="legal-live-badge">
            <span className="legal-live-dot" />
            LIVE
          </div>
        </div>
        <div className="legal-header-right">
          <Link href="/login" className="legal-btn-login">Login</Link>
          <Link href="/pricing" className="legal-btn-pro">Get Pro &euro;19</Link>
        </div>
      </header>

      {/* Content */}
      <div className="legal-page">
        <div className="legal-page-header">
          <h1>{title}</h1>
          <p>Last updated: {lastUpdated}</p>
        </div>

        <nav className="legal-nav">
          {NAV.map(({ href, label }) => (
            <Link key={href} href={href} className={path === href ? 'active' : ''}>
              {label}
            </Link>
          ))}
        </nav>

        <div className="legal-content">{children}</div>
      </div>

      {/* Footer */}
      <footer className="legal-footer">
        <div className="legal-footer-inner">
          <span>&copy; {new Date().getFullYear()} skot UG. All rights reserved.</span>
          <div className="legal-footer-links">
            <Link href="/privacy">Privacy</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
