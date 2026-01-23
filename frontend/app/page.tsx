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
    isFetching,
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
      {/* Header - Ultra Professional & Mobile Responsive */}
      <header className="relative border-b border-acid-border/30 bg-gradient-to-br from-acid-surface via-acid-bg to-acid-surface backdrop-blur-2xl sticky top-0 z-50 shadow-2xl">
        {/* Animated gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-r from-acid-primary/5 via-transparent to-acid-accent/5 opacity-50"></div>
        
        <div className="relative container mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
          {/* Mobile Layout */}
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
            {/* Left: Branding */}
            <div className="flex items-center gap-3 sm:gap-5">
              {/* Logo with animation */}
              <div className="relative group flex-shrink-0">
                <div className="absolute inset-0 bg-gradient-to-br from-acid-primary to-acid-accent rounded-xl sm:rounded-2xl blur-md opacity-50 group-hover:opacity-75 transition-opacity"></div>
                <div className="relative w-10 h-10 sm:w-12 sm:h-12 lg:w-14 lg:h-14 rounded-xl sm:rounded-2xl bg-gradient-to-br from-acid-primary via-acid-accent to-purple-500 flex items-center justify-center shadow-2xl transform group-hover:scale-105 transition-transform">
                  <Zap className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7 text-white drop-shadow-lg" />
                </div>
              </div>
              
              {/* Title & Stats */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
                  <h1 className="text-xl sm:text-2xl lg:text-3xl font-black bg-gradient-to-r from-acid-primary via-acid-accent to-purple-400 bg-clip-text text-transparent tracking-tight truncate">
                    AI Benchmark Dashboard
                  </h1>
                  <div className="px-2 sm:px-3 py-0.5 sm:py-1 rounded-full bg-acid-primary/10 border border-acid-primary/20 backdrop-blur-sm flex-shrink-0">
                    <span className="text-[10px] sm:text-xs font-bold text-acid-primary">v2.0</span>
                  </div>
                </div>
                <div className="flex items-center gap-2 sm:gap-4 mt-1 flex-wrap">
                  <p className="text-xs sm:text-sm text-acid-text-muted flex items-center gap-1.5 sm:gap-2">
                    <span className="relative flex h-2 w-2 sm:h-2.5 sm:w-2.5">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-full w-full bg-green-400"></span>
                    </span>
                    <span className="hidden sm:inline">Live Metrics</span>
                    <span className="sm:hidden">Live</span>
                  </p>
                  <div className="h-3 sm:h-4 w-px bg-acid-border/50"></div>
                  <p className="text-[10px] sm:text-xs text-acid-text-muted font-medium">
                    {filteredMetrics.length} Providers • {totalSamples.toLocaleString()} Samples
                  </p>
                </div>
              </div>
            </div>
            
            {/* Right: Controls */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4">
              {/* Quick Stats Pills - Mobile: Full width, Desktop: Auto */}
              <div className="flex items-center gap-2 sm:w-auto">
                <div className="px-3 py-2 rounded-xl bg-acid-surface/50 border border-acid-border/30 backdrop-blur-sm flex-1 sm:flex-none">
                  <div className="flex items-center justify-center sm:justify-start gap-2">
                    <Zap className="w-4 h-4 text-acid-accent flex-shrink-0" />
                    <span className="text-xs font-semibold text-acid-text">{avgTTFT.toFixed(0)}ms</span>
                  </div>
                </div>
              </div>
              
              {/* Time Range Selector - Mobile: Full width, Desktop: Auto */}
              <div className="relative flex items-center gap-1 bg-acid-bg/60 rounded-xl p-1 sm:p-1.5 border border-acid-border/40 shadow-inner backdrop-blur-sm flex-1 sm:flex-none">
                {(['1h', '24h', '7d', '30d'] as const).map((range) => (
                  <button
                    key={range}
                    onClick={() => setTimeRange(range)}
                    disabled={isFetching && timeRange === range}
                    className={`relative flex-1 sm:flex-none px-3 sm:px-4 lg:px-5 py-1.5 sm:py-2 rounded-lg text-xs sm:text-sm font-bold transition-all duration-300 touch-manipulation ${
                      timeRange === range
                        ? 'bg-gradient-to-r from-acid-primary to-acid-accent text-white shadow-lg shadow-acid-primary/30 scale-105'
                        : 'text-acid-text-muted hover:text-acid-text hover:bg-acid-surface/60 active:bg-acid-surface/80'
                    } ${isFetching && timeRange === range ? 'opacity-75' : ''}`}
                  >
                    {timeRange === range && (
                      <>
                        <div className="absolute inset-0 bg-gradient-to-r from-acid-primary to-acid-accent rounded-lg blur-sm opacity-50"></div>
                        {/* Subtle loading indicator */}
                        {isFetching && !isRefetching && (
                          <div className="absolute top-1 right-1 w-1.5 h-1.5 bg-white/80 rounded-full animate-pulse"></div>
                        )}
                      </>
                    )}
                    <span className="relative">{range}</span>
                  </button>
                ))}
              </div>
              
              {/* Refresh Button - Mobile: Full width, Desktop: Auto */}
              <button
                onClick={() => refetch()}
                disabled={isRefetching}
                className="group relative px-4 sm:px-6 py-2 sm:py-2.5 rounded-xl bg-gradient-to-r from-acid-surface to-acid-surface/80 border border-acid-border/40 text-acid-text font-semibold hover:border-acid-accent/50 active:border-acid-accent transition-all duration-300 shadow-lg hover:shadow-xl flex items-center justify-center gap-2 sm:gap-2.5 disabled:opacity-50 disabled:cursor-not-allowed overflow-hidden touch-manipulation w-full sm:w-auto"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-acid-accent/0 via-acid-accent/5 to-acid-accent/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
                {isRefetching ? (
                  <span className="relative inline-block animate-spin text-acid-accent text-base sm:text-lg">⟳</span>
                ) : (
                  <span className="relative text-base sm:text-lg">🔄</span>
                )}
                <span className="relative text-sm sm:text-base">Refresh</span>
              </button>
            </div>
          </div>
        </div>
      </header>
      
      {/* Main Content */}
      <main className="container mx-auto px-3 sm:px-4 lg:px-6 py-6 sm:py-8 lg:py-10">
        {/* Stats Cards - Enhanced Professional Layout */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5 lg:gap-6 mb-6 sm:mb-8 lg:mb-10">
          {/* Fastest Provider */}
          <div className="card group relative overflow-hidden">
            {/* Accent border on hover */}
            <div className="absolute inset-0 border-2 border-transparent group-hover:border-green-500/30 rounded-2xl transition-all duration-500 pointer-events-none"></div>
            
            <div className="relative">
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-acid-border/20">
                <span className="text-[10px] sm:text-xs font-bold text-acid-text-muted uppercase tracking-wider">Fastest</span>
                <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-green-500/20 to-emerald-500/20 border border-green-500/30 flex items-center justify-center group-hover:scale-110 group-hover:border-green-500/50 transition-all duration-300 shadow-lg shadow-green-500/10">
                  <Zap className="text-green-400" size={16} />
                </div>
              </div>
              {topSpeed ? (
                <div className="space-y-2">
                  <div className="text-2xl sm:text-3xl lg:text-4xl font-black bg-gradient-to-r from-green-400 via-emerald-400 to-green-300 bg-clip-text text-transparent capitalize mb-2 truncate">
                    {topSpeed.provider}
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-xs sm:text-sm font-semibold text-acid-text-muted">TTFT:</span>
                    <span className="text-base sm:text-lg font-bold text-green-400">{Math.round(topSpeed.avgTTFT)}ms</span>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-acid-text-muted py-4">No data available</div>
              )}
            </div>
          </div>
          
          {/* Most Stable */}
          <div className="card group relative overflow-hidden">
            {/* Accent border on hover */}
            <div className="absolute inset-0 border-2 border-transparent group-hover:border-green-500/30 rounded-2xl transition-all duration-500 pointer-events-none"></div>
            
            <div className="relative">
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-acid-border/20">
                <span className="text-[10px] sm:text-xs font-bold text-acid-text-muted uppercase tracking-wider">Most Stable</span>
                <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-green-500/20 to-emerald-500/20 border border-green-500/30 flex items-center justify-center group-hover:scale-110 group-hover:border-green-500/50 transition-all duration-300 shadow-lg shadow-green-500/10">
                  <Activity className="text-green-400" size={16} />
                </div>
              </div>
              {mostStable ? (
                <div className="space-y-2">
                  <div className="text-2xl sm:text-3xl lg:text-4xl font-black bg-gradient-to-r from-green-400 via-emerald-400 to-green-300 bg-clip-text text-transparent capitalize mb-2 truncate">
                    {mostStable.provider}
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-xs sm:text-sm font-semibold text-acid-text-muted">Jitter:</span>
                    <span className="text-base sm:text-lg font-bold text-green-400">{mostStable.jitter.toFixed(1)}ms</span>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-acid-text-muted py-4">No data available</div>
              )}
            </div>
          </div>
          
          {/* Best Value */}
          <div className="card group relative overflow-hidden sm:col-span-2 lg:col-span-1">
            {/* Accent border on hover */}
            <div className="absolute inset-0 border-2 border-transparent group-hover:border-green-500/30 rounded-2xl transition-all duration-500 pointer-events-none"></div>
            
            <div className="relative">
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-acid-border/20">
                <span className="text-[10px] sm:text-xs font-bold text-acid-text-muted uppercase tracking-wider">Best Value</span>
                <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-green-500/20 to-emerald-500/20 border border-green-500/30 flex items-center justify-center group-hover:scale-110 group-hover:border-green-500/50 transition-all duration-300 shadow-lg shadow-green-500/10">
                  <DollarSign className="text-green-400" size={16} />
                </div>
              </div>
              {topValue ? (
                <div className="space-y-2">
                  <div className="text-2xl sm:text-3xl lg:text-4xl font-black bg-gradient-to-r from-green-400 via-emerald-400 to-green-300 bg-clip-text text-transparent capitalize mb-2 truncate">
                    {topValue.provider}
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-xs sm:text-sm font-semibold text-acid-text-muted">Score:</span>
                    <span className="text-base sm:text-lg font-bold text-green-400">{topValue.valueScore.toLocaleString()}</span>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-acid-text-muted py-4">No data available</div>
              )}
            </div>
          </div>
        </div>
        
        {/* Main Grid - Mobile: Stacked, Desktop: 3 columns */}
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr_320px] xl:grid-cols-[300px_1fr_350px] gap-5 sm:gap-6 lg:gap-7">
          {/* Sidebar - Filters - Mobile: Top, Desktop: Left */}
          <div className="space-y-5 sm:space-y-6 lg:space-y-7 order-2 lg:order-1">
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
            <div className="card group relative overflow-hidden">
              <div className="card-header">
                <h3 className="card-title">
                  <span className="text-lg sm:text-xl">📊</span>
                  <span>Data Info</span>
                </h3>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center py-2.5 px-3 rounded-xl bg-gradient-to-r from-acid-bg/40 via-acid-surface/20 to-acid-bg/40 border border-acid-border/20 group-hover:border-acid-primary/30 group-hover:bg-acid-surface/30 transition-all duration-300">
                  <span className="text-xs sm:text-sm font-medium text-acid-text-muted">Providers:</span>
                  <span className="text-base sm:text-lg font-bold bg-gradient-to-r from-acid-primary to-acid-accent bg-clip-text text-transparent">
                    {filteredMetrics.length}
                  </span>
                </div>
                <div className="flex justify-between items-center py-2.5 px-3 rounded-xl bg-gradient-to-r from-acid-bg/40 via-acid-surface/20 to-acid-bg/40 border border-acid-border/20 group-hover:border-acid-primary/30 group-hover:bg-acid-surface/30 transition-all duration-300">
                  <span className="text-xs sm:text-sm font-medium text-acid-text-muted">Time Range:</span>
                  <span className="text-base sm:text-lg font-bold bg-gradient-to-r from-acid-primary to-acid-accent bg-clip-text text-transparent">
                    Last {timeRange}
                  </span>
                </div>
                <div className="flex justify-between items-center py-2.5 px-3 rounded-xl bg-gradient-to-r from-acid-bg/40 via-acid-surface/20 to-acid-bg/40 border border-acid-border/20 group-hover:border-acid-primary/30 group-hover:bg-acid-surface/30 transition-all duration-300">
                  <span className="text-xs sm:text-sm font-medium text-acid-text-muted">Last Updated:</span>
                  <span className="text-base sm:text-lg font-bold bg-gradient-to-r from-acid-primary to-acid-accent bg-clip-text text-transparent">
                    {new Date().toLocaleTimeString()}
                  </span>
                </div>
              </div>
            </div>
            
            {/* Insights - Left Sidebar */}
            <div className="card h-[200px] sm:h-[280px] flex flex-col group relative overflow-hidden">
              <div className="card-header flex-shrink-0">
                <h3 className="card-title">
                  <span className="text-lg sm:text-xl">💡</span>
                  <span>Insights</span>
                </h3>
              </div>
              
              <div className="space-y-2.5 text-xs sm:text-sm flex-grow overflow-y-auto custom-scrollbar pr-1">
                {/* Always show top performers */}
                {topSpeed && (
                  <div className="p-2.5 sm:p-3 rounded-xl bg-gradient-to-r from-blue-500/10 via-blue-500/5 to-transparent border border-blue-500/20 hover:border-blue-500/30 hover:bg-blue-500/15 transition-all duration-300">
                    <span className="text-blue-400 font-medium">⚡ Fastest: {topSpeed.providerDisplayName} ({Math.round(topSpeed.avgTTFT)}ms TTFT)</span>
                  </div>
                )}
                
                {mostStable && (
                  <div className="p-2.5 sm:p-3 rounded-xl bg-gradient-to-r from-blue-500/10 via-blue-500/5 to-transparent border border-blue-500/20 hover:border-blue-500/30 hover:bg-blue-500/15 transition-all duration-300">
                    <span className="text-blue-400 font-medium">✓ Most Stable: {mostStable.providerDisplayName} ({mostStable.jitter.toFixed(1)}ms jitter)</span>
                  </div>
                )}
                
                {topValue && (
                  <div className="p-2.5 sm:p-3 rounded-xl bg-gradient-to-r from-blue-500/10 via-blue-500/5 to-transparent border border-blue-500/20 hover:border-blue-500/30 hover:bg-blue-500/15 transition-all duration-300">
                    <span className="text-blue-400 font-medium">💰 Best Value: {topValue.providerDisplayName} (Score: {topValue.valueScore.toLocaleString()})</span>
                  </div>
                )}
                
                {/* Performance insights */}
                {topSpeed && topSpeed.avgTTFT < 200 && (
                  <div className="p-2.5 sm:p-3 rounded-xl bg-gradient-to-r from-green-500/10 via-green-500/5 to-transparent border border-green-500/20 hover:border-green-500/30 hover:bg-green-500/15 transition-all duration-300">
                    <span className="text-green-400 font-medium">🚀 {topSpeed.providerDisplayName} has ultra-fast response times!</span>
                  </div>
                )}
                
                {topSpeed && topSpeed.avgTTFT >= 200 && topSpeed.avgTTFT < 500 && (
                  <div className="p-2.5 sm:p-3 rounded-xl bg-gradient-to-r from-green-500/10 via-green-500/5 to-transparent border border-green-500/20 hover:border-green-500/30 hover:bg-green-500/15 transition-all duration-300">
                    <span className="text-green-400 font-medium">⚡ {topSpeed.providerDisplayName} shows good response times</span>
                  </div>
                )}
                
                {mostStable && mostStable.jitter < 100 && (
                  <div className="p-2.5 sm:p-3 rounded-xl bg-gradient-to-r from-green-500/10 via-green-500/5 to-transparent border border-green-500/20 hover:border-green-500/30 hover:bg-green-500/15 transition-all duration-300">
                    <span className="text-green-400 font-medium">✓ {mostStable.providerDisplayName} is highly stable</span>
                  </div>
                )}
                
                {topValue && topValue.valueScore > 1000 && (
                  <div className="p-2.5 sm:p-3 rounded-xl bg-gradient-to-r from-green-500/10 via-green-500/5 to-transparent border border-green-500/20 hover:border-green-500/30 hover:bg-green-500/15 transition-all duration-300">
                    <span className="text-green-400 font-medium">💰 {topValue.providerDisplayName} offers excellent value</span>
                  </div>
                )}
                
                {topValue && topValue.valueScore > 100 && topValue.valueScore <= 1000 && (
                  <div className="p-2.5 sm:p-3 rounded-xl bg-gradient-to-r from-blue-500/10 via-blue-500/5 to-transparent border border-blue-500/20 hover:border-blue-500/30 hover:bg-blue-500/15 transition-all duration-300">
                    <span className="text-blue-400 font-medium">💵 {topValue.providerDisplayName} provides good value</span>
                  </div>
                )}
                
                {/* Warnings */}
                {avgTTFT > 1000 && (
                  <div className="p-2.5 sm:p-3 rounded-xl bg-gradient-to-r from-yellow-500/10 via-yellow-500/5 to-transparent border border-yellow-500/20 hover:border-yellow-500/30 hover:bg-yellow-500/15 transition-all duration-300">
                    <span className="text-yellow-400 font-medium">⚠️ Average response time is high across providers</span>
                  </div>
                )}
                
                {filteredMetrics.length === 1 && (
                  <div className="p-2.5 sm:p-3 rounded-xl bg-gradient-to-r from-purple-500/10 via-purple-500/5 to-transparent border border-purple-500/20 hover:border-purple-500/30 hover:bg-purple-500/15 transition-all duration-300">
                    <span className="text-purple-400 font-medium">📊 Showing data for 1 provider</span>
                  </div>
                )}
              </div>
            </div>
          </div>
          
          {/* Main Charts - Mobile: Full width, Desktop: Center column */}
          <div className="space-y-5 sm:space-y-6 lg:space-y-7 order-1 lg:order-2">
            {/* Speed Chart */}
            <SpeedChart
              data={filteredMetrics}
              height={300}
              sortOrder="asc"
            />
            
            {/* Provider Cards Grid - Mobile: 2 cols, Tablet: 3 cols, Desktop: 4-5 cols */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-3 sm:gap-4">
              {filteredMetrics.map((metric) => (
                <div key={metric.provider} className="card group relative overflow-hidden p-3 sm:p-4 hover:border-acid-accent/50 active:scale-[0.98] transition-all duration-300 touch-manipulation">
                  {/* Hover accent border */}
                  <div className="absolute inset-0 border-2 border-transparent group-hover:border-acid-accent/20 rounded-2xl transition-all duration-500 pointer-events-none"></div>
                  
                  <div className="relative space-y-3">
                    {/* Header */}
                    <div className="flex items-center justify-between pb-2 border-b border-acid-border/20">
                      <h3 className="text-xs sm:text-sm font-bold text-acid-text capitalize truncate flex-1">
                        {metric.provider}
                      </h3>
                    </div>
                    
                    {/* Stability Badge */}
                    <div>
                      <StabilityBadge jitter={metric.jitter} />
                    </div>
                    
                    {/* Metrics */}
                    <div className="space-y-2 pt-1">
                      <div className="flex justify-between items-center py-1.5 px-2 rounded-lg bg-acid-bg/30 border border-acid-border/10 group-hover:bg-acid-surface/40 group-hover:border-acid-border/30 transition-all duration-300">
                        <span className="text-[10px] sm:text-xs font-medium text-acid-text-muted">TTFT</span>
                        <span className="text-xs sm:text-sm font-bold text-acid-text">
                          {Math.round(metric.avgTTFT)}ms
                        </span>
                      </div>
                      
                      <div className="flex justify-between items-center py-1.5 px-2 rounded-lg bg-acid-bg/30 border border-acid-border/10 group-hover:bg-acid-surface/40 group-hover:border-acid-border/30 transition-all duration-300">
                        <span className="text-[10px] sm:text-xs font-medium text-acid-text-muted">Value</span>
                        <span className="text-xs sm:text-sm font-bold text-acid-accent">
                          {metric.valueScore.toLocaleString()}
                        </span>
                      </div>
                      
                      <div className="text-center pt-1">
                        <div className="text-[10px] sm:text-xs text-acid-text-muted font-medium">
                          {metric.sampleSize} samples
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Stats Panel - Right Sidebar - Mobile: Bottom, Desktop: Right */}
          <div className="space-y-4 sm:space-y-6 order-3">
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
      <footer className="border-t border-acid-border bg-acid-surface/50 mt-8 sm:mt-12 lg:mt-16">
        <div className="container mx-auto px-4 sm:px-6 py-4 sm:py-6">
          <div className="text-center text-xs sm:text-sm text-acid-text-muted">
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

