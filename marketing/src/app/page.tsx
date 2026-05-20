import MarketingHomePage from "../components/home/homepage";
import { buildMarketingMetadata } from "../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "POKROV для YouTube, TikTok и нужных вам сайтов | Android и Windows",
  "Скачайте POKROV на Android или Windows, попробуйте 5 дней без карты и продлите доступ от 99 ₽ за 30 дней.",
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
