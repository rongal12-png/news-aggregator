import { Story } from '@/lib/api';
import { Locale } from '@/lib/i18n';
import StoryCard from './StoryCard';
import { InFeedAd } from './GoogleAds';

interface StoryListProps {
  stories: Story[];
  locale: Locale;
  showExplanation?: boolean;
}

// Show an ad after every N stories
const AD_INTERVAL = 5;

export default function StoryList({ stories, locale, showExplanation = false }: StoryListProps) {
  return (
    <div className="story-list">
      {stories.map((story, index) => (
        <>
          <StoryCard
            key={story.id}
            story={story}
            locale={locale}
            showExplanation={showExplanation}
          />
          {/* Insert ad after every AD_INTERVAL stories */}
          {(index + 1) % AD_INTERVAL === 0 && index < stories.length - 1 && (
            <InFeedAd key={`ad-${index}`} />
          )}
        </>
      ))}
    </div>
  );
}
