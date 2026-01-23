/**
 * LockedState Component
 * 
 * Displays a placeholder for locked/premium features.
 * Used when metrics are gated behind freemium paywall.
 * 
 * Features:
 * - Blur effect
 * - Lock icon
 * - Upgrade CTA
 * - Customizable message
 */

import { Lock } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface LockedStateProps {
  /** Custom message to display (optional) */
  message?: string;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Show upgrade button */
  showUpgradeButton?: boolean;
  /** Custom className */
  className?: string;
}

export function LockedState({
  message = 'Upgrade to Pro to unlock this metric',
  size = 'md',
  showUpgradeButton = true,
  className,
}: LockedStateProps) {
  // Size variants
  const sizeClasses = {
    sm: 'h-24',
    md: 'h-32',
    lg: 'h-48',
  };
  
  const iconSizes = {
    sm: 24,
    md: 32,
    lg: 48,
  };
  
  const textSizes = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
  };
  
  return (
    <div
      className={cn(
        'relative flex flex-col items-center justify-center',
        'bg-acid-surface/50 rounded-lg border-2 border-dashed border-acid-border',
        'backdrop-blur-sm',
        sizeClasses[size],
        className
      )}
    >
      {/* Lock Icon with Glow */}
      <div className="relative mb-2">
        <div className="absolute inset-0 bg-acid-accent/20 blur-xl rounded-full" />
        <Lock 
          className="relative text-acid-accent" 
          size={iconSizes[size]} 
        />
      </div>
      
      {/* Message */}
      <p className={cn(
        'text-acid-text-muted text-center px-4 mb-3',
        textSizes[size]
      )}>
        {message}
      </p>
      
      {/* Upgrade Button */}
      {showUpgradeButton && (
        <button
          onClick={() => {
            // TODO: Implement upgrade flow
            console.log('Upgrade clicked');
          }}
          className={cn(
            'px-4 py-1.5 rounded-md font-medium',
            'bg-gradient-to-r from-acid-primary to-acid-accent',
            'text-white text-sm',
            'hover:shadow-lg hover:shadow-acid-primary/50',
            'transition-all duration-200',
            'focus:outline-none focus:ring-2 focus:ring-acid-primary focus:ring-offset-2 focus:ring-offset-acid-bg'
          )}
        >
          Upgrade to Pro
        </button>
      )}
      
      {/* Animated Border Glow */}
      <div 
        className="absolute inset-0 rounded-lg opacity-50 animate-pulse-glow pointer-events-none"
        style={{
          background: 'linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.1), transparent)',
        }}
      />
    </div>
  );
}

/**
 * LockedStateCard - Wrapper for card-style locked content
 * 
 * Usage:
 * ```tsx
 * <LockedStateCard title="Value Score">
 *   <LockedState message="Upgrade to see value score" />
 * </LockedStateCard>
 * ```
 */
export interface LockedStateCardProps {
  title: string;
  children?: React.ReactNode;
  className?: string;
}

export function LockedStateCard({ 
  title, 
  children, 
  className 
}: LockedStateCardProps) {
  return (
    <div className={cn('card', className)}>
      <h3 className="text-lg font-semibold mb-4 text-acid-text">
        {title}
      </h3>
      {children || <LockedState />}
    </div>
  );
}

/**
 * LockedStateInline - Inline locked indicator
 * 
 * Usage:
 * ```tsx
 * <div>
 *   Value Score: <LockedStateInline />
 * </div>
 * ```
 */
export function LockedStateInline() {
  return (
    <span className="inline-flex items-center gap-1 text-acid-text-muted">
      <Lock size={14} className="text-acid-accent" />
      <span className="text-sm">Locked</span>
    </span>
  );
}

