import { Metadata } from 'next';
import { locales, Locale, localeConfig, t } from '@/lib/i18n';
import Header from '@/components/Header';
import AdSenseScript from '@/components/AdSenseScript';
import { FooterAd } from '@/components/GoogleAds';
import { AuthProvider } from '@/components/AuthProvider';

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: { locale: Locale };
}): Promise<Metadata> {
  const { locale } = params;

  return {
    title: t(locale, 'site.title'),
    description: t(locale, 'site.description'),
    icons: {
      icon: [
        { url: '/favicon.svg', type: 'image/svg+xml' },
      ],
      apple: '/icon-192.svg',
    },
  };
}

export default function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { locale: Locale };
}) {
  const { locale } = params;
  const dir = localeConfig[locale]?.dir || 'ltr';

  return (
    <html lang={locale} dir={dir}>
      <body>
        <AuthProvider>
          <AdSenseScript />
          <Header locale={locale} />
          <main className="container">
            {children}
            <FooterAd />
          </main>
        </AuthProvider>
      </body>
    </html>
  );
}
