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
      <section className="mx-auto flex max-w-5xl flex-col gap-4 px-4 pt-10 pb-8 sm:px-6 sm:pt-14">
        <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">
          Помощь по задаче · {USER_GUIDES.length} готовых инструкций
        </span>
        <h1 className="max-w-3xl font-display text-[2.25rem] leading-[1.1] font-extrabold tracking-[-0.01em] text-ink">
          Найдите ответ, а не читайте всё подряд
        </h1>
        <p className="max-w-2xl text-base leading-relaxed text-ink-soft">
          Введите название кнопки или проблему. Откройте только нужную карточку
          — шаги, снимки и восстановление спрятаны внутри.
        </p>
        <details className="max-w-3xl rounded-control border border-line bg-canvas-alt px-4 py-3 text-sm text-ink-soft">
          <summary className="min-h-8 cursor-pointer font-semibold text-ink">
            Что есть в справочнике
          </summary>
          <p className="mt-2 leading-6">
            Отдельный атлас экранов POKROV, инструкции по Android и Windows,
            настройка запасных клиентов и честные ветки «если не получилось».
            Версия каталога {TRUST_CATALOG_VERSION}; проверено {TRUST_CATALOG_LAST_VERIFIED}.
          </p>
        </details>
      </section>
      <section className="mx-auto flex max-w-5xl flex-col gap-4 px-4 pb-16 sm:px-6">
        <GuidesClient />
      </section>
    </PageShell>
  );
}
