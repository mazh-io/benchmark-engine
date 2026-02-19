import type { OAuthProvider } from '@/hooks/useLoginForm';
import { ContinueWithGoogle } from './ContinueWithGoogle';
import { ContinueWithGithub } from './ContinueWithGithub';
import { ContinueWithEmail } from './ContinueWithEmail';

export interface LoginEmailStepProps {
  email: string;
  loading: boolean;
  error: string | null;
  oauthLoading: 'google' | 'github' | null;
  onEmailChange: (value: string) => void;
  onOAuth: (provider: OAuthProvider) => void;
  onEmailSubmit: (e: React.FormEvent) => void;
}

export function LoginEmailStep({
  email,
  loading,
  error,
  oauthLoading,
  onEmailChange,
  onOAuth,
  onEmailSubmit,
}: LoginEmailStepProps) {
  return (
    <>
      <div className="login-header">
        <div className="login-logo">MAZH</div>
        <h1 className="login-title">Welcome back</h1>
        <p className="login-subtitle">Sign in to access your dashboard</p>
      </div>

      {error && <p className="login-error">{error}</p>}
      <div className="oauth-buttons">
        <ContinueWithGoogle
          loading={oauthLoading === 'google'}
          onClick={() => onOAuth('google')}
        />
        <ContinueWithGithub
          loading={oauthLoading === 'github'}
          onClick={() => onOAuth('github')}
        />
      </div>

      <div className="login-divider">
        <span className="login-divider-line" />
        <span className="login-divider-text">or</span>
        <span className="login-divider-line" />
      </div>

      <ContinueWithEmail
        email={email}
        loading={loading}
        onEmailChange={onEmailChange}
        onSubmit={onEmailSubmit}
      />
    </>
  );
}
