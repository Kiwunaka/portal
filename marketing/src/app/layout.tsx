import type { Metadata } from "next";
import { Golos_Text } from "next/font/google";

import JsonLd from "../components/json-ld";
import FunnelTracker from "../components/funnel-tracker";
import {
  buildOrganizationJsonLd,
  buildWebSiteJsonLd,
  DEFAULT_MARKETING_SHARE_IMAGE_HEIGHT,
  DEFAULT_MARKETING_SHARE_IMAGE_PATH,
  DEFAULT_MARKETING_SHARE_IMAGE_WIDTH,
  DEFAULT_MARKETING_TWITTER_IMAGE_PATH,
} from "../lib/marketing-site";
import { CANONICAL_MARKETING_SITE_URL, CANONICAL_PLATFORM_BRAND, getDesignTokenThemeCss } from "../lib/pokrov";
import "./globals.css";

const golosText = Golos_Text({
  subsets: ["latin", "cyrillic"],
  variable: "--font-golos",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(CANONICAL_MARKETING_SITE_URL),
  title: {
    default: "POKROV VPN для Android и Windows — 5 дней бесплатно",
    template: "%s",
  },
  description:
    "Быстрый VPN для YouTube, TikTok, ChatGPT и сайтов. 5 дней бесплатно без карты, затем безлимитный трафик от 99 ₽.",
  applicationName: CANONICAL_PLATFORM_BRAND,
  alternates: {
    canonical: `${CANONICAL_MARKETING_SITE_URL}/`,
  },
  manifest: "/manifest.webmanifest",
  openGraph: {
    type: "website",
    locale: "ru_RU",
    siteName: CANONICAL_PLATFORM_BRAND,
    title: "POKROV VPN для Android и Windows",
    description: "Android и Windows, 5 дней бесплатно без карты, затем безлимитный трафик от 99 ₽.",
    url: `${CANONICAL_MARKETING_SITE_URL}/`,
    images: [
      {
        url: DEFAULT_MARKETING_SHARE_IMAGE_PATH,
        width: DEFAULT_MARKETING_SHARE_IMAGE_WIDTH,
        height: DEFAULT_MARKETING_SHARE_IMAGE_HEIGHT,
        alt: `${CANONICAL_PLATFORM_BRAND} для Android и Windows`,
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "POKROV VPN для Android и Windows",
    description: "YouTube, TikTok, ChatGPT и сайты одной кнопкой. 5 дней бесплатно без карты.",
    images: [
      {
        url: DEFAULT_MARKETING_TWITTER_IMAGE_PATH,
        width: DEFAULT_MARKETING_SHARE_IMAGE_WIDTH,
        height: DEFAULT_MARKETING_SHARE_IMAGE_HEIGHT,
        alt: `${CANONICAL_PLATFORM_BRAND} — приложение, кабинет и поддержка для Android и Windows`,
      },
    ],
  },
  icons: {
    icon: [
      { url: "/pokrov-logo.svg?v=20260722", type: "image/svg+xml", sizes: "any" },
      { url: "/tab-icon-32.png?v=20260722", type: "image/png", sizes: "32x32" },
      { url: "/favicon.ico?v=20260722", sizes: "any" },
    ],
    shortcut: [{ url: "/favicon.ico?v=20260722", sizes: "any" }],
    apple: [{ url: "/apple-icon.png?v=20260722", type: "image/png", sizes: "512x512" }],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const designTokenThemeCss = getDesignTokenThemeCss("public");

  return (
    <html lang="ru" className={golosText.variable} data-scroll-behavior="smooth" suppressHydrationWarning>
      <head>
        <style id="pokrov-design-tokens" dangerouslySetInnerHTML={{ __html: designTokenThemeCss }} />
      </head>
      <body>
        <a href="#main-content" className="skip-link">
          Перейти к содержимому
        </a>
        <JsonLd data={buildOrganizationJsonLd()} />
        <JsonLd data={buildWebSiteJsonLd()} />
        <FunnelTracker />
        {children}
      </body>
    </html>
  );
}
