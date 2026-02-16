'use client';

import { useState } from 'react';
import { FEATURES, type CellType } from '@/data/early-access';

function CellIcon({ type }: { type: CellType }) {
  switch (type) {
    case 'check': return <span className="ea-check">✓</span>;
    case 'lock':  return <span className="ea-lock">🔒</span>;
    case 'soon':  return <span className="ea-soon">Q2</span>;
    default:      return <span className="ea-lock">—</span>;
  }
}

export function FeatureTable() {
  const [open, setOpen] = useState(false);

  return (
    <section className="ea-detail-section">
      <button
        className={`ea-detail-toggle ${open ? 'open' : ''}`}
        onClick={() => setOpen(!open)}
      >
        View full feature comparison
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      <div className={`ea-table-wrapper ${open ? 'open' : ''}`}>
        <table className="ea-table">
          <thead>
            <tr>
              <th>Feature</th>
              <th>Free</th>
              <th>Pro</th>
            </tr>
          </thead>
          {FEATURES.map((group) => (
            <tbody key={group.group}>
              <tr>
                <td colSpan={3} className="ea-feature-group">{group.group}</td>
              </tr>
              {group.items.map((f) => (
                <tr key={f.name}>
                  <td className="ea-feature-name">{f.name}</td>
                  <td><CellIcon type={f.free} /></td>
                  <td><CellIcon type={f.pro} /></td>
                </tr>
              ))}
            </tbody>
          ))}
        </table>
      </div>
    </section>
  );
}
