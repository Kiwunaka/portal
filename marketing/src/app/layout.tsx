import type { Metadata } from "next";

import JsonLd from "../components/json-ld";
import {
  buildOrganizationJsonLd,
  buildSoftwareApplicationJsonLd,
  buildWebSiteJsonLd,
  DEFAULT_MARKETING_SHARE_IMAGE_PATH,
  DEFAULT_MARKETING_TWITTER_IMAGE_PATH,
} from "../lib/marketing-site";
import { CANONICAL_CLIENT_BRAND, CANONICAL_MARKETING_SITE_URL } from "../lib/pokrov";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(CANONICAL_MARKETING_SITE_URL),
  title: {
    default: "POKROV VPN | Приложение для Android и Windows",
    template: "%s",
  },
  description:
    "POKROV VPN помогает начать с приложения, получить 5 дней бесплатного теста и перейти к кабинету, оплате и поддержке без лишней путаницы.",
  applicationName: CANONICAL_CLIENT_BRAND,
  alternates: {
    canonical: "/",
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
    title: "POKROV VPN | Приложение для Android и Windows",
    description:
      "VPN-сервис с app-first входом, бесплатным 5-дневным тестом и безопасным продолжением через кабинет или Telegram.",
    url: `${CANONICAL_MARKETING_SITE_URL}/`,
    images: [{ url: DEFAULT_MARKETING_SHARE_IMAGE_PATH, width: 1200, height: 630, alt: CANONICAL_CLIENT_BRAND }],
  },
  twitter: {
    card: "summary_large_image",
    title: "POKROV VPN | Приложение для Android и Windows",
    description:
      "Скачайте приложение, включите тест и продолжайте через кабинет и безопасный checkout-маршрут.",
    images: [DEFAULT_MARKETING_TWITTER_IMAGE_PATH],
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
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        <a href="#main-content" className="skip-link">
          Перейти к содержимому
        </a>
        <JsonLd data={buildOrganizationJsonLd()} />
        <JsonLd data={buildWebSiteJsonLd()} />
        <JsonLd data={buildSoftwareApplicationJsonLd()} />
        {children}
      </body>
    </html>
  );
}
