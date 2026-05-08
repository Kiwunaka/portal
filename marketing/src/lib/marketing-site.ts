import type { MetadataRoute } from "next";

import {
  CANONICAL_BOT_URL,
  CANONICAL_CHECKOUT_URL,
  CANONICAL_CONTACT_EMAIL,
  CANONICAL_MARKETING_SITE_URL,
  CANONICAL_NEWS_CHANNEL_URL,
  CANONICAL_PLATFORM_BRAND,
  CANONICAL_PUBLIC_PLATFORM_SCOPE,
  CANONICAL_SUPPORT_BOT_URL,
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
  "Приложения для Android и Windows",
  "Бесплатный 5-дневный старт в приложении",
  "Один кабинет для доступа, устройств и продления",
  "Поддержка и восстановление без лишней путаницы",
  "Telegram как бонус и запасной путь связи",
] as const;

export type MarketingRouteConfig = {
  path: string;
  changeFrequency: NonNullable<MetadataRoute.Sitemap[number]["changeFrequency"]>;
  priority: number;
};

export const MARKETING_SITEMAP_ROUTES: MarketingRouteConfig[] = [
  { path: MARKETING_CANONICAL_PATHS.home, changeFrequency: "weekly", priority: 1 },
  { path: MARKETING_CANONICAL_PATHS.mobile, changeFrequency: "weekly", priority: 0.9 },
  { path: MARKETING_CANONICAL_PATHS.devices, changeFrequency: "weekly", priority: 0.88 },
  { path: MARKETING_CANONICAL_PATHS.youtube, changeFrequency: "weekly", priority: 0.82 },
  { path: MARKETING_CANONICAL_PATHS.tiktok, changeFrequency: "weekly", priority: 0.82 },
  { path: MARKETING_CANONICAL_PATHS.telegram, changeFrequency: "weekly", priority: 0.78 },
  { path: MARKETING_CANONICAL_PATHS.checkout, changeFrequency: "weekly", priority: 0.76 },
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
    question: "С чего начать?",
    answer:
      "Скачайте приложение для Android или Windows, откройте его и начните с бесплатных 5 дней. Никакой лишней переписки для старта не нужно.",
  },
  {
    question: "Что будет после бесплатных 5 дней?",
    answer:
      "Вы сможете спокойно выбрать платный срок и продолжить в том же аккаунте. Если с продлением что-то не так, кабинет и поддержка помогут без ручной путаницы.",
  },
  {
    question: "Как устроено продление?",
    answer:
      "Вы выбираете срок, проверяете статус платежного маршрута и продолжаете пользоваться тем же доступом после подтвержденного продления. Все привязано к вашему приложению и кабинету, а не к случайным ручным настройкам.",
  },
  {
    question: "Нужен ли Telegram для старта?",
    answer:
      "Нет. Основной старт идет через приложение. Telegram полезен для бонуса, восстановления доступа и быстрого контакта с поддержкой.",
  },
  {
    question: "Если что-то не получается, куда идти?",
    answer:
      "Сначала откройте кабинет или раздел поддержки в приложении. В бета-волне команда отвечает по мере возможности, без обещания круглосуточной реакции.",
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
    description:
      "POKROV помогает начать через приложение, спокойно проверить сервис и дальше управлять доступом без лишней технической путаницы.",
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
    operatingSystem: CANONICAL_PUBLIC_PLATFORM_SCOPE.join(", "),
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
    downloadUrl: buildMarketingUrl(MARKETING_CANONICAL_PATHS.install),
    mainEntityOfPage: canonicalUrl,
    url: canonicalUrl,
    description:
      "POKROV помогает начать с приложения на Android или Windows, получить бесплатные 5 дней и дальше спокойно управлять доступом и устройствами.",
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

export function buildCheckoutHostHref(planCode: string, promoCode?: string): string {
  const url = new URL(CANONICAL_CHECKOUT_URL);
  url.searchParams.set("plan", planCode);
  if (promoCode) {
    url.searchParams.set("promo", promoCode);
  }
  return url.toString();
}
