import JsonLd from "../../components/json-ld";
import { PageShell } from "../../components/layout/page-shell";
import { buildBreadcrumbJsonLd, buildMarketingMetadata } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";
import { StatusClient } from "./status-client";

export const metadata = buildMarketingMetadata(
  "Статус POKROV и подтверждённые инциденты",
  "Текущий серверный статус POKROV, журнал подтверждённых инцидентов и состояние компенсаций.",
  { path: "/status/" },
);

export default function StatusPage() {
  return (
    <PageShell>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: "/" },
          { name: "Статус", path: "/status/" },
        ])}
      />
      <section className="mx-auto flex max-w-4xl flex-col gap-4 px-4 pt-12 pb-10 sm:px-6 sm:pt-16">
        <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">До входа в аккаунт</span>
        <h1 className="font-display text-[2.25rem] leading-[1.1] font-extrabold tracking-[-0.01em] text-ink">
          Статус и подтверждённые инциденты
        </h1>
        <p className="max-w-3xl text-base leading-relaxed text-ink-soft">
          Открывается без входа. Здесь только серверная правда; состояние туннеля, DNS, HTTPS и маршрутов конкретного
          устройства проверяет приложение.
        </p>
      </section>
      <section className="mx-auto flex max-w-4xl flex-col gap-4 px-4 pb-16 sm:px-6">
        <StatusClient />
      </section>
    </PageShell>
  );
}
