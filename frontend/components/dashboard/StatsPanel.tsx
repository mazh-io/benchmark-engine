/**
 * Stats Panel Component
 * 
 * Professional stats sidebar showing:
 * - Top 3 Performers
 * - Quick Stats
 * - Performance Insights
 */

'use client';

import { Trophy, TrendingUp, Activity, DollarSign, Zap } from 'lucide-react';
import type { ProviderMetrics } from '@/lib/types';

interface StatsPanelProps {
  topSpeed: ProviderMetrics | null;
  topValue: ProviderMetrics | null;
  mostStable: ProviderMetrics | null;
  totalProviders: number;
  totalSamples: number;
  avgTTFT: number;
}

export function StatsPanel({
  topSpeed,
  topValue,
  mostStable,
  totalProviders,
  totalSamples,
  avgTTFT,
}: StatsPanelProps) {
  return (
    <div className="space-y-6">
      {/* Top Performers */}
      <div className="card group hover:border-acid-primary/50">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 rounded-lg bg-acid-accent/10 border border-acid-accent/20 flex items-center justify-center group-hover:bg-acid-accent/20 transition-colors">
            <Trophy className="w-5 h-5 text-acid-accent" />
          </div>
          <h3 className="text-lg font-bold text-acid-text">Top Performers</h3>
        </div>
        
        <div className="space-y-3">
          {/* Fastest */}
          {topSpeed && (
            <div className="p-3 rounded-xl bg-gradient-to-br from-acid-bg/50 to-acid-surface/30 border border-acid-border/40 hover:border-green-500/40 hover:bg-green-500/5 transition-all duration-300">
              <div className="flex items-center gap-2 mb-1.5">
                <Zap className="w-4 h-4 text-green-400" />
                <span className="text-xs text-acid-text-muted uppercase tracking-wide font-semibold">Fastest</span>
              </div>
              <div className="text-lg font-bold bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">{topSpeed.providerDisplayName}</div>
              <div className="text-sm text-acid-accent font-semibold">{topSpeed.avgTTFT.toFixed(0)}ms TTFT</div>
            </div>
          )}
          
          {/* Most Stable */}
          {mostStable && (
            <div className="p-3 rounded-xl bg-gradient-to-br from-acid-bg/50 to-acid-surface/30 border border-acid-border/40 hover:border-green-500/40 hover:bg-green-500/5 transition-all duration-300">
              <div className="flex items-center gap-2 mb-1.5">
                <Activity className="w-4 h-4 text-green-400" />
                <span className="text-xs text-acid-text-muted uppercase tracking-wide font-semibold">Most Stable</span>
              </div>
              <div className="text-lg font-bold bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">{mostStable.providerDisplayName}</div>
              <div className="text-sm text-acid-accent font-semibold">{mostStable.jitter.toFixed(1)}ms jitter</div>
            </div>
          )}
          
          {/* Best Value */}
          {topValue && (
            <div className="p-3 rounded-xl bg-gradient-to-br from-acid-bg/50 to-acid-surface/30 border border-acid-border/40 hover:border-green-500/40 hover:bg-green-500/5 transition-all duration-300">
              <div className="flex items-center gap-2 mb-1.5">
                <DollarSign className="w-4 h-4 text-green-400" />
                <span className="text-xs text-acid-text-muted uppercase tracking-wide font-semibold">Best Value</span>
              </div>
              <div className="text-lg font-bold bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">{topValue.providerDisplayName}</div>
              <div className="text-sm text-acid-accent font-semibold">Score: {topValue.valueScore.toLocaleString()}</div>
            </div>
          )}
        </div>
      </div>
      
      {/* Quick Stats */}
      <div className="card group hover:border-acid-primary/50">
        <h3 className="text-lg font-bold text-acid-text mb-4 flex items-center gap-2">
          <span className="text-xl">📈</span>
          <span>Quick Stats</span>
        </h3>
        
        <div className="space-y-3">
          <div className="flex justify-between items-center py-1.5 px-2 rounded-lg bg-acid-bg/30 group-hover:bg-acid-bg/50 transition-colors">
            <span className="text-sm text-acid-text-muted">Providers Tested:</span>
            <span className="text-lg font-bold bg-gradient-to-r from-acid-primary to-acid-accent bg-clip-text text-transparent">{totalProviders}</span>
          </div>
          
          <div className="flex justify-between items-center py-1.5 px-2 rounded-lg bg-acid-bg/30 group-hover:bg-acid-bg/50 transition-colors">
            <span className="text-sm text-acid-text-muted">Total Samples:</span>
            <span className="text-lg font-bold bg-gradient-to-r from-acid-primary to-acid-accent bg-clip-text text-transparent">{totalSamples.toLocaleString()}</span>
          </div>
          
          <div className="flex justify-between items-center py-1.5 px-2 rounded-lg bg-acid-bg/30 group-hover:bg-acid-bg/50 transition-colors">
            <span className="text-sm text-acid-text-muted">Avg TTFT:</span>
            <span className="text-lg font-bold bg-gradient-to-r from-acid-primary to-acid-accent bg-clip-text text-transparent">{avgTTFT.toFixed(0)}ms</span>
          </div>
        </div>
      </div>
      
      {/* Performance Insights */}
      <div className="card h-[255px] flex flex-col group hover:border-acid-primary/50">
        <h3 className="text-lg font-bold text-acid-text mb-4 flex items-center gap-2">
          <span className="text-xl">💡</span>
          <span>Insights</span>
        </h3>
        
        <div className="space-y-2 text-sm flex-grow overflow-y-auto custom-scrollbar">
          {/* Always show top performers */}
          {topSpeed && (
            <div className="p-2 rounded bg-blue-500/10 border border-blue-500/20">
              <span className="text-blue-400">⚡ Fastest: {topSpeed.providerDisplayName} ({topSpeed.avgTTFT.toFixed(0)}ms TTFT)</span>
            </div>
          )}
          
          {mostStable && (
            <div className="p-2 rounded bg-blue-500/10 border border-blue-500/20">
              <span className="text-blue-400">✓ Most Stable: {mostStable.providerDisplayName} ({mostStable.jitter.toFixed(1)}ms jitter)</span>
            </div>
          )}
          
          {topValue && (
            <div className="p-2 rounded bg-blue-500/10 border border-blue-500/20">
              <span className="text-blue-400">💰 Best Value: {topValue.providerDisplayName} (Score: {topValue.valueScore.toLocaleString()})</span>
            </div>
          )}
          
          {/* Performance insights */}
          {topSpeed && topSpeed.avgTTFT < 200 && (
            <div className="p-2 rounded bg-green-500/10 border border-green-500/20">
              <span className="text-green-400">🚀 {topSpeed.providerDisplayName} has ultra-fast response times!</span>
            </div>
          )}
          
          {topSpeed && topSpeed.avgTTFT >= 200 && topSpeed.avgTTFT < 500 && (
            <div className="p-2 rounded bg-green-500/10 border border-green-500/20">
              <span className="text-green-400">⚡ {topSpeed.providerDisplayName} shows good response times</span>
            </div>
          )}
          
          {mostStable && mostStable.jitter < 100 && (
            <div className="p-2 rounded bg-green-500/10 border border-green-500/20">
              <span className="text-green-400">✓ {mostStable.providerDisplayName} is highly stable</span>
            </div>
          )}
          
          {topValue && topValue.valueScore > 1000 && (
            <div className="p-2 rounded bg-green-500/10 border border-green-500/20">
              <span className="text-green-400">💰 {topValue.providerDisplayName} offers excellent value</span>
            </div>
          )}
          
          {topValue && topValue.valueScore > 100 && topValue.valueScore <= 1000 && (
            <div className="p-2 rounded bg-blue-500/10 border border-blue-500/20">
              <span className="text-blue-400">💵 {topValue.providerDisplayName} provides good value</span>
            </div>
          )}
          
          {/* Warnings */}
          {avgTTFT > 1000 && (
            <div className="p-2 rounded bg-yellow-500/10 border border-yellow-500/20">
              <span className="text-yellow-400">⚠️ Average response time is high across providers</span>
            </div>
          )}
        </div>
      </div>
      
    </div>
  );
}

