'use client';

import Link from 'next/link';
import { Header } from '@/layout/Header';
import { useLoginForm } from '@/hooks/useLoginForm';
import { LoginEmailStep } from '@/templates/login/LoginEmailStep';
import { OtpCodePanel } from '@/templates/login/OtpCodePanel';

export default function LoginPage() {
  const login = useLoginForm();

  if (login.isReady && login.isLoggedIn) {
    return <div className="min-h-screen bg-black" />;
  }

  return (
    <div className="login-page">
      <Header tier="logged-out" />

      <main className="login-main">
        <div className="login-card">
          {login.screen === 'email' && (
            <LoginEmailStep
              email={login.email}
              loading={login.loading}
              error={login.error}
              oauthLoading={login.oauthLoading}
              onEmailChange={login.setEmail}
              onOAuth={login.handleOAuth}
              onEmailSubmit={login.handleEmailSubmit}
            />
          )}

          {login.screen === 'otp' && (
            <OtpCodePanel
              email={login.email}
              loading={login.loading}
              error={login.error}
              canResend={login.canResend}
              secondsUntilResend={login.secondsUntilResend}
              onBack={login.handleOtpBack}
              onRef={login.setOtpRef}
              onInput={login.handleOtpInput}
              onKeyDown={login.handleOtpKeyDown}
              onPaste={login.handleOtpPaste}
              onSubmit={login.handleOtpSubmit}
              onResend={login.handleResend}
            />
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
