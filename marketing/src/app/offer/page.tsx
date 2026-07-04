import Link from "next/link";

import JsonLd from "../../components/json-ld";
import { PageShell } from "../../components/layout/page-shell";
import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { buildBreadcrumbJsonLd, buildMarketingMetadata, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND, getPokrovPublicConfig } from "../../lib/pokrov";

const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);

export const metadata = buildMarketingMetadata(
  "Публичная оферта | POKROV",
  "Базовые условия цифровой подписки POKROV, порядок продления и контакты поддержки.",
  {
    path: "/offer/",
    keywords: ["оферта pokrov", "условия подписки", "pokrov offer"],
  },
);

const LIST_CLASS = "m-0 flex list-disc flex-col gap-2.5 pl-5 text-[0.9375rem] leading-relaxed text-ink-soft";

export default function OfferPage() {
  return (
    <PageShell>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: "/" },
          { name: "Публичная оферта", path: "/offer/" },
        ])}
      />

      <section className="mx-auto flex max-w-3xl flex-col gap-4 px-4 pt-12 pb-10 sm:px-6 sm:pt-16">
        <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">
          Юридическая информация
        </span>
        <h1 className="font-display text-[2.25rem] leading-[1.1] font-extrabold tracking-[-0.01em] text-ink">
          Публичная оферта
        </h1>
        <p className="text-base leading-relaxed text-ink-soft">
          Здесь собраны базовые условия доступа к цифровым услугам POKROV, порядок продления и рабочий способ связаться
          с командой, если нужен разбор спорной ситуации.
        </p>
      </section>

      <section className="mx-auto flex max-w-3xl flex-col gap-4 px-4 pb-16 sm:px-6">
        <Card className="flex flex-col gap-3">
          <h2 className="font-display text-[1.25rem] font-bold text-ink">Основные условия</h2>
          <ul className={LIST_CLASS}>
            <li>Текущая волна — бета-контур с честными ограничениями, а не обещание широкого стабильного запуска.</li>
            <li>
              Сервис предоставляется как цифровой доступ на выбранный срок; автоматическое списание не включается без
              отдельного явного согласия пользователя.
            </li>
            <li>
              Бесплатный тест длится 5 дней, а отдельные режимы доступа могут иметь ограничения по устройствам, функциям
              и доступным файлам приложения.
            </li>
            <li>
              Если продление выдает код активации, его нужно применить в приложении или кабинете, чтобы продолжить тот
              же аккаунт без ручной настройки.
            </li>
            <li>
              Возвраты, отмены, спорные статусы оплаты и ручная сверка рассматриваются через поддержку; итог зависит от
              фактического статуса платежа и уже выданного доступа.
            </li>
          </ul>
        </Card>

        <Card className="flex flex-col gap-3">
          <h2 className="font-display text-[1.25rem] font-bold text-ink">Бета-ограничения</h2>
          <ul className={LIST_CLASS}>
            <li>Android-файл может быть доступен как бета-установка до завершения публикации и финальной проверки.</li>
            <li>Windows может показать предупреждение перед установкой, пока приложение в бете.</li>
            <li>Поддержка отвечает по мере возможности без обещания круглосуточного ответа или фиксированного SLA.</li>
            <li>
              Если оплата, загрузка или активация кода временно остановлены, команда показывает доступное действие
              вместо имитации успешной загрузки или оплаты.
            </li>
          </ul>
        </Card>

        <Card className="flex flex-col gap-3">
          <h2 className="font-display text-[1.25rem] font-bold text-ink">Где смотреть актуальную версию</h2>
          <p className="text-[0.9375rem] leading-relaxed text-ink-soft">
            Актуальные версии документов доступны на сайте, в кабинете и по запросу в поддержку.
          </p>
          <p className="text-[0.9375rem] leading-relaxed text-ink-soft">
            Полезные страницы:{" "}
            <Link href="/" className="font-semibold text-brand no-underline hover:text-brand-strong">
              главная POKROV
            </Link>
            ,{" "}
            <Link
              href={MARKETING_CANONICAL_PATHS.mobile}
              className="font-semibold text-brand no-underline hover:text-brand-strong"
            >
              мобильный старт
            </Link>{" "}
            и{" "}
            <Link
              href={MARKETING_CANONICAL_PATHS.devices}
              className="font-semibold text-brand no-underline hover:text-brand-strong"
            >
              Android и Windows
            </Link>
            .
          </p>
        </Card>

        <Card className="flex flex-col gap-3">
          <h2 className="font-display text-[1.25rem] font-bold text-ink">Контакты</h2>
          <ul className="m-0 flex list-none flex-col gap-2 p-0 text-[0.9375rem] text-ink-soft">
            <li>
              Support:{" "}
              <a href={`mailto:${config.contactEmail}`} className="font-semibold text-brand no-underline hover:text-brand-strong">
                {config.contactEmail}
              </a>
            </li>
            <li>
              Enterprise:{" "}
              <a href={`mailto:${config.enterpriseEmail}`} className="font-semibold text-brand no-underline hover:text-brand-strong">
                {config.enterpriseEmail}
              </a>
            </li>
            <li>
              Telegram:{" "}
              <a
                href={config.supportTelegramUrl}
                target="_blank"
                rel="noreferrer"
                className="font-semibold text-brand no-underline hover:text-brand-strong"
              >
                {config.supportTelegramUrl}
              </a>
            </li>
            <li>
              Канал новостей:{" "}
              <a
                href={config.newsChannelUrl}
                target="_blank"
                rel="noreferrer"
                className="font-semibold text-brand no-underline hover:text-brand-strong"
              >
                {config.newsChannelUrl}
              </a>
            </li>
          </ul>
          <div className="mt-2 flex flex-wrap gap-3">
            <Button href="/" variant="secondary">
              На главную POKROV
            </Button>
            <Button href={config.botUrl} target="_blank" rel="noreferrer">
              Открыть Telegram-бота
            </Button>
          </div>
        </Card>
      </section>
    </PageShell>
  );
}
