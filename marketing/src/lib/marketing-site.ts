import type { Metadata, MetadataRoute } from "next";

import {
  CANONICAL_BOT_URL,
  CANONICAL_CHECKOUT_URL,
  CANONICAL_CONTACT_EMAIL,
  CANONICAL_GITHUB_RELEASES_URL,
  CANONICAL_MARKETING_SITE_URL,
  CANONICAL_NEWS_CHANNEL_URL,
  CANONICAL_PLATFORM_BRAND,
  CANONICAL_PUBLIC_PLATFORM_SCOPE,
  CANONICAL_SUPPORT_BOT_URL,
  getTariffPlans,
} from "./pokrov";
import {
  SEO_LAST_REVIEWED_DATE,
  SEO_PAGE_PATHS,
  SEO_SITEMAP_ROUTES,
  TELEGRAM_START_PROMISE,
  type SeoPage,
} from "./seo-pages";

export const DEFAULT_MARKETING_SHARE_IMAGE_PATH = "/opengraph-image.png";
export const DEFAULT_MARKETING_TWITTER_IMAGE_PATH = "/twitter-image.png";
export const DEFAULT_MARKETING_SHARE_IMAGE_WIDTH = 1200;
export const DEFAULT_MARKETING_SHARE_IMAGE_HEIGHT = 630;

