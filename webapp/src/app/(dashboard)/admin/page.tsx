"use client";

import AppRouteLink from "@/components/app-route-link";
import {
  AdminBadge,
  AdminEmptyState,
  AdminMetricStrip,
  AdminPanelHeader,
  adminButtonClass,
  adminInsetPanelClass,
  adminPanelClass,
} from "@/components/admin/admin-shell";
import { usePortalSession } from "@/lib/session";
import { ADMIN_NAV_GROUPS } from "./nav";

function AdminHomeSkeleton() {
  return (
    <section className="space-y-4" aria-busy="true" aria-live="polite">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="h-24 animate-pulse rounded-[1rem] bg-slate-200" />
        ))}
      </div>
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.35fr),minmax(320px,0.65fr)]">
        <article className="h-[420px] animate-pulse rounded-[1rem] border border-slate-200 bg-white" />
        <article className="h-[420px] animate-pulse rounded-[1rem] border border-slate-200 bg-white" />
      </div>
    </section>
  );
}

export default function AdminHomePage() {
  const { loading } = usePortalSession();

  if (loading) {
    return <AdminHomeSkeleton />;
  }

  const totalLanes = ADMIN_NAV_GROUPS.reduce((sum, group) => sum + group.items.length, 0);

  return (
    <section className="space-y-4">
      <article className={adminPanelClass("neutral")}>
        <AdminPanelHeader
          eyebrow="операторская карта"
          title="Оперативные категории"
          description="Сводка по админке без лишнего шума: какие рабочие зоны открыты, куда идти первым экраном и где лежат очереди по смене."
          actions={
            <AppRouteLink href="/admin/dashboard" className={adminButtonClass("primary", "sm")}>
              Открыть сводку
            </AppRouteLink>
          }
        />
        <div className="flex flex-wrap gap-2">
          <AdminBadge tone="success">Веб-админка — основной операторский интерфейс. Telegram используйте только для быстрых fallback-действий.</AdminBadge>
        </div>
      </article>

      <AdminMetricStrip
        items={[
          {
            label: "Категории",
            value: ADMIN_NAV_GROUPS.length,
            hint: "Крупные рабочие области внутри админки.",
          },
          {
            label: "Активные разделы",
            value: totalLanes,
            hint: "Маршруты, доступные оператору сейчас.",
            tone: "accent",
          },
          {
            label: "Первый экран",
            value: "Сводка",
            hint: "Используйте /admin/dashboard как основную точку входа в смену.",
            tone: "success",
          },
          {
            label: "Режим",
            value: "Utility",
            hint: "Только статусы, очереди, таблицы и действия.",
          },
        ]}
      />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.35fr),minmax(320px,0.65fr)]">
        <section className={adminPanelClass("neutral")}>
          <AdminPanelHeader
            eyebrow="категории"
            title="Каталог рабочих зон"
            description="Слева быстрый обзор по всем admin-направлениям. Открывайте раздел напрямую, если уже знаете тип задачи."
          />

          <div className="space-y-3">
            {ADMIN_NAV_GROUPS.map((group) => (
              <section key={group.id} className={adminInsetPanelClass}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h2 className="text-sm font-semibold text-slate-900">{group.label}</h2>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{group.description}</p>
                  </div>
                  <AdminBadge tone="accent">{group.items.length} экр.</AdminBadge>
                </div>

                {group.items.length ? (
                  <div className="mt-3 overflow-hidden rounded-[0.9rem] border border-slate-200/60">
                    {group.items.map((item, index) => (
                      <AppRouteLink
                        key={item.href}
                        href={item.href}
                        className={`block bg-white/60 px-3 py-3 transition hover:bg-emerald-50/40 ${index > 0 ? "border-t border-slate-200/60" : ""}`}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="material-symbols-rounded text-sm text-slate-500" style={{ fontSize: "16px" }}>
                                {item.icon}
                              </span>
                              <h3 className="text-sm font-semibold text-slate-800">{item.label}</h3>
                            </div>
                            <p className="mt-1 text-xs leading-5 text-slate-500">{item.summary}</p>
                          </div>
                          <span className="text-[11px] font-semibold text-slate-400">Открыть</span>
                        </div>
                      </AppRouteLink>
                    ))}
                  </div>
                ) : (
                  <AdminEmptyState
                    className="mt-3 min-h-[120px]"
                    title="Разделы пока не настроены"
                    description="Для этой категории ещё нет рабочих admin-экранов."
                  />
                )}
              </section>
            ))}
          </div>
        </section>

        <section className="space-y-4">
          <article className={adminPanelClass("neutral")}>
            <AdminPanelHeader
              eyebrow="как заходить в смену"
              title="Порядок просмотра"
              description="Если нет срочного контекста, начинайте с одинаковой последовательности."
            />
            <div className="space-y-2 text-sm">
              {[
                "Сводка: очереди, ошибки, свежесть данных.",
                "Пользователи: точечные кейсы, ручные действия, observer-сигналы.",
                "Сеть: ноды, точки доступа и инфраструктурные тревоги.",
                "Обращения: открытые треды и статус ответа операторов.",
              ].map((line) => (
                <div key={line} className="rounded-[0.9rem] border border-slate-200/60 bg-white/60 px-3 py-2.5 text-slate-700">
                  {line}
                </div>
              ))}
            </div>
          </article>

          <article className={adminPanelClass("neutral")}>
            <AdminPanelHeader
              eyebrow="быстрые переходы"
              title="Частые точки входа"
              description="Переходы на рабочие экраны без лишнего клика через каталог."
            />
            <div className="grid gap-2">
              {[
                { href: "/admin/dashboard", label: "Сводка" },
                { href: "/admin/users", label: "Пользователи" },
                { href: "/admin/nodes", label: "Ноды" },
                { href: "/admin/tickets", label: "Обращения" },
              ].map((item) => (
                <AppRouteLink key={item.href} href={item.href} className={adminButtonClass("secondary", "sm")}>
                  {item.label}
                </AppRouteLink>
              ))}
            </div>
          </article>
        </section>
      </div>
    </section>
  );
}
