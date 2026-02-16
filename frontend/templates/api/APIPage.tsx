'use client';

import { useState, type ComponentType } from 'react';
import { NavCards } from './NavCards';
import { RestSection } from './RestSection';
import { PlaygroundSection } from './PlaygroundSection';
import { KeysSection } from './KeysSection';
import { WidgetsSection } from './WidgetsSection';
import type { APISection } from './types';

const SECTIONS: Record<APISection, ComponentType> = {
  docs: RestSection,
  playground: PlaygroundSection,
  keys: KeysSection,
  widgets: WidgetsSection,
};

export function APIPage() {
  const [active, setActive] = useState<APISection>('docs');
  const Content = SECTIONS[active];

  return (
    <div className="api-page">
      <div className="api-hero">
        <h1 className="api-hero-title">API &amp; Widgets</h1>
        <p className="api-hero-desc">
          Integrate real-time LLM performance data into your apps,
          <br />
          or embed live charts on your website.
        </p>
      </div>

      <NavCards activeSection={active} onSectionChange={setActive} />

      <div className="api-content">
        <Content />
      </div>
    </div>
  );
}
