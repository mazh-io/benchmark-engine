'use client';

import Link from 'next/link';
import { LaunchpadMenu } from '@/layout/header/LaunchpadMenu';
import { AvatarDropdown } from '@/layout/header/AvatarDropdown';

type Tier = 'logged-out' | 'free' | 'pro';

interface Props {
  tier?: Tier;
  user?: { initials: string; name: string; email: string };
  showSocial?: boolean;
}

const MOCK_USER = { initials: 'SV', name: 'Sven', email: 'sven@example.com' };

export function Header({ tier = 'free', user = MOCK_USER, showSocial = true }: Props) {
  return (
    <header className="header">
      <div className="header-container">
        {/* LEFT */}
        <div className="header-left">
          <LaunchpadMenu />

          <span className="header-divider" />

          <Link href="/" className="header-logo">MAZH</Link>

          <div className="header-live-badge">
            <span className="inline-flex h-2 w-2 rounded-full bg-[#22c55e] animate-status-dot" />
            LIVE
          </div>
        </div>

        {/* RIGHT */}
        <div className="header-right">
          {showSocial && tier !== 'logged-out' && (
            <a
              href="https://x.com/mazh_io"
              target="_blank"
              rel="noreferrer"
              className="header-link"
              title="@mazh_io"
            >
              𝕏
            </a>
          )}

          {tier === 'logged-out' && (
            <>
              <Link href="/login" className="btn-login">Login</Link>
              <Link href="/early-access" className="btn-upgrade">
                Get Pro €19
              </Link>
            </>
          )}

          {tier === 'free' && (
            <>
              <Link href="/early-access" className="btn-upgrade">
                Upgrade to Pro — €19/mo
              </Link>
              {user && (
                <AvatarDropdown
                  initials={user.initials}
                  name={user.name}
                  email={user.email}
                />
              )}
            </>
          )}

          {tier === 'pro' && user && (
            <>
              <AvatarDropdown
                initials={user.initials}
                name={user.name}
                email={user.email}
              />
              <span className="pro-badge">PRO</span>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
