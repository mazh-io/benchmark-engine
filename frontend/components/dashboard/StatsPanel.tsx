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
    <div className="space-y-5 sm:space-y-6 lg:space-y-7">
      {/* Top Performers */}
      <div className="card group relative overflow-hidden">
        <div className="card-header">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-acid-accent/20 to-purple-500/20 border border-acid-accent/30 flex items-center justify-center group-hover:scale-110 group-hover:border-acid-accent/50 transition-all duration-300 shadow-lg shadow-acid-accent/10">
              <Trophy className="w-5 h-5 text-acid-accent" />
            </div>
            <h3 className="card-title">Top Performers</h3>
          </div>
        </div>
        
        <div className="space-y-3">
          {/* Fastest */}
          {topSpeed && (
            <div className="p-3 sm:p-3.5 rounded-xl bg-gradient-to-br from-acid-bg/50 via-acid-surface/30 to-acid-bg/50 border border-acid-border/30 hover:border-green-500/40 hover:bg-gradient-to-br hover:from-green-500/10 hover:via-green-500/5 hover:to-transparent transition-all duration-300 shadow-sm hover:shadow-md">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="w-4 h-4 text-green-400 flex-shrink-0" />
                <span className="text-[10px] sm:text-xs text-acid-text-muted uppercase tracking-wider font-bold">Fastest</span>
              </div>
              <div className="text-base sm:text-lg font-black bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent truncate mb-1">{topSpeed.providerDisplayName}</div>
              <div className="text-xs sm:text-sm text-acid-accent font-bold">{topSpeed.avgTTFT.toFixed(0)}ms TTFT</div>
            </div>
          )}
          
          {/* Most Stable */}
          {mostStable && (
            <div className="p-3 sm:p-3.5 rounded-xl bg-gradient-to-br from-acid-bg/50 via-acid-surface/30 to-acid-bg/50 border border-acid-border/30 hover:border-green-500/40 hover:bg-gradient-to-br hover:from-green-500/10 hover:via-green-500/5 hover:to-transparent transition-all duration-300 shadow-sm hover:shadow-md">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-4 h-4 text-green-400 flex-shrink-0" />
                <span className="text-[10px] sm:text-xs text-acid-text-muted uppercase tracking-wider font-bold">Most Stable</span>
              </div>
              <div className="text-base sm:text-lg font-black bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent truncate mb-1">{mostStable.providerDisplayName}</div>
              <div className="text-xs sm:text-sm text-acid-accent font-bold">{mostStable.jitter.toFixed(1)}ms jitter</div>
            </div>
          )}
          
          {/* Best Value */}
          {topValue && (
            <div className="p-3 sm:p-3.5 rounded-xl bg-gradient-to-br from-acid-bg/50 via-acid-surface/30 to-acid-bg/50 border border-acid-border/30 hover:border-green-500/40 hover:bg-gradient-to-br hover:from-green-500/10 hover:via-green-500/5 hover:to-transparent transition-all duration-300 shadow-sm hover:shadow-md">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="w-4 h-4 text-green-400 flex-shrink-0" />
                <span className="text-[10px] sm:text-xs text-acid-text-muted uppercase tracking-wider font-bold">Best Value</span>
              </div>
              <div className="text-base sm:text-lg font-black bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent truncate mb-1">{topValue.providerDisplayName}</div>
              <div className="text-xs sm:text-sm text-acid-accent font-bold">Score: {topValue.valueScore.toLocaleString()}</div>
            </div>
          )}
        </div>
      </div>
      
      {/* Quick Stats */}
      <div className="card group relative overflow-hidden">
        <div className="card-header">
          <h3 className="card-title">
            <span className="text-lg sm:text-xl">📈</span>
            <span>Quick Stats</span>
          </h3>
        </div>
        
        <div className="space-y-3">
          <div className="flex justify-between items-center py-2.5 px-3 rounded-xl bg-gradient-to-r from-acid-bg/40 via-acid-surface/20 to-acid-bg/40 border border-acid-border/20 group-hover:border-acid-primary/30 group-hover:bg-acid-surface/30 transition-all duration-300">
            <span className="text-xs sm:text-sm font-medium text-acid-text-muted">Providers Tested:</span>
            <span className="text-base sm:text-lg font-bold bg-gradient-to-r from-acid-primary to-acid-accent bg-clip-text text-transparent">{totalProviders}</span>
          </div>
          
          <div className="flex justify-between items-center py-2.5 px-3 rounded-xl bg-gradient-to-r from-acid-bg/40 via-acid-surface/20 to-acid-bg/40 border border-acid-border/20 group-hover:border-acid-primary/30 group-hover:bg-acid-surface/30 transition-all duration-300">
            <span className="text-xs sm:text-sm font-medium text-acid-text-muted">Total Samples:</span>
            <span className="text-base sm:text-lg font-bold bg-gradient-to-r from-acid-primary to-acid-accent bg-clip-text text-transparent">{totalSamples.toLocaleString()}</span>
          </div>
          
          <div className="flex justify-between items-center py-2.5 px-3 rounded-xl bg-gradient-to-r from-acid-bg/40 via-acid-surface/20 to-acid-bg/40 border border-acid-border/20 group-hover:border-acid-primary/30 group-hover:bg-acid-surface/30 transition-all duration-300">
            <span className="text-xs sm:text-sm font-medium text-acid-text-muted">Avg TTFT:</span>
            <span className="text-base sm:text-lg font-bold bg-gradient-to-r from-acid-primary to-acid-accent bg-clip-text text-transparent">{avgTTFT.toFixed(0)}ms</span>
          </div>
        </div>
      </div>
      
      {/* Performance Insights */}
      <div className="card h-[200px] sm:h-[280px] flex flex-col group relative overflow-hidden">
        <div className="card-header flex-shrink-0">
          <h3 className="card-title">
            <span className="text-lg sm:text-xl">💡</span>
            <span>Insights</span>
          </h3>
        </div>
        
        <div className="space-y-2 text-xs sm:text-sm flex-grow overflow-y-auto custom-scrollbar">
          {/* Always show top performers */}
          {topSpeed && (
            <div className="p-1.5 sm:p-2 rounded bg-blue-500/10 border border-blue-500/20">
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

