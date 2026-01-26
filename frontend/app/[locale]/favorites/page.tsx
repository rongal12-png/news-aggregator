'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/components/AuthProvider';
import { getFavorites, FavoriteStory, removeFavorite } from '@/lib/auth';
import { Locale, formatTimeAgo } from '@/lib/i18n';

interface PageProps {
  params: { locale: Locale };
}

const categoryConfig: Record<string, { icon: string; en: string; he: string }> = {
  israel: { icon: '🇮🇱', en: 'Israel', he: 'ישראל' },
  world: { icon: '🌍', en: 'World', he: 'עולם' },
  politics: { icon: '🏛️', en: 'Politics', he: 'פוליטיקה' },
  tech: { icon: '💻', en: 'Tech', he: 'טכנולוגיה' },
  crypto: { icon: '₿', en: 'Crypto', he: 'קריפטו' },
  finance: { icon: '📈', en: 'Finance', he: 'כלכלה' },
  sports: { icon: '⚽', en: 'Sports', he: 'ספורט' },
  general: { icon: '📰', en: 'General', he: 'כללי' },
};

export default function FavoritesPage({ params }: PageProps) {
  const { locale } = params;
  const { user, loading: authLoading } = useAuth();
  const [favorites, setFavorites] = useState<FavoriteStory[]>([]);
  const [loading, setLoading] = useState(true);
  const [removingId, setRemovingId] = useState<number | null>(null);

  useEffect(() => {
    if (user) {
      loadFavorites();
    } else if (!authLoading) {
      setLoading(false);
    }
  }, [user, authLoading]);

  async function loadFavorites() {
    try {
      const data = await getFavorites();
      setFavorites(data);
    } catch (error) {
      console.error('Failed to load favorites:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleRemove(storyId: number) {
    setRemovingId(storyId);
    try {
      await removeFavorite(storyId);
      // Add delay for animation
      setTimeout(() => {
        setFavorites(favorites.filter(f => f.story_id !== storyId));
        setRemovingId(null);
      }, 300);
    } catch (error) {
      console.error('Failed to remove favorite:', error);
      setRemovingId(null);
    }
  }

  const texts = {
    title: locale === 'he' ? 'המועדפים שלי' : 'My Favorites',
    subtitle: locale === 'he' ? 'הכתבות ששמרת לקריאה מאוחרת' : 'Stories you saved for later',
    empty: locale === 'he' ? 'אין לך עדיין מועדפים' : "You don't have any favorites yet",
    emptyHint: locale === 'he' ? 'לחץ על ❤️ בכתבה כדי לשמור אותה כאן' : 'Click ❤️ on a story to save it here',
    browse: locale === 'he' ? 'גלה חדשות' : 'Browse stories',
    loginRequired: locale === 'he' ? 'התחבר כדי לראות את המועדפים שלך' : 'Login to see your favorites',
    login: locale === 'he' ? 'התחבר' : 'Login',
    remove: locale === 'he' ? 'הסר מהמועדפים' : 'Remove from favorites',
    savedOn: locale === 'he' ? 'נשמר ' : 'Saved ',
    count: (n: number) => locale === 'he' ? `${n} כתבות שמורות` : `${n} saved ${n === 1 ? 'story' : 'stories'}`,
  };

  if (authLoading || loading) {
    return (
      <div className="favorites-page">
        <div className="page-header">
          <h1 className="page-title">{texts.title}</h1>
          <p className="page-subtitle">{texts.subtitle}</p>
        </div>
        <div className="loading">
          <div className="loading-spinner"></div>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="favorites-page">
        <div className="page-header">
          <h1 className="page-title">{texts.title}</h1>
        </div>
        <div className="empty-state">
          <div className="empty-icon">🔐</div>
          <p>{texts.loginRequired}</p>
        </div>
      </div>
    );
  }

  const getCategoryDisplay = (category: string) => {
    const config = categoryConfig[category] || categoryConfig.general;
    return {
      icon: config.icon,
      name: locale === 'he' ? config.he : config.en
    };
  };

  return (
    <div className="favorites-page">
      <div className="page-header">
        <h1 className="page-title">{texts.title}</h1>
        {favorites.length > 0 && (
          <p className="page-subtitle">{texts.count(favorites.length)}</p>
        )}
      </div>

      {favorites.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">❤️</div>
          <p className="empty-text">{texts.empty}</p>
          <p className="empty-hint">{texts.emptyHint}</p>
          <Link href={`/${locale}`} className="browse-link">
            {locale === 'he' ? `${texts.browse} ←` : `${texts.browse} →`}
          </Link>
        </div>
      ) : (
        <div className="favorites-list">
          {favorites.map((fav, index) => {
            const cat = getCategoryDisplay(fav.category);
            const isRemoving = removingId === fav.story_id;
            return (
              <div
                key={fav.story_id}
                className={`favorite-item ${isRemoving ? 'removing' : ''}`}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <div className="favorite-content">
                  <Link href={`/${locale}/story/${fav.story_id}`} className="favorite-title">
                    {fav.title}
                  </Link>
                  <div className="favorite-meta">
                    <span className="favorite-category">
                      <span className="category-icon">{cat.icon}</span>
                      {cat.name}
                    </span>
                    <span className="favorite-date">
                      {texts.savedOn}{formatTimeAgo(fav.favorited_at, locale)}
                    </span>
                  </div>
                </div>
                <button
                  className="favorite-remove"
                  onClick={() => handleRemove(fav.story_id)}
                  title={texts.remove}
                  disabled={isRemoving}
                >
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
                  </svg>
                </button>
              </div>
            );
          })}
        </div>
      )}

      <style jsx>{`
        .favorites-page {
          max-width: 800px;
          margin: 0 auto;
        }

        .page-subtitle {
          color: var(--text-muted);
          font-size: 0.9375rem;
          margin-top: var(--spacing-xs);
        }

        .empty-state {
          text-align: center;
          padding: var(--spacing-2xl) var(--spacing-lg);
        }

        .empty-icon {
          font-size: 3rem;
          margin-bottom: var(--spacing-lg);
          opacity: 0.8;
        }

        .empty-text {
          font-size: 1.125rem;
          color: var(--text-primary);
          margin-bottom: var(--spacing-sm);
        }

        .empty-hint {
          font-size: 0.9375rem;
          color: var(--text-muted);
          margin-bottom: var(--spacing-xl);
        }

        .browse-link {
          display: inline-block;
          padding: 12px 24px;
          background: var(--accent-gradient);
          color: white;
          border-radius: var(--radius-md);
          font-weight: 600;
          transition: all var(--transition-fast);
          box-shadow: var(--shadow-md);
        }

        .browse-link:hover {
          transform: translateY(-2px);
          box-shadow: var(--shadow-lg);
        }

        .favorites-list {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-md);
        }

        .favorite-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--spacing-lg);
          background: var(--bg-card);
          border: 1px solid var(--border-color);
          border-radius: var(--radius-lg);
          gap: var(--spacing-md);
          transition: all var(--transition-fast);
          animation: slideIn 0.3s ease-out backwards;
        }

        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .favorite-item.removing {
          opacity: 0;
          transform: translateX(${locale === 'he' ? '-20px' : '20px'});
          transition: all 0.3s ease-out;
        }

        .favorite-item:hover {
          border-color: var(--accent-color);
          box-shadow: var(--shadow-md);
        }

        .favorite-content {
          flex: 1;
          min-width: 0;
        }

        .favorite-title {
          display: block;
          font-size: 1.0625rem;
          font-weight: 600;
          color: var(--text-primary);
          margin-bottom: 8px;
          line-height: 1.4;
          transition: color var(--transition-fast);
        }

        .favorite-title:hover {
          color: var(--accent-color);
        }

        .favorite-meta {
          display: flex;
          flex-wrap: wrap;
          gap: var(--spacing-md);
          font-size: 0.8125rem;
          color: var(--text-muted);
        }

        .favorite-category {
          display: flex;
          align-items: center;
          gap: 4px;
          color: var(--text-secondary);
          font-weight: 500;
        }

        .category-icon {
          font-size: 0.875rem;
        }

        .favorite-remove {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 40px;
          height: 40px;
          background: transparent;
          border: 1.5px solid var(--border-color);
          border-radius: var(--radius-md);
          color: #ef4444;
          cursor: pointer;
          transition: all var(--transition-fast);
          flex-shrink: 0;
        }

        .favorite-remove svg {
          width: 18px;
          height: 18px;
        }

        .favorite-remove:hover {
          background: rgba(239, 68, 68, 0.1);
          border-color: #ef4444;
          transform: scale(1.05);
        }

        .favorite-remove:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        @media (max-width: 600px) {
          .favorite-item {
            flex-direction: column;
            align-items: stretch;
          }

          .favorite-remove {
            align-self: flex-end;
            margin-top: var(--spacing-sm);
          }
        }
      `}</style>
    </div>
  );
}
