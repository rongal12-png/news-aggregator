'use client';

import { useState, useEffect, useCallback } from 'react';

export type SummaryMode = 'standard' | 'tldr' | 'delta' | 'forward';

export interface UserPreferences {
  preferredTags: string[];
  blockedTags: string[];
  blockedSources: string[];
  defaultSummaryMode: SummaryMode;
  showExplanations: boolean;
}

const PREFERENCES_KEY = 'briefer_preferences';

const DEFAULT_PREFERENCES: UserPreferences = {
  preferredTags: [],
  blockedTags: [],
  blockedSources: [],
  defaultSummaryMode: 'standard',
  showExplanations: false,
};

/**
 * Hook for managing user preferences stored in localStorage.
 * Works without authentication - purely client-side.
 */
export function usePreferences() {
  const [preferences, setPreferences] = useState<UserPreferences>(DEFAULT_PREFERENCES);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load preferences from localStorage on mount
  useEffect(() => {
    if (typeof window === 'undefined') return;

    try {
      const stored = localStorage.getItem(PREFERENCES_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setPreferences({ ...DEFAULT_PREFERENCES, ...parsed });
      }
    } catch (error) {
      console.error('Failed to load preferences:', error);
    }
    setIsLoaded(true);
  }, []);

  // Save preferences to localStorage whenever they change
  const updatePreferences = useCallback((updates: Partial<UserPreferences>) => {
    setPreferences(prev => {
      const newPrefs = { ...prev, ...updates };
      try {
        localStorage.setItem(PREFERENCES_KEY, JSON.stringify(newPrefs));
      } catch (error) {
        console.error('Failed to save preferences:', error);
      }
      return newPrefs;
    });
  }, []);

  // Helper functions for common operations
  const addPreferredTag = useCallback((tag: string) => {
    setPreferences(prev => {
      if (prev.preferredTags.includes(tag)) return prev;
      const newTags = [...prev.preferredTags, tag];
      const newPrefs = { ...prev, preferredTags: newTags };
      localStorage.setItem(PREFERENCES_KEY, JSON.stringify(newPrefs));
      return newPrefs;
    });
  }, []);

  const removePreferredTag = useCallback((tag: string) => {
    setPreferences(prev => {
      const newTags = prev.preferredTags.filter(t => t !== tag);
      const newPrefs = { ...prev, preferredTags: newTags };
      localStorage.setItem(PREFERENCES_KEY, JSON.stringify(newPrefs));
      return newPrefs;
    });
  }, []);

  const addBlockedTag = useCallback((tag: string) => {
    setPreferences(prev => {
      if (prev.blockedTags.includes(tag)) return prev;
      const newTags = [...prev.blockedTags, tag];
      const newPrefs = { ...prev, blockedTags: newTags };
      localStorage.setItem(PREFERENCES_KEY, JSON.stringify(newPrefs));
      return newPrefs;
    });
  }, []);

  const removeBlockedTag = useCallback((tag: string) => {
    setPreferences(prev => {
      const newTags = prev.blockedTags.filter(t => t !== tag);
      const newPrefs = { ...prev, blockedTags: newTags };
      localStorage.setItem(PREFERENCES_KEY, JSON.stringify(newPrefs));
      return newPrefs;
    });
  }, []);

  const addBlockedSource = useCallback((source: string) => {
    setPreferences(prev => {
      if (prev.blockedSources.includes(source)) return prev;
      const newSources = [...prev.blockedSources, source];
      const newPrefs = { ...prev, blockedSources: newSources };
      localStorage.setItem(PREFERENCES_KEY, JSON.stringify(newPrefs));
      return newPrefs;
    });
  }, []);

  const removeBlockedSource = useCallback((source: string) => {
    setPreferences(prev => {
      const newSources = prev.blockedSources.filter(s => s !== source);
      const newPrefs = { ...prev, blockedSources: newSources };
      localStorage.setItem(PREFERENCES_KEY, JSON.stringify(newPrefs));
      return newPrefs;
    });
  }, []);

  const setSummaryMode = useCallback((mode: SummaryMode) => {
    setPreferences(prev => {
      const newPrefs = { ...prev, defaultSummaryMode: mode };
      localStorage.setItem(PREFERENCES_KEY, JSON.stringify(newPrefs));
      return newPrefs;
    });
  }, []);

  const toggleExplanations = useCallback(() => {
    setPreferences(prev => {
      const newPrefs = { ...prev, showExplanations: !prev.showExplanations };
      localStorage.setItem(PREFERENCES_KEY, JSON.stringify(newPrefs));
      return newPrefs;
    });
  }, []);

  const resetPreferences = useCallback(() => {
    localStorage.removeItem(PREFERENCES_KEY);
    setPreferences(DEFAULT_PREFERENCES);
  }, []);

  return {
    preferences,
    isLoaded,
    updatePreferences,
    addPreferredTag,
    removePreferredTag,
    addBlockedTag,
    removeBlockedTag,
    addBlockedSource,
    removeBlockedSource,
    setSummaryMode,
    toggleExplanations,
    resetPreferences,
  };
}

/**
 * Build API query string from preferences and filters.
 */
export function buildQueryParams(
  locale: string,
  preferences: UserPreferences,
  filters?: {
    category?: string;
    tags?: string[];
  }
): URLSearchParams {
  const params = new URLSearchParams({
    lang: locale,
    limit: '20',
  });

  // Add summary mode
  if (preferences.defaultSummaryMode !== 'standard') {
    params.set('summary_mode', preferences.defaultSummaryMode);
  }

  // Add explanation flag
  if (preferences.showExplanations) {
    params.set('include_explanation', 'true');
  }

  // Add category filter
  if (filters?.category && filters.category !== 'all') {
    params.set('category', filters.category);
  }

  // Add tag filters
  if (filters?.tags && filters.tags.length > 0) {
    params.set('tags', filters.tags.join(','));
  }

  // Add blocked tags
  if (preferences.blockedTags.length > 0) {
    params.set('exclude_tags', preferences.blockedTags.join(','));
  }

  return params;
}
