import type { ReactNode, ReactElement } from 'react';

interface Props {
  icon: string;
  title: string;
  onClose: () => void;
  children: ReactNode;
  /** If set, renders a pro-overlay with this text */
  pro?: string;
}

export function DetailPanel({ icon, title, onClose, children, pro }: Props): ReactElement {
  return (
    <div className={`insight-detail active${pro ? ' pro-overlay-section' : ''}`}>
      <div className="detail-header">
        <div className="detail-title">
          <span className="icon">{icon}</span> {title}
        </div>
        <div className="detail-actions">
          <button className="detail-info-btn">ⓘ</button>
          <button className="detail-close" onClick={onClose}>✕</button>
        </div>
      </div>

      <div className="detail-content">{children}</div>

      {pro && (
        <div className="pro-overlay">
          <div className="pro-overlay-icon">🔒</div>
          <div className="pro-overlay-title">Pro Feature</div>
          <div className="pro-overlay-text">{pro}</div>
          <button className="pro-overlay-btn">€19/mo</button>
        </div>
      )}
    </div>
  );
}

