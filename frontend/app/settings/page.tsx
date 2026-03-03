'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Header } from '@/layout/Header';
import { useAuth } from '@/contexts/AuthContext';
import { MainNav, type Tab } from '@/layout/MainNav';
import { AccountSection, type AccountSectionRef } from '@/templates/settings/AccountSection';
import { BillingSection } from '@/templates/settings/BillingSection';

type SettingsTab = 'account' | 'billing' | 'api';

export default function SettingsPage() {
  const router = useRouter();
  const { isLoggedIn, isReady, user } = useAuth();
  const [tab, setTab] = useState<SettingsTab>('account');
  const [accountDirty, setAccountDirty] = useState(false);
  const [pendingTab, setPendingTab] = useState<SettingsTab | null>(null);
  const [savingFromModal, setSavingFromModal] = useState(false);
  const accountSectionRef = useRef<AccountSectionRef>(null);

  useEffect(() => {
    if (!isReady) return;
    if (!isLoggedIn) {
      router.replace('/login');
      return;
    }
  }, [isReady, isLoggedIn, router]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      if (window.location.hash === '#billing') setTab('billing');
      if (window.location.hash === '#api') setTab('api');
    }
  }, []);

  if (!isReady || !isLoggedIn) {
    return <div className="min-h-screen bg-black" />;
  }

  return (
    <div className="min-h-screen bg-black">
      <Header
        tier="pro"
        user={user ? { initials: user.initials, name: user.name, email: user.email, avatarUrl: user.avatarUrl } : undefined}
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
            onClick={() => { setPendingTab(null); setTab('account'); }}
          >
            Account
          </button>
          <button
            className={`st-tab ${tab === 'billing' ? 'active' : ''}`}
            onClick={() => {
              if (accountDirty) {
                setPendingTab('billing');
              } else {
                setTab('billing');
              }
            }}
          >
            Billing
          </button>
          <button
            className={`st-tab ${tab === 'api' ? 'active' : ''}`}
            onClick={() => {
              if (accountDirty) {
                setPendingTab('api');
              } else {
                setTab('api');
              }
            }}
          >
            API Keys
          </button>
        </div>

        {/* Sections */}
        {tab === 'account' && user && (
          <AccountSection
            ref={accountSectionRef}
            user={{
              id: user.id,
              initials: user.initials,
              firstName: user.name.split(' ')[0] ?? user.name,
              lastName: user.name.split(' ').slice(1).join(' ') ?? '',
              email: user.email,
              avatarUrl: user.avatarUrl ?? null,
            }}
            onDirtyChange={setAccountDirty}
          />
        )}
        {tab === 'billing' && <BillingSection />}
        {tab === 'api' && (
          <div className="st-section">
            <h2 className="st-section-title">API Keys</h2>
            <p className="text-[#666] text-sm">
              API access is coming soon. You&apos;ll be able to generate and manage your API keys here.
            </p>
          </div>
        )}
      </div>

      {/* Unsaved changes modal */}
      {pendingTab !== null && (
        <div className="st-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="st-unsaved-title">
          <div className="st-modal">
            <h2 id="st-unsaved-title" className="st-modal-title">You have unsaved changes</h2>
            <p className="st-modal-text">Save your changes or discard them before leaving.</p>
            <div className="st-modal-actions">
              <button
                type="button"
                className="st-btn st-btn-primary"
                disabled={savingFromModal}
                onClick={async () => {
                  setSavingFromModal(true);
                  try {
                    await accountSectionRef.current?.save();
                    const target = pendingTab;
                    setPendingTab(null);
                    setTab(target);
                  } finally {
                    setSavingFromModal(false);
                  }
                }}
              >
                {savingFromModal ? 'Saving…' : 'Save changes'}
              </button>
              <button
                type="button"
                className="st-btn st-btn-secondary"
                disabled={savingFromModal}
                onClick={() => {
                  accountSectionRef.current?.discard();
                  const target = pendingTab;
                  setPendingTab(null);
                  setTab(target);
                }}
              >
                Discard
              </button>
              <button
                type="button"
                className="st-btn st-btn-secondary"
                disabled={savingFromModal}
                onClick={() => setPendingTab(null)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
