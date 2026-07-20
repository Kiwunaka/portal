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
    headline: "VPN скачать бесплатно: POKROV для Android и Windows",
    inLanguage: "ru-RU",
    dateModified: "2026-07-04",
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
    description:
      "POKROV помогает скачать VPN для Android и Windows, начать с 5 дней бесплатно без карты и проверить подключение до оплаты.",
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
          VPN · ВПН · скачать бесплатно
        </Chip>
        <h1 className="font-display text-[2.25rem] leading-[1.1] font-extrabold tracking-[-0.01em] text-ink sm:text-[2.75rem]">
          POKROV: VPN для Android и Windows
        </h1>
        <p className="max-w-xl text-lg leading-relaxed text-ink-soft">
          Скачайте приложение, включите 5 дней бесплатно и проверьте связь на своих устройствах. Без длинной ручной
          настройки, случайных зеркал и оплаты до первого теста.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <Button href={MARKETING_CANONICAL_PATHS.install} size="lg">
            Скачать POKROV
          </Button>
          <Button href={MARKETING_CANONICAL_PATHS.checkout} size="lg" variant="secondary">
            Посмотреть тарифы
          </Button>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-16 sm:px-6">
        <Reveal>
          <SectionHeading
            kicker="Почему POKROV"
            title="Скачать ВПН и быстро проверить рабочий сценарий"
            sub="Когда человек ищет «VPN скачать бесплатно», ему не нужна лекция о протоколах. Ему нужно быстро поставить приложение, понять, работает ли связь, и не попасть на мутный файл из случайного архива."
          />
        </Reveal>

        <div className="grid gap-10 lg:grid-cols-[1.6fr_1fr]">
          <Reveal className="flex flex-col gap-8">
            <LongformBlock title="POKROV начинается с приложения, а не с инструкции на полчаса">
              <P>
                Многие VPN-страницы обещают «лучший ВПН» и «бесплатно навсегда». На практике пользователю всё равно
                приходится искать правильный файл, разбираться с профилем, читать чужие советы и угадывать, что делать,
                если подключение не поднялось.
              </P>
              <P>
                POKROV держит первый шаг проще: приложение для Android или Windows, бесплатный период на 5 дней, кабинет
                для срока и устройств, поддержка в Telegram. Это не громкое обещание для всех случаев жизни, а нормальный
                способ проверить VPN на своём устройстве до оплаты.
              </P>
            </LongformBlock>

            <LongformBlock title="Как оценивать запрос «лучший VPN»">
              <P>
                В поиске слово «лучший» понятно: хочется не сравнивать десятки сервисов, а сразу выбрать надёжный вариант.
                Но честнее смотреть на признаки, которые можно проверить: есть ли официальный источник скачивания, понятен
                ли бесплатный старт, есть ли поддержка, не заставляют ли платить до первого теста.
              </P>
              <P>
                Поэтому POKROV не строит страницу вокруг крика «мы лучшие». Мы даём сценарий проверки: скачать VPN,
                включить 5 дней бесплатно, открыть нужные сервисы, посмотреть поведение на Android или Windows, а уже
                потом принимать решение о продлении.
              </P>
            </LongformBlock>

            <LongformBlock title="Чем POKROV отличается от типичной бесплатной VPN-страницы">
              <P>
                Здесь нет обещания «бесплатно навсегда без условий». Бесплатный старт нужен, чтобы спокойно проверить
                качество связи. После пробного периода можно выбрать платный срок или остаться на базовом режиме с
                месячным лимитом.
              </P>
              <P>
                Оплата идёт разовым ключом, без автосписаний: заплатили за срок и пользуетесь, никакая подписка не
                продлевается втихую. Мы используем обычный язык, которым люди ищут приложение: «VPN», «ВПН», «скачать»,
                «бесплатно». За этими словами стоит понятный ответ: где скачать, что именно бесплатно и когда писать
                в поддержку.
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
              <h3 className="text-[1.0625rem] font-semibold text-ink">5 дней бесплатно</h3>
              <p className="text-[0.9375rem] leading-relaxed text-ink-soft">
                Без карты. Сначала установка и проверка, потом решение о продлении.
              </p>
            </Card>
            <Card className="flex flex-col gap-1.5">
              <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">Устройства</span>
              <h3 className="text-[1.0625rem] font-semibold text-ink">Android и Windows</h3>
              <p className="text-[0.9375rem] leading-relaxed text-ink-soft">
                Публичная бета сфокусирована на двух основных платформах этой волны.
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
              kicker="FAQ"
              title="Короткие ответы по VPN и POKROV"
              sub="Самое важное перед установкой: бесплатный старт, устройства, ручная настройка и честные ограничения."
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
              Тарифы
            </Button>
          </Reveal>
        </div>
      </section>

      <FinalCta />
    </PageShell>
  );
}
