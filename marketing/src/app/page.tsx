import MarketingHomePage from "../components/home/homepage";
import { buildMarketingMetadata } from "../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "POKROV — приложение для доступа к сайтам | Android и Windows",
  "Скачайте POKROV для Android или Windows: 5 дней бесплатно без карты, продление от 99 ₽ за 30 дней, до 5 устройств и поддержка в Telegram.",
  {
    path: "/",
    keywords: [
      "pokrov",
      "доступ к сайтам",
      "приложение для подключения",
      "android",
      "windows",
      "5 дней бесплатно",
      "кабинет pokrov",
      "поддержка pokrov",
    ],
  },
);

export default function HomePage() {
  return <MarketingHomePage />;
}
