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
  buildTrustLinksJsonLd,
  MARKETING_FAQ,
} from "../lib/marketing-site";

export const metadata = buildMarketingMetadata(
  "POKROV VPN для Android и Windows — 5 дней бесплатно",
  "Быстрый VPN для YouTube, TikTok, ChatGPT и сайтов. 5 дней бесплатно без карты, затем безлимитный трафик от 99 ₽.",
  {
    path: "/",
  },
);

export default function HomePage() {
  return (
    <PageShell>
      <JsonLd data={buildSoftwareApplicationJsonLd({ pagePath: "/" })} />
      <JsonLd data={buildFaqJsonLd(MARKETING_FAQ)} />
      <JsonLd data={buildTrustLinksJsonLd()} />
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
