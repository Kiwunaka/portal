import type { MetadataRoute } from "next";

import {
  CANONICAL_BOT_URL,
  CANONICAL_CONTACT_EMAIL,
  CANONICAL_MARKETING_SITE_URL,
  CANONICAL_NEWS_CHANNEL_URL,
  CANONICAL_PLATFORM_BRAND,
  CANONICAL_SUPPORT_BOT_URL,
  getCopyText,
} from "./pokrov";

export const DEFAULT_MARKETING_SHARE_IMAGE_PATH = "/opengraph-image.png";
export const DEFAULT_MARKETING_TWITTER_IMAGE_PATH = "/twitter-image.png";
export const DEFAULT_MARKETING_SHARE_IMAGE_WIDTH = 1200;
export const DEFAULT_MARKETING_SHARE_IMAGE_HEIGHT = 630;
export const MARKETING_CANONICAL_PATHS = {
  home: "/",
  mobile: "/mobile/",
  tiktok: "/tiktok/",
  youtube: "/youtube/",
  devices: "/devices/",
  telegram: "/telegram/",
  checkout: "/checkout/",
  install: "/install/",
  offer: "/offer/",
  privacy: "/privacy/",
} as const;

export const MARKETING_FEATURE_LIST = [
  "5 дней бесплатного тест-драйва",
  "Приложения для Android и Windows",
  "Личный кабинет для управления",
  "Поддержка через Telegram и email",
] as const;

export type MarketingRouteConfig = {
  path: string;
  changeFrequency: NonNullable<MetadataRoute.Sitemap[number]["changeFrequency"]>;
  priority: number;
};

export const MARKETING_SITEMAP_ROUTES: MarketingRouteConfig[] = [
  { path: MARKETING_CANONICAL_PATHS.home, changeFrequency: "weekly", priority: 1 },
  { path: MARKETING_CANONICAL_PATHS.mobile, changeFrequency: "weekly", priority: 0.9 },
  { path: MARKETING_CANONICAL_PATHS.youtube, changeFrequency: "weekly", priority: 0.86 },
  { path: MARKETING_CANONICAL_PATHS.tiktok, changeFrequency: "weekly", priority: 0.86 },
  { path: MARKETING_CANONICAL_PATHS.devices, changeFrequency: "weekly", priority: 0.88 },
  { path: MARKETING_CANONICAL_PATHS.telegram, changeFrequency: "weekly", priority: 0.78 },
  { path: MARKETING_CANONICAL_PATHS.offer, changeFrequency: "monthly", priority: 0.36 },
  { path: MARKETING_CANONICAL_PATHS.privacy, changeFrequency: "monthly", priority: 0.34 },
];

export type MarketingFaqItem = {
  question: string;
  answer: string;
};

export type MarketingBreadcrumbItem = {
  name: string;
  path: string;
};

export type MarketingStructuredReview = {
  author: string;
  body: string;
  datePublished?: string;
};

export const MARKETING_FAQ: MarketingFaqItem[] = [
  {
    question: getCopyText("marketing.faq.1.q", "Как ускорить интернет с POKROV?"),
    answer: getCopyText(
      "marketing.faq.1.a",
      "Просто установите наше приложение, запустите тест-драйв на 5 дней и наслаждайтесь магией скорости. Кабинет нужен для управления.",
    ),
  },
  {
    question: getCopyText("marketing.faq.2.q", "Что входит в бесплатные 5 дней?"),
    answer: getCopyText(
      "marketing.faq.2.a",
      "Это полноценный премиум-доступ на 5 дней: можно спокойно проверить скорость, стабильность и качество сети перед продлением.",
    ),
  },
  {
    question: getCopyText("marketing.faq.3.q", "Как оформить продление?"),
    answer: getCopyText(
      "marketing.faq.3.a",
      "Сначала откройте кабинет или персональную ссылку из Telegram. После этого checkout покажет только подходящие способы оплаты и честную сумму.",
    ),
  },
  {
    question: getCopyText("marketing.faq.4.q", "Куда обратиться, если нужна помощь?"),
    answer: getCopyText(
      "marketing.faq.4.a",
      "Напишите в @pokrov_supportbot или на support@pokrov.space. Если нужно, поддержка переведёт вас в нужный маршрут.",
    ),
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
    name: CANONICAL_PLATFORM_BRAND,
    url: `${CANONICAL_MARKETING_SITE_URL}/`,
    logo: buildMarketingUrl("/pokrov-logo.svg"),
    description: getCopyText(
      "marketing.meta.description",
      "Скачайте приложение для Android или Windows, получите 5 дней бесплатно и продолжайте через личный кабинет и безопасный checkout-маршрут.",
    ),
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
    name: CANONICAL_PLATFORM_BRAND,
    url: `${CANONICAL_MARKETING_SITE_URL}/`,
    inLanguage: "ru-RU",
    publisher: {
      "@type": "Organization",
      name: CANONICAL_PLATFORM_BRAND,
    },
  };
}

export function buildSoftwareApplicationJsonLd(options?: {
  pagePath?: string;
  reviews?: MarketingStructuredReview[];
}) {
  const canonicalUrl = buildMarketingUrl(options?.pagePath || "/");
  const review =
    options?.reviews
      ?.filter((item) => item.author.trim() && item.body.trim())
      .map((item) => ({
        "@type": "Review",
        author: {
          "@type": "Person",
          name: item.author,
        },
        reviewBody: item.body,
        ...(item.datePublished ? { datePublished: item.datePublished } : {}),
      })) || [];

  return {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: CANONICAL_PLATFORM_BRAND,
    applicationCategory: "UtilitiesApplication",
    operatingSystem: "Android, Windows",
    inLanguage: "ru-RU",
    image: buildMarketingUrl(DEFAULT_MARKETING_SHARE_IMAGE_PATH),
    screenshot: buildMarketingUrl(DEFAULT_MARKETING_SHARE_IMAGE_PATH),
    featureList: MARKETING_FEATURE_LIST,
    ...(review.length ? { review } : {}),
    publisher: {
      "@type": "Organization",
      name: CANONICAL_PLATFORM_BRAND,
      url: `${CANONICAL_MARKETING_SITE_URL}/`,
    },
    softwareHelp: {
      "@type": "ContactPoint",
      contactType: "customer support",
      email: CANONICAL_CONTACT_EMAIL,
      url: CANONICAL_SUPPORT_BOT_URL,
      availableLanguage: ["ru"],
    },
    offers: {
      "@type": "Offer",
      price: "99",
      priceCurrency: "RUB",
      availability: "https://schema.org/InStock",
      url: buildMarketingUrl("/checkout/"),
    },
    downloadUrl: buildMarketingUrl("/install/"),
    mainEntityOfPage: canonicalUrl,
    url: canonicalUrl,
    description: getCopyText(
      "marketing.meta.description",
      "Скачайте приложение для Android или Windows, получите 5 дней бесплатно и продолжайте через личный кабинет и безопасный checkout-маршрут.",
    ),
  };
}

export function buildBreadcrumbJsonLd(items: MarketingBreadcrumbItem[]) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      item: buildMarketingUrl(item.path),
    })),
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
