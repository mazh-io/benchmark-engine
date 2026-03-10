'use client';

import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/api/supabase';

// ============================================================================
// TYPES
// ============================================================================

export interface MonitoringResult {
  id: string;
  provider: string | null;
  model: string | null;
  ttft_ms: number | null;
  tps: number | null;
  success: boolean;
  status_code: number | null;
  error_message: string | null;
  created_at: string;
}

export interface QueueStats {
  pending: number;
  processing: number;
  completed: number;
  failed: number;
}

export interface RunError {
  id: string;
  provider: string | null;
  model: string | null;
  error_type: string;
  error_message: string;
  status_code: number | null;
  timestamp: string;
}

export interface ProviderStatus {
  key: string;
  displayName: string;
  models: ModelStatus[];
  totalModels: number;
  liveModels: number;
  errorModels: number;
  lastBenchmark: string | null;
  status: 'green' | 'yellow' | 'red';
  datapoints: number;
}

export interface ModelStatus {
  name: string;
  status: 'live' | 'error' | 'stale';
  ttft_ms: number | null;
  tps: number | null;
  lastBenchmark: string | null;
  errorMessage: string | null;
  datapoints: number;
}

export interface MonitoringData {
  providers: ProviderStatus[];
  queue: QueueStats;
  errors: RunError[];
  totalModels: number;
  liveModels: number;
  errorModels: number;
  totalDatapoints: number;
}

// ============================================================================
// PROVIDER CONFIG (frontend mirror)
// ============================================================================

const PROVIDER_DISPLAY: Record<string, string> = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  google: 'Google',
  deepseek: 'DeepSeek',
  xai: 'xAI',
  mistral: 'Mistral AI',
  groq: 'Groq',
  together: 'Together AI',
  cerebras: 'Cerebras',
  fireworks: 'Fireworks AI',
  sambanova: 'SambaNova',
  perplexity: 'Perplexity',
  cohere: 'Cohere',
  openrouter: 'OpenRouter',
};

// Provider display order (determines card sort within same status)
const PROVIDER_ORDER: string[] = [
  'openai', 'anthropic', 'google', 'deepseek', 'xai', 'mistral',
  'groq', 'together', 'cerebras', 'fireworks', 'sambanova',
  'perplexity', 'cohere', 'openrouter',
];

// ============================================================================
// QUERY FUNCTIONS
// ============================================================================

async function fetchLatestResults(): Promise<MonitoringResult[]> {
  const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();

  const { data, error } = await supabase
    .from('benchmark_results')
    .select('id, provider, model, ttft_ms, tps, success, status_code, error_message, created_at')
    .gte('created_at', cutoff)
    .order('created_at', { ascending: false })
    .limit(5000);

  if (error) throw new Error(`Failed to fetch results: ${error.message}`);
  return (data ?? []) as MonitoringResult[];
}

async function fetchQueueStats(): Promise<QueueStats> {
  const { data, error } = await supabase
    .from('benchmark_queue')
    .select('status')
    .order('created_at', { ascending: false })
    .limit(500);

  if (error) throw new Error(`Failed to fetch queue: ${error.message}`);

  const stats: QueueStats = { pending: 0, processing: 0, completed: 0, failed: 0 };
  for (const row of (data ?? []) as { status: string }[]) {
    const s = row.status as keyof QueueStats;
    if (s in stats) stats[s]++;
  }
  return stats;
}

async function fetchDatapointCounts(): Promise<Map<string, number>> {
  // Use RPC or paginated fetch to get ALL successful results counted per provider::model
  // Supabase default limit is 1000, so we paginate
  const PAGE = 5000;
  let offset = 0;
  const counts = new Map<string, number>();

  // eslint-disable-next-line no-constant-condition
  while (true) {
    const { data, error } = await supabase
      .from('benchmark_results')
      .select('provider, model')
      .eq('success', true)
      .range(offset, offset + PAGE - 1);

    if (error) throw new Error(`Failed to fetch counts: ${error.message}`);
    if (!data || data.length === 0) break;

    for (const row of data as { provider: string | null; model: string | null }[]) {
      if (!row.provider || !row.model) continue;
      const key = `${row.provider}::${row.model}`;
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }

    if (data.length < PAGE) break;
    offset += PAGE;
  }

  return counts;
}

async function fetchRecentErrors(): Promise<RunError[]> {
  const cutoff = new Date(Date.now() - 60 * 60 * 1000).toISOString(); // last 1h

  const { data, error } = await supabase
    .from('run_errors')
    .select('id, provider, model, error_type, error_message, status_code, timestamp')
    .gte('timestamp', cutoff)
    .order('timestamp', { ascending: false })
    .limit(100);

  if (error) throw new Error(`Failed to fetch errors: ${error.message}`);
  return (data ?? []) as RunError[];
}

// ============================================================================
// AGGREGATION
// ============================================================================

