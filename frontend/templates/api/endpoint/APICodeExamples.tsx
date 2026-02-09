'use client';

import { useState } from 'react';
import { highlightCode } from '../syntaxHighlighting';
import type { CodeExample } from '../types';

const LANGUAGE_LABELS: Record<CodeExample['language'], { tab: string; header: string }> = {
  curl: { tab: 'cURL', header: 'cURL' },
  python: { tab: 'Python', header: 'PYTHON' },
  javascript: { tab: 'JavaScript', header: 'JAVASCRIPT' },
};

interface Props {
  codeExamples: CodeExample[];
}

export function APICodeExamples({ codeExamples }: Props) {
  const [activeLanguage, setActiveLanguage] = useState<CodeExample['language']>('curl');

  if (!codeExamples.length) return null;

  const activeExample = codeExamples.find((ex) => ex.language === activeLanguage);

  return (
    <div>
      <h3 className="api-subsection-title">Code Examples</h3>

      <div className="api-code-tabs">
        {codeExamples.map((example) => (
          <button
            key={example.language}
            onClick={() => setActiveLanguage(example.language)}
            className={`api-code-tab ${activeLanguage === example.language ? 'active' : ''}`}
          >
            {LANGUAGE_LABELS[example.language].tab}
          </button>
        ))}
      </div>

      <div className="api-code-example">
        <div className="api-code-example-header">
          <span>{LANGUAGE_LABELS[activeLanguage].header}</span>
          <button className="api-copy-btn">Copy</button>
        </div>

        <div className="api-code-example-content">
          {activeExample && (
            <pre
              dangerouslySetInnerHTML={{
                __html: highlightCode(activeExample.code, activeExample.language),
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
}
