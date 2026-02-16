'use client';

export type Tab = 'grid' | 'insights' | 'api';

const TABS: { key: Tab; label: string }[] = [
  { key: 'grid', label: 'Index' },
  { key: 'insights', label: 'Insights' },
  { key: 'api', label: 'API' },
];

interface Props {
  activeTab: Tab | null;
  onTabChange: (tab: Tab) => void;
}

export function MainNav({ activeTab, onTabChange }: Props) {
  return (
    <nav className="main-nav">
      {TABS.map(({ key, label }) => (
        <button
          key={key}
          className={`nav-tab ${activeTab === key ? 'active' : ''}`}
          onClick={() => onTabChange(key)}
        >
          {label}
        </button>
      ))}
    </nav>
  );
}
