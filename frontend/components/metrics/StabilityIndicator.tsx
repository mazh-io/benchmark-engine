/**
 * StabilityIndicator Component
 * 
 * Displays jitter (standard deviation of latency) as a traffic light indicator.
 * Lower jitter = more stable = green light
 * 
 * Features:
 * - Traffic light colors (🟢 Green / 🟡 Yellow / 🔴 Red)
 * - Smooth glow effects
 * - Tooltip with jitter value
 * - Null-safe rendering (shows locked state)
 * - Animated transitions
 */

'use client';

import { useMemo } from 'react';
import { Activity, Lock } from 'lucide-react';
import { cn } from '@/lib/utils';
import { getJitterColor, JITTER_THRESHOLDS } from '@/lib/calculations';
import { LockedState } from '@/components/ui/LockedState';

export interface StabilityIndicatorProps {
  /** Jitter value in milliseconds - null for locked state */
  jitter: number | null;
  /** Provider name */
  provider?: string;
  /** Show numeric value alongside indicator */
  showValue?: boolean;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Custom className */
  className?: string;
}

export function StabilityIndicator({
  jitter,
  provider,
  showValue = true,
  size = 'md',
  className,
}: StabilityIndicatorProps) {
  // If jitter is null, show locked state
  if (jitter === null) {
    return (
      <div className={cn('card', className)}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-acid-text">
            Stability
          </h3>
          <Activity className="text-acid-primary" size={20} />
        </div>
        <LockedState 
          size="sm" 
          message="Upgrade to see stability metrics"
        />
      </div>
    );
  }
  
  // Get color based on jitter thresholds
  const color = useMemo(() => getJitterColor(jitter), [jitter]);
  
  // Color mappings
  const colorClasses = {
    green: {
      bg: 'bg-acid-success',
      text: 'text-acid-success',
      glow: 'shadow-[0_0_30px_rgba(16,185,129,0.6)]',
      ring: 'ring-acid-success/30',
    },
    yellow: {
      bg: 'bg-acid-warning',
      text: 'text-acid-warning',
      glow: 'shadow-[0_0_30px_rgba(245,158,11,0.6)]',
      ring: 'ring-acid-warning/30',
    },
    red: {
      bg: 'bg-acid-danger',
      text: 'text-acid-danger',
      glow: 'shadow-[0_0_30px_rgba(239,68,68,0.6)]',
      ring: 'ring-acid-danger/30',
    },
  };
  
  const currentColor = colorClasses[color];
  
  // Size variants
  const circleSizes = {
    sm: 'w-12 h-12',
    md: 'w-16 h-16',
    lg: 'w-24 h-24',
  };
  
  const textSizes = {
    sm: 'text-xl',
    md: 'text-2xl',
    lg: 'text-3xl',
  };
  
  // Status text
  const getStatusText = (jitterColor: 'green' | 'yellow' | 'red') => {
    switch (jitterColor) {
      case 'green':
        return 'Excellent stability';
      case 'yellow':
        return 'Moderate stability';
      case 'red':
        return 'Poor stability';
    }
  };
  
  return (
    <div className={cn('card', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-acid-text">
            Stability
          </h3>
          {provider && (
            <p className="text-sm text-acid-text-muted capitalize">
              {provider}
            </p>
          )}
        </div>
        <Activity className="text-acid-primary" size={20} />
      </div>
      
      {/* Traffic Light Indicator */}
      <div className="flex items-center justify-center py-6">
        <div className="relative">
          {/* Outer glow ring */}
          <div 
            className={cn(
              'absolute inset-0 rounded-full animate-pulse-glow',
              'ring-4',
              currentColor.ring
            )}
          />
          
          {/* Main circle with glow */}
          <div 
            className={cn(
              'relative rounded-full transition-all duration-500',
              'flex items-center justify-center',
              circleSizes[size],
              currentColor.bg,
              currentColor.glow
            )}
          >
            {/* Inner pulse */}
            <div className="w-1/2 h-1/2 bg-white/30 rounded-full animate-pulse" />
          </div>
        </div>
      </div>
      
      {/* Jitter Value */}
      {showValue && (
        <div className="text-center mb-4">
          <div className={cn(
            'font-bold font-mono',
            textSizes[size],
            currentColor.text
          )}>
            {jitter.toFixed(1)} ms
          </div>
          <p className="text-sm text-acid-text-muted mt-1">
            Jitter (Std Dev)
          </p>
        </div>
      )}
      
      {/* Status Footer */}
      <div className="pt-4 border-t border-acid-border">
        <div className="flex items-center justify-between">
          <p className={cn('text-sm font-medium', currentColor.text)}>
            {getStatusText(color)}
          </p>
          
          {/* Threshold info */}
          <div className="text-xs text-acid-text-muted">
            <span className="opacity-70">
              {color === 'green' && `< ${JITTER_THRESHOLDS.GREEN}ms`}
              {color === 'yellow' && `${JITTER_THRESHOLDS.GREEN}-${JITTER_THRESHOLDS.YELLOW}ms`}
              {color === 'red' && `> ${JITTER_THRESHOLDS.YELLOW}ms`}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * StabilityBadge - Compact badge version
 * 
 * Usage:
 * ```tsx
 * <StabilityBadge jitter={150} />
 * ```
 */
export interface StabilityBadgeProps {
  jitter: number | null;
  showLabel?: boolean;
  className?: string;
}

export function StabilityBadge({
  jitter,
  showLabel = true,
  className,
}: StabilityBadgeProps) {
  if (jitter === null) {
    return (
      <div className={cn('inline-flex items-center gap-1', className)}>
        <Lock size={12} className="text-acid-text-muted" />
        <span className="text-xs text-acid-text-muted">Locked</span>
      </div>
    );
  }
  
  const color = getJitterColor(jitter);
  
  const colorClasses = {
    green: 'bg-acid-success/20 text-acid-success ring-acid-success/50',
    yellow: 'bg-acid-warning/20 text-acid-warning ring-acid-warning/50',
    red: 'bg-acid-danger/20 text-acid-danger ring-acid-danger/50',
  };
  
  return (
    <div className={cn(
      'inline-flex items-center gap-2 px-2 py-1 rounded-full ring-1',
      colorClasses[color],
      className
    )}>
      {/* Colored dot */}
      <div className={cn(
        'w-2 h-2 rounded-full',
        color === 'green' && 'bg-acid-success',
        color === 'yellow' && 'bg-acid-warning',
        color === 'red' && 'bg-acid-danger'
      )} />
      
      {showLabel && (
        <span className="text-xs font-medium">
          {jitter.toFixed(0)}ms
        </span>
      )}
    </div>
  );
}

/**
 * StabilityList - Shows all three states
 * Useful for legend or documentation
 */
export function StabilityLegend({ className }: { className?: string }) {
  return (
    <div className={cn('flex flex-col gap-2', className)}>
      <div className="flex items-center gap-3">
        <div className="w-4 h-4 rounded-full bg-acid-success glow-success" />
        <span className="text-sm text-acid-text">
          Stable (&lt; {JITTER_THRESHOLDS.GREEN}ms)
        </span>
      </div>
      <div className="flex items-center gap-3">
        <div className="w-4 h-4 rounded-full bg-acid-warning glow-warning" />
        <span className="text-sm text-acid-text">
          Moderate ({JITTER_THRESHOLDS.GREEN}-{JITTER_THRESHOLDS.YELLOW}ms)
        </span>
      </div>
      <div className="flex items-center gap-3">
        <div className="w-4 h-4 rounded-full bg-acid-danger glow-danger" />
        <span className="text-sm text-acid-text">
          Unstable (&gt; {JITTER_THRESHOLDS.YELLOW}ms)
        </span>
      </div>
    </div>
  );
}

