'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { supabase } from '@/api/supabase';
import type { AccountUser, EmailMessage } from './accountTypes';

export interface UseAccountSectionOptions {
  onDirtyChange?: (dirty: boolean) => void;
}

export function useAccountSection(user: AccountUser, options: UseAccountSectionOptions = {}) {
  const { onDirtyChange } = options;
  const [firstName, setFirstName] = useState(user.firstName);
  const [lastName, setLastName] = useState(user.lastName);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  const [stagedAvatarFile, setStagedAvatarFile] = useState<File | null>(null);
  const [stagedAvatarPreview, setStagedAvatarPreview] = useState<string | null>(null);
  const stagedUrlRef = useRef<string | null>(null);

  const [changeEmailMode, setChangeEmailMode] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [changingEmail, setChangingEmail] = useState(false);
  const [emailMessage, setEmailMessage] = useState<EmailMessage>(null);
  const [emailError, setEmailError] = useState<string | null>(null);
  const [emailSuccessNewEmail, setEmailSuccessNewEmail] = useState<string | null>(null);

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const [avatarUploading, setAvatarUploading] = useState(false);
  const [avatarError, setAvatarError] = useState<string | null>(null);

  const isDirty =
    firstName !== user.firstName ||
    lastName !== user.lastName ||
    stagedAvatarFile !== null;

  useEffect(() => {
    onDirtyChange?.(isDirty);
  }, [isDirty, onDirtyChange]);

  useEffect(() => {
    return () => {
      if (stagedUrlRef.current) {
        URL.revokeObjectURL(stagedUrlRef.current);
        stagedUrlRef.current = null;
      }
    };
  }, []);

  const clearSaveSuccess = useCallback(() => {
    setSaveSuccess(null);
  }, []);

  const handleSaveProfile = useCallback(
    async (e?: React.FormEvent) => {
      e?.preventDefault?.();
      setSaveError(null);
      setSaveSuccess(null);
      setSaving(true);
      setAvatarError(null);
      try {
        let avatarUrl: string | null = null;
        if (stagedAvatarFile && user.id) {
          const ext = stagedAvatarFile.name.split('.').pop()?.toLowerCase() || 'jpg';
          const path = `${user.id}/avatar.${ext}`;
          const { error: uploadError } = await supabase.storage
            .from('avatars')
            .upload(path, stagedAvatarFile, { upsert: true, contentType: stagedAvatarFile.type });
          if (uploadError) {
            setAvatarError(uploadError.message || 'Upload failed');
            setSaving(false);
            return;
          }
          const { data: urlData } = supabase.storage.from('avatars').getPublicUrl(path);
          avatarUrl = urlData.publicUrl;
        }
        const data: { first_name: string; last_name: string; avatar_url?: string } = {
          first_name: firstName.trim(),
          last_name: lastName.trim(),
        };
        if (avatarUrl !== null) data.avatar_url = avatarUrl;
        const { error } = await supabase.auth.updateUser({ data });
        if (error) {
          setSaveError(error.message || 'Failed to save');
          setSaving(false);
          return;
        }
        if (stagedUrlRef.current) {
          URL.revokeObjectURL(stagedUrlRef.current);
          stagedUrlRef.current = null;
        }
        setStagedAvatarFile(null);
        setStagedAvatarPreview(null);
        setSaveSuccess('Your changes have been saved.');
        setTimeout(clearSaveSuccess, 4000);
      } finally {
        setSaving(false);
      }
    },
    [firstName, lastName, stagedAvatarFile, user.id, clearSaveSuccess],
  );

  const handleDiscard = useCallback(() => {
    setFirstName(user.firstName);
    setLastName(user.lastName);
    setSaveError(null);
    setAvatarError(null);
    if (stagedUrlRef.current) {
      URL.revokeObjectURL(stagedUrlRef.current);
      stagedUrlRef.current = null;
    }
    setStagedAvatarFile(null);
    setStagedAvatarPreview(null);
  }, [user.firstName, user.lastName]);

  const handleChangeEmail = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = newEmail.trim();
    if (!trimmed) return;
    if (trimmed.toLowerCase() === user.email.toLowerCase()) {
      setEmailError('Enter a different email address.');
      return;
    }
    setEmailMessage(null);
    setEmailError(null);
    setChangingEmail(true);
    const redirectTo =
      typeof window !== 'undefined'
        ? `${window.location.origin}/auth?next=${encodeURIComponent('/settings')}`
        : undefined;
    const { error } = await supabase.auth.updateUser(
      { email: trimmed },
      { emailRedirectTo: redirectTo },
    );
    setChangingEmail(false);
    if (error) {
      setEmailMessage('error');
      setEmailError(error.message || 'Failed to update email.');
      return;
    }
    setEmailSuccessNewEmail(trimmed);
    setEmailMessage('success');
    setChangeEmailMode(false);
    setNewEmail('');
  }, [newEmail, user.email]);

  const handleDeleteAccount = useCallback(async () => {
    setDeleteError(null);
    setDeleting(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session?.access_token) {
        setDeleteError('Not logged in');
        setDeleting(false);
        return;
      }
      const res = await fetch('/api/account', {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (!res.ok) {
        let detail: string;
        if (res.status === 503) {
          detail =
            'Account deletion is not configured on the server. Contact support to remove your account.';
        } else {
          const body = await res.json().catch(() => null);
          detail =
            body?.error || `Failed to delete account (${res.status})`;
        }
        setDeleteError(detail);
        setDeleting(false);
        return;
      }
      await supabase.auth.signOut();
      window.location.replace('/login');
    } catch (e) {
      setDeleteError(e instanceof Error ? e.message : 'Something went wrong');
      setDeleting(false);
    }
  }, []);

  const cancelEmailEdit = useCallback(() => {
    setChangeEmailMode(false);
    setNewEmail('');
    setEmailMessage(null);
    setEmailError(null);
  }, []);

  const cancelDelete = useCallback(() => {
    setShowDeleteConfirm(false);
    setDeleteError(null);
  }, []);

  const handleAvatarUpload = useCallback((file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase() || 'jpg';
    if (!['jpg', 'jpeg', 'png', 'webp'].includes(ext)) {
      setAvatarError('Use JPG, PNG or WebP');
      return;
    }
    setAvatarError(null);
    if (stagedUrlRef.current) {
      URL.revokeObjectURL(stagedUrlRef.current);
      stagedUrlRef.current = null;
    }
    const url = URL.createObjectURL(file);
    stagedUrlRef.current = url;
    setStagedAvatarPreview(url);
    setStagedAvatarFile(file);
  }, []);

  return {
    profile: {
      firstName,
      setFirstName,
      lastName,
      setLastName,
      saving,
      saveError,
      saveSuccess,
      saveSuccessClear: clearSaveSuccess,
      handleSaveProfile,
      handleDiscard,
      isDirty,
    },
    email: {
      changeEmailMode,
      setChangeEmailMode,
      newEmail,
      setNewEmail,
      changingEmail,
      emailMessage,
      emailError,
      emailSuccessNewEmail,
      handleChangeEmail,
      cancelEmailEdit,
    },
    dangerZone: {
      showDeleteConfirm,
      setShowDeleteConfirm,
      deleting,
      deleteError,
      handleDeleteAccount,
      cancelDelete,
    },
    avatar: {
      avatarUploading,
      avatarError,
      avatarPreviewUrl: stagedAvatarPreview ?? user.avatarUrl ?? null,
      handleAvatarUpload,
    },
  };
}
