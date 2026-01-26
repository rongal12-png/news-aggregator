'use client';

import { Locale } from '@/lib/i18n';
import { SummaryMode } from '@/lib/preferences';

interface SummaryModeSelectorProps {
  locale: Locale;
  value: SummaryMode;
  onChange: (mode: SummaryMode) => void;
  compact?: boolean;
}

const MODES: Array<{
  id: SummaryMode;
  icon: string;
  en: string;
  he: string;
  description: { en: string; he: string };
}> = [
  {
    id: 'standard',
    icon: '📝',
    en: 'Standard',
    he: 'רגיל',
    description: {
      en: 'Full summary with key points',
      he: 'סיכום מלא עם נקודות מפתח',
    },
  },
  {
    id: 'tldr',
    icon: '⚡',
    en: 'TL;DR',
    he: 'בקיצור',
    description: {
      en: 'One-line summary',
      he: 'סיכום בשורה אחת',
    },
  },
  {
    id: 'delta',
    icon: '🔄',
    en: "What's New",
    he: 'מה חדש',
    description: {
      en: 'Latest developments',
      he: 'ההתפתחויות האחרונות',
    },
  },
  {
    id: 'forward',
    icon: '🔮',
    en: 'What Next',
    he: 'מה הלאה',
    description: {
      en: 'Implications & outlook',
      he: 'השלכות ותחזיות',
    },
  },
];

export default function SummaryModeSelector({
  locale,
  value,
  onChange,
  compact = false,
}: SummaryModeSelectorProps) {
  return (
    <div className={`summary-mode-selector ${compact ? 'compact' : ''}`}>
      {MODES.map((mode) => {
        const isActive = value === mode.id;
        return (
          <button
            key={mode.id}
            className={`mode-btn ${isActive ? 'active' : ''}`}
            onClick={() => onChange(mode.id)}
            title={locale === 'he' ? mode.description.he : mode.description.en}
            aria-pressed={isActive}
          >
            <span className="mode-icon">{mode.icon}</span>
            <span className="mode-label">{locale === 'he' ? mode.he : mode.en}</span>
          </button>
        );
      })}

      <style jsx>{`
        .summary-mode-selector {
          display: flex;
          gap: var(--spacing-xs);
          background: var(--bg-secondary);
          padding: 4px;
          border-radius: var(--radius-lg);
          overflow-x: auto;
          -webkit-overflow-scrolling: touch;
        }

        .summary-mode-selector.compact {
          background: transparent;
          padding: 0;
        }

        .mode-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 14px;
          background: transparent;
          border: none;
          border-radius: var(--radius-md);
          font-size: 0.875rem;
          font-weight: 500;
          color: var(--text-secondary);
          cursor: pointer;
          transition: all var(--transition-fast);
          white-space: nowrap;
          flex-shrink: 0;
        }

        .compact .mode-btn {
          padding: 6px 10px;
          font-size: 0.8125rem;
          background: var(--bg-card);
          border: 1px solid var(--border-color);
        }

        .mode-btn:hover {
          color: var(--text-primary);
          background: var(--bg-hover);
        }

        .mode-btn.active {
          background: var(--bg-card);
          color: var(--accent-color);
          box-shadow: var(--shadow-sm);
        }

        .compact .mode-btn.active {
          background: var(--accent-color);
          color: white;
          border-color: var(--accent-color);
        }

        .mode-icon {
          font-size: 1rem;
          line-height: 1;
        }

        .compact .mode-icon {
          font-size: 0.875rem;
        }

        .mode-label {
          line-height: 1;
        }

        @media (max-width: 600px) {
          .summary-mode-selector {
            justify-content: stretch;
          }

          .mode-btn {
            flex: 1;
            justify-content: center;
            padding: 8px 10px;
          }

          .mode-label {
            display: none;
          }

          .compact .mode-label {
            display: inline;
          }
        }
      `}</style>
    </div>
  );
}
