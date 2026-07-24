import JsonLd from "../../components/json-ld";
import { PageShell } from "../../components/layout/page-shell";
import { buildBreadcrumbJsonLd, buildMarketingMetadata } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";
import {
  TRUST_CATALOG_LAST_VERIFIED,
  TRUST_CATALOG_VERSION,
  USER_GUIDES,
} from "../../../../shared/trust-and-guides";
import { GuidesClient } from "./guides-client";

export const metadata = buildMarketingMetadata(
  "Инструкции POKROV | Приложение и fallback-клиенты",
  "Поиск по инструкциям POKROV: все экраны приложения, подключение, DNS, маршруты, восстановление и подробная настройка популярных fallback-клиентов.",
  { path: "/guides/" },
);

export default function GuidesPage() {
  return (
    <PageShell>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: "/" },
          { name: "Инструкции", path: "/guides/" },
        ])}
      />
      <section className="mx-auto flex max-w-5xl flex-col gap-4 px-4 pt-12 pb-10 sm:px-6 sm:pt-16">
        <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">
          {USER_GUIDES.length} задач · версия {TRUST_CATALOG_VERSION} · проверено {TRUST_CATALOG_LAST_VERIFIED}
        </span>
        <h1 className="font-display text-[2.25rem] leading-[1.1] font-extrabold tracking-[-0.01em] text-ink">
          Инструкции по POKROV и запасным клиентам
        </h1>
        <p className="max-w-3xl text-base leading-relaxed text-ink-soft">
          Ищите по задаче, кнопке, платформе или клиенту и фильтруйте по
          категориям. Для POKROV есть отдельный атлас всех текущих экранов с
          реальными снимками. Для семи fallback-клиентов собраны 18 реальных
          экранов, стартовые настройки, назначение кнопок, безопасный порядок
          импорта и честный уровень проверки. Короткие видео добавляются только
          после записи на чистом эмуляторе без личных данных и ссылок.
        </p>
      </section>
      <section className="mx-auto flex max-w-5xl flex-col gap-4 px-4 pb-16 sm:px-6">
        <GuidesClient />
      </section>
    </PageShell>
  );
}
