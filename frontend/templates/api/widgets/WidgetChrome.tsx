'use client';

import type { ReactNode } from 'react';
import { highlightHTML } from '../syntaxHighlighting';

export type WidgetSize = 's' | 'm' | 'l';

interface WidgetChromeProps {
  id: string;
  title: string;
  description: string;
  size: WidgetSize;
  onSizeChange: (size: WidgetSize) => void;
  preview: ReactNode;
  embedCode: string;
  embedLabel?: string;
}

const SIZES: WidgetSize[] = ['s', 'm', 'l'];

export function WidgetChrome({
  id,
  title,
  description,
  size,
  onSizeChange,
  preview,
  embedCode,
  embedLabel = 'Embed Code',
}: WidgetChromeProps) {
  const copyCode = (code: string) => {
    navigator.clipboard?.writeText(code).catch(() => {});
  };

  return (
    <section className="widget-type-section" id={id}>
      <div className="widget-type-header">
        <div>
          <h3 className="widget-type-title">{title}</h3>
          <p className="widget-type-desc">{description}</p>
        </div>

        <div className="widget-sizes">
          {SIZES.map((variant) => (
            <button
              key={variant}
              type="button"
              onClick={() => onSizeChange(variant)}
              className={`widget-size-btn ${size === variant ? 'active' : ''}`}
            >
              {variant.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div className="widget-preview-container">
        <div className="widget-preview-box">{preview}</div>

        <div className="widget-embed-box">
          <div className="embed-code-box">
            <div className="embed-code-header">
              <span className="embed-code-title">{embedLabel}</span>
              <button
                type="button"
                className="code-block-copy"
                onClick={() => copyCode(embedCode)}
              >
                Copy
              </button>
            </div>
            <div className="embed-code-body">
              <pre>
                <code dangerouslySetInnerHTML={{ __html: highlightHTML(embedCode) }} />
              </pre>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
