import type { CSSProperties } from "react";
import type { Metadata } from "next";

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
import { CANONICAL_MARKETING_SITE_URL, CANONICAL_PLATFORM_BRAND, getDesignTokenCssVariables } from "../lib/pokrov";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(CANONICAL_MARKETING_SITE_URL),
  title: {
    default: "POKROV открывает YouTube, TikTok и другие сервисы | Android и Windows",
    template: "%s",
  },
  description:
    "Скачайте POKROV на Android или Windows, попробуйте 5 дней без карты и продлите доступ от 99 ₽ за 30 дней.",
  applicationName: CANONICAL_PLATFORM_BRAND,
  alternates: {
    canonical: `${CANONICAL_MARKETING_SITE_URL}/`,
  },
  manifest: "/manifest.webmanifest",
  openGraph: {
    type: "website",
    locale: "ru_RU",
    siteName: CANONICAL_PLATFORM_BRAND,
    title: "POKROV открывает YouTube, TikTok и другие сервисы",
    description: "Android и Windows, 5 дней бесплатно без карты, продление от 99 ₽ за 30 дней и поддержка рядом.",
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
    title: "POKROV | Android и Windows",
    description: "Скачайте приложение для Android или Windows, получите 5 дней бесплатно без карты и продолжайте через кабинет.",
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
      { url: "/tab-icon-32.png", type: "image/png", sizes: "32x32" },
      { url: "/favicon.ico", sizes: "any" },
      { url: "/pokrov-logo.svg", type: "image/svg+xml", sizes: "any" },
    ],
    shortcut: [{ url: "/favicon.ico", sizes: "any" }],
    apple: [{ url: "/apple-icon.png", type: "image/png", sizes: "512x512" }],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const designTokenVars = getDesignTokenCssVariables("public") as CSSProperties;

  return (
    <html lang="ru" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html:
              "(function(){var key='pokrov-theme';var root=document.documentElement;var media=window.matchMedia?window.matchMedia('(prefers-color-scheme: dark)'):null;function stored(){try{var value=localStorage.getItem(key);return value==='light'||value==='dark'?value:null;}catch(_e){return null;}}function syncButtons(theme){var dark=theme==='dark';var label=dark?'Переключить на светлую тему':'Переключить на тёмную тему';var buttons=document.querySelectorAll('[data-theme-toggle]');for(var i=0;i<buttons.length;i+=1){buttons[i].setAttribute('aria-pressed',dark?'true':'false');buttons[i].setAttribute('aria-label',label);buttons[i].setAttribute('title',label);}}function resolveTheme(){var saved=stored();if(saved){return saved;}return media&&media.matches?'dark':'light';}function apply(theme,persist){root.setAttribute('data-theme',theme);root.style.colorScheme=theme;syncButtons(theme);if(persist){try{localStorage.setItem(key,theme);}catch(_e){}}}function refresh(){apply(resolveTheme(),false);}refresh();document.addEventListener('DOMContentLoaded',refresh);document.addEventListener('click',function(event){var target=event.target;if(!target||!target.closest){return;}var button=target.closest('[data-theme-toggle]');if(!button){return;}var next=root.getAttribute('data-theme')==='dark'?'light':'dark';apply(next,true);});if(media){var handleChange=function(){if(!stored()){refresh();}};if(media.addEventListener){media.addEventListener('change',handleChange);}else if(media.addListener){media.addListener(handleChange);}}})();",
          }}
        />
      </head>
      <body style={designTokenVars}>
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
