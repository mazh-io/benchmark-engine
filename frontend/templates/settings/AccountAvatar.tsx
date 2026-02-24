'use client';

import { useRef } from 'react';

export interface AccountAvatarProps {
  initials: string;
  avatarUrl: string | null;
  onUpload: (file: File) => void;
  uploading: boolean;
  error: string | null;
}

export function AccountAvatar({ initials, avatarUrl, onUpload, uploading, error }: AccountAvatarProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onUpload(file);
    e.target.value = '';
  };

  return (
    <div className="st-avatar-upload">
      <div className="st-avatar-large">
        {avatarUrl ? (
          <img
            src={avatarUrl}
            alt=""
            className="st-avatar-img"
            style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 'inherit' }}
          />
        ) : (
          initials
        )}
      </div>
      <div className="st-avatar-actions">
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="sr-only"
          aria-label="Upload photo"
          onChange={handleChange}
          disabled={uploading}
        />
        <button
          type="button"
          className="st-btn st-btn-secondary"
          disabled={uploading}
          onClick={() => inputRef.current?.click()}
        >
          {uploading ? 'Uploading…' : 'Upload Photo'}
        </button>
        <p className="st-avatar-hint">PNG or JPG, at least 240x240px.</p>
        {error && (
          <p className="st-form-hint" style={{ color: 'var(--st-danger, #ef4444)', marginTop: 4 }}>
            {error}
          </p>
        )}
      </div>
    </div>
  );
}
