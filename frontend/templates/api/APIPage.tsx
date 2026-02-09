'use client';

import { useState, type ComponentType } from 'react';
import { APINavigationCards } from './APINavigationCards';
import { APIRestSection } from './APIRestSection';
import { APIPlaygroundSection } from './APIPlaygroundSection';
import { APIKeysSection } from './APIKeysSection';
import { APIWidgetsSection } from './APIWidgetsSection';
import type { APISection } from './types';

const SECTION_COMPONENTS: Record<APISection, ComponentType> = {
  docs: APIRestSection,
  playground: APIPlaygroundSection,
  keys: APIKeysSection,
  widgets: APIWidgetsSection,
};

export function APIPage() {
  const [activeSection, setActiveSection] = useState<APISection>('docs');
  const ActiveContent = SECTION_COMPONENTS[activeSection];

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

      <APINavigationCards activeSection={activeSection} onSectionChange={setActiveSection} />

      <div className="api-content">
        <ActiveContent />
      </div>
    </div>
  );
}
