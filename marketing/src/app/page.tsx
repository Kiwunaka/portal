import MarketingLanding, { buildMarketingMetadata, type MarketingReview } from "../components/marketing-landing";
import { getPokrovPublicConfig } from "../lib/pokrov";

export const metadata = buildMarketingMetadata();

async function loadFeaturedReviews(): Promise<MarketingReview[]> {
  const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);
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
  return <MarketingLanding featuredReviews={featuredReviews} />;
}
