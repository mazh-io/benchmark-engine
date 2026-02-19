'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { supabase } from '@/api/supabase';
import { useAuth } from '@/contexts/AuthContext';

export default function AuthPage() {
  const router = useRouter();
  const { loginFromSession } = useAuth();
  const [status, setStatus] = useState<'loading' | 'ok' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    let cancelled = false;

    async function finish() {
      for (let i = 0; i < 3; i++) {
        const { data: { session }, error } = await supabase.auth.getSession();
        if (cancelled) return;
        if (error) {
          setStatus('error');
          setMessage(error.message || 'Could not complete sign in');
          return;
        }
        if (session) {
          loginFromSession(session);
          setStatus('ok');
          router.replace('/');
          return;
        }
        await new Promise((r) => setTimeout(r, 300));
      }
      if (cancelled) return;
      setStatus('error');
      setMessage('No session returned. Try signing in again.');
    }

    finish();
    return () => {
      cancelled = true;
    };
  }, [loginFromSession, router]);

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
