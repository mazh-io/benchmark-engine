'use client';

type AccountUser = {
  initials: string;
  firstName: string;
  lastName: string;
  email: string;
};

interface AccountSectionProps {
  user: AccountUser;
}

export function AccountSection({ user }: AccountSectionProps) {
  return (
    <section>
      <h2 className="st-section-title">Account</h2>

      {/* Avatar upload */}
      <div className="st-avatar-upload">
        <div className="st-avatar-large">{user.initials}</div>
        <div className="st-avatar-actions">
          <button type="button" className="st-btn st-btn-secondary">
            Upload Photo
          </button>
          <p className="st-avatar-hint">PNG or JPG, at least 240x240px.</p>
        </div>
      </div>

      {/* Profile form */}
      <form
        onSubmit={(event) => {
          event.preventDefault();
        }}
      >
        <div className="st-form-row">
          <div className="st-form-group">
            <label className="st-form-label" htmlFor="first-name">
              First name
            </label>
            <input
              id="first-name"
              className="st-form-input"
              defaultValue={user.firstName}
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
              defaultValue={user.lastName}
              placeholder="Last name"
            />
          </div>
        </div>

        <div className="st-form-group">
          <label className="st-form-label" htmlFor="email">
            Email
          </label>
          <div className="st-email-row">
            <input
              id="email"
              type="email"
              className="st-form-input"
              defaultValue={user.email}
              placeholder="you@example.com"
            />
            <button type="button" className="st-btn st-btn-secondary">
              Change email
            </button>
          </div>
          <p className="st-form-hint">
            We&apos;ll use this address for account notifications and receipts.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
          <button type="submit" className="st-btn st-btn-primary">
            Save changes
          </button>
          <button type="button" className="st-btn st-btn-secondary">
            Cancel
          </button>
        </div>
      </form>

      {/* Danger zone */}
      <div className="st-danger-zone">
        <h3 className="st-danger-title">Danger zone</h3>
        <p className="st-danger-desc">
          Deleting your account will permanently remove your workspace, API keys, and all
          benchmark data. This action cannot be undone.
        </p>
        <button type="button" className="st-btn st-btn-danger">
          Delete account
        </button>
      </div>
    </section>
  );
}

