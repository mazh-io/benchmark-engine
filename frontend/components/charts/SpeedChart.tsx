/**
 * SpeedChart Component
 * 
 * Bar chart displaying Time to First Token (TTFT) by provider.
 * Lower is better - faster response time.
 * 
 * Features:
 * - Recharts bar chart
 * - Dark theme with neon accents
 * - Animated bars on load
 * - Custom tooltips
 * - Responsive design
 * - Sort by value
 */

'use client';

import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
} from 'recharts';
import { Zap, TrendingDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ProviderMetrics } from '@/lib/types';

export interface SpeedChartProps {
  /** Provider metrics data */
  data: ProviderMetrics[];
  /** Chart height in pixels */
  height?: number;
  /** Show legend */
  showLegend?: boolean;
  /** Sort order */
  sortOrder?: 'asc' | 'desc' | 'none';
  /** Custom className */
  className?: string;
}

export function SpeedChart({
  data,
  height = 400,
  showLegend = true,
  sortOrder = 'asc',
  className,
}: SpeedChartProps) {
  // Sort data
  const sortedData = useMemo(() => {
    if (sortOrder === 'none') return data;
    
    return [...data].sort((a, b) => {
      if (sortOrder === 'asc') {
        return a.avgTTFT - b.avgTTFT; // Ascending (fastest first)
      }
      return b.avgTTFT - a.avgTTFT; // Descending (slowest first)
    });
  }, [data, sortOrder]);
  
  // Transform data for Recharts
  const chartData = useMemo(() => {
    return sortedData.map((metric) => ({
      name: metric.provider.charAt(0).toUpperCase() + metric.provider.slice(1),
      ttft: Math.round(metric.avgTTFT),
      sampleSize: metric.sampleSize,
    }));
  }, [sortedData]);
  
  // Get color for bar based on value (lower is better)
  const getBarColor = (ttft: number) => {
    if (ttft < 500) return '#10B981'; // Green - Fast
    if (ttft < 1000) return '#F59E0B'; // Yellow - Medium
    return '#EF4444'; // Red - Slow
  };
  
  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload[0]) return null;
    
    const data = payload[0].payload;
    
    return (
      <div className="custom-tooltip">
        <p className="label">{data.name}</p>
        <div className="space-y-1 mt-2">
          <p className="flex items-center justify-between gap-4">
            <span className="text-acid-text-muted">TTFT:</span>
            <span className="font-bold text-acid-text">{data.ttft} ms</span>
          </p>
          <p className="flex items-center justify-between gap-4">
            <span className="text-acid-text-muted">Samples:</span>
            <span className="text-acid-text">{data.sampleSize}</span>
          </p>
        </div>
        <div className="mt-2 pt-2 border-t border-acid-border">
          <p className="text-xs text-acid-text-muted">
            {data.ttft < 500 ? '🟢 Fast' : data.ttft < 1000 ? '🟡 Medium' : '🔴 Slow'}
          </p>
        </div>
      </div>
    );
  };
  
  // If no data
  if (!chartData || chartData.length === 0) {
    return (
      <div className={cn('card', className)}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-acid-text">
            Speed (TTFT)
          </h3>
          <Zap className="text-acid-warning" size={20} />
        </div>
        <div className="flex items-center justify-center h-64 text-acid-text-muted">
          No data available
        </div>
      </div>
    );
  }
  
  return (
    <div className={cn('card p-4 sm:p-6', className)}>
      {/* Header - Mobile Responsive */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4 mb-4 sm:mb-6">
        <div className="flex-1 min-w-0">
          <h3 className="text-base sm:text-lg font-semibold text-acid-text flex items-center gap-2">
            <Zap className="text-acid-warning w-4 h-4 sm:w-5 sm:h-5" />
            <span className="truncate">Speed (Time to First Token)</span>
          </h3>
          <p className="text-xs sm:text-sm text-acid-text-muted mt-1">
            Lower is better · Measured in milliseconds
          </p>
        </div>
        
        <div className="flex items-center gap-2 text-acid-success flex-shrink-0">
          <TrendingDown size={14} className="sm:w-4 sm:h-4" />
          <span className="text-[10px] sm:text-xs font-medium whitespace-nowrap">
            Fastest: {Math.min(...chartData.map(d => d.ttft))}ms
          </span>
        </div>
      </div>
      
      {/* Chart - Mobile Responsive */}
      <div style={{ width: '100%', height, minHeight: '250px' }} className="overflow-x-auto">
        <ResponsiveContainer width="100%" height="100%" minHeight={250}>
          <BarChart
            data={chartData}
            margin={{ 
              top: 10, 
              right: 5, 
              left: -10, 
              bottom: chartData.length > 5 ? 60 : 40 
            }}
          >
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke="#2D3748" 
              vertical={false}
            />
            
            <XAxis
              dataKey="name"
              stroke="#94A3B8"
              fontSize={10}
              angle={chartData.length > 5 ? -45 : 0}
              textAnchor={chartData.length > 5 ? "end" : "middle"}
              height={chartData.length > 5 ? 70 : 40}
              tick={{ fill: '#94A3B8', fontSize: 10 }}
              interval={0}
            />
            
            <YAxis
              stroke="#94A3B8"
              fontSize={10}
              tick={{ fill: '#94A3B8', fontSize: 10 }}
              width={40}
              label={{
                value: 'TTFT (ms)',
                angle: -90,
                position: 'insideLeft',
                style: { fill: '#94A3B8', fontSize: 10 },
              }}
            />
            
            <Tooltip content={<CustomTooltip />} cursor={{ fill: '#252B37' }} />
            
            {showLegend && (
              <Legend
                wrapperStyle={{ paddingTop: '10px', fontSize: '10px' }}
                iconType="circle"
                formatter={() => 'Time to First Token'}
              />
            )}
            
            <Bar
              dataKey="ttft"
              radius={[6, 6, 0, 0]}
              animationDuration={1000}
              animationEasing="ease-out"
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={getBarColor(entry.ttft)}
                  className="hover:opacity-80 transition-opacity"
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      
      {/* Footer Legend - Mobile Responsive */}
      <div className="mt-3 sm:mt-4 pt-3 sm:pt-4 border-t border-acid-border">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-center gap-2 sm:gap-4 lg:gap-6 text-[10px] sm:text-xs">
          <div className="flex items-center gap-1.5 sm:gap-2">
            <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded bg-acid-success flex-shrink-0" />
            <span className="text-acid-text-muted whitespace-nowrap">&lt; 500ms (Fast)</span>
          </div>
          <div className="flex items-center gap-1.5 sm:gap-2">
            <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded bg-acid-warning flex-shrink-0" />
            <span className="text-acid-text-muted whitespace-nowrap">500-1000ms (Medium)</span>
          </div>
          <div className="flex items-center gap-1.5 sm:gap-2">
            <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded bg-acid-danger flex-shrink-0" />
            <span className="text-acid-text-muted whitespace-nowrap">&gt; 1000ms (Slow)</span>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * SpeedChartCompact - Smaller version without card wrapper
 */
export interface SpeedChartCompactProps {
  data: ProviderMetrics[];
  height?: number;
  className?: string;
}

export function SpeedChartCompact({
  data,
  height = 200,
  className,
}: SpeedChartCompactProps) {
  const chartData = useMemo(() => {
    return data
      .sort((a, b) => a.avgTTFT - b.avgTTFT)
      .slice(0, 5) // Top 5 fastest
      .map((metric) => ({
        name: metric.provider.substring(0, 8), // Truncate name
        ttft: Math.round(metric.avgTTFT),
      }));
  }, [data]);
  
  return (
    <div className={cn('w-full', className)} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 5, right: 5, left: 0, bottom: 20 }}>
          <XAxis
            dataKey="name"
            stroke="#94A3B8"
            fontSize={10}
            angle={-45}
            textAnchor="end"
            height={40}
          />
          <YAxis hide />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1A1F29',
              border: '1px solid #2D3748',
              borderRadius: '8px',
              fontSize: '12px',
            }}
          />
          <Bar dataKey="ttft" fill="#10B981" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

