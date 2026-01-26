'use client';

import { useRouter, usePathname } from 'next/navigation';
import { Category } from '@/lib/api';
import { Locale } from '@/lib/i18n';

interface CategoryFilterProps {
  categories: Category[];
  currentCategory: string;
  locale: Locale;
  onCategoryChange?: (categoryId: string) => void;
}

export default function CategoryFilter({
  categories,
  currentCategory,
  locale,
  onCategoryChange,
}: CategoryFilterProps) {
  const router = useRouter();
  const pathname = usePathname();

  const handleCategoryChange = (categoryId: string) => {
    if (onCategoryChange) {
      // Use callback if provided (client-side filtering)
      onCategoryChange(categoryId);
    } else {
      // Default: navigate with URL change
      const params = new URLSearchParams();
      if (categoryId !== 'all') {
        params.set('category', categoryId);
      }
      const queryString = params.toString();
      router.push(queryString ? `${pathname}?${queryString}` : pathname);
    }
  };

  return (
    <div className="category-filter">
      {categories.map((cat) => (
        <button
          key={cat.id}
          onClick={() => handleCategoryChange(cat.id)}
          className={`category-btn ${currentCategory === cat.id ? 'active' : ''}`}
        >
          {cat.icon && <span className="category-icon">{cat.icon}</span>}
          <span className="category-name">
            {locale === 'he' ? cat.name_he : cat.name}
          </span>
        </button>
      ))}
    </div>
  );
}
