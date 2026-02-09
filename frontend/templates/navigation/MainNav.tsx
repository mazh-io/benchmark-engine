'use client';

export type Tab = 'grid' | 'insights' | 'api';

interface MainNavProps {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}

export function MainNav({ activeTab, onTabChange }: MainNavProps) {
  return (
    <nav className="main-nav">
      <button
        className={`nav-tab ${activeTab === 'grid' ? 'active' : ''}`}
        onClick={() => onTabChange('grid')}
      >
        Index
      </button>
      <button
        className={`nav-tab ${activeTab === 'insights' ? 'active' : ''}`}
        onClick={() => onTabChange('insights')}
      >
        Insights
      </button>
      <button
        className={`nav-tab ${activeTab === 'api' ? 'active' : ''}`}
        onClick={() => onTabChange('api')}
      >
        API
      </button>
    </nav>
  );
}

