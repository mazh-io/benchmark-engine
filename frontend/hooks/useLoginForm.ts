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
    const redirectTo = typeof window !== 'undefined' ? `${window.location.origin}/auth` : '';
    const { error: err } = await supabase.auth.signInWithOtp({
      email: email.trim(),
      options: { shouldCreateUser: true, emailRedirectTo: redirectTo },
    });
    setLoading(false);
    if (err) {
q      const isRateLimit = /security purposes|rate limit|too many/i.test(err.message ?? '');
      if (isRateLimit) {
        const secsMatch = err.message?.match(/(\d+)\s*seconds?/i);
        const waitMs = secsMatch ? parseInt(secsMatch[1], 10) * 1000 : RESEND_COOLDOWN_MS;
        setResendAvailableAt(Date.now() + waitMs);
        setScreen('otp');
        return;
      }
      setError(err.message || 'Failed to send code. Please try again.');
      return;
    }
    setScreen('otp');
    setResendAvailableAt(Date.now() + RESEND_COOLDOWN_MS);
  }, [email]);

  const clearOtpInputs = useCallback(() => {
    otpRefs.current.forEach((el) => {
      if (el) {
        el.value = '';
      }
    });
    otpRefs.current[0]?.focus();
  }, []);

  const runOtpVerify = useCallback(async () => {
    const code = otpRefs.current.map((r) => r?.value || '').join('');
    if (code.length !== 6 || loading) return;
    setError(null);
    setLoading(true);

    const { data, error: verifyErr } = await supabase.auth.verifyOtp({
      email: email.trim(),
      token: code,
      type: 'email',
    });

    if (!verifyErr && data.session) {
      setLoading(false);
      loginFromSession(data.session);
      router.push('/');
      return;
    }

    // SDK returned error — try raw verify with magiclink type as fallback
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
    const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '';
    try {
      const res = await fetch(`${supabaseUrl}/auth/v1/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          apikey: anonKey,
          Authorization: `Bearer ${anonKey}`,
        },
        body: JSON.stringify({ email: email.trim(), token: code, type: 'magiclink' }),
      });
      const body = await res.json();
      if (res.ok && body.access_token) {
        const { data: sessionData } = await supabase.auth.setSession({
          access_token: body.access_token,
          refresh_token: body.refresh_token,
        });
        setLoading(false);
        if (sessionData.session) {
          loginFromSession(sessionData.session);
          router.push('/');
        }
        return;
      }
    } catch (_) {
      // fallback failed
    }

    setLoading(false);
    clearOtpInputs();
    setError(verifyErr?.message || 'Invalid or expired code. Click "Resend code" to get a new one.');
  }, [email, loading, loginFromSession, router, clearOtpInputs]);

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
    const redirectTo = typeof window !== 'undefined' ? `${window.location.origin}/auth` : '';
    const { error: err } = await supabase.auth.signInWithOtp({
      email: email.trim(),
      options: { shouldCreateUser: true, emailRedirectTo: redirectTo },
    });
    setLoading(false);
    if (err) {
      const isRateLimit = /security purposes|rate limit|too many/i.test(err.message ?? '');
      if (isRateLimit) {
        const secsMatch = err.message?.match(/(\d+)\s*seconds?/i);
        const waitMs = secsMatch ? parseInt(secsMatch[1], 10) * 1000 : RESEND_COOLDOWN_MS;
        setResendAvailableAt(Date.now() + waitMs);
        return;
      }
      setError(err.message || 'Failed to resend code. Please try again.');
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
