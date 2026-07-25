import JsonLd from "../../components/json-ld";
import { PageShell } from "../../components/layout/page-shell";
import { Card } from "../../components/ui/card";
import { buildBreadcrumbJsonLd, buildMarketingMetadata } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND } from "../../lib/pokrov";
import {
  RESPONSIBILITY_MAP,
  ROUTE_TAXONOMY,
  TRUST_CATALOG_LAST_VERIFIED,
  TRUST_CATALOG_VERSION,
} from "../../../../shared/trust-and-guides";

export const metadata = buildMarketingMetadata(
  "Кто за что отвечает | POKROV",
  "Роли POKROV, платёжных и инфраструктурных провайдеров, системных VPN-настроек и сторонних клиентов.",
  { path: "/transparency/" },
);

export default function TransparencyPage() {
  return (
    <PageShell>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: "/" },
          { name: "Прозрачность", path: "/transparency/" },
        ])}
      />
      <section className="mx-auto flex max-w-5xl flex-col gap-4 px-4 pt-12 pb-10 sm:px-6 sm:pt-16">
        <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">
          Версия {TRUST_CATALOG_VERSION} · проверено {TRUST_CATALOG_LAST_VERIFIED}
        </span>
        <h1 className="font-display text-[2.25rem] leading-[1.1] font-extrabold tracking-[-0.01em] text-ink">
          Кто за что отвечает
        </h1>
        <p className="max-w-3xl text-base leading-relaxed text-ink-soft">
          Без формулировки «за всё отвечает VPN». Ниже разделены аккаунт, туннель на устройстве, платёж,
          инфраструктура, распространение приложения и сторонние fallback-клиенты.
        </p>
      </section>

      <section className="mx-auto grid max-w-5xl gap-4 px-4 pb-12 sm:px-6 lg:grid-cols-2">
        {RESPONSIBILITY_MAP.rows.map((row) => (
          <Card key={row.area} className="flex flex-col gap-3">
            <div>
              <p className="text-xs font-semibold tracking-[0.08em] text-brand uppercase">{row.owner}</p>
              <h2 className="mt-1 font-display text-xl font-bold text-ink">{row.area}</h2>
            </div>
            <p className="text-[0.9375rem] leading-relaxed text-ink-soft">{row.responsibility}</p>
            <p className="mt-auto text-sm font-semibold text-ink">Куда идти: {row.contact}</p>
          </Card>
        ))}
      </section>

      <section className="mx-auto flex max-w-5xl flex-col gap-4 px-4 pb-16 sm:px-6">
        <div>
          <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">Маршруты</span>
          <h2 className="mt-2 font-display text-2xl font-bold text-ink">Одинаковые названия во всех интерфейсах</h2>
        </div>
        <div className="overflow-hidden rounded-panel border border-line bg-surface">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] border-collapse text-left text-sm">
              <thead className="bg-canvas-alt text-ink">
                <tr>
                  <th className="px-4 py-3 font-semibold">Режим</th>
                  <th className="px-4 py-3 font-semibold">Куда</th>
                  <th className="px-4 py-3 font-semibold">Состояние</th>
                  <th className="px-4 py-3 font-semibold">Что означает</th>
                </tr>
              </thead>
              <tbody>
                {ROUTE_TAXONOMY.map((row) => (
                  <tr key={row.id} className="border-t border-line align-top">
                    <td className="px-4 py-3 font-semibold text-ink">{row.title}</td>
                    <td className="px-4 py-3 text-ink-soft">{row.direction}</td>
                    <td className="px-4 py-3 text-ink-soft">
                      {row.state === "available" ? "Доступно" : "Исследование"}
                    </td>
                    <td className="px-4 py-3 leading-relaxed text-ink-soft">{row.explanation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        {RESPONSIBILITY_MAP.legal_identity_state === "owner_details_required_before_commercial_publication" ? (
          <Card className="border-line bg-canvas-alt">
            <h2 className="font-display text-lg font-bold text-ink">Открытый юридический пункт</h2>
            <p className="mt-2 text-sm leading-relaxed text-ink-soft">
              Полные реквизиты оператора должны быть опубликованы владельцем в оферте до коммерческого запуска. Мы не
              подставляем вымышленное юрлицо; конкретный платёжный провайдер и продавец также должны быть видны до оплаты
              и в чеке.
            </p>
          </Card>
        ) : null}
      </section>
    </PageShell>
  );
}
