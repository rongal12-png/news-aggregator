// Server-side uses API_URL (internal Docker network), client-side uses NEXT_PUBLIC_API_URL
function getApiUrl() {
  return process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
}

export interface StoryExplanation {
  score_breakdown: Record<string, number>;
  matching_preferences: string[];
  tags_involved: string[];
  sources_involved: string[];
  why_text: string;
  why_text_he: string;
}

export interface Story {
  id: number;
  title: string;
  bullets: string[];
  tags: string[];
  source_count: number;
  sources: string[];
  category: string;
  published_at: string;
  score_factors?: Record<string, number>;
  explanation?: StoryExplanation;
}

// SummaryMode type is defined in preferences.ts to avoid circular imports
type SummaryMode = 'standard' | 'tldr' | 'delta' | 'forward';

export interface StoriesQueryParams {
  locale: string;
  limit?: number;
  offset?: number;
  category?: string;
  tags?: string[];
  excludeTags?: string[];
  sources?: string[];
  summaryMode?: SummaryMode;
  includeExplanation?: boolean;
}

export interface StoryDetail extends Story {
  articles: Article[];
}

export interface Article {
  id: number;
  title: string;
  url: string;
  source: string;
  published_at: string;
}

export interface Source {
  id: number;
  name: string;
  feed_url: string;
  language: string;
  category: string;
  weight: number;
  is_active: boolean;
}

export interface Category {
  id: string;
  name: string;
  name_he: string;
  icon?: string;
  color?: string;
  locale_filter?: string | null;
}

export async function getTopStories(
  locale: string = 'en',
  limit: number = 20,
  category?: string
): Promise<Story[]> {
  const apiUrl = getApiUrl();
  let url = `${apiUrl}/stories/top?lang=${locale}&limit=${limit}`;
  if (category && category !== 'all') {
    url += `&category=${category}`;
  }

  const res = await fetch(url, {
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error('Failed to fetch stories');
  }

  return res.json();
}

export async function getTopStoriesWithParams(params: StoriesQueryParams): Promise<Story[]> {
  const apiUrl = getApiUrl();
  const searchParams = new URLSearchParams();

  searchParams.set('lang', params.locale);
  searchParams.set('limit', String(params.limit || 20));
  if (params.offset) {
    searchParams.set('offset', String(params.offset));
  }

  if (params.category && params.category !== 'all') {
    searchParams.set('category', params.category);
  }
  if (params.tags && params.tags.length > 0) {
    searchParams.set('tags', params.tags.join(','));
  }
  if (params.excludeTags && params.excludeTags.length > 0) {
    searchParams.set('exclude_tags', params.excludeTags.join(','));
  }
  if (params.sources && params.sources.length > 0) {
    searchParams.set('sources', params.sources.join(','));
  }
  if (params.summaryMode && params.summaryMode !== 'standard') {
    searchParams.set('summary_mode', params.summaryMode);
  }
  if (params.includeExplanation) {
    searchParams.set('include_explanation', 'true');
  }

  const res = await fetch(`${apiUrl}/stories/top?${searchParams.toString()}`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error('Failed to fetch stories');
  }

  return res.json();
}

export async function getStory(
  id: number,
  locale: string = 'en'
): Promise<StoryDetail> {
  const apiUrl = getApiUrl();
  const res = await fetch(`${apiUrl}/stories/${id}?lang=${locale}`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error('Failed to fetch story');
  }

  return res.json();
}

export async function getCategories(locale: string = 'en'): Promise<Category[]> {
  const apiUrl = getApiUrl();
  const res = await fetch(`${apiUrl}/stories/categories?lang=${locale}`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    const defaults = [
      { id: 'all', name: 'All', name_he: 'הכל', icon: '🌐' },
      { id: 'israel', name: 'Israel', name_he: 'ישראל', icon: '🇮🇱', locale_filter: 'he' },
      { id: 'world', name: 'World', name_he: 'עולם', icon: '🌍' },
      { id: 'politics', name: 'Politics', name_he: 'פוליטיקה', icon: '🏛️' },
      { id: 'tech', name: 'Technology', name_he: 'טכנולוגיה', icon: '💻' },
      { id: 'finance', name: 'Finance', name_he: 'כלכלה', icon: '📈' },
      { id: 'crypto', name: 'Crypto', name_he: 'קריפטו', icon: '₿' },
      { id: 'sports', name: 'Sports', name_he: 'ספורט', icon: '⚽' },
      { id: 'general', name: 'General', name_he: 'כללי', icon: '📰' },
    ];
    // Filter by locale
    return defaults.filter(c => !c.locale_filter || c.locale_filter === locale);
  }

  const data = await res.json();
  return data.categories;
}

export async function trackPageView(
  path: string,
  locale: string,
  storyId?: number,
  category?: string
): Promise<void> {
  try {
    const apiUrl = getApiUrl();
    const params = new URLSearchParams({
      path,
      locale,
      ...(storyId && { story_id: String(storyId) }),
      ...(category && { category }),
    });
    await fetch(`${apiUrl}/admin/track?${params}`, {
      method: 'POST',
      cache: 'no-store',
    });
  } catch {
    // Silently fail - analytics shouldn't break the app
  }
}

export async function getSources(): Promise<Source[]> {
  const apiUrl = getApiUrl();
  const res = await fetch(`${apiUrl}/sources`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error('Failed to fetch sources');
  }

  return res.json();
}
