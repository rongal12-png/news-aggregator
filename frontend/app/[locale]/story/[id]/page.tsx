import Link from 'next/link';
import { notFound } from 'next/navigation';
import { Locale, t, formatTimeAgo } from '@/lib/i18n';
import { getStory } from '@/lib/api';
import StoryActions from '@/components/StoryActions';
import Comments from '@/components/Comments';

export const dynamic = 'force-dynamic';

const categoryNames: Record<string, Record<Locale, string>> = {
  tech: { en: 'Technology', he: 'טכנולוגיה' },
  crypto: { en: 'Crypto', he: 'קריפטו' },
  general: { en: 'General', he: 'כללי' },
};

export default async function StoryPage({
  params,
}: {
  params: { locale: Locale; id: string };
}) {
  const { locale, id } = params;
  const storyId = parseInt(id, 10);

  if (isNaN(storyId)) {
    notFound();
  }

  let story;
  try {
    story = await getStory(storyId, locale);
  } catch (e) {
    notFound();
  }

  const categoryName = categoryNames[story.category]?.[locale] || story.category;

  return (
    <div className="story-detail">
      <nav className="breadcrumb">
        <Link href={`/${locale}`} className="back-link">
          {locale === 'he' ? `${t(locale, 'story.back')} →` : `← ${t(locale, 'story.back')}`}
        </Link>
        <span className="breadcrumb-separator">/</span>
        <span className="breadcrumb-category">{categoryName}</span>
      </nav>

      <article className="story-content">
        <header className="story-header">
          <h1 className="story-title">{story.title}</h1>
          <div className="story-meta">
            <span className="story-time">{formatTimeAgo(story.published_at, locale)}</span>
            <span className="story-sources-count">
              {locale === 'he'
                ? `${story.articles.length} מקורות`
                : `${story.articles.length} sources`}
            </span>
          </div>
          <StoryActions storyId={storyId} locale={locale} />
        </header>

        <div className="tags">
          {story.tags.map((tag) => (
            <span key={tag} className="tag">
              #{tag}
            </span>
          ))}
        </div>

        <section className="summary-section">
          <h2 className="section-title">
            {locale === 'he' ? 'תקציר' : 'Summary'}
          </h2>
          <ul className="bullets">
            {story.bullets.map((bullet, index) => (
              <li key={index}>{bullet}</li>
            ))}
          </ul>
        </section>

        <section className="articles-section">
          <h2 className="section-title">
            {locale === 'he' ? 'מקורות' : 'Sources'}
          </h2>

          <div className="articles-list">
            {story.articles.map((article) => (
              <a
                key={article.id}
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="article-item"
              >
                <div className="article-content">
                  <span className="article-title">{article.title}</span>
                  <span className="article-meta">
                    <span className="article-source" dir="ltr">{article.source}</span>
                    <span className="article-time">
                      {formatTimeAgo(article.published_at, locale)}
                    </span>
                  </span>
                </div>
                <span className="external-icon">{locale === 'he' ? '↖' : '↗'}</span>
              </a>
            ))}
          </div>
        </section>

        <Comments storyId={storyId} locale={locale} />
      </article>
    </div>
  );
}
