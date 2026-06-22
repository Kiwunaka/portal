import AppRouteLink from "@/components/app-route-link";
import { CabinetIcon } from "@/components/cabinet/icon";
import { EmptyState, Timeline } from "@/components/shell-primitives";

export default function DashboardRouteNotFound() {
  return (
    <main className="relative mx-auto flex min-h-[calc(100vh-2rem)] w-[min(96vw,1060px)] items-center justify-center px-4 py-8 sm:px-6 lg:py-10">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,_rgba(11,72,50,0.12),_transparent_34%),radial-gradient(circle_at_bottom_right,_rgba(197,138,42,0.1),_transparent_30%)]" />
      <section className="glass-card w-full overflow-hidden border border-[color:var(--atlas-border)] p-6 dark:border-[#243129]/80 sm:p-8">
        <EmptyState
          icon={<CabinetIcon name="explore_off" className="h-8 w-8" />}
          title="Страница кабинета не найдена"
          description="Такой путь не существует внутри главного кабинета. Вернитесь на старт или откройте поддержку, если пришли по старой ссылке."
          actions={
            <>
              <AppRouteLink href="/dashboard/" className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
                На главную кабинета
              </AppRouteLink>
              <AppRouteLink href="/support/" className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
                В поддержку
              </AppRouteLink>
            </>
          }
        />

        <div className="mt-6 rounded-[1.5rem] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-5 dark:border-white/10 dark:bg-white/[0.04]">
          <Timeline
            items={[
              { title: "Откройте главную кабинета", description: "Главная страница показывает активный доступ, срок и быстрые действия.", tone: "success" },
              { title: "Проверьте путь", description: "Возможно, ссылка в закладке устарела после обновления кабинета.", tone: "warning" },
              { title: "Попросите помощь", description: "Если экран нужен срочно, поддержка подскажет точную ссылку.", tone: "info" },
            ]}
          />
        </div>
      </section>
    </main>
  );
}
