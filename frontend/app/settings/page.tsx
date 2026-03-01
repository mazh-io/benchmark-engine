'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Header } from '@/layout/Header';
import { useAuth } from '@/contexts/AuthContext';
import { MainNav, type Tab } from '@/layout/MainNav';
import { AccountSection, type AccountSectionRef } from '@/templates/settings/AccountSection';
import { BillingSection } from '@/templates/settings/BillingSection';

type SettingsTab = 'account' | 'billing';

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
    if (typeof window !== 'undefined' && window.location.hash === '#billing') setTab('billing');
  }, []);

  if (!isReady || !isLoggedIn) {
    return <div className="min-h-screen bg-black" />;
  }

  return (
    <div className="min-h-screen bg-black">
      <Header
        tier="pro"
        user={user ? { initials: user.initials, name: user.name, email: user.email } : undefined}
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
