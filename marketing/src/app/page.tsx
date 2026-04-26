import MarketingHomePage from "../components/home/homepage";
import { buildMarketingMetadata } from "../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "POKROV | Спокойный старт, понятная оплата и кабинет рядом",
  "POKROV помогает сначала спокойно попробовать сервис в приложении, а потом без лишнего шума перейти к оплате, кабинету и поддержке.",
  {
    path: "/",
    keywords: ["pokrov", "android", "windows", "оплата pokrov", "кабинет pokrov", "поддержка pokrov"],
  },
);

export default function HomePage() {
  return <MarketingHomePage />;
}
