import MarketingHomePage from "../components/home/homepage";
import { buildMarketingMetadata } from "../components/marketing-landing";

export const metadata = buildMarketingMetadata(
  "POKROV | Установка, статус и кабинет рядом",
  "POKROV помогает спокойно начать в приложении, проверить статус доступа и продолжить в кабинете или поддержке без лишнего шума.",
  {
    path: "/",
    keywords: ["pokrov", "android", "windows", "установка pokrov", "статус доступа", "кабинет pokrov", "поддержка pokrov"],
  },
);

export default function HomePage() {
  return <MarketingHomePage />;
}
