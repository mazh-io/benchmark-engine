/**
 * Dashboard Home Page
 * 
 * Main dashboard displaying real-time AI provider benchmarks.
 * 
 * Features:
 * - Speed Chart (TTFT)
 * - Stability Indicators
 * - Value Scores
 * - Provider Filter
 * - Auto-refresh data
 * - SSR optimized (< 1s load time)
 */

'use client';

import { useState, useMemo } from 'react';
import { Activity, Zap, DollarSign, Filter as FilterIcon } from 'lucide-react';
import { SpeedChart } from '@/components/charts/SpeedChart';
import { StabilityIndicator, StabilityBadge } from '@/components/metrics/StabilityIndicator';
import { ValueScore, ValueScoreCompact } from '@/components/metrics/ValueScore';
import { ProviderFilter, ProviderFilterCompact } from '@/components/filters/ProviderFilter';
import { StatsPanel } from '@/components/dashboard/StatsPanel';
import { useBenchmarkData } from '@/hooks/useBenchmarkData';
import { PROVIDER_CATEGORIES } from '@/lib/types';
import type { ProviderCategory } from '@/lib/types';

export default function DashboardPage() {
  // Filter state
  const [providerFilter, setProviderFilter] = useState<ProviderCategory | 'all'>('all');
  const [timeRange, setTimeRange] = useState<'1h' | '24h' | '7d' | '30d'>('24h');
  
  // Fetch data with React Query
  const {
    data,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useBenchmarkData({
    timeRange,
    autoRefresh: true,
  });
  
  // Filter data by provider category
  const filteredMetrics = useMemo(() => {
    if (!data?.metrics) return [];
    
    // Convert Map to Array
    const metricsArray = Array.from(data.metrics.values());
    
    if (providerFilter === 'all') {
      return metricsArray;
    }
    
    return metricsArray.filter(metric => {
      const category = PROVIDER_CATEGORIES[metric.provider];
      return category === providerFilter;
    });
  }, [data?.metrics, providerFilter]);
  
  // Get top performers
  const topSpeed = useMemo(() => {
    if (!filteredMetrics.length) return null;
    return [...filteredMetrics].sort((a, b) => a.avgTTFT - b.avgTTFT)[0];
  }, [filteredMetrics]);
  
  const topValue = useMemo(() => {
    if (!filteredMetrics.length) return null;
    return [...filteredMetrics].sort((a, b) => b.valueScore - a.valueScore)[0];
  }, [filteredMetrics]);
  
  const mostStable = useMemo(() => {
    if (!filteredMetrics.length) return null;
    return [...filteredMetrics].sort((a, b) => a.jitter - b.jitter)[0];
  }, [filteredMetrics]);
  
  // Calculate aggregate stats for StatsPanel
  const totalSamples = useMemo(() => {
    return filteredMetrics.reduce((sum, m) => sum + m.sampleSize, 0);
  }, [filteredMetrics]);
  
  const avgTTFT = useMemo(() => {
    if (!filteredMetrics.length) return 0;
    const total = filteredMetrics.reduce((sum, m) => sum + m.avgTTFT, 0);
    return total / filteredMetrics.length;
  }, [filteredMetrics]);
  
  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-acid-bg flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-acid-primary border-t-transparent" />
          <p className="mt-4 text-acid-text-muted">Loading benchmarks...</p>
        </div>
      </div>
    );
  }
  
  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-acid-bg flex items-center justify-center">
        <div className="card max-w-md text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-acid-text mb-2">
            Failed to Load Data
          </h2>
          <p className="text-acid-text-muted mb-4">
            {error instanceof Error ? error.message : 'An error occurred'}
          </p>
          <button
            onClick={() => refetch()}
            className="btn btn-primary"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-acid-bg">
      {/* Header - Ultra Professional */}
      <header className="relative border-b border-acid-border/30 bg-gradient-to-br from-acid-surface via-acid-bg to-acid-surface backdrop-blur-2xl sticky top-0 z-50 shadow-2xl">
        {/* Animated gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-r from-acid-primary/5 via-transparent to-acid-accent/5 opacity-50"></div>
        
        <div className="relative container mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            {/* Left: Branding */}
            <div className="flex items-center gap-5">
              {/* Logo with animation */}
              <div className="relative group">
                <div className="absolute inset-0 bg-gradient-to-br from-acid-primary to-acid-accent rounded-2xl blur-md opacity-50 group-hover:opacity-75 transition-opacity"></div>
                <div className="relative w-14 h-14 rounded-2xl bg-gradient-to-br from-acid-primary via-acid-accent to-purple-500 flex items-center justify-center shadow-2xl transform group-hover:scale-105 transition-transform">
                  <Zap className="w-7 h-7 text-white drop-shadow-lg" />
                </div>
              </div>
              
              {/* Title & Stats */}
              <div>
                <div className="flex items-center gap-3">
                  <h1 className="text-3xl font-black bg-gradient-to-r from-acid-primary via-acid-accent to-purple-400 bg-clip-text text-transparent tracking-tight">
                    AI Benchmark Dashboard
                  </h1>
                  <div className="px-3 py-1 rounded-full bg-acid-primary/10 border border-acid-primary/20 backdrop-blur-sm">
                    <span className="text-xs font-bold text-acid-primary">v2.0</span>
                  </div>
                </div>
                <div className="flex items-center gap-4 mt-1.5">
                  <p className="text-sm text-acid-text-muted flex items-center gap-2">
                    <span className="relative flex h-2.5 w-2.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-400"></span>
                    </span>
                    Live Metrics
                  </p>
                  <div className="h-4 w-px bg-acid-border/50"></div>
                  <p className="text-xs text-acid-text-muted font-medium">
                    {filteredMetrics.length} Providers • {totalSamples.toLocaleString()} Samples
                  </p>
                </div>
              </div>
            </div>
            
            {/* Right: Controls */}
            <div className="flex items-center gap-4">
              {/* Quick Stats Pills */}
              <div className="flex items-center gap-2">
                <div className="px-3 py-2 rounded-xl bg-acid-surface/50 border border-acid-border/30 backdrop-blur-sm">
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4 text-acid-accent" />
                    <span className="text-xs font-semibold text-acid-text">{avgTTFT.toFixed(0)}ms</span>
                  </div>
                </div>
              </div>
              
              {/* Time Range Selector */}
              <div className="flex items-center gap-1 bg-acid-bg/60 rounded-xl p-1.5 border border-acid-border/40 shadow-inner backdrop-blur-sm">
                {(['1h', '24h', '7d', '30d'] as const).map((range) => (
                  <button
                    key={range}
                    onClick={() => setTimeRange(range)}
                    className={`relative px-5 py-2 rounded-lg text-sm font-bold transition-all duration-300 ${
                      timeRange === range
                        ? 'bg-gradient-to-r from-acid-primary to-acid-accent text-white shadow-lg shadow-acid-primary/30 scale-105'
                        : 'text-acid-text-muted hover:text-acid-text hover:bg-acid-surface/60'
                    }`}
                  >
                    {timeRange === range && (
                      <div className="absolute inset-0 bg-gradient-to-r from-acid-primary to-acid-accent rounded-lg blur-sm opacity-50"></div>
                    )}
                    <span className="relative">{range}</span>
                  </button>
                ))}
              </div>
              
              {/* Refresh Button */}
              <button
                onClick={() => refetch()}
                disabled={isRefetching}
                className="group relative px-6 py-2.5 rounded-xl bg-gradient-to-r from-acid-surface to-acid-surface/80 border border-acid-border/40 text-acid-text font-semibold hover:border-acid-accent/50 transition-all duration-300 shadow-lg hover:shadow-xl flex items-center gap-2.5 disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-acid-accent/0 via-acid-accent/5 to-acid-accent/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
                {isRefetching ? (
                  <span className="relative inline-block animate-spin text-acid-accent">⟳</span>
                ) : (
                  <span className="relative text-lg">🔄</span>
                )}
                <span className="relative">Refresh</span>
              </button>
            </div>
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Fastest Provider */}
          <div className="card group hover:border-acid-primary/50">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-acid-text-muted uppercase tracking-wide">Fastest</span>
              <div className="w-8 h-8 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center justify-center group-hover:bg-green-500/20 transition-colors">
                <Zap className="text-green-400" size={16} />
              </div>
            </div>
            {topSpeed ? (
              <>
                <div className="text-3xl font-black bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent capitalize mb-1">
                  {topSpeed.provider}
                </div>
                <div className="text-sm font-semibold text-acid-text-muted">
                  {Math.round(topSpeed.avgTTFT)}ms TTFT
                </div>
              </>
            ) : (
              <div className="text-acid-text-muted">No data</div>
            )}
          </div>
          
          {/* Most Stable */}
          <div className="card group hover:border-acid-primary/50">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-acid-text-muted uppercase tracking-wide">Most Stable</span>
              <div className="w-8 h-8 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center justify-center group-hover:bg-green-500/20 transition-colors">
                <Activity className="text-green-400" size={16} />
              </div>
            </div>
            {mostStable ? (
              <>
                <div className="text-3xl font-black bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent capitalize mb-1">
                  {mostStable.provider}
                </div>
                <div className="text-sm font-semibold text-acid-text-muted">
                  {mostStable.jitter.toFixed(1)}ms jitter
                </div>
              </>
            ) : (
              <div className="text-acid-text-muted">No data</div>
            )}
          </div>
          
          {/* Best Value */}
          <div className="card group hover:border-acid-primary/50">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-acid-text-muted uppercase tracking-wide">Best Value</span>
              <div className="w-8 h-8 rounded-lg bg-green-500/10 border border-green-500/20 flex items-center justify-center group-hover:bg-green-500/20 transition-colors">
                <DollarSign className="text-green-400" size={16} />
              </div>
            </div>
            {topValue ? (
              <>
                <div className="text-3xl font-black bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent capitalize mb-1">
                  {topValue.provider}
                </div>
                <div className="text-sm font-semibold text-acid-text-muted">
                  Score: {topValue.valueScore.toLocaleString()}
                </div>
              </>
            ) : (
              <div className="text-acid-text-muted">No data</div>
            )}
          </div>
        </div>
        
        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr_350px] gap-6">
          {/* Sidebar - Filters */}
          <div className="space-y-6">
            <ProviderFilter
              value={providerFilter}
              onChange={setProviderFilter}
              showCounts
              counts={{
                all: data?.metrics?.size || 0,
                direct: Array.from(data?.metrics?.values() || []).filter(m => PROVIDER_CATEGORIES[m.provider] === 'direct').length || 0,
                proxy: Array.from(data?.metrics?.values() || []).filter(m => PROVIDER_CATEGORIES[m.provider] === 'proxy').length || 0,
              }}
            />
            
            {/* Data Info */}
            <div className="card group hover:border-acid-primary/50">
              <h3 className="text-lg font-bold text-acid-text mb-4 flex items-center gap-2">
                <span className="text-xl">📊</span>
                <span>Data Info</span>
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center py-1.5 px-2 rounded-lg bg-acid-bg/30 group-hover:bg-acid-bg/50 transition-colors">
                  <span className="text-sm text-acid-text-muted">Providers:</span>
                  <span className="text-lg font-bold bg-gradient-to-r from-acid-primary to-acid-accent bg-clip-text text-transparent">
                    {filteredMetrics.length}
                  </span>
                </div>
                <div className="flex justify-between items-center py-1.5 px-2 rounded-lg bg-acid-bg/30 group-hover:bg-acid-bg/50 transition-colors">
                  <span className="text-sm text-acid-text-muted">Time Range:</span>
                  <span className="text-lg font-bold bg-gradient-to-r from-acid-primary to-acid-accent bg-clip-text text-transparent">
                    Last {timeRange}
                  </span>
                </div>
                <div className="flex justify-between items-center py-1.5 px-2 rounded-lg bg-acid-bg/30 group-hover:bg-acid-bg/50 transition-colors">
                  <span className="text-sm text-acid-text-muted">Last Updated:</span>
                  <span className="text-lg font-bold bg-gradient-to-r from-acid-primary to-acid-accent bg-clip-text text-transparent">
                    {new Date().toLocaleTimeString()}
                  </span>
                </div>
              </div>
            </div>
            
            {/* Insights - Left Sidebar */}
            <div className="card h-[255px] flex flex-col group hover:border-acid-primary/50">
              <h3 className="text-lg font-bold text-acid-text mb-4 flex items-center gap-2">
                <span className="text-xl">💡</span>
                <span>Insights</span>
              </h3>
              
              <div className="space-y-2 text-sm flex-grow overflow-y-auto custom-scrollbar">
                {/* Always show top performers */}
                {topSpeed && (
                  <div className="p-2 rounded bg-blue-500/10 border border-blue-500/20">
                    <span className="text-blue-400">⚡ Fastest: {topSpeed.providerDisplayName} ({Math.round(topSpeed.avgTTFT)}ms TTFT)</span>
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
                
                {filteredMetrics.length === 1 && (
                  <div className="p-2 rounded bg-purple-500/10 border border-purple-500/20">
                    <span className="text-purple-400">📊 Showing data for 1 provider</span>
                  </div>
                )}
              </div>
            </div>
          </div>
          
          {/* Main Charts */}
          <div className="space-y-6">
            {/* Speed Chart */}
            <SpeedChart
              data={filteredMetrics}
              height={400}
              sortOrder="asc"
            />
            
            {/* Provider Cards Grid - 5 columns as per sketch */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
              {filteredMetrics.map((metric) => (
                <div key={metric.provider} className="card p-4 hover:border-acid-accent/50 hover:shadow-[0_10px_30px_rgba(139,92,246,0.2)] transition-all duration-300 group">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-semibold text-acid-text capitalize truncate">
                      {metric.provider}
                    </h3>
                  </div>
                  
                  <StabilityBadge jitter={metric.jitter} />
                  
                  <div className="mt-2 space-y-1.5">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-acid-text-muted">TTFT:</span>
                      <span className="font-bold text-acid-text">
                        {Math.round(metric.avgTTFT)}ms
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-acid-text-muted">Value:</span>
                      <span className="font-bold text-acid-accent">
                        {metric.valueScore.toLocaleString()}
                      </span>
                    </div>
                    
                    <div className="text-xs text-acid-text-muted text-center pt-1">
                      {metric.sampleSize} samples
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Stats Panel - Right Sidebar */}
          <div className="space-y-6">
            <StatsPanel
              topSpeed={topSpeed}
              topValue={topValue}
              mostStable={mostStable}
              totalProviders={filteredMetrics.length}
              totalSamples={totalSamples}
              avgTTFT={avgTTFT}
            />
          </div>
        </div>
      </main>
      
      {/* Footer */}
      <footer className="border-t border-acid-border bg-acid-surface/50 mt-16">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center text-sm text-acid-text-muted">
            <p>AI Benchmark Engine · Real-time Performance Metrics</p>
            <p className="mt-1">
              Auto-refreshes every 60 seconds
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

