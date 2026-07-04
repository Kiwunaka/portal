import Link from "next/link";

import JsonLd from "../../components/json-ld";
import { PageShell } from "../../components/layout/page-shell";
import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { buildBreadcrumbJsonLd, buildMarketingMetadata, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND, getPokrovPublicConfig } from "../../lib/pokrov";

const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);

export const metadata = buildMarketingMetadata(
  "Политика конфиденциальности | POKROV",
  "Какие данные использует POKROV для работы аккаунта, поддержки и платежей, и как связаться с поддержкой.",
  {
    path: "/privacy/",
    keywords: ["политика конфиденциальности", "privacy pokrov", "данные pokrov"],
  },
);

const LIST_CLASS = "m-0 flex list-disc flex-col gap-2.5 pl-5 text-[0.9375rem] leading-relaxed text-ink-soft";
const LINK_CLASS = "font-semibold text-brand no-underline hover:text-brand-strong";

export default function PrivacyPage() {
  return (
    <PageShell>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: "/" },
          { name: "Политика конфиденциальности", path: "/privacy/" },
        ])}
      />

      <section className="mx-auto flex max-w-3xl flex-col gap-4 px-4 pt-12 pb-10 sm:px-6 sm:pt-16">
        <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">Данные и поддержка</span>
        <h1 className="font-display text-[2.25rem] leading-[1.1] font-extrabold tracking-[-0.01em] text-ink">
          Политика конфиденциальности
        </h1>
        <p className="text-base leading-relaxed text-ink-soft">
          POKROV использует только те данные, которые нужны для работы аккаунта, поддержки, защиты сервиса и проведения
          платежей. Здесь — короткая версия того, что именно мы храним и зачем.
        </p>
      </section>

      <section className="mx-auto flex max-w-3xl flex-col gap-4 px-4 pb-16 sm:px-6">
        <Card className="flex flex-col gap-3">
          <h2 className="font-display text-[1.25rem] font-bold text-ink">Какие данные используются</h2>
          <ul className={LIST_CLASS}>
            <li>Данные аккаунта: идентификатор, срок доступа, активный план и служебные метки для работы продукта.</li>
            <li>
              Технические события: ошибки оплаты, события авторизации, обращения в поддержку и сигналы стабильности
              сервиса.
            </li>
            <li>
              Платёжные события: номер или статус заказа внутри POKROV, выбранный срок, сумма, статус оплаты и отметки
              ручной сверки без хранения карточных данных на стороне POKROV.
            </li>
            <li>Сообщения и файлы, которые пользователь сам отправляет в поддержку.</li>
          </ul>
        </Card>

        <Card className="flex flex-col gap-3">
          <h2 className="font-display text-[1.25rem] font-bold text-ink">Как мы с этим обращаемся</h2>
          <p className="text-[0.9375rem] leading-relaxed text-ink-soft">
            Мы не продаём персональные данные и используем их только там, где это нужно для работы сервиса и обязательных
            расчётов.
          </p>
          <p className="text-[0.9375rem] leading-relaxed text-ink-soft">
            Во время оплачиваемой беты часть платёжной обработки выполняет внешняя платёжная система. Данные передаются
            только в объёме, который нужен для оплаты, возврата, сверки спорного статуса или поддержки пользователя.
          </p>
          <p className="text-[0.9375rem] leading-relaxed text-ink-soft">
            Полезные страницы:{" "}
            <Link href="/" className={LINK_CLASS}>
              главная POKROV
            </Link>
            ,{" "}
            <Link href={MARKETING_CANONICAL_PATHS.youtube} className={LINK_CLASS}>
              YouTube
            </Link>{" "}
            и{" "}
            <Link href={MARKETING_CANONICAL_PATHS.telegram} className={LINK_CLASS}>
              Telegram и поддержка
            </Link>
            .
          </p>
        </Card>

        <Card className="flex flex-col gap-3">
          <h2 className="font-display text-[1.25rem] font-bold text-ink">Контакты</h2>
          <ul className="m-0 flex list-none flex-col gap-2 p-0 text-[0.9375rem] text-ink-soft">
            <li>
              Support:{" "}
              <a href={`mailto:${config.contactEmail}`} className={LINK_CLASS}>
                {config.contactEmail}
              </a>
            </li>
            <li>
              Enterprise:{" "}
              <a href={`mailto:${config.enterpriseEmail}`} className={LINK_CLASS}>
                {config.enterpriseEmail}
              </a>
            </li>
            <li>
              Telegram:{" "}
              <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className={LINK_CLASS}>
                {config.supportTelegramUrl}
              </a>
            </li>
            <li>
              Канал новостей:{" "}
              <a href={config.newsChannelUrl} target="_blank" rel="noreferrer" className={LINK_CLASS}>
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
