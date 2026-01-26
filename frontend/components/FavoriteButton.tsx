'use client';

import { useState, useEffect } from 'react';
import { useAuth } from './AuthProvider';
import { addFavorite, removeFavorite, checkFavorite } from '@/lib/auth';
import { Locale } from '@/lib/i18n';

interface FavoriteButtonProps {
  storyId: number;
  locale: Locale;
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
}

export default function FavoriteButton({
  storyId,
  locale,
  size = 'md',
  showText = false
}: FavoriteButtonProps) {
  const { user } = useAuth();
  const [isFavorite, setIsFavorite] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (user && !checked) {
      checkFavorite(storyId).then((result) => {
        setIsFavorite(result);
        setChecked(true);
      });
    }
  }, [user, storyId, checked]);

  // Don't render if not logged in
  if (!user) return null;

  const handleToggle = async () => {
    if (loading) return;

    setLoading(true);
    try {
      if (isFavorite) {
        await removeFavorite(storyId);
        setIsFavorite(false);
      } else {
        await addFavorite(storyId);
        setIsFavorite(true);
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    } finally {
      setLoading(false);
    }
  };

  const texts = {
    add: locale === 'he' ? 'הוסף למועדפים' : 'Add to favorites',
    remove: locale === 'he' ? 'הסר מהמועדפים' : 'Remove from favorites',
  };

  const sizeClasses = {
    sm: 'fav-btn-sm',
    md: 'fav-btn-md',
    lg: 'fav-btn-lg',
  };

  return (
    <>
      <button
        className={`fav-btn ${sizeClasses[size]} ${isFavorite ? 'active' : ''}`}
        onClick={handleToggle}
        disabled={loading}
        title={isFavorite ? texts.remove : texts.add}
        aria-label={isFavorite ? texts.remove : texts.add}
      >
        <svg
          viewBox="0 0 24 24"
          fill={isFavorite ? 'currentColor' : 'none'}
          stroke="currentColor"
          strokeWidth="2"
          className="fav-icon"
        >
          <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
        </svg>
        {showText && (
          <span className="fav-text">
            {isFavorite
              ? (locale === 'he' ? 'במועדפים' : 'Saved')
              : (locale === 'he' ? 'שמור' : 'Save')}
          </span>
        )}
      </button>

      <style jsx>{`
        .fav-btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          background: transparent;
          border: 1.5px solid var(--border-color);
          border-radius: var(--radius-md);
          color: var(--text-muted);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .fav-btn:hover {
          border-color: #ef4444;
          color: #ef4444;
          background: rgba(239, 68, 68, 0.05);
        }

        .fav-btn.active {
          border-color: #ef4444;
          color: #ef4444;
          background: rgba(239, 68, 68, 0.1);
        }

        .fav-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .fav-btn-sm {
          padding: 6px;
        }

        .fav-btn-sm .fav-icon {
          width: 16px;
          height: 16px;
        }

        .fav-btn-md {
          padding: 8px;
        }

        .fav-btn-md .fav-icon {
          width: 20px;
          height: 20px;
        }

        .fav-btn-lg {
          padding: 10px 14px;
        }

        .fav-btn-lg .fav-icon {
          width: 22px;
          height: 22px;
        }

        .fav-icon {
          flex-shrink: 0;
          transition: transform var(--transition-fast);
        }

        .fav-btn:hover .fav-icon {
          transform: scale(1.1);
        }

        .fav-btn.active .fav-icon {
          animation: heartPop 0.3s ease-out;
        }

        @keyframes heartPop {
          0% { transform: scale(1); }
          50% { transform: scale(1.3); }
          100% { transform: scale(1); }
        }

        .fav-text {
          font-size: 0.875rem;
          font-weight: 500;
        }
      `}</style>
    </>
  );
}
