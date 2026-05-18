import MarketingHomePage from "../components/home/homepage";
import { buildMarketingMetadata } from "../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "POKROV | 5 дней бесплатно для Android и Windows",
  "Поставьте POKROV, включите доступ в приложении и проверьте свои сервисы 5 дней бесплатно. Продление, устройства и поддержка — в кабинете.",
  {
    path: "/",
    keywords: ["pokrov", "android", "windows", "оплата pokrov", "кабинет pokrov", "поддержка pokrov"],
  },
);

export default function HomePage() {
  return <MarketingHomePage />;
}
