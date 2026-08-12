import Link from "next/link";

import JsonLd from "../../components/json-ld";
import { PageShell } from "../../components/layout/page-shell";
import { Reveal } from "../../components/motion/reveal";
import { Accordion } from "../../components/ui/accordion";
import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { Chip } from "../../components/ui/chip";
import { SectionHeading } from "../../components/ui/section-heading";
import { FinalCta } from "../../components/home/final-cta";
import {
  buildBreadcrumbJsonLd,
  buildFaqJsonLd,
  buildMarketingMetadata,
  buildMarketingUrl,
  buildWebPageJsonLd,
  MARKETING_CANONICAL_PATHS,
} from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND, getPokrovPublicConfig } from "../../lib/pokrov";
import { getSeoPage, SEO_PAGE_PATHS, TELEGRAM_START_PROMISE } from "../../lib/seo-pages";

const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);
const SEO_PAGE = getSeoPage(MARKETING_CANONICAL_PATHS.vpn);

const VPN_FAQ = SEO_PAGE.faq;

function buildArticleJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: SEO_PAGE.h1,
    inLanguage: "ru-RU",
    dateModified: SEO_PAGE.lastReviewed,
    author: {
      "@type": "Organization",
      name: CANONICAL_PLATFORM_BRAND,
    },
    publisher: {
      "@type": "Organization",
      name: CANONICAL_PLATFORM_BRAND,
      logo: {
        "@type": "ImageObject",
        url: buildMarketingUrl("/pokrov-logo.svg"),
      },
    },
    mainEntityOfPage: buildMarketingUrl(MARKETING_CANONICAL_PATHS.vpn),
    description: SEO_PAGE.description,
  };
}

export const metadata = buildMarketingMetadata(
  SEO_PAGE.title,
  SEO_PAGE.description,
  {
    path: MARKETING_CANONICAL_PATHS.vpn,
  },
);

function LongformBlock({ children, title }: { children: React.ReactNode; title: string }) {
  return (
    <div className="flex flex-col gap-3">
      <h2 className="font-display text-[1.375rem] font-bold tracking-[-0.01em] text-ink">{title}</h2>
      {children}
    </div>
  );
}

function P({ children }: { children: React.ReactNode }) {
  return <p className="text-[0.9375rem] leading-relaxed text-ink-soft">{children}</p>;
}

