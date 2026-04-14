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
import { CANONICAL_MARKETING_SITE_URL, CANONICAL_PLATFORM_BRAND } from "../lib/pokrov";
import "./globals.css";

const bodyFont = Manrope({ subsets: ["latin", "cyrillic"], variable: "--font-body" });
const displayFont = Playfair_Display({ subsets: ["latin", "cyrillic"], variable: "--font-display" });
const monoFont = JetBrains_Mono({ subsets: ["latin", "cyrillic"], variable: "--font-mono" });

export const metadata: Metadata = {
  metadataBase: new URL(CANONICAL_MARKETING_SITE_URL),
  title: {
    default: "POKROV | Быстрый маршрут для интернета и низкого пинга",
    template: "%s",
  },
  description:
    "POKROV помогает начать с приложения, спокойно проверить сервис 5 дней бесплатно и управлять своим маршрутом без путаницы.",
  applicationName: CANONICAL_PLATFORM_BRAND,
  alternates: {
    canonical: `${CANONICAL_MARKETING_SITE_URL}/`,
  },
  manifest: "/manifest.webmanifest",
  openGraph: {
    type: "website",
    locale: "ru_RU",
    siteName: CANONICAL_PLATFORM_BRAND,
    title: "POKROV | Тихий premium-маршрут и стабильная связь",
    description:
      "Спокойный app-first сервис для ускорения сети с бесплатным 5-дневным тестом, понятным кабинетом и поддержкой без лишнего шума.",
    url: `${CANONICAL_MARKETING_SITE_URL}/`,
    images: [
      {
        url: DEFAULT_MARKETING_SHARE_IMAGE_PATH,
        width: DEFAULT_MARKETING_SHARE_IMAGE_WIDTH,
        height: DEFAULT_MARKETING_SHARE_IMAGE_HEIGHT,
        alt: `${CANONICAL_PLATFORM_BRAND} — Умный маршрут для интернета`,
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "POKROV | Чистая скорость и стабильный пинг",
    description:
      "Скачайте приложение, включите 5 дней теста и наслаждайтесь скоростью. Переходите к кабинету только тогда, когда вам это действительно нужно.",
    images: [
      {
        url: DEFAULT_MARKETING_TWITTER_IMAGE_PATH,
        width: DEFAULT_MARKETING_SHARE_IMAGE_WIDTH,
        height: DEFAULT_MARKETING_SHARE_IMAGE_HEIGHT,
        alt: `${CANONICAL_PLATFORM_BRAND} — Умная оптимизация интернета`,
      },
    ],
  },
  icons: {
    icon: [{ url: "/pokrov-logo.svg", type: "image/svg+xml", sizes: "any" }],
    shortcut: [{ url: "/pokrov-logo.svg", type: "image/svg+xml", sizes: "any" }],
    apple: [{ url: "/pokrov-logo.svg", type: "image/svg+xml", sizes: "any" }],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
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
