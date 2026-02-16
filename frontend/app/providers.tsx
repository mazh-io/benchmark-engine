'use client';

import { useState } from 'react';
import { QueryClient, QueryClientProvider as RQProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/contexts/AuthContext';

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            gcTime: 5 * 60_000,
            refetchOnWindowFocus: true,
            refetchOnReconnect: true,
            refetchInterval: false,
            retry: 3,
            retryDelay: (n) => Math.min(1000 * 2 ** n, 30_000),
            networkMode: 'online',
          },
          mutations: {
            retry: 1,
            networkMode: 'online',
          },
        },
      }),
  );

  return (
    <RQProvider client={client}>
      <AuthProvider>{children}</AuthProvider>
    </RQProvider>
  );
}