export const MARKETING_CANONICAL_PATHS = {
  home: "/",
  android: SEO_PAGE_PATHS.android,
  windows: SEO_PAGE_PATHS.windows,
  mobile: "/mobile/",
  tiktok: "/tiktok/",
  youtube: "/youtube/",
  devices: "/devices/",
  telegram: "/telegram/",
  vpn: "/vpn/",
  bestVpn: SEO_PAGE_PATHS.bestVpn,
  installAndroid: SEO_PAGE_PATHS.installAndroid,
  installWindows: SEO_PAGE_PATHS.installWindows,
  trialNoCard: SEO_PAGE_PATHS.trialNoCard,
  billingNoAutopay: SEO_PAGE_PATHS.billingNoAutopay,
  trustGithubReleases: SEO_PAGE_PATHS.trustGithubReleases,
  compareFreeVpn: SEO_PAGE_PATHS.compareFreeVpn,
  supportInstall: SEO_PAGE_PATHS.supportInstall,
  checkout: "/checkout/",
  install: "/install/",
  offer: "/offer/",
  privacy: "/privacy/",
  transparency: "/transparency/",
  status: "/status/",
  guides: "/guides/",
  guidesPokrovApp: "/guides/pokrov-app/",
  fallback: "/fallback/",
  programs: "/programs/",
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

export const PAID_REWARDS_MARKETING_ENABLED = process.env.NEXT_PUBLIC_PAID_REWARDS_MARKETING_ENABLED === "1";

export const PAID_REWARDS_MARKETING_COPY =
  "Для активной платной подписки доступно колесо бонусов раз в 14 дней. В нём есть скидки, бонусные дни и редкий джекпот +30 дней; календарь пока отключён.";

export const MARKETING_FEATURE_LIST = [
  "Доступ к привычным сервисам на Android и Windows",
  "5 дней за 0 ₽ без банковской карты",
  "Безлимитный трафик на платных тарифах",
  "YouTube, TikTok, ChatGPT и другие сервисы одной кнопкой",
  "Первый полный месяц от 99 ₽",
  "До 5 устройств в одном платном аккаунте",
  TELEGRAM_START_PROMISE,
  ...(PAID_REWARDS_MARKETING_ENABLED ? [PAID_REWARDS_MARKETING_COPY] : []),
] as const;

export type MarketingRouteConfig = {
  path: string;
  changeFrequency: NonNullable<MetadataRoute.Sitemap[number]["changeFrequency"]>;
  lastReviewed: string;
  priority: number;
};

export const MARKETING_SITEMAP_ROUTES: MarketingRouteConfig[] = [
  { path: MARKETING_CANONICAL_PATHS.home, changeFrequency: "weekly", lastReviewed: SEO_LAST_REVIEWED_DATE, priority: 1 },
  ...SEO_SITEMAP_ROUTES,
  {
    path: MARKETING_CANONICAL_PATHS.checkout,
    changeFrequency: "weekly",
    lastReviewed: SEO_LAST_REVIEWED_DATE,
    priority: 0.76,
  },
  {
    path: MARKETING_MACHINE_READABLE_PATHS.pricing,
    changeFrequency: "weekly",
    lastReviewed: SEO_LAST_REVIEWED_DATE,
    priority: 0.64,
  },
  {
    path: MARKETING_MACHINE_READABLE_PATHS.llms,
    changeFrequency: "weekly",
    lastReviewed: SEO_LAST_REVIEWED_DATE,
    priority: 0.58,
  },
  {
    path: MARKETING_CANONICAL_PATHS.offer,
    changeFrequency: "monthly",
    lastReviewed: SEO_LAST_REVIEWED_DATE,
    priority: 0.36,
  },
  {
    path: MARKETING_CANONICAL_PATHS.privacy,
    changeFrequency: "monthly",
    lastReviewed: SEO_LAST_REVIEWED_DATE,
    priority: 0.34,
  },
  {
    path: MARKETING_CANONICAL_PATHS.transparency,
    changeFrequency: "monthly",
    lastReviewed: SEO_LAST_REVIEWED_DATE,
    priority: 0.48,
  },
  {
    path: MARKETING_CANONICAL_PATHS.status,
    changeFrequency: "always",
    lastReviewed: SEO_LAST_REVIEWED_DATE,
    priority: 0.62,
  },
  {
    path: MARKETING_CANONICAL_PATHS.guides,
    changeFrequency: "weekly",
    lastReviewed: SEO_LAST_REVIEWED_DATE,
    priority: 0.68,
  },
  {
    path: MARKETING_CANONICAL_PATHS.guidesPokrovApp,
    changeFrequency: "weekly",
    lastReviewed: SEO_LAST_REVIEWED_DATE,
    priority: 0.66,
  },
  {
    path: MARKETING_CANONICAL_PATHS.fallback,
    changeFrequency: "monthly",
    lastReviewed: SEO_LAST_REVIEWED_DATE,
    priority: 0.46,
  },
  {
    path: MARKETING_CANONICAL_PATHS.programs,
    changeFrequency: "monthly",
    lastReviewed: SEO_LAST_REVIEWED_DATE,
    priority: 0.52,
  },
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
      "Заберите 5 дней бесплатно: скачайте POKROV для Android или Windows, войдите и нажмите «Подключить». Карта не нужна.",
  },
  {
    question: "Что будет после бесплатных 5 дней?",
    answer:
      "Если POKROV подходит, выберите приветственный месяц за 99 ₽ или более выгодный срок. Без оплаты доступ остановится; цена и лимит устройств видны заранее.",
  },
  {
    question: "Нужно ли настраивать профили вручную?",
    answer:
      "Нет. POKROV берёт настройку на себя: установите приложение, войдите и нажмите одну кнопку. Ручные режимы нужны только как запасной путь.",
  },
  {
    question: "Как устроено продление?",
    answer:
      "Выберите срок, оплатите один раз и продолжайте в том же аккаунте POKROV. Автосписаний нет; код активации применяется в приложении или кабинете.",
  },
  {
    question: "Нужен ли Telegram для старта?",
    answer: TELEGRAM_START_PROMISE,
  },
  {
    question: "Что видит провайдер и что хранит POKROV?",
    answer:
      "Провайдер видит зашифрованное соединение, а не то, какие сайты и видео вы открываете. POKROV хранит только нужное для работы аккаунта: идентификатор, срок доступа, технические события и статусы платежей. Карточные данные на стороне POKROV не хранятся, персональные данные не продаются. Подробнее — в политике конфиденциальности.",
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
  noIndex?: boolean;
};

export function buildMarketingMetadata(
  title = "POKROV VPN для Android и Windows — 5 дней бесплатно",
  description = "Быстрый VPN для YouTube, TikTok, ChatGPT и сайтов. 5 дней бесплатно без карты, затем безлимитный трафик от 99 ₽.",
  options: MarketingMetadataOptions = {},
): Metadata {
  const canonical = buildMarketingUrl(options.path || "/");
  const shareAlt = `${title} | ${CANONICAL_PLATFORM_BRAND}`;

  return {
    title,
    description,
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
    lastModified: new Date(route.lastReviewed),
    changeFrequency: route.changeFrequency,
    priority: route.priority,
  }));
}

