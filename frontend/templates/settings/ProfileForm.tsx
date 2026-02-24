export interface ProfileFormProps {
  firstName: string;
  lastName: string;
  onFirstNameChange: (v: string) => void;
  onLastNameChange: (v: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  onDiscard?: () => void;
  saving: boolean;
}

export function ProfileForm({
  firstName,
  lastName,
  onFirstNameChange,
  onLastNameChange,
  onSubmit,
  onDiscard,
  saving,
}: ProfileFormProps) {
  return (
    <form onSubmit={onSubmit}>
      <div className="st-form-row">
        <div className="st-form-group">
          <label className="st-form-label" htmlFor="first-name">
            First name
          </label>
          <input
            id="first-name"
            className="st-form-input"
            value={firstName}
            onChange={(e) => onFirstNameChange(e.target.value)}
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
            onChange={(e) => onLastNameChange(e.target.value)}
            placeholder="Last name"
          />
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
        <button type="submit" className="st-btn st-btn-primary" disabled={saving}>
          {saving ? 'Saving…' : 'Save changes'}
        </button>
        {onDiscard && (
          <button type="button" className="st-btn st-btn-secondary" onClick={onDiscard} disabled={saving}>
            Discard
          </button>
        )}
      </div>
    </form>
  );
}
