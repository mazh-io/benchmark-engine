import type { EmailMessage } from './accountTypes';

export interface EmailFieldProps {
  email: string;
  isEditing: boolean;
  onStartEdit: () => void;
  newEmail: string;
  onNewEmailChange: (v: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  changing: boolean;
  message: EmailMessage;
  error?: string | null;
  successNewEmail?: string | null;
}

export function EmailField({
  email,
  isEditing,
  onStartEdit,
  newEmail,
  onNewEmailChange,
  onSubmit,
  onCancel,
  changing,
  message,
  error,
  successNewEmail,
}: EmailFieldProps) {
  return (
    <div className="st-form-group">
      <label className="st-form-label" htmlFor="email">
        Email
      </label>
      {!isEditing ? (
        <>
          <div
            className="st-email-row st-email-row-clickable"
            onClick={onStartEdit}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onStartEdit(); } }}
            role="button"
            tabIndex={0}
            aria-label="Change email"
          >
            <input
              id="email"
              type="email"
              className="st-form-input"
              value={email}
              readOnly
              placeholder="you@example.com"
              tabIndex={-1}
            />
            <span className="st-btn st-btn-secondary" aria-hidden>
              Change email
            </span>
          </div>
        </>
      ) : (
        <form onSubmit={onSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <input
            id="new-email"
            type="email"
            className="st-form-input"
            value={newEmail}
            onChange={(e) => onNewEmailChange(e.target.value)}
            placeholder="New email address"
            required
            autoFocus
            autoComplete="email"
            aria-label="New email address"
          />
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button type="submit" className="st-btn st-btn-primary" disabled={changing}>
              {changing ? 'Sending…' : 'Update email'}
            </button>
            <button type="button" className="st-btn st-btn-secondary" onClick={onCancel}>
              Cancel
            </button>
          </div>
          {error && (
            <p className="st-form-hint" style={{ color: 'var(--st-danger, #ef4444)' }}>
              {error}
            </p>
          )}
          {message === 'success' && (
            <p className="st-form-hint st-form-success">
              We&apos;ve sent a confirmation link to {successNewEmail || 'your new email'}. Check that inbox and click the link to confirm the change.
            </p>
          )}
        </form>
      )}
      {!isEditing && (
        <>
          <p className="st-form-hint">
            We&apos;ll use this address for account notifications and receipts. Click &quot;Change email&quot; to enter a new address.
          </p>
          {message === 'success' && successNewEmail && (
            <p className="st-form-hint st-form-success">
              We&apos;ve sent a confirmation link to {successNewEmail}. Check that inbox and click the link to confirm the change.
            </p>
          )}
        </>
      )}
    </div>
  );
}
