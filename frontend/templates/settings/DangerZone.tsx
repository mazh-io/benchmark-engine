export interface DangerZoneProps {
  showConfirm: boolean;
  onStartDelete: () => void;
  onConfirmDelete: () => void;
  onCancel: () => void;
  deleting: boolean;
  error: string | null;
}

export function DangerZone({
  showConfirm,
  onStartDelete,
  onConfirmDelete,
  onCancel,
  deleting,
  error,
}: DangerZoneProps) {
  return (
    <div className="st-danger-zone">
      <h3 className="st-danger-title">Danger zone</h3>
      <p className="st-danger-desc">
        Deactivating your account will sign you out and disable access. Your data remains
        in our system but your account will no longer be active. Contact support if you
        want to restore it later.
      </p>
      {!showConfirm ? (
        <button type="button" className="st-btn st-btn-danger" onClick={onStartDelete}>
          Delete account
        </button>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <p className="st-form-hint" style={{ color: 'var(--st-danger, #ef4444)' }}>
            Are you sure? You will be signed out immediately.
          </p>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button
              type="button"
              className="st-btn st-btn-danger"
              disabled={deleting}
              onClick={onConfirmDelete}
            >
              {deleting ? 'Deactivating…' : 'Yes, delete my account'}
            </button>
            <button
              type="button"
              className="st-btn st-btn-secondary"
              disabled={deleting}
              onClick={onCancel}
            >
              Cancel
            </button>
          </div>
          {error && (
            <p className="st-form-hint" style={{ color: 'var(--st-danger, #ef4444)' }}>
              {error}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
