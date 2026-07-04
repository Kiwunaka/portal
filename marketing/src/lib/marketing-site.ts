import type { Metadata, MetadataRoute } from "next";

import {
  CANONICAL_BOT_URL,
  CANONICAL_CHECKOUT_URL,
  CANONICAL_CONTACT_EMAIL,
  CANONICAL_MARKETING_SITE_URL,
  CANONICAL_NEWS_CHANNEL_URL,
  CANONICAL_PLATFORM_BRAND,
  CANONICAL_PUBLIC_PLATFORM_SCOPE,
  CANONICAL_SUPPORT_BOT_URL,
  getTariffPlans,
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
  vpn: "/vpn/",
  checkout: "/checkout/",
  install: "/install/",
  offer: "/offer/",
  privacy: "/privacy/",
} as const;

export const MARKETING_MACHINE_READABLE_PATHS = {
  llms: "/llms.txt",
  pricing: "/pricing.md",
} as const;

const PUBLIC_TARIFF_PLANS = getTariffPlans()
  .slice()
  .filter((plan) => Boolean(plan.is_active))
  .sort((left, right) => Number(left.sort_order || 0) - Number(right.sort_order || 0));

const START_PLAN = PUBLIC_TARIFF_PLANS[0] || null;
const SEO_LAST_REVIEWED_DATE = "2026-06-01";

export const MARKETING_FEATURE_LIST = [
  "Android и Windows, 5 дней бесплатно",
  "5 дней бесплатно без карты",
  "Одна кнопка подключения в приложении",
  "Продление от 99 ₽ за 30 дней",
  "До 5 устройств в платном доступе",
  "Telegram-бонус +10 дней и поддержка",
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
  { path: MARKETING_CANONICAL_PATHS.vpn, changeFrequency: "weekly", priority: 0.8 },
  { path: MARKETING_CANONICAL_PATHS.telegram, changeFrequency: "weekly", priority: 0.78 },
  { path: MARKETING_CANONICAL_PATHS.checkout, changeFrequency: "weekly", priority: 0.76 },
  { path: MARKETING_MACHINE_READABLE_PATHS.pricing, changeFrequency: "weekly", priority: 0.64 },
  { path: MARKETING_MACHINE_READABLE_PATHS.llms, changeFrequency: "weekly", priority: 0.58 },
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
      "Скачайте приложение для Android или Windows, откройте его и активируйте 5 дней бесплатно без карты.",
  },
  {
    question: "Что будет после бесплатных 5 дней?",
    answer:
      "Можно выбрать платный срок от 99 ₽ за 30 дней или остаться на базовом режиме. Цена, срок и лимит устройств видны до оплаты.",
  },
  {
    question: "Нужно ли настраивать профили вручную?",
    answer:
      "Нет. Основной путь идет через приложение: установите его, войдите в аккаунт и нажмите подключение. Ручные режимы остаются только для восстановления и совместимости.",
  },
  {
    question: "Как устроено продление?",
    answer:
      "Вы выбираете срок, переходите к оплате и продолжаете тот же аккаунт POKROV. Если получаете код активации, его можно применить в приложении или кабинете.",
  },
  {
    question: "Нужен ли Telegram для старта?",
    answer:
      "Нет. Начать можно без Telegram. Он полезен для бонуса +10 дней, восстановления доступа и быстрого контакта с поддержкой.",
  },
  {
    question: "Если что-то не получается, куда идти?",
    answer:
      "Откройте кабинет или напишите в поддержку. Мы подскажем, где скачать приложение, как войти, забрать Telegram-бонус или продлить срок.",
  },
  {
    question: "Что если файл пока недоступен?",
    answer:
      "POKROV остается в бете. Если файл не открыт вашему аккаунту, сайт покажет кабинет, инструкцию или поддержку вместо пустой кнопки.",
  },
];

