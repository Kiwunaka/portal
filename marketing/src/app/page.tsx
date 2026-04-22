import MarketingLanding, { buildMarketingMetadata, type MarketingReview } from "../components/marketing-landing";
import { getPokrovPublicConfig } from "../lib/pokrov";

export const metadata = buildMarketingMetadata(undefined, undefined, {
  path: "/",
  keywords: ["pokrov", "android", "windows", "managed premium", "activation key", "all except ru"],
});

async function loadFeaturedReviews(): Promise<MarketingReview[]> {
  const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);
  const apiBase = (config.apiBaseUrl || "https://api.pokrov.space").replace(/\/+$/, "");

  try {
    const response = await fetch(`${apiBase}/api/reviews`, { cache: "no-store" });
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
        role: item.date ? `TELEGRAM • ${item.date}` : `REVIEW • ${item.rating ? `${item.rating}/5` : "verified"}`,
        text: String(item.text || "").trim(),
        date: item.date,
      }))
      .filter((item) => Boolean(item.text));
  } catch {
    return [];
  }
}

export default async function HomePage() {
  const featuredReviews = await loadFeaturedReviews();

  return <MarketingLanding pagePath="/" featuredReviews={featuredReviews} />;
}
