'use client';

import { forwardRef, useImperativeHandle, useRef } from 'react';
import type { AccountUser } from './accountTypes';
import { useAccountSection } from './useAccountSection';
import { AccountAvatar } from './AccountAvatar';
import { ProfileForm } from './ProfileForm';
import { EmailField } from './EmailField';
import { DangerZone } from './DangerZone';

export type { AccountUser };

export interface AccountSectionProps {
  user: AccountUser;
  onDirtyChange?: (dirty: boolean) => void;
}

export interface AccountSectionRef {
  save: () => Promise<void>;
  discard: () => void;
}

export const AccountSection = forwardRef<AccountSectionRef, AccountSectionProps>(function AccountSection(
  { user, onDirtyChange },
  ref,
) {
  const { profile, email, dangerZone, avatar } = useAccountSection(user, { onDirtyChange });
  const saveRef = useRef(profile.handleSaveProfile);
  saveRef.current = profile.handleSaveProfile;

  useImperativeHandle(ref, () => ({
    save: () => saveRef.current?.(),
    discard: profile.handleDiscard,
  }), [profile.handleDiscard]);

  return (
    <section>
      <h2 className="st-section-title">Account</h2>

      <AccountAvatar
        initials={user.initials}
        avatarUrl={avatar.avatarPreviewUrl}
        onUpload={avatar.handleAvatarUpload}
        uploading={profile.saving}
        error={avatar.avatarError}
      />

      <ProfileForm
        firstName={profile.firstName}
        lastName={profile.lastName}
        onFirstNameChange={profile.setFirstName}
        onLastNameChange={profile.setLastName}
        onSubmit={(e) => profile.handleSaveProfile(e)}
        onDiscard={profile.isDirty ? profile.handleDiscard : undefined}
        saving={profile.saving}
      />

      {profile.saveSuccess && (
        <p className="st-form-hint st-form-success">
          {profile.saveSuccess}
        </p>
      )}
      {profile.saveError && (
        <p className="st-form-hint" style={{ color: 'var(--st-danger, #ef4444)' }}>
          {profile.saveError}
        </p>
      )}

      <div className="st-mt">
        <EmailField
        email={user.email}
        isEditing={email.changeEmailMode}
        onStartEdit={() => email.setChangeEmailMode(true)}
        newEmail={email.newEmail}
        onNewEmailChange={email.setNewEmail}
        onSubmit={email.handleChangeEmail}
        onCancel={email.cancelEmailEdit}
        changing={email.changingEmail}
        message={email.emailMessage}
        error={email.emailError}
        successNewEmail={email.emailSuccessNewEmail}
      />
      </div>

      <DangerZone
        showConfirm={dangerZone.showDeleteConfirm}
        onStartDelete={() => dangerZone.setShowDeleteConfirm(true)}
        onConfirmDelete={dangerZone.handleDeleteAccount}
        onCancel={dangerZone.cancelDelete}
        deleting={dangerZone.deleting}
        error={dangerZone.deleteError}
      />
    </section>
  );
});
