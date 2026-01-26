'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { Story, Category, getTopStoriesWithParams } from '@/lib/api';
import { SummaryMode } from '@/lib/preferences';
import { Locale, t } from '@/lib/i18n';
import { usePreferences } from '@/lib/preferences';
import StoryList from './StoryList';
import CategoryFilter from './CategoryFilter';
import SummaryModeSelector from './SummaryModeSelector';

interface HomePageContentProps {
  initialStories: Story[];
  categories: Category[];
  locale: Locale;
  initialCategory: string;
}

const INITIAL_LIMIT = 15;
const LOAD_MORE_LIMIT = 10;

export default function HomePageContent({
  initialStories,
  categories,
  locale,
  initialCategory,
}: HomePageContentProps) {
  const { preferences, isLoaded, updatePreferences } = usePreferences();
  const [stories, setStories] = useState<Story[]>(initialStories);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [category, setCategory] = useState(initialCategory);
  const [hasMore, setHasMore] = useState(initialStories.length >= INITIAL_LIMIT);
  const [offset, setOffset] = useState(initialStories.length);

  // Local state for UI controls - initialized to defaults, synced with preferences once loaded
  const [summaryMode, setSummaryMode] = useState<SummaryMode>('standard');
  const [showExplanations, setShowExplanations] = useState(false);

  // Track if we've synced with preferences
  const hasSyncedRef = useRef(false);
  const loadMoreRef = useRef<HTMLDivElement>(null);
  const observerRef = useRef<IntersectionObserver | null>(null);

  // Sync local state with preferences once loaded
  useEffect(() => {
    if (isLoaded && !hasSyncedRef.current) {
      setSummaryMode(preferences.defaultSummaryMode);
      setShowExplanations(preferences.showExplanations);
      hasSyncedRef.current = true;
    }
  }, [isLoaded, preferences.defaultSummaryMode, preferences.showExplanations]);

  const fetchStories = useCallback(async (mode: SummaryMode, explain: boolean, cat: string, reset: boolean = true) => {
    if (reset) {
      setLoading(true);
      setError(null);
    }

    try {
      const newStories = await getTopStoriesWithParams({
        locale,
        limit: INITIAL_LIMIT,
        category: cat !== 'all' ? cat : undefined,
        excludeTags: preferences.blockedTags.length > 0 ? preferences.blockedTags : undefined,
        summaryMode: mode,
        includeExplanation: explain,
      });
      setStories(newStories);
      setOffset(newStories.length);
      setHasMore(newStories.length >= INITIAL_LIMIT);
    } catch (e) {
      console.error('Failed to fetch stories:', e);
      setError(locale === 'he' ? 'שגיאה בטעינת החדשות' : 'Failed to load stories');
    } finally {
      setLoading(false);
    }
  }, [locale, preferences.blockedTags]);

  const loadMoreStories = useCallback(async () => {
    if (loadingMore || !hasMore) return;

    setLoadingMore(true);

    try {
      const moreStories = await getTopStoriesWithParams({
        locale,
        limit: LOAD_MORE_LIMIT,
        category: category !== 'all' ? category : undefined,
        excludeTags: preferences.blockedTags.length > 0 ? preferences.blockedTags : undefined,
        summaryMode,
        includeExplanation: showExplanations,
        offset,
      });

      if (moreStories.length === 0) {
        setHasMore(false);
      } else {
        // Filter out duplicates based on story ID
        const existingIds = new Set(stories.map(s => s.id));
        const uniqueNewStories = moreStories.filter(s => !existingIds.has(s.id));

        setStories(prev => [...prev, ...uniqueNewStories]);
        setOffset(prev => prev + moreStories.length);
        setHasMore(moreStories.length >= LOAD_MORE_LIMIT);
      }
    } catch (e) {
      console.error('Failed to load more stories:', e);
    } finally {
      setLoadingMore(false);
    }
  }, [locale, category, preferences.blockedTags, summaryMode, showExplanations, offset, stories, loadingMore, hasMore]);

  // Intersection Observer for infinite scroll
  useEffect(() => {
    if (observerRef.current) {
      observerRef.current.disconnect();
    }

    observerRef.current = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore && !loading) {
          loadMoreStories();
        }
      },
      { threshold: 0.1, rootMargin: '100px' }
    );

    if (loadMoreRef.current) {
      observerRef.current.observe(loadMoreRef.current);
    }

    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect();
      }
    };
  }, [loadMoreStories, hasMore, loadingMore, loading]);

  const handleCategoryChange = (newCategory: string) => {
    setCategory(newCategory);
    // Update URL without reload
    const url = new URL(window.location.href);
    if (newCategory === 'all') {
      url.searchParams.delete('category');
    } else {
      url.searchParams.set('category', newCategory);
    }
    window.history.pushState({}, '', url.toString());

    // Fetch with new category
    fetchStories(summaryMode, showExplanations, newCategory);
  };

  const handleSummaryModeChange = (mode: SummaryMode) => {
    setSummaryMode(mode);
    updatePreferences({ defaultSummaryMode: mode });
    // Fetch with new mode
    fetchStories(mode, showExplanations, category);
  };

  const handleExplanationsToggle = () => {
    const newValue = !showExplanations;
    setShowExplanations(newValue);
    updatePreferences({ showExplanations: newValue });
    // Fetch with new explanation setting
    fetchStories(summaryMode, newValue, category);
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">{t(locale, 'home.title')}</h1>
        <CategoryFilter
          categories={categories}
          currentCategory={category}
          locale={locale}
          onCategoryChange={handleCategoryChange}
        />
      </div>

      <div className="filters-toolbar">
        <div className="filters-left">
          <SummaryModeSelector
            locale={locale}
            value={summaryMode}
            onChange={handleSummaryModeChange}
          />
        </div>
        <div className="filters-right">
          <button
            className={`explanation-toggle ${showExplanations ? 'active' : ''}`}
            onClick={handleExplanationsToggle}
            title={locale === 'he' ? 'הסבר למה אני רואה את זה' : 'Why am I seeing this?'}
          >
            <span>ℹ️</span>
            <span>{locale === 'he' ? 'הסברים' : 'Explain'}</span>
          </button>
        </div>
      </div>

      {loading ? (
        <div className="empty-state">
          {locale === 'he' ? 'טוען...' : 'Loading...'}
        </div>
      ) : error ? (
        <div className="empty-state error">{error}</div>
      ) : stories.length === 0 ? (
        <div className="empty-state">{t(locale, 'home.no_stories')}</div>
      ) : (
        <>
          <StoryList
            stories={stories}
            locale={locale}
            showExplanation={showExplanations}
          />

          {/* Infinite scroll trigger */}
          <div ref={loadMoreRef} className="load-more-trigger">
            {loadingMore && (
              <div className="loading-more">
                <div className="spinner-small"></div>
                <span>{locale === 'he' ? 'טוען עוד...' : 'Loading more...'}</span>
              </div>
            )}
          </div>

          {!hasMore && stories.length > INITIAL_LIMIT && (
            <div className="no-more-stories">
              {locale === 'he' ? 'אין עוד סיפורים' : 'No more stories'}
            </div>
          )}
        </>
      )}

      <style jsx>{`
        .load-more-trigger {
          padding: 20px;
          min-height: 60px;
        }

        .loading-more {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          color: var(--text-muted);
        }

        .spinner-small {
          width: 20px;
          height: 20px;
          border: 2px solid var(--border-color);
          border-top-color: var(--accent-color);
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        .no-more-stories {
          text-align: center;
          padding: 20px;
          color: var(--text-muted);
          font-size: 0.875rem;
        }
      `}</style>
    </div>
  );
}
