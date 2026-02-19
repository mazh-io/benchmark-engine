import type { FormEvent, ChangeEvent } from 'react';
import Link from 'next/link';

interface ContinueWithEmailProps {
  email: string;
  loading: boolean;
  onEmailChange: (value: string) => void;
  onSubmit: (e: FormEvent) => void;
}

export function ContinueWithEmail({
  email,
  loading,
  onEmailChange,
  onSubmit,
}: ContinueWithEmailProps) {
  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    onEmailChange(e.target.value);
  };

  return (
    <>
      <form className="login-email-form" onSubmit={onSubmit}>
        <div className="login-input-group">
          <label htmlFor="email">Email address</label>
          <input
            id="email"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={handleChange}
            required
          />
        </div>
        <button type="submit" className="login-btn-submit" disabled={loading}>
          {loading ? 'Sending…' : 'Continue with Email'}
        </button>
      </form>

      <p className="login-terms">
        By continuing, you agree to our
        <br />
        <Link href="/terms">Terms of Service</Link> and <Link href="/privacy">Privacy Policy</Link>
      </p>
    </>
  );
}
