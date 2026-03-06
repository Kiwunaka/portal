export type PortalPublicConfig = {
  apiBaseUrl: string;
  webappUrl: string;
  checkoutUrl: string;
  botUrl: string;
  helpbotUrl: string;
  supportTelegramUrl: string;
  contactEmail: string;
  enterpriseEmail: string;
  contactFormUrl: string;
  newsChannelUrl: string;
  androidPlayUrl: string;
  androidApkUrl: string;
  androidMirrorUrl: string;
  windowsExeUrl: string;
  windowsMirrorUrl: string;
  docsUrl: string;
};

export const PLAN_ALIAS_TO_CODE = {
  start: "start_99",
  pro: "1_month",
  ultra: "12_months",
} as const;

export type PlanAlias = keyof typeof PLAN_ALIAS_TO_CODE;
export type PlanCode = (typeof PLAN_ALIAS_TO_CODE)[PlanAlias] | "3_months" | "6_months" | "9_months";

type CatalogItem = {
  ru: string;
};

const COPY: Record<string, CatalogItem> = {
  "webapp.entry.title": { ru: "Вход в кабинет PORTAL" },
  "webapp.entry.subtitle": { ru: "В Telegram вход происходит автоматически. В браузере можно быстро продолжить через Telegram без ручной настройки." },
  "webapp.dashboard.primary_cta": { ru: "Открыть оплату" },
  "webapp.dashboard.support_cta": { ru: "Поддержка" },
  "webapp.subscription.title": { ru: "Управление доступом" },
  "webapp.subscription.subtitle": { ru: "Сравните планы, проверьте лимиты и продлите доступ без лишних шагов." },
  "webapp.checkout.title": { ru: "Оплата и продление" },
  "webapp.checkout.subtitle": { ru: "Сумма и скидка видны до перехода на страницу оплаты. Если вход не привязан, можно быстро продолжить через Telegram." },
  "webapp.support.title": { ru: "Поддержка PORTAL" },
  "webapp.support.subtitle": { ru: "Быстрые ответы, обращения в один шаг и вся история общения в одном разделе." },
  "webapp.support.empty_tickets": { ru: "Обращений пока нет. Создайте первое сообщение, если нужна помощь." },
  "webapp.devices.title": { ru: "Сессии и точки подключения" },
  "webapp.devices.subtitle": { ru: "Здесь видны текущие лимиты, активные сессии и доступные точки подключения по вашему плану." },
  "webapp.statistics.title": { ru: "Сводка по использованию" },
  "webapp.statistics.subtitle": { ru: "Показываем только те данные, которые уже есть в системе: срок доступа, лимиты, трафик и состояние точек подключения." },
  "webapp.downloads.title": { ru: "Приложения и быстрый запуск" },
  "webapp.downloads.subtitle": { ru: "Показываем только актуальные ссылки, которые уже настроены в системе для Android, Windows и справки." },
};

function trim(value: string | undefined, fallback = ""): string {
  return String(value || fallback).trim();
}

function cleanUrl(value: string, fallback = ""): string {
  return trim(value, fallback).replace(/\/+$/, "");
}

export function normalizeTelegramUrl(raw: string, fallback: string): string {
  const value = cleanUrl(raw, fallback);
  if (!value) return fallback;
  if (value.startsWith("http://") || value.startsWith("https://")) return value;
  return `https://t.me/${value.replace(/^@+/, "")}`;
}

export function normalizeCheckoutUrl(raw: string, webDomainFallback = "https://portal-privacy.online"): string {
  const value = cleanUrl(raw);
  if (!value) return `${cleanUrl(webDomainFallback)}/checkout`;
  return value;
}

export function normalizePlanCode(raw: string | null | undefined, fallback: PlanCode = "1_month"): PlanCode {
  const normalized = String(raw || "").trim().toLowerCase();
  if (!normalized) return fallback;
  if (normalized in PLAN_ALIAS_TO_CODE) {
    return PLAN_ALIAS_TO_CODE[normalized as PlanAlias];
  }
  if (["start_99", "1_month", "3_months", "6_months", "9_months", "12_months"].includes(normalized)) {
    return normalized as PlanCode;
  }
  return fallback;
}

export function getPortalPublicConfig(env: Record<string, string | undefined>): PortalPublicConfig {
  const apiBaseUrl = cleanUrl(
    env.NEXT_PUBLIC_API_BASE_URL ||
      env.NEXT_PUBLIC_PUBLIC_API_BASE_URL ||
      env.VITE_PUBLIC_API_BASE_URL ||
      "https://portal-privacy.online",
  );
  const webappUrl = cleanUrl(env.NEXT_PUBLIC_WEBAPP_URL || "https://portal-privacy.online/webapp");
  const botUrl = normalizeTelegramUrl(env.NEXT_PUBLIC_TELEGRAM_BOT_URL || "", "https://t.me/portal_privacy_bot");
  const helpbotUrl = normalizeTelegramUrl(
    env.NEXT_PUBLIC_CONTACT_TG_URL || env.NEXT_PUBLIC_SUPPORT_TG_URL || "",
    "https://t.me/portal_privacy_helpbot",
  );
  const contactFormUrl = normalizeTelegramUrl(env.NEXT_PUBLIC_CONTACT_FORM_URL || "", helpbotUrl);
  const checkoutUrl = normalizeCheckoutUrl(
    env.NEXT_PUBLIC_CHECKOUT_PAGE_URL || env.NEXT_PUBLIC_PAY_CHECKOUT_URL || env.PAY_CHECKOUT_URL || "",
    "https://portal-privacy.online",
  );
  return {
    apiBaseUrl,
    webappUrl,
    checkoutUrl,
    botUrl,
    helpbotUrl,
    supportTelegramUrl: helpbotUrl,
    contactEmail: trim(env.NEXT_PUBLIC_CONTACT_EMAIL, "support@portal-privacy.online"),
    enterpriseEmail: trim(env.NEXT_PUBLIC_ENTERPRISE_EMAIL, "enterprise@portal-privacy.online"),
    contactFormUrl,
    newsChannelUrl: normalizeTelegramUrl(
      env.NEXT_PUBLIC_TG_CHANNEL_LINK || env.NEXT_PUBLIC_NEWS_CHANNEL || "",
      "https://t.me/portal_privacy",
    ),
    androidPlayUrl: trim(env.NEXT_PUBLIC_APP_ANDROID_PLAY_URL),
    androidApkUrl: trim(env.NEXT_PUBLIC_APP_ANDROID_APK_URL),
    androidMirrorUrl: trim(env.NEXT_PUBLIC_APP_ANDROID_MIRROR_URL),
    windowsExeUrl: trim(env.NEXT_PUBLIC_APP_WINDOWS_EXE_URL),
    windowsMirrorUrl: trim(env.NEXT_PUBLIC_APP_WINDOWS_MIRROR_URL),
    docsUrl: trim(env.NEXT_PUBLIC_APP_DOCS_URL),
  };
}

export function getCatalogItem(key: string): CatalogItem | null {
  return COPY[key] || null;
}

export function getCopyText(
  key: string,
  fallback = "",
  variables?: Record<string, string | number | null | undefined>,
): string {
  const base = COPY[key]?.ru || fallback;
  if (!variables || !base) return base;
  return base.replace(/\{([a-zA-Z0-9_]+)\}/g, (_match, name: string) => {
    const value = variables[name];
    return value == null ? "" : String(value);
  });
}

export function getCopyCatalogVersion(): string {
  return "2026-03-06";
}
