/**
 * QueryClientProvider Component
 * 
 * Wraps the app with React Query's QueryClientProvider.
 * Configures default options for caching, retries, and refetching.
 */

'use client';

import { useState } from 'react';
import { QueryClient, QueryClientProvider as TanStackQueryClientProvider } from '@tanstack/react-query';

export function QueryClientProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Caching strategy
            staleTime: 30_000, // Data is fresh for 30 seconds
            gcTime: 5 * 60 * 1000, // Cache persists for 5 minutes (renamed from cacheTime in v5)
            
            // Refetching behavior
            refetchOnWindowFocus: true, // Refetch when user returns to tab
            refetchOnReconnect: true, // Refetch on network reconnection
            refetchInterval: false, // Disable automatic polling (we use it per-hook)
            
            // Error handling
            retry: 3, // Retry failed requests 3 times
            retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff
            
            // Performance
            networkMode: 'online', // Only fetch when online
          },
          mutations: {
            // Mutation defaults
            retry: 1,
            networkMode: 'online',
          },
        },
      })
  );

  return (
    <TanStackQueryClientProvider client={queryClient}>
      {children}
    </TanStackQueryClientProvider>
  );
}

