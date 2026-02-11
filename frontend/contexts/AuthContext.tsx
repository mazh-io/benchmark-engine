'use client';

import { createContext, useContext, useState, useCallback, useEffect } from 'react';

const STORAGE_KEY = 'mazh_auth';

type User = { initials: string; name: string; email: string };

interface AuthState {
  isLoggedIn: boolean;
  user: User | null;
}

function getStored(): AuthState {
  if (typeof window === 'undefined') return { isLoggedIn: false, user: null };
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { isLoggedIn: false, user: null };
    const parsed = JSON.parse(raw);
    return { isLoggedIn: !!parsed.user, user: parsed.user || null };
  } catch {
    return { isLoggedIn: false, user: null };
  }
}

function toInitials(email: string): string {
  const part = email.split('@')[0];
  if (!part) return '?';
  if (part.length >= 2) return part.slice(0, 2).toUpperCase();
  return part[0].toUpperCase();
}

const AuthContext = createContext<{
  isLoggedIn: boolean;
  user: User | null;
  login: (email: string) => void;
  logout: () => void;
} | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({ isLoggedIn: false, user: null });

  useEffect(() => {
    setState(getStored());
  }, []);

  const login = useCallback((email: string) => {
    const name = email.split('@')[0] || 'User';
    const user: User = {
      initials: toInitials(email),
      name: name.charAt(0).toUpperCase() + name.slice(1),
      email,
    };
    setState({ isLoggedIn: true, user });
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ user }));
    } catch {}
  }, []);

  const logout = useCallback(() => {
    setState({ isLoggedIn: false, user: null });
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {}
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
