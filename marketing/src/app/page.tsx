import MarketingLanding, { buildMarketingMetadata, type MarketingReview } from "../components/marketing-landing";
import { getPortalPublicConfig } from "../lib/portal";

export const metadata = buildMarketingMetadata(
  "POKROV VPN | Свободный интернет без лишней суеты",
  "Запуск через Telegram, тест на 5 дней, кабинет, поддержка и продление без сложной настройки и лишних шагов.",
);

async function loadFeaturedReviews(): Promise<MarketingReview[]> {
  const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);
  const apiBase = (config.apiBaseUrl || "https://api.pokrov.space").replace(/\/+$/, "");

  try {
    const response = await fetch(`${apiBase}/api/reviews`);
    if (!response.ok) return [];

    const data = (await response.json()) as {
      reviews?: Array<{
        username?: string;
        rating?: number;
        text?: string;
        date?: string;
      }>;
    };

    return (Array.isArray(data.reviews) ? data.reviews : [])
      .filter((item) => Boolean(item?.username || item?.text))
      .slice(0, 3)
      .map((item) => ({
        name: String(item.username || "user").trim() || "user",
        role: item.date ? `Telegram • ${item.date}` : `Telegram • ${item.rating ? `${item.rating}/5` : "отзыв"}`,
        text: String(item.text || "").trim(),
      }))
      .filter((item) => Boolean(item.text));
  } catch {
    return [];
  }
}

export default async function HomePage() {
  const featuredReviews = await loadFeaturedReviews();

  return (
    <MarketingLanding
      heroKicker="POKROV VPN • Telegram • тест 5 дней"
      heroTitle="Свободный интернет без лишней суеты"
      heroSubtitle="Сначала запускаете тест в Telegram, спокойно проверяете сервис на своих задачах, а потом уже решаете, нужен ли платный доступ."
      clusterTitle="Полезные страницы под частые сценарии"
      clusterBody="Мы собрали отдельные страницы под YouTube, TikTok, телефон, разные устройства и Telegram-бота, чтобы быстрее вести человека в понятный маршрут: бот, тест, кабинет и оплата."
      featuredReviews={featuredReviews}
    />
  );
}
