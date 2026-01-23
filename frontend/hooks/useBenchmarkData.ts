/**
 * React Query Hook for Benchmark Data
 * 
 * Provides optimized data fetching with:
 * - Automatic caching (30s stale time)
 * - Background refetching (60s interval)
 * - Automatic retries on failure
 * - Loading and error states
 * - Server-side rendering support
 * 
 * Usage:
 * ```tsx
 * const { data, isLoading, error, refetch } = useBenchmarkData({ timeRange: '24h' });
 * ```
 */

'use client';

import { useQuery, useQueryClient, type UseQueryResult } from '@tanstack/react-query';
import { getBenchmarkResults, getProviders, getRecentRuns } from '@/lib/supabase';
import { aggregateAllProviderMetrics } from '@/lib/calculations';
import { TIME_RANGES, type DashboardFilters, type ProviderMetrics } from '@/lib/types';
import type { BenchmarkResultWithRelations, Provider, Run } from '@/lib/types';

// ============================================================================
// TYPES
// ============================================================================

export interface BenchmarkDataResult {
  results: BenchmarkResultWithRelations[];
  metrics: Map<string, ProviderMetrics>;
  providers: Provider[];
  runs: Run[];
  lastUpdated: string;
}

export interface UseBenchmarkDataOptions {
  timeRange?: '1h' | '24h' | '7d' | '30d';
  autoRefresh?: boolean;
  enabled?: boolean;
}

// ============================================================================
// QUERY KEYS
// ============================================================================

/**
 * Query key factory for React Query
 * 
 * Benefits:
 * - Type-safe query keys
 * - Centralized key management
 * - Easy cache invalidation
 */
const benchmarkKeys = {
  all: ['benchmark'] as const,
  results: (timeRange: string) => ['benchmark', 'results', timeRange] as const,
  providers: () => ['benchmark', 'providers'] as const,
  runs: () => ['benchmark', 'runs'] as const,
};

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
  options: UseBenchmarkDataOptions = {}
): UseQueryResult<BenchmarkDataResult> {
  const {
    timeRange = '24h',
    autoRefresh = true,
    enabled = true,
  } = options;
  
  const hours = TIME_RANGES[timeRange] / (60 * 60 * 1000);
  
  return useQuery({
    queryKey: benchmarkKeys.results(timeRange),
    queryFn: async (): Promise<BenchmarkDataResult> => {
      const startTime = performance.now();
      
      // Fetch all data in parallel for better performance
      const [results, providers, runs] = await Promise.all([
        getBenchmarkResults(hours),
        getProviders(),
        getRecentRuns(10),
      ]);
      
      // Aggregate metrics on client side
      // This is faster than server-side aggregation for < 10K rows
      const metrics = aggregateAllProviderMetrics(results as BenchmarkResultWithRelations[]);
      
      const endTime = performance.now();
      
      // Performance monitoring
      if (process.env.NODE_ENV === 'development') {
        console.log(`🔄 Data fetch completed in ${(endTime - startTime).toFixed(2)}ms`);
        console.log(`📊 ${results.length} results, ${metrics.size} providers`);
      }
      
      return {
        results: results as BenchmarkResultWithRelations[],
        metrics,
        providers,
        runs,
        lastUpdated: new Date().toISOString(),
      };
    },
    
    // Caching strategy (optimized for dashboard)
    staleTime: 30_000,           // Data is fresh for 30 seconds
    gcTime: 5 * 60 * 1000,       // Cache for 5 minutes (renamed from cacheTime)
    refetchInterval: autoRefresh ? 60_000 : false,  // Auto-refresh every 60s
    refetchOnWindowFocus: true,  // Refresh when tab regains focus
    refetchOnReconnect: true,    // Refresh when internet reconnects
    
    // Retry strategy
    retry: 3,                    // Retry failed requests 3 times
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    
    // Enable/disable query
    enabled,
    
    // Error handling
    throwOnError: false,         // Don't throw errors, handle via error state
  });
}

// ============================================================================
// PROVIDER-SPECIFIC HOOKS
// ============================================================================

/**
 * Fetch providers only (cached separately)
 * 
 * Providers change infrequently, so we cache them longer
 */
