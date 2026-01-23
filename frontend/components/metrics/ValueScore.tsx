/**
 * ValueScore Component
 * 
 * Displays the Value Score metric (TPS / Cost Per Million)
 * Higher is better - represents "bang for buck"
 * 
 * Features:
 * - Big number display with formatting (e.g., "2,500")
 * - Gradient background
 * - Count-up animation (optional)
 * - Null-safe (shows LockedState when null)
 * - Responsive sizing
 */

'use client';

import { useMemo } from 'react';
import { TrendingUp, DollarSign } from 'lucide-react';
import { cn, formatNumber, formatCompactNumber } from '@/lib/utils';
import { LockedState } from '@/components/ui/LockedState';

export interface ValueScoreProps {
  /** Value score (integer) - null for locked state */
  value: number | null;
  /** Provider name */
  provider?: string;
  /** Show compact notation (e.g., "2.5K" instead of "2,500") */
  compact?: boolean;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Show trend indicator */
  showTrend?: boolean;
  /** Custom className */
  className?: string;
}

export function ValueScore({
  value,
  provider,
  compact = false,
  size = 'md',
  showTrend = true,
  className,
}: ValueScoreProps) {
  // If value is null, show locked state
  if (value === null) {
    return (
      <div className={cn('card', className)}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-acid-text">
            Value Score
          </h3>
          <DollarSign className="text-acid-success" size={20} />
        </div>
        <LockedState 
          size="sm" 
          message="Upgrade to see value scores"
        />
      </div>
    );
  }
  
  // Format the number
  const formattedValue = useMemo(() => {
    if (compact) {
      return formatCompactNumber(value);
    }
    return formatNumber(value);
  }, [value, compact]);
  
  // Size variants
  const textSizes = {
    sm: 'text-3xl',
    md: 'text-4xl md:text-5xl',
    lg: 'text-5xl md:text-6xl',
  };
  
  const subtextSizes = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };
  
  // Color based on value (higher is better)
  const getColorClass = (score: number) => {
    if (score >= 1000) return 'text-acid-success';
    if (score >= 100) return 'text-acid-warning';
    return 'text-acid-danger';
  };
  
  const colorClass = getColorClass(value);
  
  return (
    <div className={cn('card relative overflow-hidden', className)}>
      {/* Background Gradient */}
      <div 
        className="absolute inset-0 opacity-10 pointer-events-none"
        style={{
          background: value >= 1000 
            ? 'linear-gradient(135deg, #10B981 0%, #3B82F6 100%)'
            : value >= 100
            ? 'linear-gradient(135deg, #F59E0B 0%, #EF4444 100%)'
            : 'linear-gradient(135deg, #EF4444 0%, #991B1B 100%)',
        }}
      />
      
      {/* Header */}
      <div className="relative flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-acid-text">
            Value Score
          </h3>
          {provider && (
            <p className="text-sm text-acid-text-muted capitalize">
              {provider}
            </p>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          <DollarSign className={cn('transition-colors', colorClass)} size={24} />
          {showTrend && (
            <TrendingUp className={cn('transition-colors', colorClass)} size={20} />
          )}
        </div>
      </div>
      
      {/* Main Value */}
      <div className="relative">
        <div className={cn(
          'font-bold font-mono tracking-tight',
          'transition-colors duration-300',
          textSizes[size],
          colorClass
        )}>
          {formattedValue}
        </div>
        
        {/* Subtitle */}
        <p className={cn(
          'text-acid-text-muted mt-2',
          subtextSizes[size]
        )}>
          Tokens/sec per dollar
        </p>
      </div>
      
      {/* Info Footer */}
      <div className="relative mt-4 pt-4 border-t border-acid-border">
        <p className="text-xs text-acid-text-muted">
          {value >= 1000 ? (
            <span className="flex items-center gap-1">
              <span className="inline-block w-2 h-2 rounded-full bg-acid-success" />
              Excellent value
            </span>
          ) : value >= 100 ? (
            <span className="flex items-center gap-1">
              <span className="inline-block w-2 h-2 rounded-full bg-acid-warning" />
              Good value
            </span>
          ) : (
            <span className="flex items-center gap-1">
              <span className="inline-block w-2 h-2 rounded-full bg-acid-danger" />
              Low value
            </span>
          )}
        </p>
      </div>
    </div>
  );
}

/**
 * ValueScoreCompact - Inline/compact version
 * 
 * Usage:
 * ```tsx
 * <ValueScoreCompact value={2500} />
 * ```
 */
export interface ValueScoreCompactProps {
  value: number | null;
  showLabel?: boolean;
  className?: string;
}

export function ValueScoreCompact({
  value,
  showLabel = true,
  className,
}: ValueScoreCompactProps) {
  if (value === null) {
    return (
      <div className={cn('inline-flex items-center gap-2', className)}>
        {showLabel && (
          <span className="text-sm text-acid-text-muted">Value:</span>
        )}
        <span className="text-sm text-acid-text-muted">—</span>
      </div>
    );
  }
  
  const colorClass = value >= 1000 
    ? 'text-acid-success' 
    : value >= 100 
    ? 'text-acid-warning' 
    : 'text-acid-danger';
  
  return (
    <div className={cn('inline-flex items-center gap-2', className)}>
      {showLabel && (
        <span className="text-sm text-acid-text-muted">Value:</span>
      )}
      <span className={cn('text-lg font-bold font-mono', colorClass)}>
        {formatCompactNumber(value)}
      </span>
    </div>
  );
}

