import type { MetadataRoute } from "next";

import {
  CANONICAL_BOT_URL,
  CANONICAL_CLIENT_BRAND,
  CANONICAL_CONTACT_EMAIL,
  CANONICAL_MARKETING_SITE_URL,
  CANONICAL_NEWS_CHANNEL_URL,
  CANONICAL_SUPPORT_BOT_URL,
} from "./pokrov";

export const DEFAULT_MARKETING_SHARE_IMAGE_PATH = "/opengraph-image.png";
export const DEFAULT_MARKETING_TWITTER_IMAGE_PATH = "/twitter-image.png";

export type MarketingRouteConfig = {
  path: string;
  changeFrequency: NonNullable<MetadataRoute.Sitemap[number]["changeFrequency"]>;
  priority: number;
};

export const MARKETING_SITEMAP_ROUTES: MarketingRouteConfig[] = [
  { path: "/", changeFrequency: "weekly", priority: 1 },
  { path: "/bystryy-vpn-na-telefon/", changeFrequency: "weekly", priority: 0.9 },
  { path: "/vpn-dlya-youtube/", changeFrequency: "weekly", priority: 0.86 },
  { path: "/vpn-dlya-tiktok/", changeFrequency: "weekly", priority: 0.86 },
  { path: "/vpn-na-iphone-android-windows/", changeFrequency: "weekly", priority: 0.88 },
  { path: "/vpn-telegram-bot/", changeFrequency: "weekly", priority: 0.78 },
  { path: "/checkout/", changeFrequency: "weekly", priority: 0.72 },
  { path: "/offer/", changeFrequency: "monthly", priority: 0.36 },
  { path: "/privacy/", changeFrequency: "monthly", priority: 0.34 },
];

export type MarketingFaqItem = {
  question: string;
  answer: string;
};

export const MARKETING_FAQ: MarketingFaqItem[] = [
  {
    question: "Как начать пользоваться POKROV VPN?",
    answer:
      "Скачайте приложение для Android или Windows, запустите бесплатный 5-дневный период и проверьте сервис в своих обычных сценариях. Кабинет и Telegram нужны уже для управления доступом и поддержкой.",
  },
  {
    question: "Что входит в бесплатный тест?",
    answer:
      "Во время теста доступен полноценный премиум-маршрут: основные локации, стабильное подключение и тот же интерфейс, который остаётся в платной версии.",
  },
  {
    question: "Как проходит оплата?",
    answer:
      "Публичная страница только объясняет следующий шаг. Саму оплату мы открываем после личного входа в кабинет или через персональный маршрут из Telegram.",
  },
  {
    question: "Куда писать, если нужна помощь?",
    answer:
      "Для поддержки используйте @pokrov_supportbot или письмо на support@pokrov.space. Если нужно, мы переводим и в запасной маршрут оплаты или подключения.",
  },
];

export function buildMarketingUrl(path = "/"): string {
  if (!path || path === "/") {
    return `${CANONICAL_MARKETING_SITE_URL}/`;
  }
  return `${CANONICAL_MARKETING_SITE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

export function buildMarketingSitemap(): MetadataRoute.Sitemap {
  return MARKETING_SITEMAP_ROUTES.map((route) => ({
    url: buildMarketingUrl(route.path),
    lastModified: new Date(),
    changeFrequency: route.changeFrequency,
    priority: route.priority,
  }));
}

export function buildOrganizationJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: CANONICAL_CLIENT_BRAND,
    url: `${CANONICAL_MARKETING_SITE_URL}/`,
    logo: buildMarketingUrl("/icon.png"),
    email: CANONICAL_CONTACT_EMAIL,
    contactPoint: [
      {
        "@type": "ContactPoint",
        contactType: "customer support",
        email: CANONICAL_CONTACT_EMAIL,
        url: CANONICAL_SUPPORT_BOT_URL,
        availableLanguage: ["ru"],
      },
    ],
    sameAs: [CANONICAL_BOT_URL, CANONICAL_SUPPORT_BOT_URL, CANONICAL_NEWS_CHANNEL_URL],
  };
}

export function buildWebSiteJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: CANONICAL_CLIENT_BRAND,
    url: `${CANONICAL_MARKETING_SITE_URL}/`,
    inLanguage: "ru-RU",
    publisher: {
      "@type": "Organization",
      name: CANONICAL_CLIENT_BRAND,
    },
  };
}

export function buildSoftwareApplicationJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: CANONICAL_CLIENT_BRAND,
    applicationCategory: "SecurityApplication",
    operatingSystem: "Android, Windows",
    inLanguage: "ru-RU",
    offers: {
      "@type": "Offer",
      price: "99",
      priceCurrency: "RUB",
      availability: "https://schema.org/InStock",
      url: buildMarketingUrl("/checkout/"),
    },
    downloadUrl: buildMarketingUrl("/#downloads"),
    url: `${CANONICAL_MARKETING_SITE_URL}/`,
    description:
      "Приложение VPN для Android и Windows с app-first стартом, бесплатным 5-дневным тестом и поддержкой через Telegram.",
  };
}

export function buildFaqJsonLd(items: MarketingFaqItem[]) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: items.map((item) => ({
      "@type": "Question",
      name: item.question,
      acceptedAnswer: {
        "@type": "Answer",
        text: item.answer,
      },
    })),
  };
}