export function useProviders(): UseQueryResult<Provider[]> {
  return useQuery({
    queryKey: benchmarkKeys.providers(),
    queryFn: getProviders,
    staleTime: 5 * 60 * 1000,    // Fresh for 5 minutes
    gcTime: 30 * 60 * 1000,      // Cache for 30 minutes
    retry: 2,
  });
}

/**
 * Fetch recent runs
 */
export function useRecentRuns(limit: number = 10): UseQueryResult<Run[]> {
  return useQuery({
    queryKey: [...benchmarkKeys.runs(), limit],
    queryFn: () => getRecentRuns(limit),
    staleTime: 60_000,           // Fresh for 1 minute
    gcTime: 10 * 60 * 1000,      // Cache for 10 minutes
    retry: 2,
  });
}

// ============================================================================
// FILTERED DATA HOOKS
// ============================================================================

/**
 * Get filtered benchmark data based on dashboard filters
 * 
 * This hook applies client-side filtering on top of cached data
 * to avoid unnecessary API calls
 * 
 * @param filters - Dashboard filter options
 */
export function useFilteredBenchmarkData(
  filters: DashboardFilters
): UseQueryResult<BenchmarkDataResult> {
  const baseQuery = useBenchmarkData({ timeRange: filters.timeRange });
  
  // Transform data based on filters
  return {
    ...baseQuery,
    data: baseQuery.data ? filterBenchmarkData(baseQuery.data, filters) : undefined,
  } as UseQueryResult<BenchmarkDataResult>;
}

/**
 * Apply filters to benchmark data
 * 
 * @param data - Raw benchmark data
 * @param filters - Filter options
 * @returns Filtered data
 */
function filterBenchmarkData(
  data: BenchmarkDataResult,
  filters: DashboardFilters
): BenchmarkDataResult {
  let { results, metrics } = data;
  
  // Filter by category (direct vs proxy)
  if (filters.category !== 'all') {
    results = results.filter(r => {
      const category = r.provider && PROVIDER_CATEGORIES[r.provider];
      return category === filters.category;
    });
    
    // Recalculate metrics for filtered results
    metrics = aggregateAllProviderMetrics(results);
  }
  
  // Filter by minimum sample size
  if (filters.minSampleSize > 0) {
    const filteredMetrics = new Map<string, ProviderMetrics>();
    
    for (const [provider, metric] of metrics.entries()) {
      if (metric.sampleSize >= filters.minSampleSize) {
        filteredMetrics.set(provider, metric);
      }
    }
    
    metrics = filteredMetrics;
  }
  
  return {
    ...data,
    results,
    metrics,
  };
}

// ============================================================================
// CACHE MANAGEMENT
// ============================================================================

/**
 * Hook to invalidate (refresh) benchmark data
 * 
 * Usage:
 * ```tsx
 * const invalidate = useInvalidateBenchmarkData();
 * 
 * // Force refresh
 * invalidate();
 * ```
 */
export function useInvalidateBenchmarkData() {
  const queryClient = useQueryClient();
  
  return () => {
    queryClient.invalidateQueries({ queryKey: benchmarkKeys.all });
  };
}

/**
 * Hook to prefetch data (for better UX)
 * 
 * Useful for prefetching data before navigation
 * 
 * Usage:
 * ```tsx
 * const prefetch = usePrefetchBenchmarkData();
 * 
 * <button onMouseEnter={() => prefetch('7d')}>
 *   View 7-day data
 * </button>
 * ```
 */
export function usePrefetchBenchmarkData() {
  const queryClient = useQueryClient();
  
  return (timeRange: '1h' | '24h' | '7d' | '30d') => {
    const hours = TIME_RANGES[timeRange] / (60 * 60 * 1000);
    
    queryClient.prefetchQuery({
      queryKey: benchmarkKeys.results(timeRange),
      queryFn: async () => {
        const [results, providers, runs] = await Promise.all([
          getBenchmarkResults(hours),
          getProviders(),
          getRecentRuns(10),
        ]);
        
        const metrics = aggregateAllProviderMetrics(results as BenchmarkResultWithRelations[]);
        
        return {
          results: results as BenchmarkResultWithRelations[],
          metrics,
          providers,
          runs,
          lastUpdated: new Date().toISOString(),
        };
      },
      staleTime: 30_000,
    });
  };
}

// ============================================================================
// HELPER IMPORTS
// ============================================================================

import { PROVIDER_CATEGORIES } from '@/lib/types';

