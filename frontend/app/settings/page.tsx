'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Header } from '@/layout/Header';
import { MainNav, type Tab } from '@/layout/MainNav';
import { AccountSection } from '@/templates/settings/AccountSection';
import { BillingSection } from '@/templates/settings/BillingSection';

type SettingsTab = 'account' | 'billing';

const MOCK_USER = {
  initials: 'SV',
  firstName: 'Sven',
  lastName: 'Mazh',
  email: 'sven@example.com',
};

export default function SettingsPage() {
  const [tab, setTab] = useState<SettingsTab>('account');
  const router = useRouter();

  useEffect(() => {
    if (window.location.hash === '#billing') setTab('billing');
  }, []);

  return (
    <div className="min-h-screen bg-black">
      <Header
        tier="pro"
        user={{ initials: 'SV', name: 'Sven Mazh', email: 'sven@example.com' }}
        showSocial={false}
      />
      <div className="h-px bg-[#0f0f0f]" />
      <MainNav
        activeTab={null}
        onTabChange={(tabKey: Tab) => {
          if (tabKey === 'grid') router.push('/');
          if (tabKey === 'insights') router.push('/?tab=insights');
          if (tabKey === 'api') router.push('/?tab=api');
        }}
      />

      <div className="st-content">
        <div className="st-page-header">
          <h1 className="st-page-title">Settings</h1>
          <p className="st-page-subtitle">Manage your account and subscription</p>
        </div>

        {/* Tabs */}
        <div className="st-tabs">
          <button
            className={`st-tab ${tab === 'account' ? 'active' : ''}`}
            onClick={() => setTab('account')}
          >
            Account
          </button>
          <button
            className={`st-tab ${tab === 'billing' ? 'active' : ''}`}
            onClick={() => setTab('billing')}
          >
            Billing
          </button>
          <Link href="/" className="st-tab st-tab-link">
            API Keys
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} width={12} height={12}>
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
          </Link>
        </div>

        {/* Sections */}
        {tab === 'account' && <AccountSection user={MOCK_USER} />}
        {tab === 'billing' && <BillingSection />}
      </div>
    </div>
  );
}
