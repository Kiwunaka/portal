import { Faq } from "../components/home/faq";
import { FinalCta } from "../components/home/final-cta";
import { Hero } from "../components/home/hero";
import { HonestyStrip } from "../components/home/honesty-strip";
import { Pricing } from "../components/home/pricing";
import { ServicesGrid } from "../components/home/services-grid";
import { Showcase } from "../components/home/showcase";
import { Steps } from "../components/home/steps";
import { TelegramBonus } from "../components/home/telegram-bonus";
import JsonLd from "../components/json-ld";
import { PageShell } from "../components/layout/page-shell";
import {
  buildFaqJsonLd,
  buildMarketingMetadata,
  buildSoftwareApplicationJsonLd,
  MARKETING_FAQ,
} from "../lib/marketing-site";

export const metadata = buildMarketingMetadata(
  "POKROV открывает YouTube, TikTok и другие сервисы | Android и Windows",
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
  return (
    <PageShell>
      <JsonLd data={buildSoftwareApplicationJsonLd({ pagePath: "/" })} />
      <JsonLd data={buildFaqJsonLd(MARKETING_FAQ)} />
      <Hero />
      <HonestyStrip />
      <ServicesGrid />
      <Steps />
      <Showcase />
      <Pricing />
      <TelegramBonus />
      <Faq />
      <FinalCta />
    </PageShell>
  );
}
