import type { FormEvent, KeyboardEvent } from 'react';

interface OtpCodePanelProps {
  email: string;
  loading: boolean;
  error: string | null;
  canResend: boolean;
  secondsUntilResend: number;
  onBack: () => void;
  onRef: (index: number, el: HTMLInputElement | null) => void;
  onInput: (index: number, value: string) => void;
  onKeyDown: (index: number, key: string) => void;
  onPaste: (e: React.ClipboardEvent<HTMLDivElement>) => void;
  onSubmit: (e: FormEvent) => void;
  onResend: () => void;
}

export function OtpCodePanel({
  email,
  loading,
  error,
  canResend,
  secondsUntilResend,
  onBack,
  onRef,
  onInput,
  onKeyDown,
  onPaste,
  onSubmit,
  onResend,
}: OtpCodePanelProps) {
  const handleKeyDown = (index: number) => (e: KeyboardEvent<HTMLInputElement>) => {
    onKeyDown(index, e.key);
  };

  const handleInput = (index: number) => (e: React.FormEvent<HTMLInputElement>) => {
    onInput(index, (e.target as HTMLInputElement).value);
  };

  return (
    <>
      <button className="login-btn-back" type="button" onClick={onBack}>
        <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <path d="M19 12H5M12 19l-7-7 7-7" />
        </svg>
        Back
      </button>

      <div className="login-header">
        <div className="login-logo">MAZH</div>
        <h1 className="login-title">Check your email</h1>
      </div>

      <div className="login-otp-info">
        <p>We sent a 6-digit code to</p>
        <p className="login-otp-email">{email}</p>
      </div>

      {error && <p className="login-error">{error}</p>}

      <form onSubmit={onSubmit}>
        <div className="login-otp-inputs" onPaste={onPaste}>
          {Array.from({ length: 6 }).map((_, index) => (
            <input
              key={index}
              ref={(el) => onRef(index, el)}
              type="text"
              className="login-otp-input"
              maxLength={1}
              inputMode="numeric"
              pattern="[0-9]"
              required
              onInput={handleInput(index)}
              onKeyDown={handleKeyDown(index)}
            />
          ))}
        </div>
        <button type="submit" className="login-btn-submit" style={{ width: '100%' }} disabled={loading}>
          {loading ? 'Verifying…' : 'Verify'}
        </button>
      </form>

      <p className="login-otp-resend">
        {!canResend ? (
          <>
            You can request a new code in <strong>{secondsUntilResend}s</strong>.
          </>
        ) : (
          <>
            Didn&apos;t receive the code?{' '}
            <button type="button" onClick={onResend} disabled={loading}>
              Resend
            </button>
          </>
        )}
      </p>
    </>
  );
}
