import JsonLd from "../json-ld";
import { FinalCta } from "../home/final-cta";
import { PageShell } from "../layout/page-shell";
import { Reveal, Stagger } from "../motion/reveal";
import { Accordion } from "../ui/accordion";
import { Button } from "../ui/button";
import { Card } from "../ui/card";
import { Chip } from "../ui/chip";
import { SectionHeading } from "../ui/section-heading";
import {
  buildBreadcrumbJsonLd,
  buildFaqJsonLd,
  buildHowToJsonLd,
  buildItemListJsonLd,
  buildWebPageJsonLd,
  MARKETING_CANONICAL_PATHS,
} from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";
import type { SeoLink, SeoPage } from "../../lib/seo-pages";

function SeoButton({ link, variant = "primary" }: { link: SeoLink; variant?: "primary" | "secondary" | "ghost" }) {
  return (
    <Button
      href={link.href}
      size="lg"
      target={link.external ? "_blank" : undefined}
      rel={link.external ? "noreferrer" : undefined}
      variant={variant}
    >
      {link.label}
    </Button>
  );
}

export function SeoContentPage({ page }: { page: SeoPage }) {
  const faqItems = page.faq.map((item) => ({
    answer: item.answer,
    question: item.question,
  }));
  const compactSupportItems = page.cluster === "support"
    ? [
        ...page.sections.map((section) => ({
          question: section.title,
          answer: [section.body, ...(section.bullets || [])].join(" "),
        })),
        ...(page.steps?.length
          ? [{
              question: "Что делать по порядку?",
              answer: page.steps.map((step, index) => `${index + 1}. ${step.name}: ${step.text}`).join(" "),
            }]
          : []),
      ]
    : [];

  return (
    <PageShell>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: MARKETING_CANONICAL_PATHS.home },
          { name: page.breadcrumbName, path: page.path },
        ])}
      />
      <JsonLd data={buildWebPageJsonLd(page)} />
      {page.faq.length ? <JsonLd data={buildFaqJsonLd(faqItems)} /> : null}
      {page.steps?.length ? <JsonLd data={buildHowToJsonLd(page)} /> : null}
      {page.comparisonRows?.length ? <JsonLd data={buildItemListJsonLd(page)} /> : null}

      <section className="mx-auto flex max-w-3xl flex-col items-center gap-6 px-4 pt-12 pb-12 text-center sm:px-6 sm:pt-16">
        <Chip>
          <span className="size-1.5 rounded-full bg-status-green" />
          {page.heroKicker}
        </Chip>
        <h1 className="font-display text-[2.25rem] leading-[1.1] font-extrabold tracking-[-0.01em] text-ink sm:text-[2.75rem]">
          {page.h1}
        </h1>
        <p className="max-w-2xl text-lg leading-relaxed text-ink-soft">{page.answer}</p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          {page.primaryCta ? <SeoButton link={page.primaryCta} /> : null}
          {page.secondaryCta ? <SeoButton link={page.secondaryCta} variant="secondary" /> : null}
        </div>
      </section>

      {page.cards.length ? (
        <section className="mx-auto max-w-6xl px-4 pb-16 sm:px-6">
          <div className="grid gap-4 md:grid-cols-3">
            <Stagger>
              {page.cards.map((card) => (
                <Card key={card.title} hover className="flex h-full flex-col gap-2.5">
                  <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">
                    {card.eyebrow}
                  </span>
                  <h2 className="text-[1.0625rem] font-semibold text-ink">{card.title}</h2>
                  <p className="text-[0.9375rem] leading-relaxed text-ink-soft">{card.body}</p>
                </Card>
              ))}
            </Stagger>
          </div>
        </section>
      ) : null}

      {compactSupportItems.length ? (
        <section className="border-t border-line bg-canvas-alt">
          <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6 sm:py-16">
            <Reveal>
              <SectionHeading kicker="По шагам" title="Проверьте основное" sub="Откройте только нужный пункт." />
            </Reveal>
            <Reveal>
              <Accordion items={compactSupportItems} defaultOpenFirst={false} />
            </Reveal>
          </div>
        </section>
      ) : page.sections.length ? (
        <section className="border-t border-line bg-canvas-alt">
          <div className="mx-auto grid max-w-6xl gap-8 px-4 py-16 sm:px-6 sm:py-20 lg:grid-cols-[0.95fr_1.35fr]">
            <Reveal>
              <SectionHeading
                kicker="Преимущества"
                title="Что важно знать перед установкой"
                sub="Факты о первом запуске, бесплатной проверке, официальных файлах и продлении."
              />
            </Reveal>
            <Reveal className="flex flex-col gap-5">
              {page.sections.map((section) => (
                <Card key={section.title} className="flex flex-col gap-3">
                  <h2 className="text-[1.125rem] font-semibold text-ink">{section.title}</h2>
                  <p className="text-[0.9375rem] leading-relaxed text-ink-soft">{section.body}</p>
                  {section.bullets?.length ? (
                    <ul className="m-0 flex list-none flex-col gap-2 p-0">
                      {section.bullets.map((bullet) => (
                        <li key={bullet} className="flex gap-2 text-[0.9375rem] leading-relaxed text-ink-soft">
                          <span className="mt-2 size-1.5 shrink-0 rounded-full bg-brand" />
                          <span>{bullet}</span>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </Card>
              ))}
            </Reveal>
          </div>
        </section>
      ) : null}

      {page.steps?.length && !compactSupportItems.length ? (
        <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
          <Reveal>
            <SectionHeading title="Порядок действий" sub="Сначала файл из официального источника, потом запуск и проверка." />
          </Reveal>
          <div className="grid gap-4 md:grid-cols-4">
            <Stagger>
              {page.steps.map((step, index) => (
                <Card key={step.name} className="flex h-full flex-col gap-2.5">
                  <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">
                    Шаг {index + 1}
                  </span>
                  <h2 className="text-[1.0625rem] font-semibold text-ink">{step.name}</h2>
                  <p className="text-[0.9375rem] leading-relaxed text-ink-soft">{step.text}</p>
                </Card>
              ))}
            </Stagger>
          </div>
        </section>
      ) : null}

      {page.comparisonRows?.length ? (
        <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 sm:py-20">
          <Reveal>
            <SectionHeading
              title="Сравнение по проверяемым критериям"
              sub="Источник файлов, бесплатный старт, оплата и поддержка — всё, что стоит проверить до установки."
            />
          </Reveal>
          <div className="overflow-hidden rounded-(--radius-card) border border-line bg-surface shadow-soft">
            <div className="grid grid-cols-[1fr_1fr_1fr] border-b border-line bg-canvas-alt text-[0.8125rem] font-semibold tracking-[0.08em] text-ink-soft uppercase">
              <div className="p-4">Критерий</div>
              <div className="border-l border-line p-4">Типичный бесплатный VPN</div>
              <div className="border-l border-line p-4">POKROV</div>
            </div>
            {page.comparisonRows.map((row) => (
              <div key={row.criterion} className="grid grid-cols-[1fr_1fr_1fr] border-b border-line last:border-b-0">
                <div className="p-4 text-[0.9375rem] font-semibold text-ink">{row.criterion}</div>
                <div className="border-l border-line p-4 text-[0.9375rem] leading-relaxed text-ink-soft">{row.freeVpn}</div>
                <div className="border-l border-line p-4 text-[0.9375rem] leading-relaxed text-ink-soft">{row.pokrov}</div>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {page.faq.length ? (
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

      {page.related.length ? (
        <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
          <Reveal className="flex flex-col items-center gap-5">
            <h2 className="text-[1.125rem] font-semibold text-ink">Связанные страницы</h2>
            <div className="flex flex-wrap justify-center gap-2.5">
              {page.related
                .filter((link) => link.href !== page.path)
                .map((link) => (
                  <Button
                    key={link.href}
                    href={link.href}
                    target={link.external ? "_blank" : undefined}
                    rel={link.external ? "noreferrer" : undefined}
                    variant="secondary"
                  >
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
