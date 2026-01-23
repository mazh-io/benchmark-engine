/**
 * ProviderFilter Component
 * 
 * Toggle filter for switching between Direct and Proxy providers.
 * - Direct: Native APIs (OpenAI, Anthropic, Google, etc.)
 * - Proxy: Aggregators (OpenRouter, Together, etc.)
 * 
 * Features:
 * - Modern pill-style toggle
 * - Smooth transitions
 * - Active state styling
 * - Keyboard accessible
 */

'use client';

import { useState } from 'react';
import { Server, Globe, Filter } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ProviderCategory } from '@/lib/types';

export interface ProviderFilterProps {
  /** Current selected category */
  value: ProviderCategory | 'all';
  /** Callback when filter changes */
  onChange: (category: ProviderCategory | 'all') => void;
  /** Show provider counts */
  showCounts?: boolean;
  /** Provider counts by category */
  counts?: {
    all: number;
    direct: number;
    proxy: number;
  };
  /** Custom className */
  className?: string;
}

export function ProviderFilter({
  value,
  onChange,
  showCounts = false,
  counts,
  className,
}: ProviderFilterProps) {
  const options = [
    {
      value: 'all' as const,
      label: 'All Providers',
      icon: Filter,
      description: 'Show all providers',
    },
    {
      value: 'direct' as const,
      label: 'Direct',
      icon: Server,
      description: 'Native API providers',
    },
    {
      value: 'proxy' as const,
      label: 'Proxy',
      icon: Globe,
      description: 'Aggregator services',
    },
  ];
  
  return (
    <div className={cn('card', className)}>
      {/* Header */}
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-acid-text flex items-center gap-2">
          <Filter size={18} />
          Provider Type
        </h3>
        <p className="text-sm text-acid-text-muted mt-1">
          Filter by API access method
        </p>
      </div>
      
      {/* Toggle Buttons */}
      <div className="flex flex-col gap-2">
        {options.map((option) => {
          const Icon = option.icon;
          const isActive = value === option.value;
          const count = counts?.[option.value];
          
          return (
            <button
              key={option.value}
              onClick={() => onChange(option.value)}
              className={cn(
                'flex items-center justify-between p-3 rounded-lg',
                'border transition-all duration-200',
                'focus:outline-none focus:ring-2 focus:ring-acid-primary focus:ring-offset-2 focus:ring-offset-acid-bg',
                isActive ? [
                  'bg-acid-primary/10 border-acid-primary text-acid-primary',
                  'shadow-lg shadow-acid-primary/20',
                ] : [
                  'bg-acid-surface border-acid-border text-acid-text',
                  'hover:bg-acid-surface-hover hover:border-acid-primary/50',
                ]
              )}
            >
              <div className="flex items-center gap-3">
                <Icon size={20} className={cn(
                  'transition-colors',
                  isActive ? 'text-acid-primary' : 'text-acid-text-muted'
                )} />
                
                <div className="text-left">
                  <div className={cn(
                    'font-medium',
                    isActive ? 'text-acid-primary' : 'text-acid-text'
                  )}>
                    {option.label}
                  </div>
                  <div className="text-xs text-acid-text-muted">
                    {option.description}
                  </div>
                </div>
              </div>
              
              {showCounts && count !== undefined && (
                <div className={cn(
                  'px-2 py-1 rounded-full text-xs font-medium',
                  isActive 
                    ? 'bg-acid-primary/20 text-acid-primary'
                    : 'bg-acid-surface-hover text-acid-text-muted'
                )}>
                  {count}
                </div>
              )}
            </button>
          );
        })}
      </div>
      
      {/* Info Footer */}
      <div className="mt-4 pt-4 border-t border-acid-border">
        <div className="flex items-start gap-2 text-xs text-acid-text-muted">
          <div className="mt-0.5">ℹ️</div>
          <div>
            <strong>Direct:</strong> Native APIs with direct access.{' '}
            <strong>Proxy:</strong> Aggregators that route to multiple providers.
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * ProviderFilterCompact - Horizontal pill toggle
 * 
 * Usage:
 * ```tsx
 * <ProviderFilterCompact value={filter} onChange={setFilter} />
 * ```
 */
export interface ProviderFilterCompactProps {
  value: ProviderCategory | 'all';
  onChange: (category: ProviderCategory | 'all') => void;
  className?: string;
}

export function ProviderFilterCompact({
  value,
  onChange,
  className,
}: ProviderFilterCompactProps) {
  const options = [
    { value: 'all' as const, label: 'All' },
    { value: 'direct' as const, label: 'Direct' },
    { value: 'proxy' as const, label: 'Proxy' },
  ];
  
  return (
    <div className={cn(
      'inline-flex items-center gap-1 p-1 bg-acid-surface rounded-lg border border-acid-border',
      className
    )}>
      {options.map((option) => {
        const isActive = value === option.value;
        
        return (
          <button
            key={option.value}
            onClick={() => onChange(option.value)}
            className={cn(
              'px-4 py-1.5 rounded-md text-sm font-medium',
              'transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-acid-primary focus:ring-offset-1 focus:ring-offset-acid-surface',
              isActive ? [
                'bg-acid-primary text-white',
                'shadow-md shadow-acid-primary/30',
              ] : [
                'text-acid-text-muted',
                'hover:text-acid-text hover:bg-acid-surface-hover',
              ]
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}

/**
 * ProviderFilterSegmented - iOS-style segmented control
 */
export function ProviderFilterSegmented({
  value,
  onChange,
  className,
}: ProviderFilterCompactProps) {
  const options = [
    { value: 'all' as const, label: 'All', icon: Filter },
    { value: 'direct' as const, label: 'Direct', icon: Server },
    { value: 'proxy' as const, label: 'Proxy', icon: Globe },
  ];
  
  return (
    <div className={cn(
      'inline-flex items-center bg-acid-surface rounded-lg p-1 border border-acid-border',
      className
    )}>
      {options.map((option, index) => {
        const Icon = option.icon;
        const isActive = value === option.value;
        
        return (
          <button
            key={option.value}
            onClick={() => onChange(option.value)}
            className={cn(
              'relative px-4 py-2 rounded-md text-sm font-medium',
              'transition-all duration-200',
              'focus:outline-none focus:z-10',
              isActive ? [
                'bg-acid-primary text-white',
                'shadow-lg shadow-acid-primary/30',
              ] : [
                'text-acid-text-muted',
                'hover:text-acid-text',
              ]
            )}
          >
            <span className="flex items-center gap-2">
              <Icon size={16} />
              {option.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}