export default function VpnSeoPage() {
  return (
    <PageShell>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: MARKETING_CANONICAL_PATHS.home },
          { name: "VPN для Android и Windows", path: MARKETING_CANONICAL_PATHS.vpn },
        ])}
      />
      <JsonLd data={buildArticleJsonLd()} />
      <JsonLd data={buildWebPageJsonLd(SEO_PAGE)} />
      <JsonLd data={buildFaqJsonLd(VPN_FAQ)} />

      <section className="mx-auto flex max-w-3xl flex-col items-center gap-6 px-4 pt-12 pb-12 text-center sm:px-6 sm:pt-16">
        <Chip>
          <span className="size-1.5 rounded-full bg-status-green" />
          {SEO_PAGE.heroKicker}
        </Chip>
        <h1 className="font-display text-[2.25rem] leading-[1.1] font-extrabold tracking-[-0.01em] text-ink sm:text-[2.75rem]">
          {SEO_PAGE.h1}
        </h1>
        <p className="max-w-2xl text-lg leading-relaxed text-ink-soft">{SEO_PAGE.answer}</p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Button href={MARKETING_CANONICAL_PATHS.install} size="lg">
            Попробовать бесплатно
          </Button>
          <Button href={MARKETING_CANONICAL_PATHS.checkout} size="lg" variant="secondary">
            Выбрать тариф от 99 ₽
          </Button>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-16 sm:px-6">
        <Reveal>
          <SectionHeading
            kicker="POKROV PREMIUM"
            title="VPN для Android и Windows"
            sub="YouTube, TikTok, ChatGPT, соцсети и сайты одной кнопкой. 5 дней бесплатно без карты, затем безлимитный трафик от 99 ₽."
          />
        </Reveal>

        <div className="grid gap-10 lg:grid-cols-[1.6fr_1fr]">
          <Reveal className="flex flex-col gap-8">
            <LongformBlock title="Всё нужное — одной кнопкой">
              <P>
                Скачайте POKROV для Android или Windows, войдите и нажмите «Подключить». YouTube, TikTok, ChatGPT,
                соцсети, мессенджеры и сайты работают через одно приложение — без ручных профилей и копирования ключей.
              </P>
              <P>
                {TELEGRAM_START_PROMISE} Основные тарифы поддерживают до 5 устройств, а решение о продлении остаётся за
                пользователем.
              </P>
            </LongformBlock>

            <LongformBlock title="Что входит в POKROV PREMIUM">
              <P>
                Безлимитный трафик, все доступные платные локации, Android и Windows, до 5 устройств на основных
                тарифах и поддержка в Telegram. Первый полный месяц стоит от 99 ₽, длинные тарифы экономят до 30%.
              </P>
              <P>
                POKROV не ставит тарифный лимит скорости. Фактическая скорость зависит от сети, устройства, выбранной
                локации и текущей нагрузки.
              </P>
            </LongformBlock>

            <LongformBlock title="Сначала 5 дней бесплатно">
              <P>
                Карта не нужна. Установите POKROV и пять дней проверяйте свои обычные сервисы на домашнем Wi-Fi,
                мобильной сети, телефоне и компьютере.
              </P>
              <P>
                После теста выберите платный срок от 99 ₽ или не продлевайте. Оплата разовая,
                автосписаний нет.
              </P>
            </LongformBlock>

            <LongformBlock title="Как скачать VPN безопасно">
              <P>
                Скачивайте POKROV только через официальные поверхности: сайт, кабинет, основной бот или поддержку. Не
                используйте случайные APK, пересланные архивы и «обновлённые версии» из подборок. Для VPN это особенно
                важно: приложение получает сетевой доступ, поэтому источник файла должен быть понятным.
              </P>
              <P>
                Текущая публичная бета рассчитана на Android и Windows. Для Windows файл может показать предупреждение о
                неизвестном издателе. Это стандартное поведение системы для приложений вне магазина.
              </P>
            </LongformBlock>

            <LongformBlock title="Что проверить в первые 5 дней">
              <P>
                Проверьте не только сам факт подключения, а свои обычные сценарии: браузер, YouTube, TikTok, Telegram,
                работу на домашнем Wi-Fi и мобильной сети, поведение после перезапуска устройства. Если что-то не
                работает, напишите в поддержку до оплаты, а не пытайтесь менять настройки вслепую.
              </P>
              <P>
                Если POKROV подходит для повседневных задач, продление идёт через тот же аккаунт, кабинет и официальный
                раздел оплаты. {TELEGRAM_START_PROMISE} Платные планы могут включать несколько устройств в зависимости от
                выбранного срока.
              </P>
            </LongformBlock>
          </Reveal>

          <Reveal className="flex flex-col gap-4" aria-label="Короткая сводка">
            <Card className="flex flex-col gap-1.5">
              <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">На старте</span>
              <h3 className="text-[1.0625rem] font-semibold text-ink">5 дней за 0 ₽</h3>
              <p className="text-[0.9375rem] leading-relaxed text-ink-soft">
                Без карты и автосписаний. Сначала проверка на вашей сети, потом решение о продлении.
              </p>
            </Card>
            <Card className="flex flex-col gap-1.5">
              <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">Устройства</span>
              <h3 className="text-[1.0625rem] font-semibold text-ink">Android + Windows · до 5 устройств</h3>
              <p className="text-[0.9375rem] leading-relaxed text-ink-soft">
                Один аккаунт для телефона и компьютера на основных платных тарифах.
              </p>
            </Card>
            <Card className="flex flex-col gap-3">
              <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">Где скачать</span>
              <h3 className="text-[1.0625rem] font-semibold text-ink">Только официальный путь</h3>
              <p className="text-[0.9375rem] leading-relaxed text-ink-soft">
                Откройте страницу установки и следуйте трём шагам. Файл выдаст кабинет.
              </p>
              <Button href={MARKETING_CANONICAL_PATHS.install}>Открыть установку</Button>
            </Card>
            <Card className="flex flex-col gap-3">
              <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">Сценарии</span>
              <h3 className="text-[1.0625rem] font-semibold text-ink">YouTube, TikTok, Telegram</h3>
              <p className="text-[0.9375rem] leading-relaxed text-ink-soft">
                Для популярных задач есть отдельные страницы с более точным описанием.
              </p>
              <div className="flex flex-wrap gap-2">
                <Link href={MARKETING_CANONICAL_PATHS.youtube} className="text-[0.875rem] font-semibold text-brand no-underline hover:text-brand-strong">
                  YouTube
                </Link>
                <Link href={MARKETING_CANONICAL_PATHS.tiktok} className="text-[0.875rem] font-semibold text-brand no-underline hover:text-brand-strong">
                  TikTok
                </Link>
                <Link href={MARKETING_CANONICAL_PATHS.telegram} className="text-[0.875rem] font-semibold text-brand no-underline hover:text-brand-strong">
                  Telegram
                </Link>
                <Link href={MARKETING_CANONICAL_PATHS.bestVpn} className="text-[0.875rem] font-semibold text-brand no-underline hover:text-brand-strong">
                  Лучший VPN 2026
                </Link>
                <Link href={SEO_PAGE_PATHS.android} className="text-[0.875rem] font-semibold text-brand no-underline hover:text-brand-strong">
                  Android
                </Link>
                <Link href={SEO_PAGE_PATHS.windows} className="text-[0.875rem] font-semibold text-brand no-underline hover:text-brand-strong">
                  Windows
                </Link>
              </div>
            </Card>
          </Reveal>
        </div>
      </section>

      <section className="border-t border-line bg-canvas-alt">
        <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6 sm:py-20">
          <Reveal>
            <SectionHeading
              kicker="Перед стартом"
              title="Всё, что нужно знать перед бесплатными 5 днями"
              sub="Устройства, официальный файл, подключение и условия продления — без поиска по мелкому шрифту."
            />
          </Reveal>
          <Reveal>
            <Accordion items={VPN_FAQ} />
          </Reveal>
          <Reveal className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Button href={config.webappUrl} variant="ghost" target="_blank" rel="noreferrer">
              Кабинет
            </Button>
            <Button href={MARKETING_CANONICAL_PATHS.checkout} variant="secondary">
              Тарифы от 99 ₽
            </Button>
          </Reveal>
        </div>
      </section>

      <FinalCta />
    </PageShell>
  );
}
