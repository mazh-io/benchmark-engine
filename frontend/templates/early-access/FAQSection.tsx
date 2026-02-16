'use client';

import { useState } from 'react';
import { FAQ } from '@/data/early-access';

export function FAQSection() {
  const [openIdx, setOpenIdx] = useState<number | null>(null);

  const toggle = (i: number) => setOpenIdx(openIdx === i ? null : i);

  return (
    <section className="ea-faq">
      <div className="ea-section-header">
        <h2 className="ea-section-title">Questions?</h2>
      </div>

      {FAQ.map((item, i) => (
        <div key={i} className={`ea-faq-item ${openIdx === i ? 'open' : ''}`}>
          <button className="ea-faq-q" onClick={() => toggle(i)}>
            {item.q}
          </button>
          <div className="ea-faq-a">{item.a}</div>
        </div>
      ))}
    </section>
  );
}
