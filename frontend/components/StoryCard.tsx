import Link from 'next/link';
import { Story } from '@/lib/api';
import { Locale, formatTimeAgo } from '@/lib/i18n';
import FavoriteButton from './FavoriteButton';

interface StoryExplanation {
  score_breakdown: Record<string, number>;
  matching_preferences: string[];
  tags_involved: string[];
  sources_involved: string[];
  why_text: string;
  why_text_he: string;
}

interface StoryCardProps {
  story: Story & {
    explanation?: StoryExplanation;
    score_factors?: Record<string, number>;
  };
  locale: Locale;
  showExplanation?: boolean;
}

const categoryConfig: Record<string, { color: string; icon: string; en: string; he: string }> = {
  israel: { color: '#0066cc', icon: '🇮🇱', en: 'Israel', he: 'ישראל' },
  world: { color: '#0ea5e9', icon: '🌍', en: 'World', he: 'עולם' },
  politics: { color: '#8b5cf6', icon: '🏛️', en: 'Politics', he: 'פוליטיקה' },
  tech: { color: '#3b82f6', icon: '💻', en: 'Tech', he: 'טכנולוגיה' },
  crypto: { color: '#f59e0b', icon: '₿', en: 'Crypto', he: 'קריפטו' },
  finance: { color: '#10b981', icon: '📈', en: 'Finance', he: 'כלכלה' },
  sports: { color: '#ef4444', icon: '⚽', en: 'Sports', he: 'ספורט' },
  general: { color: '#6b7280', icon: '📰', en: 'General', he: 'כללי' },
};

export default function StoryCard({ story, locale, showExplanation = false }: StoryCardProps) {
  const config = categoryConfig[story.category] || categoryConfig.general;
  const explanation = story.explanation;

  return (
    <article className="story-card">
      <div className="story-header">
        <div className="story-header-left">
          <span
            className="category-badge"
            style={{ backgroundColor: config.color }}
          >
            <span className="badge-icon">{config.icon}</span>
            {locale === 'he' ? config.he : config.en}
          </span>
          <span className="story-time">{formatTimeAgo(story.published_at, locale)}</span>
        </div>
        <FavoriteButton storyId={story.id} locale={locale} size="sm" />
      </div>

      <h2 className="story-title">
        <Link href={`/${locale}/story/${story.id}`}>{story.title}</Link>
      </h2>

      <ul className="bullets">
        {story.bullets.slice(0, 4).map((bullet, index) => (
          <li key={index}>{bullet}</li>
        ))}
      </ul>

      <div className="tags">
        {story.tags.slice(0, 5).map((tag) => (
          <span key={tag} className="tag">
            #{tag}
          </span>
        ))}
      </div>

      {showExplanation && explanation && (
        <div className="story-explanation">
          <span className="explanation-icon" title={locale === 'he' ? explanation.why_text_he : explanation.why_text}>
            ℹ️
          </span>
          <span className="explanation-text">
            {locale === 'he' ? explanation.why_text_he : explanation.why_text}
          </span>
        </div>
      )}

      <div className="story-footer">
        <div className="sources">
          <span className="sources-label">
            {locale === 'he' ? 'מקורות:' : 'Sources:'}
          </span>
          <span className="sources-list" dir="ltr">
            {story.sources.slice(0, 3).map((source, idx) => (
              <span key={source} className="source-name">
                {source}{idx < Math.min(story.sources.length, 3) - 1 && ' · '}
              </span>
            ))}
            {story.source_count > 3 && (
              <span className="source-more">+{story.source_count - 3}</span>
            )}
          </span>
        </div>
        <Link href={`/${locale}/story/${story.id}`} className="read-more">
          <span>{locale === 'he' ? 'קרא עוד ←' : 'Read more →'}</span>
        </Link>
      </div>
    </article>
  );
}