export function buildOrganizationJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    "@id": `${CANONICAL_MARKETING_SITE_URL}/#organization`,
    name: CANONICAL_PLATFORM_BRAND,
    url: `${CANONICAL_MARKETING_SITE_URL}/`,
    logo: buildMarketingUrl("/pokrov-logo.svg"),
    description:
      "POKROV — VPN для быстрого старта на Android и Windows: 5 дней за 0 ₽ без карты, одна кнопка подключения и тарифы от 99 ₽.",
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
    "@id": `${CANONICAL_MARKETING_SITE_URL}/#website`,
    name: CANONICAL_PLATFORM_BRAND,
    url: `${CANONICAL_MARKETING_SITE_URL}/`,
    inLanguage: "ru-RU",
    publisher: {
      "@type": "Organization",
      "@id": `${CANONICAL_MARKETING_SITE_URL}/#organization`,
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

export function buildOfferCatalogJsonLd() {
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
      "@id": `${CANONICAL_MARKETING_SITE_URL}/#organization`,
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
      "POKROV — лучший VPN для простого старта на Android и Windows: 5 дней бесплатно, одна кнопка подключения и до 5 устройств на основных тарифах.",
  };
}

export function buildWebPageJsonLd(page: SeoPage) {
  const url = buildMarketingUrl(page.path);
  return {
    "@context": "https://schema.org",
    "@type": "WebPage",
    "@id": `${url}#webpage`,
    name: page.h1,
    headline: page.h1,
    description: page.description,
    url,
    inLanguage: "ru-RU",
    dateModified: page.lastReviewed,
    isPartOf: {
      "@type": "WebSite",
      "@id": `${CANONICAL_MARKETING_SITE_URL}/#website`,
      name: CANONICAL_PLATFORM_BRAND,
    },
    publisher: {
      "@type": "Organization",
      "@id": `${CANONICAL_MARKETING_SITE_URL}/#organization`,
      name: CANONICAL_PLATFORM_BRAND,
    },
    primaryImageOfPage: {
      "@type": "ImageObject",
      url: buildMarketingUrl(DEFAULT_MARKETING_SHARE_IMAGE_PATH),
    },
    about: [page.cluster, CANONICAL_PLATFORM_BRAND, "Android", "Windows"],
  };
}

export function buildHowToJsonLd(page: SeoPage) {
  return {
    "@context": "https://schema.org",
    "@type": "HowTo",
    "@id": `${buildMarketingUrl(page.path)}#howto`,
    name: page.h1,
    description: page.answer,
    inLanguage: "ru-RU",
    dateModified: page.lastReviewed,
    step: (page.steps || []).map((step, index) => ({
      "@type": "HowToStep",
      position: index + 1,
      name: step.name,
      text: step.text,
      url: buildMarketingUrl(page.path),
    })),
    publisher: {
      "@type": "Organization",
      "@id": `${CANONICAL_MARKETING_SITE_URL}/#organization`,
      name: CANONICAL_PLATFORM_BRAND,
    },
  };
}

export function buildItemListJsonLd(page: SeoPage) {
  return {
    "@context": "https://schema.org",
    "@type": "ItemList",
    "@id": `${buildMarketingUrl(page.path)}#criteria`,
    name: `${page.h1}: критерии`,
    itemListElement: (page.comparisonRows || []).map((row, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: row.criterion,
      description: `${row.criterion}: ${row.pokrov}`,
    })),
  };
}

export function buildCheckoutServiceJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "Service",
    "@id": `${buildMarketingUrl(MARKETING_CANONICAL_PATHS.checkout)}#service`,
    name: `${CANONICAL_PLATFORM_BRAND} access plans`,
    serviceType: "VPN application access",
    url: buildMarketingUrl(MARKETING_CANONICAL_PATHS.checkout),
    description:
      "POKROV offers paid access periods after the free Android and Windows app trial. Public checkout shows price, duration and device limit before payment.",
    provider: {
      "@type": "Organization",
      "@id": `${CANONICAL_MARKETING_SITE_URL}/#organization`,
      name: CANONICAL_PLATFORM_BRAND,
    },
    hasOfferCatalog: buildOfferCatalogJsonLd(),
  };
}

export function buildTrustLinksJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "ItemList",
    "@id": `${CANONICAL_MARKETING_SITE_URL}/#public-sources`,
    name: `${CANONICAL_PLATFORM_BRAND} public sources`,
    itemListElement: [
      {
        "@type": "ListItem",
        position: 1,
        name: "GitHub Releases",
        url: CANONICAL_GITHUB_RELEASES_URL,
      },
      {
        "@type": "ListItem",
        position: 2,
        name: "Support bot",
        url: CANONICAL_SUPPORT_BOT_URL,
      },
    ],
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