export function buildMarketingUrl(path = "/"): string {
  if (!path || path === "/") {
    return `${CANONICAL_MARKETING_SITE_URL}/`;
  }
  return `${CANONICAL_MARKETING_SITE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

export type MarketingMetadataOptions = {
  path?: string;
  keywords?: string[];
  noIndex?: boolean;
};

export function buildMarketingMetadata(
  title = "POKROV | 5 дней бесплатно без карты",
  description = "Скачайте приложение для Android или Windows, получите 5 дней бесплатно без карты и продолжайте через кабинет.",
  options: MarketingMetadataOptions = {},
): Metadata {
  const canonical = buildMarketingUrl(options.path || "/");
  const shareAlt = `${title} | ${CANONICAL_PLATFORM_BRAND}`;

  return {
    title,
    description,
    keywords: options.keywords,
    category: "technology",
    creator: CANONICAL_PLATFORM_BRAND,
    publisher: CANONICAL_PLATFORM_BRAND,
    alternates: {
      canonical,
    },
    robots: options.noIndex
      ? {
          index: false,
          follow: true,
        }
      : {
          index: true,
          follow: true,
          googleBot: {
            index: true,
            follow: true,
            "max-image-preview": "large",
            "max-snippet": -1,
            "max-video-preview": -1,
          },
        },
    openGraph: {
      type: "website",
      locale: "ru_RU",
      siteName: CANONICAL_PLATFORM_BRAND,
      title,
      description,
      url: canonical,
      images: [
        {
          url: buildMarketingUrl(DEFAULT_MARKETING_SHARE_IMAGE_PATH),
          width: DEFAULT_MARKETING_SHARE_IMAGE_WIDTH,
          height: DEFAULT_MARKETING_SHARE_IMAGE_HEIGHT,
          alt: shareAlt,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [
        {
          url: buildMarketingUrl(DEFAULT_MARKETING_TWITTER_IMAGE_PATH),
          width: DEFAULT_MARKETING_SHARE_IMAGE_WIDTH,
          height: DEFAULT_MARKETING_SHARE_IMAGE_HEIGHT,
          alt: shareAlt,
        },
      ],
    },
  };
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
      "POKROV помогает начать через приложение, получить 5 дней бесплатно без карты и дальше управлять сроком, устройствами и поддержкой.",
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
    about: [
      "Android",
      "Windows",
      "public beta",
      "app-based connection",
      "subscription management",
      "customer support",
    ],
  };
}

function buildOfferCatalogJsonLd() {
  return {
    "@type": "OfferCatalog",
    name: `${CANONICAL_PLATFORM_BRAND} access plans`,
    url: buildMarketingUrl(MARKETING_CANONICAL_PATHS.checkout),
    itemListElement: PUBLIC_TARIFF_PLANS.map((plan, index) => ({
      "@type": "ListItem",
      position: index + 1,
      item: {
        "@type": "Offer",
        name: plan.label,
        price: String(plan.amount_rub || 0),
        priceCurrency: "RUB",
        availability: "https://schema.org/LimitedAvailability",
        url: buildMarketingUrl(MARKETING_CANONICAL_PATHS.checkout),
        description: plan.marketing_note || plan.cabinet_note || plan.label,
        eligibleQuantity: {
          "@type": "QuantitativeValue",
          value: Number(plan.device_limit || 1),
          unitText: "devices",
        },
        eligibleDuration: {
          "@type": "QuantitativeValue",
          value: Number(plan.duration_days || 0),
          unitText: "days",
        },
      },
    })),
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
    dateModified: SEO_LAST_REVIEWED_DATE,
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
      price: String(START_PLAN?.amount_rub || 0),
      priceCurrency: "RUB",
      availability: "https://schema.org/LimitedAvailability",
      description:
        "POKROV install files for Android and Windows are available through official POKROV surfaces; public store and production claims are not included.",
      url: buildMarketingUrl(MARKETING_CANONICAL_PATHS.checkout),
    },
    hasOfferCatalog: buildOfferCatalogJsonLd(),
    downloadUrl: buildMarketingUrl(MARKETING_CANONICAL_PATHS.install),
    mainEntityOfPage: canonicalUrl,
    url: canonicalUrl,
    description:
      "POKROV помогает начать с приложения на Android или Windows, получить 5 дней бесплатно без карты и дальше управлять сроком и устройствами.",
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
