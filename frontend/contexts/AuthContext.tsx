'use client';

import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import type { Session } from '@supabase/supabase-js';
import { supabase } from '@/api/supabase';

type User = { initials: string; name: string; email: string };

function capitalize(s: string): string {
  return s ? s.charAt(0).toUpperCase() + s.slice(1).toLowerCase() : '';
}

function nameFromMetadata(meta: Record<string, unknown> | undefined): { first: string; last: string } | null {
  const first = typeof meta?.first_name === 'string' ? meta.first_name.trim() : '';
  const last = typeof meta?.last_name === 'string' ? meta.last_name.trim() : '';
  if (first || last) return { first: first || 'User', last };
  return null;
}

function nameFromEmail(email: string): { first: string; last: string } {
  const local = email.split('@')[0] || 'user';
  const parts = local.split(/[._-]+/).filter(Boolean);
  const first = capitalize(parts[0] || 'User');
  const last = parts.slice(1).map(capitalize).join(' ') || '';
  return { first, last };
}

function sessionToUser(session: Session | null): User | null {
  if (!session?.user?.email) return null;
  const email = session.user.email;
  const meta = session.user.user_metadata as Record<string, unknown> | undefined;
  const { first, last } = nameFromMetadata(meta) ?? nameFromEmail(email);
  const name = [first, last].filter(Boolean).join(' ');
  const initials = last
    ? (first.slice(0, 1) + last.slice(0, 1)).toUpperCase()
    : first.slice(0, 2).toUpperCase() || 'U';
  return { initials, name, email };
}

const AuthContext = createContext<{
  isLoggedIn: boolean;
  isReady: boolean;
  user: User | null;
  loginFromSession: (session: Session) => void;
  logout: () => void;
} | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isReady, setIsReady] = useState(false);

  const setFromSession = useCallback((session: Session | null) => {
    setUser(sessionToUser(session));
  }, []);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setFromSession(session);
      setIsReady(true);
    });
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setFromSession(session);
    });
    return () => subscription.unsubscribe();
  }, [setFromSession]);

  const loginFromSession = useCallback((session: Session) => {
    setUser(sessionToUser(session));
  }, []);

  const logout = useCallback(async () => {
    await supabase.auth.signOut();
    setUser(null);
  }, []);

  const isLoggedIn = !!user;

  return (
    <AuthContext.Provider value={{ isLoggedIn, isReady, user, loginFromSession, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
