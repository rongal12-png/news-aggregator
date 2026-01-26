'use client';

import FavoriteButton from './FavoriteButton';
import { Locale } from '@/lib/i18n';

interface StoryActionsProps {
  storyId: number;
  locale: Locale;
}

export default function StoryActions({ storyId, locale }: StoryActionsProps) {
  return (
    <div className="story-actions">
      <FavoriteButton storyId={storyId} locale={locale} size="lg" showText />
      <style jsx>{`
        .story-actions {
          display: flex;
          gap: var(--spacing-sm);
          margin-top: var(--spacing-md);
        }
      `}</style>
    </div>
  );
}
