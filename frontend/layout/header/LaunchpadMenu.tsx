'use client';

import { useState, useRef, useEffect } from 'react';

type Product = {
  name: string;
  href: string;
  desc: string;
  active?: boolean;
  soon?: boolean;
};

const PRODUCTS: Product[] = [
  { name: 'mazh', href: '/', desc: 'LLM Latency Benchmarks', active: true },
  { name: 'imprest', href: 'https://imprest.io', desc: 'LLM Budget & Model Routing', soon: true },
  { name: 'calladot', href: 'https://calladot.com', desc: 'Rent Premium Domains', soon: true },
  { name: 'goVisor', href: 'https://govisor.io', desc: 'EU Tender Leads', soon: true },
  { name: 'gizt', href: 'https://gizt.io', desc: 'News-to-Post Generator', soon: true },
];

export function LaunchpadMenu() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const close = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('click', close);
    return () => document.removeEventListener('click', close);
  }, []);

  return (
    <div ref={ref} className={`lp-btn ${open ? 'open' : ''}`} onClick={() => setOpen(!open)}>
      <svg viewBox="0 0 24 24" fill="none" stroke="#06b6d4">
        <rect x="4" y="9" width="8" height="10" rx="1" strokeWidth="1.2" opacity=".4" />
        <rect x="8" y="6" width="8" height="10" rx="1" strokeWidth="1.2" opacity=".6" />
        <rect x="12" y="3" width="8" height="10" rx="1" strokeWidth="1.5" opacity="1" />
      </svg>

      <div className="lp-menu" onClick={(e) => e.stopPropagation()}>
        <div className="lp-menu-header">
          <span className="lp-skot-badge">skot</span>
          <span className="lp-menu-tagline">Many products. One company.</span>
        </div>

        <div className="lp-menu-grid">
          {PRODUCTS.map((p) => (
            <a
              key={p.name}
              href={p.href}
              className={`lp-item ${p.active ? 'active' : ''}`}
              target={p.href.startsWith('http') ? '_blank' : undefined}
              rel={p.href.startsWith('http') ? 'noreferrer' : undefined}
            >
              <div className="lp-item-header">
                <span className="lp-item-name">{p.name}</span>
                {p.soon && <span className="lp-soon">Soon</span>}
              </div>
              <span className="lp-item-desc">{p.desc}</span>
            </a>
          ))}
          <div className="lp-item more">
            <span>+ More to come</span>
          </div>
        </div>
      </div>
    </div>
  );
}
