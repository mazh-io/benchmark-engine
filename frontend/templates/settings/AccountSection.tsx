'use client';

import { useState } from 'react';
import { supabase } from '@/api/supabase';

export type AccountUser = {
  initials: string;
  firstName: string;
  lastName: string;
  email: string;
};

export interface AccountSectionProps {
  user: AccountUser;
}

export function AccountSection({ user }: AccountSectionProps) {
  const [firstName, setFirstName] = useState(user.firstName);
  const [lastName, setLastName] = useState(user.lastName);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [changeEmailMode, setChangeEmailMode] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [changingEmail, setChangingEmail] = useState(false);
  const [emailMessage, setEmailMessage] = useState<'success' | 'error' | null>(null);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveError(null);
    setSaving(true);
    const { error } = await supabase.auth.updateUser({
      data: {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
      },
    });
    setSaving(false);
    if (error) {
      setSaveError(error.message || 'Failed to save');
      return;
    }
  };

  const handleChangeEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEmail.trim()) return;
    setEmailMessage(null);
    setChangingEmail(true);
    const { error } = await supabase.auth.updateUser({ email: newEmail.trim() });
    setChangingEmail(false);
    if (error) {
      setEmailMessage('error');
      setSaveError(error.message || 'Failed to update email');
      return;
    }
    setEmailMessage('success');
    setChangeEmailMode(false);
    setNewEmail('');
  };

  return (
    <section>
      <h2 className="st-section-title">Account</h2>

      <div className="st-avatar-upload">
        <div className="st-avatar-large">{user.initials}</div>
        <div className="st-avatar-actions">
          <button type="button" className="st-btn st-btn-secondary">
            Upload Photo
          </button>
          <p className="st-avatar-hint">PNG or JPG, at least 240x240px.</p>
        </div>
      </div>

      <form onSubmit={handleSaveProfile}>
        <div className="st-form-row">
          <div className="st-form-group">
            <label className="st-form-label" htmlFor="first-name">
              First name
            </label>
            <input
              id="first-name"
              className="st-form-input"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              placeholder="First name"
            />
          </div>
          <div className="st-form-group">
            <label className="st-form-label" htmlFor="last-name">
              Last name
            </label>
            <input
              id="last-name"
              className="st-form-input"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              placeholder="Last name"
            />
          </div>
        </div>

        <div className="st-form-group">
          <label className="st-form-label" htmlFor="email">
            Email
          </label>
          {!changeEmailMode ? (
            <div className="st-email-row">
              <input
                id="email"
                type="email"
                className="st-form-input"
                value={user.email}
                readOnly
                placeholder="you@example.com"
              />
              <button
                type="button"
                className="st-btn st-btn-secondary"
                onClick={() => setChangeEmailMode(true)}
              >
                Change email
              </button>
            </div>
          ) : (
            <form onSubmit={handleChangeEmail} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <input
                type="email"
                className="st-form-input"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                placeholder="New email address"
                required
              />
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button type="submit" className="st-btn st-btn-primary" disabled={changingEmail}>
                  {changingEmail ? 'Sending…' : 'Update email'}
                </button>
                <button
                  type="button"
                  className="st-btn st-btn-secondary"
                  onClick={() => {
                    setChangeEmailMode(false);
                    setNewEmail('');
                    setEmailMessage(null);
                    setSaveError(null);
                  }}
                >
                  Cancel
                </button>
              </div>
              {emailMessage === 'success' && (
                <p className="st-form-hint" style={{ color: 'var(--st-success, #22c55e)' }}>
                  Check your new email to confirm the change.
                </p>
              )}
            </form>
          )}
          {!changeEmailMode && (
            <p className="st-form-hint">
              We&apos;ll use this address for account notifications and receipts.
            </p>
          )}
        </div>

        {saveError && <p className="st-form-hint" style={{ color: 'var(--st-danger, #ef4444)' }}>{saveError}</p>}

        <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
          <button type="submit" className="st-btn st-btn-primary" disabled={saving}>
            {saving ? 'Saving…' : 'Save changes'}
          </button>
          <button type="button" className="st-btn st-btn-secondary">
            Cancel
          </button>
        </div>
      </form>

      <div className="st-danger-zone">
        <h3 className="st-danger-title">Danger zone</h3>
        <p className="st-danger-desc">
          Deleting your account will permanently remove your workspace, API keys, and all
          benchmark data. This action cannot be undone.
        </p>
        <button type="button" className="st-btn st-btn-danger" disabled title="Contact administrator">
          Delete account
        </button>
      </div>
    </section>
  );
}
