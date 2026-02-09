/**
 * React Query Hook for Benchmark Data
 *
 * Provides optimized data fetching with:
 * - Automatic caching (30s stale time)
 * - Background refetching (60s interval)
 * - Automatic retries on failure
 * - Loading and error states
 *
 * Usage:
 * ```tsx
 * const { data, isLoading, error } = useBenchmarkData({ timeRange: '24h' });
 * ```
 */

'use client';

import { useQuery, keepPreviousData, type UseQueryResult } from '@tanstack/react-query';
import { getBenchmarkResults } from '@/api/supabase';
import { aggregateAllProviderMetrics } from '@/api/calculations';
import { TIME_RANGES, type ProviderMetrics, type TimeFilter } from '@/api/types';
import type { BenchmarkResultWithRelations } from '@/api/types';

// ============================================================================
// TYPES
// ============================================================================

export interface BenchmarkDataResult {
  results: BenchmarkResultWithRelations[];
  metrics: Map<string, ProviderMetrics>;
}

export interface UseBenchmarkDataOptions {
  timeRange?: TimeFilter;
  autoRefresh?: boolean;
  enabled?: boolean;
}

// ============================================================================
// QUERY KEY
// ============================================================================

const benchmarkKey = (timeRange: string) =>
  ['benchmark', 'results', timeRange] as const;

// ============================================================================
// MAIN HOOK
// ============================================================================

/**
 * Fetch and aggregate benchmark data
 *
 * @param options - Configuration options
 * @returns Query result with data, loading, and error states
 */
export function useBenchmarkData(
  options: UseBenchmarkDataOptions = {},
): UseQueryResult<BenchmarkDataResult> {
  const {
    timeRange = '24h',
    autoRefresh = true,
    enabled = true,
  } = options;

  // For 'live', fetch last 24 hours of data
  const effectiveTimeRange = timeRange === 'live' ? '24h' : timeRange;
  const hours = TIME_RANGES[effectiveTimeRange] / (60 * 60 * 1000);

  return useQuery({
    queryKey: benchmarkKey(timeRange),

    queryFn: async (): Promise<BenchmarkDataResult> => {
      const startTime = performance.now();

      const results = await getBenchmarkResults(hours);

      // Aggregate metrics on client side (fast for < 10K rows)
      const metrics = aggregateAllProviderMetrics(
        results as BenchmarkResultWithRelations[],
      );

      if (process.env.NODE_ENV === 'development') {
        const elapsed = (performance.now() - startTime).toFixed(2);
        console.log(`🔄 Data fetch completed in ${elapsed}ms`);
        console.log(`📊 ${results.length} results, ${metrics.size} providers`);
      }

      return {
        results: results as BenchmarkResultWithRelations[],
        metrics,
      };
    },

    // Caching strategy
    staleTime: 30_000,
    gcTime: 5 * 60 * 1000,
    refetchInterval: autoRefresh ? 60_000 : false,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,

    // Keep previous data while fetching (smooth transitions)
    placeholderData: keepPreviousData,

    // Retry strategy
    retry: 3,
    retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 30_000),

    enabled,
    throwOnError: false,
  });
}
