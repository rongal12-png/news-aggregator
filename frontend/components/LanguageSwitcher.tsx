'use client';

import { usePathname, useRouter } from 'next/navigation';
import { locales, Locale, localeConfig } from '@/lib/i18n';

interface LanguageSwitcherProps {
  currentLocale: Locale;
}

export default function LanguageSwitcher({
  currentLocale,
}: LanguageSwitcherProps) {
  const router = useRouter();
  const pathname = usePathname();

  const switchLocale = (newLocale: Locale) => {
    if (newLocale === currentLocale) return;

    // Replace current locale in pathname with new locale
    const segments = pathname.split('/');
    segments[1] = newLocale;
    const newPath = segments.join('/');

    // Set cookie for persistence
    document.cookie = `locale=${newLocale};path=/;max-age=31536000`;

    router.push(newPath);
  };

  return (
    <div className="lang-switcher">
      {locales.map((locale) => (
        <button
          key={locale}
          onClick={() => switchLocale(locale)}
          className={`lang-btn ${locale === currentLocale ? 'active' : ''}`}
          aria-label={`Switch to ${localeConfig[locale].name}`}
        >
          {localeConfig[locale].nativeName}
        </button>
      ))}
    </div>
  );
}
