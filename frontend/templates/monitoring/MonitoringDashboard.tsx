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
  if (diff < 60_000) return `${Math.floor(diff / 1000)}s`;
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h`;
  return `${Math.floor(diff / 86_400_000)}d`;
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

function formatCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

function shortModelName(name: string): string {
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

function summarizeError(msg: string): string {
  if (msg.includes('Rate limit')) return 'Rate limit';
  if (msg.includes('non-serverless')) return 'Model retired';
  if (msg.includes('no longer available')) return 'Deprecated';
  if (msg.includes('temperature')) return 'Bad param';
  if (msg.includes('service tier')) return 'No tier';
  if (msg.includes('sequence item')) return 'Format bug';
  if (msg.includes('401')) return 'Auth error';
  if (msg.includes('timeout') || msg.includes('Timeout')) return 'Timeout';
  const clean = msg.replace(/^\[.*?\]\s*/, '').slice(0, 40);
  return clean || 'Unknown';
}

// ============================================================================
// PROVIDER CARD (compact)
// ============================================================================

function ProviderCard({
  provider,
  active,
  onToggle,
}: {
  provider: ProviderStatus;
  active: boolean;
  onToggle: () => void;
}) {
  const pct = provider.totalModels > 0
    ? Math.round((provider.liveModels / provider.totalModels) * 100)
    : 0;

  return (
    <div
      className={`monitoring-card monitoring-card--${provider.status} ${active ? 'monitoring-card--active' : ''}`}
      onClick={onToggle}
    >
      {/* Row 1: name + ratio */}
      <div className="monitoring-card-top">
        <div className="monitoring-card-left">
          <span className={`monitoring-dot monitoring-dot--${provider.status}`} />
          <span className="monitoring-card-name">{provider.displayName}</span>
        </div>
        <span className="monitoring-card-ratio">
          {provider.liveModels}/{provider.totalModels}
        </span>
      </div>

      {/* Progress bar */}
      <div className="monitoring-bar">
        <div
          className="monitoring-bar-fill"
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Row 2: meta */}
      <div className="monitoring-card-meta">
        <span>{timeAgo(provider.lastBenchmark)}</span>
        {provider.errorModels > 0 && (
          <span className="monitoring-card-err">
            {provider.errorModels} err
          </span>
        )}
        <span className="monitoring-card-dp">{formatCount(provider.datapoints)} dp</span>
      </div>

      {/* Expanded model table */}
      {active && (
        <div className="monitoring-detail" onClick={(e) => e.stopPropagation()}>
          <div className="monitoring-detail-head">
            <span />
            <span>Model</span>
            <span>TTFT</span>
            <span>TPS</span>
            <span>Age</span>
            <span>DP</span>
          </div>
          {provider.models.map((m) => (
            <ModelRow key={m.name} model={m} />
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// MODEL ROW
// ============================================================================

function ModelRow({ model }: { model: ModelStatus }) {
  const dotClass =
    model.status === 'live'
      ? 'monitoring-dot--green'
      : model.status === 'error'
        ? 'monitoring-dot--red'
        : 'monitoring-dot--stale';

  return (
    <>
      <div className="monitoring-detail-row" title={model.errorMessage ?? undefined}>
        <span className={`monitoring-dot ${dotClass}`} />
        <span className="monitoring-detail-name">{shortModelName(model.name)}</span>
        <span className="monitoring-detail-val">
          {formatMetric(model.ttft_ms, 'ms')}
        </span>
        <span className="monitoring-detail-val">
          {model.tps !== null ? Math.round(model.tps) : '—'}
        </span>
        <span className="monitoring-detail-dim">{timeAgo(model.lastBenchmark)}</span>
        <span className="monitoring-detail-dim">{model.datapoints}</span>
      </div>
      {model.status === 'error' && model.errorMessage && (
        <div className="monitoring-detail-err">
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
      <div className="monitoring-errors-toggle" onClick={() => setOpen(!open)}>
        <span className="monitoring-errors-title">
          Errors (1h) <span className="monitoring-errors-count">{errors.length}</span>
        </span>
        <ChevronDown
          size={14}
          className={`monitoring-chevron ${open ? 'monitoring-chevron--open' : ''}`}
        />
      </div>
      {open && (
        <div className="monitoring-errors-list">
          {errors.slice(0, 50).map((err) => (
            <div key={err.id} className="monitoring-errors-row">
              <span className="monitoring-errors-time">{formatTime(err.timestamp)}</span>
              <span className="monitoring-errors-src">
                {err.provider}/{shortModelName(err.model ?? '')}
              </span>
              <span className="monitoring-errors-msg" title={err.error_message}>
                {err.error_message}
              </span>
              <span className={`monitoring-errors-type monitoring-errors-type--${err.error_type}`}>
                {err.error_type}
                {err.status_code ? ` ${err.status_code}` : ''}
              </span>
            </div>
          ))}
        </div>
      )}
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
      {/* ── Header ── */}
      <div className="monitoring-header">
        <div>
          <div className="monitoring-header-top">
            <h1 className="monitoring-title">System Status</h1>
            <span className="monitoring-badge monitoring-badge--green">AUTO 30s</span>
          </div>
          <div className="monitoring-kpis">
            <span className="monitoring-kpi">{data.totalModels} models</span>
            <span className="monitoring-kpi monitoring-kpi--green">{data.liveModels} live</span>
            {data.errorModels > 0 && (
              <span className="monitoring-kpi monitoring-kpi--red">{data.errorModels} errors</span>
            )}
            {queueTotal > 0 && (
              <span className="monitoring-kpi monitoring-kpi--amber">{queueTotal} queued</span>
            )}
            <span className="monitoring-kpi monitoring-kpi--acid">
              {data.totalDatapoints.toLocaleString('en-US')} datapoints
            </span>
          </div>
        </div>
        <span className="monitoring-refresh">{lastRefresh}</span>
      </div>

      {/* ── Provider grid ── */}
      <div className="monitoring-grid">
        {data.providers.map((p) => (
          <ProviderCard
            key={p.key}
            provider={p}
            active={expandedProvider === p.key}
            onToggle={() =>
              setExpandedProvider(expandedProvider === p.key ? null : p.key)
            }
          />
        ))}
      </div>

      {/* ── Error log ── */}
      <ErrorLog errors={data.errors} />
    </div>
  );
}
