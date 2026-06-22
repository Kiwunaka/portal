import AppRouteLink from "@/components/app-route-link";
import { CabinetIcon } from "@/components/cabinet/icon";
import { EmptyState, Timeline } from "@/components/shell-primitives";

export default function AdminNotFound() {
  return (
    <main className="relative mx-auto flex min-h-[calc(100vh-2rem)] w-[min(96vw,1060px)] items-center justify-center px-4 py-8 sm:px-6 lg:py-10">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,_rgba(11,72,50,0.12),_transparent_34%),radial-gradient(circle_at_bottom_right,_rgba(197,138,42,0.1),_transparent_30%)]" />
      <section className="glass-card w-full overflow-hidden border border-white/70 p-6 dark:border-[color:var(--atlas-border)] sm:p-8">
        <EmptyState
          icon={<CabinetIcon name="admin_panel_settings" className="h-8 w-8" />}
          title="Раздел админки не найден"
          description="Такого операторского экрана нет в текущей админке POKROV. Вернитесь к сводке или проверьте ссылку."
          actions={
            <>
              <AppRouteLink href="/admin/dashboard" className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
                К сводке
              </AppRouteLink>
              <AppRouteLink href="/dashboard/" className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
                В кабинет
              </AppRouteLink>
            </>
          }
        />

        <div className="mt-6 rounded-[1.5rem] border border-white/70 bg-[color:var(--atlas-surface)] p-5 dark:border-white/10 dark:bg-white/[0.04]">
          <Timeline
            items={[
              { title: "Откройте рабочий стол", description: "Сводка смены показывает тревоги, очереди и свежесть данных.", tone: "success" },
              { title: "Проверьте ссылку", description: "Если вы пришли по старой закладке, маршрут мог измениться.", tone: "warning" },
              { title: "Вернитесь в кабинет", description: "Кабинет остается отдельным пользовательским маршрутом.", tone: "info" },
            ]}
          />
        </div>
      </section>
    </main>
  );
}
