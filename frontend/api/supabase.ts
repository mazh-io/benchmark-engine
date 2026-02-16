/**
 * Supabase Client Configuration
 *
 * Singleton pattern with type safety, error handling, and perf monitoring.
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';
import type { Database } from './database.types';

// ============================================================================
// CONFIGURATION
// ============================================================================

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL! || process.env.SUPABASE_URL!;
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY! || process.env.SUPABASE_ANON_KEY!;

if (!SUPABASE_URL) {
  throw new Error('Missing NEXT_PUBLIC_SUPABASE_URL environment variable');
}
if (!SUPABASE_ANON_KEY) {
  throw new Error('Missing NEXT_PUBLIC_SUPABASE_ANON_KEY environment variable');
}

// ============================================================================
// SINGLETON CLIENT
// ============================================================================

let instance: SupabaseClient<Database> | null = null;

function getClient(): SupabaseClient<Database> {
  if (!instance) {
    instance = createClient<Database>(SUPABASE_URL, SUPABASE_ANON_KEY, {
      auth: { persistSession: false },
      global: {
        headers: { 'x-client-info': 'benchmark-dashboard@1.0.0' },
      },
    });

    if (process.env.NODE_ENV === 'development') {
      console.log('✅ Supabase client initialized');
    }
  }
  return instance;
}

export const supabase = getClient();

// ============================================================================
// QUERY HELPERS
// ============================================================================

/**
 * Fetch benchmark results with provider/model relations
 *
 * Optimized: selective columns, time-based filter, success-only.
 *
 * @param hoursAgo - Filter results from last N hours (default: 24)
 * @param limit - Max rows to return (default: 1000)
 */
export async function getBenchmarkResults(hoursAgo = 24, limit = 1000) {
  const startTime = performance.now();
  const cutoff = new Date(Date.now() - hoursAgo * 60 * 60 * 1000).toISOString();

  const { data, error } = await supabase
    .from('benchmark_results')
    .select(`
      id, run_id, provider, model,
      input_tokens, output_tokens, total_latency_ms,
      ttft_ms, tps, status_code,
      cost_usd, tokens_per_dollar, created_at,
      providers:provider_id ( name ),
      models:model_id ( name )
    `)
    .eq('success', true)
    .gte('created_at', cutoff)
    .order('created_at', { ascending: false })
    .limit(limit);

  if (process.env.NODE_ENV === 'development') {
    const elapsed = (performance.now() - startTime).toFixed(2);
    console.log(`Query completed in ${elapsed}ms — ${data?.length ?? 0} rows`);
  }

  if (error) {
    console.error('Supabase query error:', error);
    throw new Error(`Failed to fetch benchmark results: ${error.message}`);
  }

  return data;
}
