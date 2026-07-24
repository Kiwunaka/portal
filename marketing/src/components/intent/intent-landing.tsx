import JsonLd from "../json-ld";
import { PageShell } from "../layout/page-shell";
import { Reveal, Stagger } from "../motion/reveal";
import { Accordion } from "../ui/accordion";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { Chip } from "../ui/chip";
import { SectionHeading } from "../ui/section-heading";
import { FinalCta } from "../home/final-cta";
import { Pricing } from "../home/pricing";
import { Steps } from "../home/steps";
import {
  buildBreadcrumbJsonLd,
  buildFaqJsonLd,
  buildSoftwareApplicationJsonLd,
  buildWebPageJsonLd,
  MARKETING_CANONICAL_PATHS,
} from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND, getCopyText } from "../../lib/pokrov";
import type { SeoPage } from "../../lib/seo-pages";

export type IntentScenarioCard = {
  desc: string;
  eyebrow: string;
  title: string;
};

export type IntentRelatedLink = {
  href: string;
  label: string;
};

export type IntentLandingProps = {
  breadcrumbName: string;
  heroKicker: string;
  heroSubtitle: string;
  heroTitle: string;
  pagePath: string;
  related?: IntentRelatedLink[];
  scenarioBody: string;
  scenarioCards: IntentScenarioCard[];
  scenarioTitle: string;
  seoPage?: SeoPage;
};

const DEFAULT_RELATED: IntentRelatedLink[] = [
  { href: MARKETING_CANONICAL_PATHS.youtube, label: "YouTube" },
  { href: MARKETING_CANONICAL_PATHS.tiktok, label: "TikTok" },
  { href: MARKETING_CANONICAL_PATHS.mobile, label: "На телефон" },
  { href: MARKETING_CANONICAL_PATHS.devices, label: "Устройства" },
  { href: MARKETING_CANONICAL_PATHS.telegram, label: "Telegram-бонус" },
  { href: MARKETING_CANONICAL_PATHS.vpn, label: "VPN-приложение" },
];

export function IntentLanding({
  breadcrumbName,
  heroKicker,
  heroSubtitle,
  heroTitle,
  pagePath,
  related,
  scenarioBody,
  scenarioCards,
  scenarioTitle,
  seoPage,
}: IntentLandingProps) {
  const relatedLinks = (related ?? seoPage?.related ?? DEFAULT_RELATED).filter((link) => link.href !== pagePath);
  const faqItems = seoPage?.faq.map((item) => ({ answer: item.answer, question: item.question })) || [];

  return (
    <PageShell>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: MARKETING_CANONICAL_PATHS.home },
          { name: breadcrumbName, path: pagePath },
        ])}
      />
      <JsonLd data={buildSoftwareApplicationJsonLd({ pagePath })} />
      {seoPage ? <JsonLd data={buildWebPageJsonLd(seoPage)} /> : null}
      {faqItems.length ? <JsonLd data={buildFaqJsonLd(faqItems)} /> : null}

      <section className="mx-auto flex max-w-3xl flex-col items-center gap-6 px-4 pt-12 pb-12 text-center sm:px-6 sm:pt-16">
        <Chip>
          <span className="size-1.5 rounded-full bg-status-green" />
          {heroKicker}
        </Chip>
        <h1 className="font-display text-[2.25rem] leading-[1.1] font-extrabold tracking-[-0.01em] text-ink sm:text-[2.75rem]">
          {heroTitle}
        </h1>
        <p className="max-w-xl text-lg leading-relaxed text-ink-soft">{heroSubtitle}</p>
        {seoPage?.answer ? (
          <p className="max-w-2xl rounded-(--radius-card) border border-line bg-surface px-5 py-4 text-[0.9375rem] leading-relaxed text-ink-soft shadow-soft">
            {seoPage.answer}
          </p>
        ) : null}
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Button href={MARKETING_CANONICAL_PATHS.install} size="lg">
            {getCopyText("marketing.intent.cta.primary", "Попробовать бесплатно")}
          </Button>
          <Button href="/#pricing" size="lg" variant="secondary">
            {getCopyText("marketing.intent.cta.secondary", "Тарифы от 99 ₽")}
          </Button>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-16 sm:px-6 sm:pb-20">
        <Reveal>
          <SectionHeading title={scenarioTitle} sub={scenarioBody} />
        </Reveal>
        <div className="grid gap-4 md:grid-cols-3">
          <Stagger>
            {scenarioCards.map((card) => (
              <Card key={card.title} hover className="flex h-full flex-col gap-2.5">
                <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">
                  {card.eyebrow}
                </span>
                <h3 className="text-[1.0625rem] font-semibold text-ink">{card.title}</h3>
                <p className="text-[0.9375rem] leading-relaxed text-ink-soft">{card.desc}</p>
              </Card>
            ))}
          </Stagger>
        </div>
      </section>

      <Steps />
      <Pricing />

      {faqItems.length ? (
        <section className="border-t border-line bg-canvas-alt">
          <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 sm:py-20">
            <Reveal>
              <SectionHeading kicker="FAQ" title="Короткие ответы" />
            </Reveal>
            <Reveal>
              <Accordion items={faqItems} />
            </Reveal>
          </div>
        </section>
      ) : null}

      {relatedLinks.length ? (
        <section className="mx-auto max-w-6xl px-4 pb-16 sm:px-6">
          <Reveal className="flex flex-col items-center gap-5">
            <h2 className="text-[1.125rem] font-semibold text-ink">
              {getCopyText("marketing.intent.related.title", "Похожие задачи")}
            </h2>
            <div className="flex flex-wrap justify-center gap-2.5">
              {relatedLinks.map((link) => (
                <Button key={link.href} href={link.href} variant="secondary">
                  {link.label}
                </Button>
              ))}
            </div>
          </Reveal>
        </section>
      ) : null}

      <FinalCta />
    </PageShell>
  );
}
