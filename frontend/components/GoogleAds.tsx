'use client';

import { useEffect } from 'react';

declare global {
  interface Window {
    adsbygoogle: any[];
  }
}

interface AdUnitProps {
  slot: string;
  format?: 'auto' | 'rectangle' | 'horizontal' | 'vertical';
  responsive?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

// Individual ad unit component
export function AdUnit({ slot, format = 'auto', responsive = true, className = '', style }: AdUnitProps) {
  useEffect(() => {
    try {
      if (typeof window !== 'undefined' && window.adsbygoogle) {
        window.adsbygoogle.push({});
      }
    } catch (err) {
      console.error('AdSense error:', err);
    }
  }, []);

  const clientId = process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID;

  // Don't render if no client ID configured
  if (!clientId) {
    return null;
  }

  return (
    <div className={`ad-container ${className}`} style={style}>
      <ins
        className="adsbygoogle"
        style={{ display: 'block', ...style }}
        data-ad-client={clientId}
        data-ad-slot={slot}
        data-ad-format={format}
        data-full-width-responsive={responsive ? 'true' : 'false'}
      />
    </div>
  );
}

// Banner ad (horizontal, goes between stories)
export function BannerAd() {
  const slot = process.env.NEXT_PUBLIC_ADSENSE_BANNER_SLOT;
  if (!slot) return null;

  return (
    <AdUnit
      slot={slot}
      format="horizontal"
      className="ad-banner"
      style={{ marginBlock: 'var(--spacing-lg)' }}
    />
  );
}

// Sidebar ad (vertical, for side panels)
export function SidebarAd() {
  const slot = process.env.NEXT_PUBLIC_ADSENSE_SIDEBAR_SLOT;
  if (!slot) return null;

  return (
    <AdUnit
      slot={slot}
      format="vertical"
      className="ad-sidebar"
    />
  );
}

// In-feed ad (within story list)
export function InFeedAd() {
  const slot = process.env.NEXT_PUBLIC_ADSENSE_INFEED_SLOT;
  if (!slot) return null;

  return (
    <AdUnit
      slot={slot}
      format="auto"
      className="ad-infeed"
      style={{
        padding: 'var(--spacing-lg)',
        background: 'var(--bg-card)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-color)',
      }}
    />
  );
}

// Footer ad (at bottom of page)
export function FooterAd() {
  const slot = process.env.NEXT_PUBLIC_ADSENSE_FOOTER_SLOT;
  if (!slot) return null;

  return (
    <AdUnit
      slot={slot}
      format="horizontal"
      className="ad-footer"
      style={{
        marginTop: 'var(--spacing-2xl)',
        paddingTop: 'var(--spacing-lg)',
        borderTop: '1px solid var(--border-color)',
      }}
    />
  );
}
