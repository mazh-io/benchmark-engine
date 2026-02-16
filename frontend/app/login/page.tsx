'use client';

import { useState, useRef, useCallback } from 'react';
import Link from 'next/link';
import { Header } from '@/layout/Header';

export default function LoginPage() {
  const [screen, setScreen] = useState<'email' | 'otp'>('email');
  const [email, setEmail] = useState('');
  const otpRefs = useRef<(HTMLInputElement | null)[]>([]);

  const handleEmailSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (email) setScreen('otp');
  };

  const handleOtpInput = useCallback((index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    const el = otpRefs.current[index];
    if (el) el.value = value;
    if (value && index < 5) otpRefs.current[index + 1]?.focus();
  }, []);

  const handleOtpKeyDown = useCallback((index: number, key: string) => {
    if (key === 'Backspace' && !otpRefs.current[index]?.value && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  }, []);

  const handleOtpPaste = useCallback((e: React.ClipboardEvent<HTMLDivElement>) => {
    e.preventDefault();
    const paste = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    paste.split('').forEach((char, i) => {
      if (otpRefs.current[i]) otpRefs.current[i]!.value = char;
    });
    if (paste.length === 6) otpRefs.current[5]?.focus();
  }, []);

  const handleOtpSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const code = otpRefs.current.map((r) => r?.value || '').join('');
    if (code.length === 6) {
      // Here you would verify the code and redirect
      console.log('Verifying code:', code, 'for email:', email);
    }
  };

  return (
    <div className="login-page">
      <Header tier="logged-out" />

      <main className="login-main">
        <div className="login-card">
          {screen === 'email' && (
            <>
              <div className="login-header">
                <div className="login-logo">MAZH</div>
                <h1 className="login-title">Welcome back</h1>
                <p className="login-subtitle">Sign in to access your dashboard</p>
              </div>

              <div className="oauth-buttons">
                <button className="oauth-btn">
                  <svg viewBox="0 0 24 24">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                  </svg>
                  Continue with Google
                </button>
                <button className="oauth-btn">
                  <svg viewBox="0 0 24 24" fill="#fff">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                  </svg>
                  Continue with GitHub
                </button>
              </div>

              <div className="login-divider">
                <span className="login-divider-line" />
                <span className="login-divider-text">or</span>
                <span className="login-divider-line" />
              </div>

              <form className="login-email-form" onSubmit={handleEmailSubmit}>
                <div className="login-input-group">
                  <label htmlFor="email">Email address</label>
                  <input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
                <button type="submit" className="login-btn-submit">
                  Continue with Email
                </button>
              </form>

              <p className="login-terms">
                By continuing, you agree to our<br />
                <Link href="/terms">Terms of Service</Link> and{' '}
                <Link href="/privacy">Privacy Policy</Link>
              </p>
            </>
          )}

          {screen === 'otp' && (
            <>
              <button className="login-btn-back" type="button" onClick={() => setScreen('email')}>
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

              <form onSubmit={handleOtpSubmit}>
                <div className="login-otp-inputs" onPaste={handleOtpPaste}>
                  {Array.from({ length: 6 }).map((_, index) => (
                    <input
                      key={index}
                      ref={(el) => {
                        otpRefs.current[index] = el;
                      }}
                      type="text"
                      className="login-otp-input"
                      maxLength={1}
                      inputMode="numeric"
                      pattern="[0-9]"
                      required
                      onInput={(e) => handleOtpInput(index, (e.target as HTMLInputElement).value)}
                      onKeyDown={(e) => handleOtpKeyDown(index, e.key)}
                    />
                  ))}
                </div>
                <button type="submit" className="login-btn-submit" style={{ width: '100%' }}>
                  Verify
                </button>
              </form>

              <p className="login-otp-resend">
                Didn&apos;t receive the code?{' '}
                <button type="button" onClick={() => console.log('Resend to', email)}>
                  Resend
                </button>
              </p>
            </>
          )}
        </div>
      </main>

      <footer className="login-footer">
        <div className="login-footer-links">
          <Link href="/privacy">Privacy</Link>
          <Link href="/terms">Terms</Link>
          <Link href="/imprint">Imprint</Link>
        </div>
      </footer>
    </div>
  );
}

