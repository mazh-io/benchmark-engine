'use client';

import { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { supabase } from '@/api/supabase';
import { useAuth } from '@/contexts/AuthContext';

const AUTH_WAIT_MS = 8000;

export default function AuthPage() {
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

    function finish(session: import('@supabase/supabase-js').Session) {
      if (doneRef.current || cancelled) return;
      doneRef.current = true;
      loginFromSession(session);
      setStatus('ok');
      router.replace(redirectPath);
    }

    const authSub = supabase.auth.onAuthStateChange((event, session) => {
      if (cancelled) return;
      if (session && (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED' || event === 'INITIAL_SESSION')) {
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
        setStatus('error');
        setMessage('No session returned. Try signing in again.');
      }
    }, 100);

    const maxWait = window.setTimeout(() => {
      if (!doneRef.current && !cancelled && status === 'loading') {
        setStatus('error');
        setMessage('No session returned. Try signing in again.');
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
    return (
      <div className="min-h-screen bg-black flex flex-col items-center justify-center gap-4 px-4">
        <p className="text-white/80 text-center">{message}</p>
        <Link href="/login" className="text-white underline hover:no-underline">
          Back to login
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
