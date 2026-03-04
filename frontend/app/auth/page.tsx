'use client';

import { Suspense, useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { supabase } from '@/api/supabase';
import { useAuth } from '@/contexts/AuthContext';

const AUTH_WAIT_MS = 8000;

export default function AuthPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-black flex items-center justify-center">
          <p className="text-white/70">Signing you in…</p>
        </div>
      }
    >
      <AuthInner />
    </Suspense>
  );
}

function parseHash(): { error?: string; message?: string } {
  if (typeof window === 'undefined') return {};
  const hash = window.location.hash;
  if (!hash) return {};
  const params = new URLSearchParams(hash.replace('#', ''));
  const error = params.get('error_description') || params.get('error');
  const message = params.get('message');
  return {
    error: error ? error.replace(/\+/g, ' ') : undefined,
    message: message ? message.replace(/\+/g, ' ') : undefined,
  };
}

function AuthInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { loginFromSession } = useAuth();
  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading');
  const [message, setMessage] = useState('');
  const doneRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    const next = searchParams.get('next');
    const redirectPath = next && next.startsWith('/') ? next : '/';
    const hashInfo = parseHash();

    // If the hash contains an actual error (expired, denied), show immediately
    if (hashInfo.error) {
      const friendly = /expired/i.test(hashInfo.error)
        ? 'This link has expired. Please request a new one.'
        : hashInfo.error;
      setStatus('error');
      setMessage(friendly);
      return;
    }

    // Detect email change double-confirmation message from hash.
    // We do NOT return early here — let Supabase SDK process the tokens first.
    const isEmailChangeMessage =
      !!hashInfo.message && /confirmation|sent.*other.*email/i.test(hashInfo.message);

    function finish(session: import('@supabase/supabase-js').Session) {
      if (doneRef.current || cancelled) return;
      doneRef.current = true;
      loginFromSession(session);

      if (isEmailChangeMessage) {
        setStatus('error');
        setMessage(
          'Almost done! We\'ve sent a confirmation link to your new email address. Please check your inbox and click the link to complete the change.',
        );
      } else {
        setStatus('ok');
        router.replace(redirectPath);
      }
    }

    const authSub = supabase.auth.onAuthStateChange((event, session) => {
      if (cancelled) return;
      if (
        session &&
        (event === 'SIGNED_IN' ||
          event === 'TOKEN_REFRESHED' ||
          event === 'INITIAL_SESSION' ||
          event === 'USER_UPDATED')
      ) {
        finish(session);
      }
    });

    const timeoutId = window.setTimeout(async () => {
      if (doneRef.current || cancelled) return;
      for (let i = 0; i < 20; i++) {
        const { data: { session }, error } = await supabase.auth.getSession();
        if (cancelled) return;
        if (error) {
          setStatus('error');
          setMessage(error.message || 'Could not complete sign in');
          return;
        }
        if (session) {
          finish(session);
          return;
        }
        await new Promise((r) => setTimeout(r, 250));
      }
      if (!doneRef.current && !cancelled) {
        if (isEmailChangeMessage) {
          setStatus('error');
          setMessage(
            'Almost done! We\'ve sent a confirmation link to your new email address. Please check your inbox and click the link to complete the change.',
          );
        } else {
          setStatus('error');
          setMessage('No session returned. Try signing in again.');
        }
      }
    }, 100);

    const maxWait = window.setTimeout(() => {
      if (!doneRef.current && !cancelled && status === 'loading') {
        if (isEmailChangeMessage) {
          setStatus('error');
          setMessage(
            'Almost done! We\'ve sent a confirmation link to your new email address. Please check your inbox and click the link to complete the change.',
          );
        } else {
          setStatus('error');
          setMessage('No session returned. Try signing in again.');
        }
      }
    }, AUTH_WAIT_MS);

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
      clearTimeout(maxWait);
      authSub?.data?.subscription?.unsubscribe?.();
    };
  }, [loginFromSession, router, searchParams]);

  if (status === 'error') {
    const backPath = searchParams.get('next') || '/login';
    const backLabel = backPath === '/login' ? 'Back to login' : 'Back to settings';
    return (
      <div className="min-h-screen bg-black flex flex-col items-center justify-center gap-4 px-4">
        <p className="text-white/80 text-center">{message}</p>
        <Link href={backPath} className="text-white underline hover:no-underline">
          {backLabel}
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black flex items-center justify-center">
      <p className="text-white/70">Signing you in…</p>
    </div>
  );
}