function aggregateMonitoringData(
  results: MonitoringResult[],
  queue: QueueStats,
  errors: RunError[],
  dpCounts: Map<string, number>,
): MonitoringData {
  const thirtyMinAgo = Date.now() - 30 * 60 * 1000;

  // Build model → latest result map (keyed by provider::model)
  // Results are already ordered desc by created_at, so first seen = latest
  const modelLatest = new Map<string, MonitoringResult>();
  for (const r of results) {
    if (!r.provider || !r.model) continue;
    const key = `${r.provider}::${r.model}`;
    if (!modelLatest.has(key)) {
      modelLatest.set(key, r);
    }
  }

  // Also add error-only models (models that only appear in run_errors, never in benchmark_results)
  // These are models that fail before producing any result row
  for (const err of errors) {
    if (!err.provider || !err.model) continue;
    const key = `${err.provider}::${err.model}`;
    if (!modelLatest.has(key)) {
      // Synthesize a "result" entry for display
      modelLatest.set(key, {
        id: err.id,
        provider: err.provider,
        model: err.model,
        ttft_ms: null,
        tps: null,
        success: false,
        status_code: err.status_code,
        error_message: err.error_message,
        created_at: err.timestamp,
      });
    }
  }

  // Group discovered models by provider
  const providerModelsMap = new Map<string, Map<string, MonitoringResult>>();
  for (const [, result] of modelLatest) {
    const provider = result.provider!;
    const model = result.model!;
    if (!providerModelsMap.has(provider)) providerModelsMap.set(provider, new Map());
    providerModelsMap.get(provider)!.set(model, result);
  }

  let totalLive = 0;
  let totalError = 0;
  let totalModels = 0;

  const providers: ProviderStatus[] = [];

  for (const [providerKey, modelsMap] of providerModelsMap) {
    const models: ModelStatus[] = [];
    let providerLastBenchmark: string | null = null;

    for (const [modelName, latest] of modelsMap) {
      totalModels++;
      const ts = new Date(latest.created_at).getTime();

      let status: 'live' | 'error' | 'stale' = 'stale';
      if (latest.success && ts > thirtyMinAgo) {
        status = 'live';
      } else if (!latest.success) {
        status = 'error';
      }

      if (status === 'live') totalLive++;
      if (status === 'error') totalError++;

      if (!providerLastBenchmark || latest.created_at > providerLastBenchmark) {
        providerLastBenchmark = latest.created_at;
      }

      const modelDp = dpCounts.get(`${providerKey}::${modelName}`) ?? 0;

      models.push({
        name: modelName,
        status,
        ttft_ms: latest.ttft_ms ?? null,
        tps: latest.tps ?? null,
        lastBenchmark: latest.created_at,
        errorMessage: latest.error_message ?? null,
        datapoints: modelDp,
      });
    }

    // Sort models: errors first, then by name
    models.sort((a, b) => {
      if (a.status === 'error' && b.status !== 'error') return -1;
      if (a.status !== 'error' && b.status === 'error') return 1;
      return a.name.localeCompare(b.name);
    });

    const liveCount = models.filter((m) => m.status === 'live').length;
    const errorCount = models.filter((m) => m.status === 'error').length;

    let provStatus: 'green' | 'yellow' | 'red' = 'green';
    if (errorCount === models.length) provStatus = 'red';
    else if (errorCount > 0 || liveCount < models.length) provStatus = 'yellow';

    const providerDp = models.reduce((sum, m) => sum + m.datapoints, 0);

    providers.push({
      key: providerKey,
      displayName: PROVIDER_DISPLAY[providerKey] ?? providerKey,
      models,
      totalModels: models.length,
      liveModels: liveCount,
      errorModels: errorCount,
      lastBenchmark: providerLastBenchmark,
      status: provStatus,
      datapoints: providerDp,
    });
  }

  // Sort: red first, then yellow, then green; within same status, by PROVIDER_ORDER
  const statusOrder = { red: 0, yellow: 1, green: 2 };
  providers.sort((a, b) => {
    const sd = statusOrder[a.status] - statusOrder[b.status];
    if (sd !== 0) return sd;
    const ai = PROVIDER_ORDER.indexOf(a.key);
    const bi = PROVIDER_ORDER.indexOf(b.key);
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
  });

  let totalDatapoints = 0;
  for (const v of dpCounts.values()) totalDatapoints += v;

  return {
    providers,
    queue,
    errors,
    totalModels,
    liveModels: totalLive,
    errorModels: totalError,
    totalDatapoints,
  };
}

// ============================================================================
// HOOK
// ============================================================================

export function useMonitoringData() {
  return useQuery({
    queryKey: ['monitoring'],
    queryFn: async (): Promise<MonitoringData> => {
      // Fetch all three in parallel, but don't let one failure kill everything
      const [results, queue, errors, dpCounts] = await Promise.all([
        fetchLatestResults().catch((e) => {
          console.error('[monitoring] results fetch failed:', e);
          return [] as MonitoringResult[];
        }),
        fetchQueueStats().catch((e) => {
          console.error('[monitoring] queue fetch failed:', e);
          return { pending: 0, processing: 0, completed: 0, failed: 0 } as QueueStats;
        }),
        fetchRecentErrors().catch((e) => {
          console.error('[monitoring] errors fetch failed:', e);
          return [] as RunError[];
        }),
        fetchDatapointCounts().catch((e) => {
          console.error('[monitoring] datapoint counts fetch failed:', e);
          return new Map<string, number>();
        }),
      ]);
      return aggregateMonitoringData(results, queue, errors, dpCounts);
    },
    staleTime: 30_000,
    gcTime: 5 * 60_000,
    refetchInterval: 30_000,
    refetchOnWindowFocus: true,
    retry: 3,
    retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 30_000),
  });
}
