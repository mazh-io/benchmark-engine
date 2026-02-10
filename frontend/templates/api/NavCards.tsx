import type { APISection, APICard } from './types';

interface Props {
  activeSection: APISection;
  onSectionChange: (section: APISection) => void;
}

const API_CARDS: APICard[] = [
  { id: 'docs', icon: '📡', label: 'API Docs' },
  { id: 'playground', icon: '⚡', label: 'API Playground' },
  { id: 'keys', icon: '🔑', label: 'API Keys' },
  { id: 'widgets', icon: '📊', label: 'Widgets' },
];

export function NavCards({ activeSection, onSectionChange }: Props) {
  return (
    <div className="api-nav-grid">
      {API_CARDS.map((card) => (
        <button
          key={card.id}
          onClick={() => onSectionChange(card.id)}
          className={`api-nav-card ${activeSection === card.id ? 'active' : ''}`}
          aria-pressed={activeSection === card.id}
        >
          <span className="api-nav-icon">{card.icon}</span>
          <span className="api-nav-label">{card.label}</span>
        </button>
      ))}
    </div>
  );
}
