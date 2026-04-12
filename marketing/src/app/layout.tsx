import type { Metadata } from "next";
import { JetBrains_Mono, Manrope, Playfair_Display } from "next/font/google";

import JsonLd from "../components/json-ld";
import {
  buildOrganizationJsonLd,
  buildWebSiteJsonLd,
  DEFAULT_MARKETING_SHARE_IMAGE_HEIGHT,
  DEFAULT_MARKETING_SHARE_IMAGE_WIDTH,
  DEFAULT_MARKETING_SHARE_IMAGE_PATH,
  DEFAULT_MARKETING_TWITTER_IMAGE_PATH,
} from "../lib/marketing-site";
import { CANONICAL_CLIENT_BRAND, CANONICAL_MARKETING_SITE_URL } from "../lib/pokrov";
import "./globals.css";

const bodyFont = Manrope({ subsets: ["latin", "cyrillic"], variable: "--font-body" });
const displayFont = Playfair_Display({ subsets: ["latin", "cyrillic"], variable: "--font-display" });
const monoFont = JetBrains_Mono({ subsets: ["latin", "cyrillic"], variable: "--font-mono" });

export const metadata: Metadata = {
  metadataBase: new URL(CANONICAL_MARKETING_SITE_URL),
  title: {
    default: "POKROV VPN | Приложение VPN для Android и Windows",
    template: "%s",
  },
  description:
    "POKROV VPN помогает начать с приложения, спокойно проверить сервис 5 дней бесплатно и управлять доступом без путаницы.",
  applicationName: CANONICAL_CLIENT_BRAND,
  alternates: {
    canonical: `${CANONICAL_MARKETING_SITE_URL}/`,
  },
  manifest: "/manifest.webmanifest",
  icons: {
    icon: [{ url: "/favicon.ico" }, { url: "/icon.png", type: "image/png" }],
    shortcut: [{ url: "/favicon.ico" }],
    apple: [{ url: "/apple-icon.png", type: "image/png" }],
  },
  openGraph: {
    type: "website",
    locale: "ru_RU",
    siteName: CANONICAL_CLIENT_BRAND,
    title: "POKROV VPN | Приложение VPN для Android и Windows",
    description:
      "Спокойный app-first VPN-сервис с бесплатным 5-дневным тестом, понятным кабинетом и поддержкой без лишнего шума.",
    url: `${CANONICAL_MARKETING_SITE_URL}/`,
    images: [
      {
        url: DEFAULT_MARKETING_SHARE_IMAGE_PATH,
        width: DEFAULT_MARKETING_SHARE_IMAGE_WIDTH,
        height: DEFAULT_MARKETING_SHARE_IMAGE_HEIGHT,
        alt: `${CANONICAL_CLIENT_BRAND} — VPN для Android и Windows`,
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "POKROV VPN | Приложение VPN для Android и Windows",
    description:
      "Скачайте приложение, включите 5 дней теста и переходите к кабинету только тогда, когда вам это действительно нужно.",
    images: [
      {
        url: DEFAULT_MARKETING_TWITTER_IMAGE_PATH,
        width: DEFAULT_MARKETING_SHARE_IMAGE_WIDTH,
        height: DEFAULT_MARKETING_SHARE_IMAGE_HEIGHT,
        alt: `${CANONICAL_CLIENT_BRAND} — VPN для Android и Windows`,
      },
    ],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html:
              "(function(){try{var t=localStorage.getItem('pokrov-theme');if(t==='light'||t==='dark'){document.documentElement.setAttribute('data-theme',t);}}catch(_e){}})();",
          }}
        />
      </head>
      <body className={`${bodyFont.variable} ${displayFont.variable} ${monoFont.variable}`}>
        <a href="#main-content" className="skip-link">
          Перейти к содержимому
        </a>
        <JsonLd data={buildOrganizationJsonLd()} />
        <JsonLd data={buildWebSiteJsonLd()} />
        {children}
      </body>
    </html>
  );
}
