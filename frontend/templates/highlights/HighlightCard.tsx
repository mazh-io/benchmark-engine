'use client';

import type { ReactNode } from 'react';

interface Props {
  title: string;
  locked?: boolean;
  pro?: boolean;
  featured?: boolean;
  isExpanded: boolean;
  isActive?: boolean;
  onToggle: () => void;
  children: ReactNode;
  tooltipHeader?: string;
  tooltipText?: string;
  showChevron?: boolean;
  showBadge?: boolean;
}

const EMOJI_RE = /^([\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]|[❌⚡🚀💔🏆💰💬📊❄️🎯⏰🌍⚔️])\s*(.+)$/u;
const LARGE_ICONS = ['Head-to-Head', 'Cold Start'];

export function HighlightCard({
  title, locked = false, pro = false, featured = false,
  isExpanded, isActive = false, onToggle, children,
  tooltipHeader, tooltipText, showChevron = true, showBadge = true,
}: Props) {
  // Card state class
  let cls = 'index-expand-card cursor-pointer transition';
  if (isExpanded || isActive) {
    cls += ' index-expand-card-active';
  } else if (featured) {
    cls += ' hover:border-[var(--acid)]';
  } else if (pro) {
    cls += ' index-expand-card-pro hover:border-[#2a2a2a]';
  } else if (locked) {
    cls += ' index-expand-card-q2';
  } else {
    cls += ' hover:border-[#2a2a2a]';
  }

  // Parse emoji from title
  const match = title.match(EMOJI_RE);
  const emoji = match?.[1] ?? '';
  const text = match?.[2] ?? title;
  const iconCls = LARGE_ICONS.some((s) => title.includes(s))
    ? 'insight-icon insight-icon-large'
    : 'insight-icon';

  return (
    <div onClick={onToggle} className={cls}>
      {tooltipHeader && tooltipText && (
        <div className="insight-tooltip">
          <div className="tooltip-header">{tooltipHeader}</div>
          <div className="tooltip-text">{tooltipText}</div>
        </div>
      )}

      {showBadge && pro && !locked && <span className="insight-pro-badge">🔒</span>}
      {showBadge && locked && <span className="insight-q2-badge">Q2</span>}

      {showChevron && (
        <div className={`card-expand-chevron ${isExpanded ? 'expanded' : ''}`}>⌄</div>
      )}

      <div className="insight-card-header">
        {emoji && <div className={iconCls}>{emoji}</div>}
        <div className="index-expand-label">{text}</div>
      </div>

      {children}
    </div>
  );
}
