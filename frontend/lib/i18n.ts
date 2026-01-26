export const locales = ['en', 'he'] as const;
export type Locale = (typeof locales)[number];

export const localeConfig: Record<
  Locale,
  { name: string; nativeName: string; dir: 'ltr' | 'rtl' }
> = {
  en: { name: 'English', nativeName: 'English', dir: 'ltr' },
  he: { name: 'Hebrew', nativeName: 'עברית', dir: 'rtl' },
};

export const translations: Record<Locale, Record<string, string>> = {
  en: {
    'site.title': 'Briefer',
    'site.tagline': 'News, Simplified',
    'site.description': 'AI-powered news summaries from multiple sources',
    'home.title': 'Top Stories',
    'home.no_stories': 'No stories available',
    'story.sources': 'Sources',
    'story.read_more': 'Read more',
    'story.back': 'Back to stories',
    'nav.language': 'Language',
    'time.ago': 'ago',
    'time.hours': 'hours',
    'time.minutes': 'minutes',
  },
  he: {
    'site.title': 'בריפר',
    'site.tagline': 'חדשות, בקצרה',
    'site.description': 'סיכומי חדשות חכמים ממגוון מקורות',
    'home.title': 'הכותרות המובילות',
    'home.no_stories': 'אין כותרות זמינות',
    'story.sources': 'מקורות',
    'story.read_more': 'קרא עוד',
    'story.back': 'חזרה לכותרות',
    'nav.language': 'שפה',
    'time.ago': 'לפני',
    'time.hours': 'שעות',
    'time.minutes': 'דקות',
  },
};

export function t(locale: Locale, key: string): string {
  return translations[locale]?.[key] || translations.en[key] || key;
}

export function getDirection(locale: Locale): 'ltr' | 'rtl' {
  return localeConfig[locale]?.dir || 'ltr';
}

export function formatTimeAgo(date: string, locale: Locale): string {
  const now = new Date();
  const then = new Date(date);
  const diffMs = now.getTime() - then.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffMinutes = Math.floor(diffMs / (1000 * 60));
  const diffDays = Math.floor(diffHours / 24);

  // Hebrew: "לפני X דקות/שעות/ימים"
  // English: "X minutes/hours/days ago"
  if (locale === 'he') {
    if (diffDays > 0) {
      const dayWord = diffDays === 1 ? 'יום' : 'ימים';
      return `לפני ${diffDays} ${dayWord}`;
    }
    if (diffHours > 0) {
      const hourWord = diffHours === 1 ? 'שעה' : 'שעות';
      return `לפני ${diffHours} ${hourWord}`;
    }
    const minWord = diffMinutes === 1 ? 'דקה' : 'דקות';
    return `לפני ${diffMinutes} ${minWord}`;
  }

  // English format
  if (diffDays > 0) {
    return `${diffDays} ${diffDays === 1 ? 'day' : 'days'} ago`;
  }
  if (diffHours > 0) {
    return `${diffHours} ${diffHours === 1 ? 'hour' : 'hours'} ago`;
  }
  return `${diffMinutes} ${diffMinutes === 1 ? 'minute' : 'minutes'} ago`;
}
