import Image from 'next/image';
import Link from 'next/link';
import { Locale, t } from '@/lib/i18n';
import LanguageSwitcher from './LanguageSwitcher';
import ThemeToggle from './ThemeToggle';
import UserMenu from './UserMenu';

interface HeaderProps {
  locale: Locale;
}

export default function Header({ locale }: HeaderProps) {
  return (
    <header className="header">
      <div className="header-content">
        <div className="site-brand">
          <Link href={`/${locale}`} className="site-title">
            <Image
              src="/favicon.svg"
              alt="Briefer"
              width={28}
              height={28}
              className="site-logo"
              priority
            />
            <span className="site-name">{t(locale, 'site.title')}</span>
          </Link>
          <span className="site-tagline">{t(locale, 'site.tagline')}</span>
        </div>
        <div className="header-actions">
          <ThemeToggle />
          <LanguageSwitcher currentLocale={locale} />
          <UserMenu locale={locale} />
        </div>
      </div>
    </header>
  );
}
