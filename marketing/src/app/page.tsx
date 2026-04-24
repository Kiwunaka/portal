import MarketingHomePage from "../components/home/homepage";
import { buildMarketingMetadata } from "../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "POKROV | Попробовать 5 дней",
  "Начните с приложения POKROV, проверьте сервис 5 дней бесплатно и продолжайте через кабинет, тарифы и поддержку без лишней сложности.",
  {
    path: "/",
    keywords: ["pokrov", "android", "windows", "попробовать pokrov", "кабинет pokrov", "поддержка pokrov"],
  },
);

export default function HomePage() {
  return <MarketingHomePage />;
}
