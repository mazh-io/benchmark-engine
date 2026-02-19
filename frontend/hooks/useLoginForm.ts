'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { supabase } from '@/api/supabase';
import { useAuth } from '@/contexts/AuthContext';

const RESEND_COOLDOWN_MS = 60 * 1000;

export type LoginScreen = 'email' | 'otp';
export type OAuthProvider = 'google' | 'github';

export interface UseLoginFormReturn {
  isReady: boolean;
  isLoggedIn: boolean;
  screen: LoginScreen;
  email: string;
  setEmail: (v: string) => void;
  loading: boolean;
  oauthLoading: 'google' | 'github' | null;
  error: string | null;
  canResend: boolean;
  secondsUntilResend: number;
  handleOAuth: (provider: OAuthProvider) => Promise<void>;
  handleEmailSubmit: (e: React.FormEvent) => Promise<void>;
  handleOtpBack: () => void;
  setOtpRef: (index: number, el: HTMLInputElement | null) => void;
  handleOtpInput: (index: number, value: string) => void;
  handleOtpKeyDown: (index: number, key: string) => void;
  handleOtpPaste: (e: React.ClipboardEvent<HTMLDivElement>) => void;
  handleOtpSubmit: (e: React.FormEvent) => Promise<void>;
  handleResend: () => Promise<void>;
}

export function useLoginForm(): UseLoginFormReturn {
  const router = useRouter();
  const { isLoggedIn, isReady, loginFromSession } = useAuth();
  const [screen, setScreen] = useState<LoginScreen>('email');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState<'google' | 'github' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [resendAvailableAt, setResendAvailableAt] = useState<number | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const otpRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    if (isReady && isLoggedIn) router.replace('/');
  }, [isReady, isLoggedIn, router]);

  useEffect(() => {
    if (screen !== 'otp') return;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [screen]);

  const secondsUntilResend =
    resendAvailableAt != null ? Math.max(0, Math.ceil((resendAvailableAt - now) / 1000)) : 0;
  const canResend = !resendAvailableAt || secondsUntilResend <= 0;

  const handleOAuth = useCallback(async (provider: OAuthProvider) => {
    setError(null);
    setOauthLoading(provider);
    const { error: err } = await supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: `${typeof window !== 'undefined' ? window.location.origin : ''}/auth`,
      },
    });
    setOauthLoading(null);
    if (err) setError(err.message || `Failed to sign in with ${provider}`);
  }, []);

  const handleEmailSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!email.trim()) return;
    setLoading(true);
    const { error: err } = await supabase.auth.signInWithOtp({
      email: email.trim(),
      options: { shouldCreateUser: true },
    });
    setLoading(false);
    if (err) {
      setError(err.message || 'Failed to send code');
      return;
    }
    setScreen('otp');
    setResendAvailableAt(Date.now() + RESEND_COOLDOWN_MS);
  }, [email]);

  const runOtpVerify = useCallback(async () => {
    const code = otpRefs.current.map((r) => r?.value || '').join('');
    if (code.length !== 6 || loading) return;
    setError(null);
    setLoading(true);
    const { data, error: err } = await supabase.auth.verifyOtp({
      email: email.trim(),
      token: code,
      type: 'email',
    });
    setLoading(false);
    if (err) {
      setError(err.message || 'Invalid or expired code');
      return;
    }
    if (data?.session) {
      loginFromSession(data.session);
      router.push('/');
    }
  }, [email, loading, loginFromSession, router]);

  const handleOtpInput = useCallback(
    (index: number, value: string) => {
      if (!/^\d*$/.test(value)) return;
      const el = otpRefs.current[index];
      if (el) el.value = value;
      if (value && index < 5) otpRefs.current[index + 1]?.focus();
      const code = otpRefs.current.map((r) => r?.value || '').join('');
      if (code.length === 6) void runOtpVerify();
    },
    [runOtpVerify],
  );

  const handleOtpKeyDown = useCallback((index: number, key: string) => {
    if (key === 'Backspace' && !otpRefs.current[index]?.value && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  }, []);

  const handleOtpPaste = useCallback(
    (e: React.ClipboardEvent<HTMLDivElement>) => {
      e.preventDefault();
      const paste = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
      paste.split('').forEach((char, i) => {
        if (otpRefs.current[i]) otpRefs.current[i]!.value = char;
      });
      if (paste.length === 6) {
        otpRefs.current[5]?.focus();
        void runOtpVerify();
      }
    },
    [runOtpVerify],
  );

  const handleOtpSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      await runOtpVerify();
    },
    [runOtpVerify],
  );

  const handleResend = useCallback(async () => {
    if (!canResend) return;
    setError(null);
    setLoading(true);
    const { error: err } = await supabase.auth.signInWithOtp({
      email: email.trim(),
      options: { shouldCreateUser: true },
    });
    setLoading(false);
    if (err) {
      setError(err.message || 'Failed to resend');
      return;
    }
    setResendAvailableAt(Date.now() + RESEND_COOLDOWN_MS);
  }, [email, canResend]);

  const setOtpRef = useCallback((index: number, el: HTMLInputElement | null) => {
    otpRefs.current[index] = el;
  }, []);

  return {
    isReady,
    isLoggedIn,
    screen,
    email,
    setEmail,
    loading,
    oauthLoading,
    error,
    canResend,
    secondsUntilResend,
    handleOAuth,
    handleEmailSubmit,
    handleOtpBack: () => setScreen('email'),
    setOtpRef,
    handleOtpInput,
    handleOtpKeyDown,
    handleOtpPaste,
    handleOtpSubmit,
    handleResend,
  };
}
