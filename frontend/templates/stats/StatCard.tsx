'use client';

import type { ReactNode } from 'react';

/* ============================================================================
   StatCard - Shared component for both TOP 5 STAT CARDS and INSIGHTS CARDS
   
   TWO TYPES OF CARDS:
   1. TOP 5 STAT CARDS (in StatsHighlightsGrid):
      - Fastest TTFT, Slowest TTFT, Best Value*, Most Stable*, Insight
      - Used for key metrics at the top of the page
      - Best Value & Most Stable use `pro={true}` (🔒 badge, blurred, unlock button)
   
   2. 12 INSIGHTS CARDS (in InsightsGrid):
      - 8 available: TTFT, Throughput, Reliability, Providers, Head-to-Head, Cost, Efficiency*, Stability*
      - 4 coming Q2: Cold Start, RAG Accuracy, Peak Hours, Geo Performance
      - Efficiency & Stability use `pro={true}` (🔒 badge, requires subscription)
      - Q2 cards use `locked={true}` (Q2 badge, coming soon)
   
   PROPS:
   - `pro={true}`: Pro features (🔒 badge) - requires subscription
   - `locked={true}`: Q2 features (Q2 badge) - coming soon
   - `showBadge={false}`: Hide floating badge (when lock is in title)
============================================================================ */

interface StatCardProps {
  title: string;
  locked?: boolean; // For Q2 features (coming soon) - shows Q2 badge
  pro?: boolean; // For Pro features (requires subscription) - shows 🔒 badge
  featured?: boolean;
  isExpanded: boolean;
  isActive?: boolean; // For active insight cards
  onToggle: () => void;
  children: ReactNode;
  tooltipHeader?: string;
  tooltipText?: string;
  showChevron?: boolean; // Control chevron visibility
  showBadge?: boolean; // Control badge visibility (default: true)
}

export function StatCard({
  title,
  locked = false,
  pro = false,
  featured = false,
  isExpanded,
  isActive = false,
  onToggle,
  children,
  tooltipHeader,
  tooltipText,
  showChevron = true,
  showBadge = true,
}: StatCardProps) {
  let cardClass = 'index-expand-card cursor-pointer transition';
  
  // Apply yellow border when expanded or active
  if (isExpanded || isActive) {
    cardClass += ' index-expand-card-active';
  } else {
    // Only apply featured/pro/locked styles when NOT active/expanded
    if (featured) {
      cardClass += ' hover:border-[var(--acid)]';
    } else if (pro) {
      cardClass += ' index-expand-card-pro hover:border-[#2a2a2a]';
    } else if (locked) {
      cardClass += ' index-expand-card-q2';
    } else {
      cardClass += ' hover:border-[#2a2a2a]';
    }
  }

  // Split emoji and text
  const emojiMatch = title.match(/^([\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[❌⚡🚀💔🏆💰💬📊❄️🎯⏰🌍⚔️])\s*(.+)$/u);
  const emoji = emojiMatch ? emojiMatch[1] : '';
  const text = emojiMatch ? emojiMatch[2] : title;

  // Some emojis render smaller, so we increase their size
  const needsLargerIcon = title.includes('Head-to-Head') || title.includes('Cold Start');
  const iconClass = needsLargerIcon ? 'insight-icon insight-icon-large' : 'insight-icon';

  return (
    <div onClick={onToggle} className={cardClass}>
      {tooltipHeader && tooltipText && (
        <div className="insight-tooltip">
          <div className="tooltip-header">{tooltipHeader}</div>
          <div className="tooltip-text">{tooltipText}</div>
        </div>
      )}

      {/* PRO BADGE (🔒): Shows for Pro features (requires subscription) */}
      {showBadge && pro && !locked && (
        <span className="insight-pro-badge">🔒</span>
      )}
      
      {/* Q2 BADGE: Shows for features coming in Q2 */}
      {showBadge && locked && (
        <span className="insight-q2-badge">Q2</span>
      )}

      {/* EXPAND CHEVRON */}
      {showChevron && (
      <div className={`card-expand-chevron ${isExpanded ? 'expanded' : ''}`}>
        ⌄
      </div>
      )}
      
      <div className="insight-card-header">
        {emoji && <div className={iconClass}>{emoji}</div>}
        <div className="index-expand-label">
          {text}
        </div>
      </div>

      {children}
    </div>
  );
}
