'use client';

import { Locale } from '@/lib/i18n';

interface QuickFiltersProps {
  locale: Locale;
  activeCategory: string | null;
  onCategoryChange: (category: string | null) => void;
}

const CATEGORIES = [
  { id: 'all', icon: '🌐', en: 'All', he: 'הכל' },
  { id: 'tech', icon: '💻', en: 'Tech', he: 'טכנולוגיה' },
  { id: 'crypto', icon: '₿', en: 'Crypto', he: 'קריפטו' },
  { id: 'finance', icon: '📈', en: 'Finance', he: 'כלכלה' },
  { id: 'world', icon: '🌍', en: 'World', he: 'עולם' },
  { id: 'politics', icon: '🏛️', en: 'Politics', he: 'פוליטיקה' },
];

export default function QuickFilters({
  locale,
  activeCategory,
  onCategoryChange,
}: QuickFiltersProps) {
  return (
    <div className="quick-filters">
      <div className="filter-chips">
        {CATEGORIES.map((cat) => {
          const isActive = activeCategory === cat.id || (cat.id === 'all' && !activeCategory);
          return (
            <button
              key={cat.id}
              className={`filter-chip ${isActive ? 'active' : ''}`}
              onClick={() => onCategoryChange(cat.id === 'all' ? null : cat.id)}
              aria-pressed={isActive}
            >
              <span className="chip-icon">{cat.icon}</span>
              <span className="chip-label">{locale === 'he' ? cat.he : cat.en}</span>
            </button>
          );
        })}
      </div>

      <style jsx>{`
        .quick-filters {
          margin-bottom: var(--spacing-lg);
          overflow-x: auto;
          -webkit-overflow-scrolling: touch;
          scrollbar-width: none;
        }

        .quick-filters::-webkit-scrollbar {
          display: none;
        }

        .filter-chips {
          display: flex;
          gap: var(--spacing-sm);
          padding: 2px;
        }

        .filter-chip {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 14px;
          background: var(--bg-card);
          border: 1.5px solid var(--border-color);
          border-radius: var(--radius-full);
          font-size: 0.875rem;
          font-weight: 500;
          color: var(--text-secondary);
          cursor: pointer;
          transition: all var(--transition-fast);
          white-space: nowrap;
          flex-shrink: 0;
        }

        .filter-chip:hover {
          border-color: var(--accent-color);
          color: var(--accent-color);
          background: var(--bg-hover);
        }

        .filter-chip.active {
          background: var(--accent-gradient);
          border-color: transparent;
          color: white;
          box-shadow: var(--shadow-sm);
        }

        .filter-chip.active:hover {
          opacity: 0.9;
        }

        .chip-icon {
          font-size: 1rem;
          line-height: 1;
        }

        .chip-label {
          line-height: 1;
        }

        @media (max-width: 600px) {
          .filter-chip {
            padding: 6px 12px;
            font-size: 0.8125rem;
          }

          .chip-icon {
            font-size: 0.875rem;
          }
        }
      `}</style>
    </div>
  );
}
