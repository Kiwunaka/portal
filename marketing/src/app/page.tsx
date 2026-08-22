import { Faq } from "../components/home/faq";
import { FinalCta } from "../components/home/final-cta";
import { Hero } from "../components/home/hero";
import { HonestyStrip } from "../components/home/honesty-strip";
import { Pricing } from "../components/home/pricing";
import { Showcase } from "../components/home/showcase";
import { Steps } from "../components/home/steps";
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
  "POKROV для Android и Windows — проверьте до оплаты",
  "Установите POKROV на Android или Windows и проверьте подключение: 5 дней бесплатно без карты. Первый полный месяц — 99 ₽ один раз, автосписаний нет.",
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
      <Steps />
      <Showcase />
      <Pricing />
      <Faq />
      <FinalCta />
    </PageShell>
  );
}
