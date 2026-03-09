'use client';

import { useState, useMemo } from 'react';
import { ChevronDown } from 'lucide-react';
import {
  useMonitoringData,
  type ProviderStatus,
  type ModelStatus,
  type RunError,
} from '@/hooks/useMonitoringData';

// ============================================================================
// HELPERS
// ============================================================================

function timeAgo(iso: string | null): string {
  if (!iso) return '—';
  const diff = Date.now() - new Date(iso).getTime();
  if (diff < 60_000) return `${Math.floor(diff / 1000)}s ago`;
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return `${Math.floor(diff / 86_400_000)}d ago`;
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatMetric(val: number | null, suffix: string): string {
  if (val === null || val === undefined) return '—';
  if (suffix === 'ms') {
    return val >= 1000 ? `${(val / 1000).toFixed(1)}s` : `${Math.round(val)}ms`;
  }
  return `${Math.round(val)} ${suffix}`;
}

function shortModelName(name: string): string {
  // Strip common prefixes for display
  return name
    .replace(/^accounts\/fireworks\/models\//, '')
    .replace(/^models\//, '')
    .replace(/^meta-llama\//, '')
    .replace(/^deepseek-ai\//, '')
    .replace(/^mistralai\//, '')
    .replace(/^Qwen\//, '')
    .replace(/^MiniMaxAI\//, '')
    .replace(/^zai-org\//, '')
    .replace(/^moonshotai\//, '')
    .replace(/^openai\//, '')
    .replace(/^minimax\//, '')
    .replace(/^x-ai\//, '')
    .replace(/^z-ai\//, '')
    .replace(/^xiaomi\//, '')
    .replace(/^qwen\//, '');
}

// ============================================================================
// STAT CARD
// ============================================================================

function StatCard({
  value,
  label,
  color,
}: {
  value: number | string;
  label: string;
  color: string;
}) {
  return (
    <div className="monitoring-stat-card">
      <div className="monitoring-stat-value" style={{ color }}>
        {value}
      </div>
      <div className="monitoring-stat-label">{label}</div>
    </div>
  );
}

// ============================================================================
// PROVIDER CARD
// ============================================================================

function ProviderCard({
  provider,
  expanded,
  onToggle,
}: {
  provider: ProviderStatus;
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <div
      className={`monitoring-card monitoring-card--${provider.status} ${expanded ? 'monitoring-card--expanded' : ''}`}
      onClick={onToggle}
    >
      <div className="monitoring-card-header">
        <div className="flex items-center gap-2">
          <span className={`monitoring-dot monitoring-dot--${provider.status}`} />
          <span className="monitoring-card-name">{provider.displayName}</span>
        </div>
        <span className="monitoring-card-ratio">
          {provider.liveModels}/{provider.totalModels}
        </span>
      </div>
      <div className="monitoring-card-meta">
        {provider.errorModels > 0 && (
          <span style={{ color: '#ef4444' }}>
            {provider.errorModels} error{provider.errorModels > 1 ? 's' : ''}
            {' · '}
          </span>
        )}
        {timeAgo(provider.lastBenchmark)}
      </div>

      {expanded && (
        <div className="monitoring-model-table">
          <div
            className="monitoring-model-row"
            style={{ color: 'var(--text-4)', fontWeight: 600, fontSize: '10px', borderBottom: '1px solid var(--border)' }}
          >
            <span />
            <span>Model</span>
            <span style={{ textAlign: 'right' }}>TTFT</span>
            <span style={{ textAlign: 'right' }}>TPS</span>
            <span style={{ textAlign: 'right' }}>Age</span>
          </div>
          {provider.models.map((model) => (
            <ModelRow key={model.name} model={model} />
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// MODEL ROW
// ============================================================================

function summarizeError(msg: string): string {
  if (msg.includes('Rate limit')) return 'Rate limit';
  if (msg.includes('non-serverless')) return 'Model retired (needs dedicated)';
  if (msg.includes('no longer available')) return 'Model deprecated';
  if (msg.includes('temperature')) return 'Bad param (temperature)';
  if (msg.includes('service tier')) return 'No service tier';
  if (msg.includes('sequence item')) return 'Response format bug';
  if (msg.includes('401')) return 'Auth error';
  if (msg.includes('timeout') || msg.includes('Timeout')) return 'Timeout';
  // Truncate to first meaningful part
  const clean = msg.replace(/^\[.*?\]\s*/, '').slice(0, 60);
  return clean || 'Unknown';
}

function ModelRow({ model }: { model: ModelStatus }) {
  const dotClass =
    model.status === 'live'
      ? 'monitoring-dot--green'
      : model.status === 'error'
        ? 'monitoring-dot--red'
        : 'monitoring-dot--stale';

  return (
    <>
      <div className="monitoring-model-row" title={model.errorMessage ?? undefined}>
        <span className={`monitoring-dot ${dotClass}`} />
        <span className="monitoring-model-name">{shortModelName(model.name)}</span>
        <span className="monitoring-model-metric">
          {formatMetric(model.ttft_ms, 'ms')}
        </span>
        <span className="monitoring-model-metric">
          {model.tps !== null ? Math.round(model.tps) : '—'}
        </span>
        <span className="monitoring-model-age">{timeAgo(model.lastBenchmark)}</span>
      </div>
      {model.status === 'error' && model.errorMessage && (
        <div className="monitoring-model-error">
          {summarizeError(model.errorMessage)}
        </div>
      )}
    </>
  );
}

// ============================================================================
// ERROR LOG
// ============================================================================

function ErrorLog({ errors }: { errors: RunError[] }) {
  const [open, setOpen] = useState(false);

  if (errors.length === 0) return null;

  return (
    <div className="monitoring-errors">
      <div className="monitoring-errors-header" onClick={() => setOpen(!open)}>
        <span className="monitoring-errors-title">Error Log (24h)</span>
        <div className="flex items-center gap-3">
          <span className="monitoring-errors-badge">{errors.length}</span>
          <ChevronDown
            size={14}
            className={`monitoring-chevron ${open ? 'monitoring-chevron--open' : ''}`}
          />
        </div>
      </div>
      {open && (
        <div className="monitoring-error-list">
          {errors.slice(0, 50).map((err) => (
            <ErrorRow key={err.id} error={err} />
          ))}
        </div>
      )}
    </div>
  );
}

function ErrorRow({ error }: { error: RunError }) {
  const typeClass = ['RATE_LIMIT', 'AUTH_ERROR', 'TIMEOUT', 'UNKNOWN_ERROR'].includes(
    error.error_type,
  )
    ? `monitoring-error-type--${error.error_type}`
    : 'monitoring-error-type--default';

  return (
    <div className="monitoring-error-row">
      <span className="monitoring-error-time">{formatTime(error.timestamp)}</span>
      <span className="monitoring-error-source">
        {error.provider}/{shortModelName(error.model ?? '')}
      </span>
      <span className="monitoring-error-message" title={error.error_message}>
        {error.error_message}
      </span>
      <span className={`monitoring-error-type ${typeClass}`}>
        {error.error_type}
        {error.status_code ? ` ${error.status_code}` : ''}
      </span>
    </div>
  );
}

// ============================================================================
// MAIN DASHBOARD
// ============================================================================

export function MonitoringDashboard() {
  const { data, isLoading, error, dataUpdatedAt } = useMonitoringData();
  const [expandedProvider, setExpandedProvider] = useState<string | null>(null);

  const lastRefresh = useMemo(() => {
    if (!dataUpdatedAt) return '—';
    return new Date(dataUpdatedAt).toLocaleTimeString('en-GB', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  }, [dataUpdatedAt]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <span className="text-white/40 text-sm">Loading monitoring data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-20">
        <span className="text-red-400 text-sm">
          Failed to load monitoring data: {error.message}
        </span>
      </div>
    );
  }

  if (!data) return null;

  const queueTotal = data.queue.pending + data.queue.processing;

  return (
    <div>
      {/* Header */}
      <div className="monitoring-header">
        <div className="monitoring-header-left">
          <h1 className="monitoring-header-title">System Status</h1>
          <span className="monitoring-auto-badge">AUTO 30s</span>
        </div>
        <span className="monitoring-header-refresh">
          Last refresh: {lastRefresh}
        </span>
      </div>

      {/* Summary bar */}
      <div className="monitoring-summary">
        <StatCard
          value={data.totalModels}
          label="Total Models"
          color="var(--text)"
        />
        <StatCard
          value={data.liveModels}
          label="Live"
          color="#22c55e"
        />
        <StatCard
          value={data.errorModels}
          label="Errors"
          color={data.errorModels > 0 ? '#ef4444' : 'var(--text-3)'}
        />
        <StatCard
          value={queueTotal > 0 ? queueTotal : '—'}
          label="Queue"
          color={queueTotal > 0 ? '#f59e0b' : 'var(--text-3)'}
        />
      </div>

      {/* Provider grid */}
      <div className="monitoring-grid">
        {data.providers.map((p) => (
          <ProviderCard
            key={p.key}
            provider={p}
            expanded={expandedProvider === p.key}
            onToggle={() =>
              setExpandedProvider(expandedProvider === p.key ? null : p.key)
            }
          />
        ))}
      </div>

      {/* Error log */}
      <ErrorLog errors={data.errors} />
    </div>
  );
}
