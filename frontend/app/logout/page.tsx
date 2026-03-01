'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export default function LogoutPage() {
  const router = useRouter();
  const { logout } = useAuth();

  useEffect(() => {
    logout();
    router.replace('/login');
  }, [logout, router]);

  return (
    <div className="min-h-screen bg-black flex items-center justify-center">
      <p className="text-white/70">Signing out…</p>
    </div>
  );
}
