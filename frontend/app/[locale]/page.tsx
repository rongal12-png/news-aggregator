import { Locale, t } from '@/lib/i18n';
import { getTopStories, getCategories, Story, Category } from '@/lib/api';
import HomePageContent from '@/components/HomePageContent';

export const dynamic = 'force-dynamic';

interface PageProps {
  params: { locale: Locale };
  searchParams: { category?: string };
}

export default async function HomePage({ params, searchParams }: PageProps) {
  const { locale } = params;
  const category = searchParams.category || 'all';

  let stories: Story[] = [];
  let categories: Category[] = [];
  let error: string | null = null;

  try {
    [stories, categories] = await Promise.all([
      getTopStories(locale, 30, category),
      getCategories(locale),
    ]);
  } catch (e) {
    error = locale === 'he' ? 'שגיאה בטעינת החדשות' : 'Failed to load stories';
  }

  if (error) {
    return (
      <div>
        <div className="page-header">
          <h1 className="page-title">{t(locale, 'home.title')}</h1>
        </div>
        <div className="empty-state error">{error}</div>
      </div>
    );
  }

  return (
    <HomePageContent
      initialStories={stories}
      categories={categories}
      locale={locale}
      initialCategory={category}
    />
  );
}
